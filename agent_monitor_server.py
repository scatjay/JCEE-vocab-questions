#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
agent_monitor_server.py — 代理人工作現況監看台（2026-09-14）
================================================================================
照社群輿情線 control_server.py 的做法：本機 HTTP server，只用標準庫，
綁 0.0.0.0 讓 Tailscale 網段連得到（手機/外出時能看），但只接受
127.x 與 Tailscale 的 100.64.0.0/10，其他來源一律 403——不會因為連到
公共 Wi-Fi 就把監看台曝露出去。

資料來源（全部唯讀，這支不寫任何檔案）：
  - .claude/agents/_runlog.jsonl   黑板：各代理人跑完寫的事件列
  - docs/PLAN.md                    WP 狀態標記（⬜/🟨/✅）
  - kb/*.md                         每隻代理人的知識庫累積了幾筆
  - ~/.claude/audit/subagent_spawns.jsonl  全機 spawn 帳本（today 用量）
"""
import ipaddress
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(HERE, ".claude", "agents")
BLACKBOARD = os.path.join(AGENTS_DIR, "_runlog.jsonl")
PLAN_MD = os.path.join(HERE, "docs", "PLAN.md")
KB_DIR = os.path.join(AGENTS_DIR, "kb")
AUDIT_SPAWNS = os.path.expanduser(r"~\.claude\audit\subagent_spawns.jsonl")
PORT = 8792

TS_NET = ipaddress.ip_network("100.64.0.0/10")  # Tailscale CGNAT 網段
WP_LINE = re.compile(r"^###\s+([⬜🟨✅])\s+(WP-\d+[^\n（(]*)")
FM_NAME = re.compile(r"^name:\s*(\S+)", re.MULTILINE)
FM_TOOLS_INLINE = re.compile(r"^tools:[ \t]*(.*)$", re.MULTILINE)
FM_TOOLS_LIST_ITEM = re.compile(r"^\s*-\s*(\S+)\s*$", re.MULTILINE)

ALL_TOOLS = ["Read", "Grep", "Glob", "Bash", "Write", "Edit", "WebSearch", "WebFetch"]

sys.path.insert(0, HERE)
import intent_ledger  # noqa: E402  （同目錄；縮小版意圖對帳，見該檔檔頭說明）

# 五棒循環 + 領域專家分組（給前端關聯圖用，agent 名字 → 圖上的節點 id）
STAGE_NODE = {
    "cycle-ideator": "ideator", "cycle-designer": "designer",
    "cycle-builder": "builder", "cycle-evaluator": "evaluator", "cycle-fixer": "fixer",
}
EXPERT_NAMES = {"english-teacher", "learning-scientist", "assessment-expert",
                "game-designer", "ux-designer", "red-team-critic"}


def allowed(ip):
    try:
        a = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return a.is_loopback or a in TS_NET


def _jread_lines(path):
    """逐行讀 jsonl，壞掉的行跳過不炸（黑板是別的進程在寫，讀到寫一半的行要容忍）。"""
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def wp_status():
    """從 PLAN.md 抓每個 WP 的狀態標記。抓不到檔案就回空清單，不炸頁面。"""
    if not os.path.exists(PLAN_MD):
        return []
    rows = []
    with open(PLAN_MD, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = WP_LINE.match(line)
            if m:
                icon, title = m.group(1), m.group(2).strip()
                rows.append({"icon": icon, "title": title})
    return rows


def agent_roster():
    """全部代理人的名字（從 .claude/agents/*.md 的 frontmatter name: 讀），
    不含 README.md/kb/ 這種非代理人檔案。這是『十四隻都要看得到』的依據——
    KB 圖表不能只列已經有檔案的那幾隻，沒開始寫的也要看得見『還沒開始』。"""
    out = []
    if not os.path.isdir(AGENTS_DIR):
        return out
    for fn in sorted(os.listdir(AGENTS_DIR)):
        if not fn.endswith(".md"):
            continue
        p = os.path.join(AGENTS_DIR, fn)
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                head = f.read(400)
            m = FM_NAME.search(head)
            if m:
                out.append(m.group(1))
        except OSError:
            continue
    return out


def kb_status():
    """每隻代理人的 KB 累積量——沒有檔案的也列出來（0行），
    這樣『還沒開始寫』本身就是一個看得見的資訊，不是被省略掉。"""
    out = []
    for name in agent_roster():
        p = os.path.join(KB_DIR, name + ".md")
        lines, revoked = 0, 0
        if os.path.exists(p):
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    ls = f.readlines()
                lines = len(ls)
                revoked = sum(1 for l in ls if "已被" in l and "推翻" in l)
            except OSError:
                pass
        out.append({"agent": name, "lines": lines, "revoked": revoked})
    out.sort(key=lambda r: -r["lines"])
    return out


def blackboard_feed(n=40):
    rows = _jread_lines(BLACKBOARD)
    rows.sort(key=lambda r: r.get("ts", ""), reverse=True)
    return rows[:n]


def tools_matrix():
    """每隻代理人 frontmatter 的 tools: 欄位——工具庫清單＋誰拿了什麼。

    tools: 兩種寫法都要吃：YAML 清單（下面接 `- Read` 這種行）跟單行逗號版
    （tools: Read, Grep, Glob）。省略這個欄位＝預設拿全部工具，這裡老實標出來，
    不要讓『沒寫』看起來像『沒有工具』。"""
    out = []
    for fn in sorted(os.listdir(AGENTS_DIR)) if os.path.isdir(AGENTS_DIR) else []:
        if not fn.endswith(".md"):
            continue
        p = os.path.join(AGENTS_DIR, fn)
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                head = f.read(1200)
        except OSError:
            continue
        nm = FM_NAME.search(head)
        if not nm:
            continue  # README.md/_DOMAIN.md 這類非代理人檔案，沒有 name: 就跳過
        name = nm.group(1)
        tm = FM_TOOLS_INLINE.search(head)
        tools = []
        val = tm.group(1).strip() if tm else ""
        if val and val != "|" and "," in val:
            tools = [t.strip() for t in val.split(",") if t.strip()]
        elif val and val != "|":
            tools = [val]
        else:
            # YAML 清單版：tools: 那行本身是空的，工具名在接下來的 `- Xxx` 行
            after = head[tm.end():] if tm else head
            stop = min([i for i in
                        (after.find("\n---"), after.find("\nmodel:"))
                        if i != -1] or [len(after)])
            tools = FM_TOOLS_LIST_ITEM.findall(after[:stop])
        out.append({"agent": name, "tools": tools or ["(未寫＝預設全部工具)"],
                    "unrestricted": not tools})
    out.sort(key=lambda r: r["agent"])
    return out


def invocation_stats():
    """全黑板（不只最近40筆）依代理人聚合：呼叫次數、最後一次時間。
    這是『觸發現況』誠實能給的資料——黑板記的是每次任務完成後的一列，
    不是逐次工具呼叫，細到『這隻用了幾次Bash』需要另外解析子代理逐字稿，
    目前沒做，不假裝有。"""
    rows = _jread_lines(BLACKBOARD)
    agg = {}
    for r in rows:
        a = r.get("agent")
        if not a:
            continue
        d = agg.setdefault(a, {"agent": a, "n": 0, "last_ts": None,
                                "ok": 0, "proposed": 0, "blocked": 0, "failed": 0})
        d["n"] += 1
        oc = r.get("outcome")
        if oc in ("ok", "proposed", "blocked", "failed"):
            d[oc] += 1
        if not d["last_ts"] or (r.get("ts") or "") > d["last_ts"]:
            d["last_ts"] = r.get("ts")
    out = list(agg.values())
    out.sort(key=lambda r: -r["n"])
    return out


def intent_summary():
    try:
        board = intent_ledger.load_board()
    except RuntimeError:
        return {"needs_human_未結案": [], "proposed_未結案": []}
    return intent_ledger.build(board)


def spawn_today():
    """今日全機 spawn 次數，依線分——跟 guard-subagent-budget.py 認的帳本同一份。"""
    rows = _jread_lines(AUDIT_SPAWNS)
    today = datetime.now().astimezone().strftime("%Y-%m-%d")
    by_line = {}
    total = 0
    for r in rows:
        ts = r.get("ts") or r.get("time") or ""
        if not ts.startswith(today):
            continue
        line = r.get("line") or r.get("cwd") or "?"
        line = os.path.basename(str(line).rstrip("\\/"))
        by_line[line] = by_line.get(line, 0) + 1
        total += 1
    return {"total": total, "by_line": by_line}


def state():
    feed = blackboard_feed()
    return {
        "at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "wp": wp_status(),
        "kb": kb_status(),
        "feed": feed,
        "spawn": spawn_today(),
        "latest_agent": feed[0]["agent"] if feed else None,
        "latest_ts": feed[0].get("ts") if feed else None,
        "tools": tools_matrix(),
        "all_tools": ALL_TOOLS,
        "invocations": invocation_stats(),
        "intent": intent_summary(),
    }


PAGE = r"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<title>代理人現況 · JCEE</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
<style>
 :root{
   --paper:#fdfdfb; --card:#ffffff; --sunk:rgba(34,64,94,0.04);
   --ink:#22405e; --muted:#5a6470; --soft:#8a929c;
   --rule:rgba(34,64,94,0.14); --rule-solid:#dfe5ec;
   --accent:#cb4b16; --link:#3f6184;
   --good:#2f7d4f; --good-bg:#e7f2ec; --warn:#b7791f; --warn-bg:#faf1de; --bad:#a83a2e; --bad-bg:#f9e8e5;
 }
 *{box-sizing:border-box}
 body{background:var(--paper);color:var(--ink);margin:0;padding:2.2rem 1.6rem 4rem;
   font-family:'Geist','Noto Sans TC',sans-serif;font-size:17px;line-height:1.7;
   max-width:1080px;margin-inline:auto}
 .eyebrow{font-family:'Geist Mono','Noto Sans TC',monospace;font-size:12px;
   letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 .4rem}
 h1{font-family:'Instrument Serif',serif;font-size:2.1rem;font-weight:400;margin:0 0 .3rem}
 .sub{color:var(--muted);font-size:1rem;margin:0 0 1.6rem;max-width:62ch}
 .sub b{color:var(--ink);font-weight:600}
 h2{font-family:'Geist Mono','Noto Sans TC',monospace;font-size:.95rem;color:var(--ink);
   text-transform:uppercase;letter-spacing:.07em;margin:2.4rem 0 .9rem;
   border-bottom:2px solid var(--rule-solid);padding-bottom:.5rem;display:flex;
   align-items:baseline;gap:.6rem}
 h2 small{font-family:'Geist','Noto Sans TC',sans-serif;text-transform:none;
   letter-spacing:0;color:var(--soft);font-size:.72rem;font-weight:400}
 .diagram-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;border-radius:8px}
 .diagram-scroll svg{min-width:640px}
 .scroll-hint{display:none;font-size:.76rem;color:var(--soft);margin:0 0 .5rem;
   font-family:'Geist Mono',monospace}
 svg{max-width:100%;height:auto;display:block}
 figcaption{font-size:.86rem;color:var(--muted);margin-top:.6rem;max-width:70ch}

 /* WP 進度：橫向段落，取代文字清單 */
 .wp-track{display:flex;gap:6px;flex-wrap:wrap}
 .wp-seg{flex:1 1 100px;min-width:100px;background:var(--card);border:1.5px solid var(--rule-solid);
   border-radius:8px;padding:.7rem .8rem;position:relative}
 .wp-seg.done{border-color:var(--good);background:var(--good-bg)}
 .wp-seg.doing{border-color:var(--warn);background:var(--warn-bg)}
 .wp-seg .num{font-family:'Geist Mono',monospace;font-size:.7rem;color:var(--soft);letter-spacing:.06em}
 .wp-seg.done .num{color:var(--good)}
 .wp-seg.doing .num{color:var(--warn)}
 .wp-seg .t{font-size:.86rem;margin-top:.15rem;line-height:1.35;color:var(--ink)}
 .wp-legend{display:flex;gap:1.4rem;margin-top:.7rem;font-size:.82rem;color:var(--muted)}
 .wp-legend span{display:inline-flex;align-items:center;gap:.35rem}
 .sw{width:11px;height:11px;border-radius:3px;display:inline-block}
 .sw.done{background:var(--good)} .sw.doing{background:var(--warn)} .sw.todo{background:var(--rule-solid)}

 /* KB 長條圖 */
 .kb-rows{display:grid;gap:5px}
 .kb-row{display:grid;grid-template-columns:150px 1fr 70px;gap:.8rem;align-items:center}
 .kb-row .nm{font-family:'Geist Mono',monospace;font-size:.82rem;color:var(--ink);
   overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 .kb-row.zero .nm{color:var(--soft)}
 .kb-row .track{height:16px;background:var(--sunk);border-radius:4px;overflow:hidden;
   border:1px solid var(--rule)}
 .kb-row .fill{height:100%;background:var(--accent);opacity:.7;border-radius:4px 0 0 4px}
 .kb-row.zero .track{border-style:dashed}
 .kb-row .n{font-family:'Geist Mono',monospace;font-size:.78rem;color:var(--muted);text-align:right}
 .kb-row .n b{color:var(--bad)}

 /* spawn */
 .spawn{background:var(--card);border:1px solid var(--rule-solid);border-radius:8px;
   padding:1rem 1.2rem}
 .spawn .line1{font-size:.92rem;color:var(--muted)}
 .spawn .line1 b{color:var(--ink);font-family:'Geist Mono',monospace}
 .spawn .bar{height:11px;background:var(--sunk);border:1px solid var(--rule);border-radius:5px;
   overflow:hidden;margin:.6rem 0}
 .spawn .bar i{display:block;height:100%;background:var(--accent);opacity:.75}
 .spawn .breakdown{display:flex;gap:1.1rem;flex-wrap:wrap;font-size:.82rem;color:var(--soft)}
 .spawn .breakdown b{color:var(--ink)}

 /* feed */
 .feed{display:grid;gap:5px}
 .ev{background:var(--card);border:1px solid var(--rule-solid);border-radius:8px;
   padding:.65rem .95rem;font-size:.88rem;display:grid;grid-template-columns:auto 1fr auto;
   gap:.7rem;align-items:baseline}
 .ev .agent{font-family:'Geist Mono',monospace;font-weight:600;color:var(--link);white-space:nowrap}
 .ev .task{color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 .ev .ts{font-family:'Geist Mono',monospace;font-size:.72rem;color:var(--soft);white-space:nowrap}
 .pill{display:inline-block;font-family:'Geist Mono',monospace;font-size:.68rem;padding:.05rem .5rem;
   border-radius:99px;margin-left:.4rem}
 .pill.ok{background:var(--good-bg);color:var(--good)}
 .pill.proposed{background:var(--warn-bg);color:var(--warn)}
 .pill.blocked,.pill.failed{background:var(--bad-bg);color:var(--bad)}
 .empty{color:var(--soft);font-size:.9rem;font-style:italic;padding:.6rem 0}

 /* 工具能力矩陣 */
 .matrix-wrap{overflow-x:auto;border:1px solid var(--rule-solid);border-radius:8px;background:var(--card)}
 table.matrix{border-collapse:collapse;font-size:.82rem;width:100%}
 table.matrix th, table.matrix td{padding:.5rem .6rem;text-align:center;border-bottom:1px solid var(--rule)}
 table.matrix th{font-family:'Geist Mono',monospace;font-size:.7rem;color:var(--muted);
   text-transform:uppercase;letter-spacing:.05em;white-space:nowrap}
 table.matrix td.nm{text-align:left;font-family:'Geist Mono',monospace;font-size:.8rem;
   color:var(--ink);white-space:nowrap}
 table.matrix td.yes{color:var(--accent);font-weight:700}
 table.matrix td.no{color:var(--rule-solid)}
 .unrestricted{font-size:.68rem;color:var(--warn);margin-left:.3rem}

 /* 觸發統計 */
 .inv-rows{display:grid;gap:5px}
 .inv-row{display:grid;grid-template-columns:150px 1fr 90px 120px;gap:.7rem;align-items:center;font-size:.85rem}
 .inv-row .nm{font-family:'Geist Mono',monospace;color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 .inv-row .track{height:14px;background:var(--sunk);border:1px solid var(--rule);border-radius:4px;overflow:hidden}
 .inv-row .fill{height:100%;background:var(--link);opacity:.7}
 .inv-row .n{font-family:'Geist Mono',monospace;font-size:.78rem;color:var(--muted);text-align:right}
 .inv-row .last{font-family:'Geist Mono',monospace;font-size:.72rem;color:var(--soft);white-space:nowrap}

 /* 意圖對帳 */
 .intent-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
 @media(max-width:720px){.intent-grid{grid-template-columns:1fr}}
 .intent-col h3{font-family:'Geist Mono',monospace;font-size:.78rem;color:var(--muted);
   text-transform:uppercase;letter-spacing:.05em;margin:0 0 .5rem}
 .intent-card{background:var(--card);border:1px solid var(--warn);border-left-width:3px;
   border-radius:6px;padding:.6rem .85rem;margin-bottom:6px;font-size:.83rem}
 .intent-card .who{font-family:'Geist Mono',monospace;font-weight:600;color:var(--ink)}
 .intent-card .age{float:right;font-family:'Geist Mono',monospace;font-size:.72rem;color:var(--warn)}
 .intent-card .txt{color:var(--muted);margin-top:.2rem;display:block}
 footer{margin-top:2.6rem;padding-top:1rem;border-top:1px solid var(--rule);
   font-family:'Geist Mono',monospace;font-size:.72rem;color:var(--soft)}

 /* 手機（≤640px）：間距收緊、長條圖行改兩行式排版、圖表提示橫滑 */
 @media (max-width:640px){
   body{padding:1.2rem .9rem 3rem;font-size:15.5px}
   h1{font-size:1.55rem}
   .sub{font-size:.9rem}
   h2{font-size:.82rem;margin:1.9rem 0 .7rem;gap:.4rem;flex-wrap:wrap}
   h2 small{font-size:.66rem}
   .scroll-hint{display:block}
   .wp-seg{flex:1 1 84px;min-width:84px;padding:.55rem .6rem}
   .wp-seg .t{font-size:.78rem}
   .wp-legend{gap:.9rem;font-size:.76rem}

   .kb-row{grid-template-columns:88px 1fr 46px;gap:.5rem}
   .kb-row .nm{font-size:.74rem}
   .kb-row .n{font-size:.7rem}

   /* 觸發統計在手機上改兩行：第一行 名字+次數，第二行 長條，避免四欄擠爆 */
   .inv-row{grid-template-columns:1fr auto;grid-template-rows:auto auto;
     row-gap:.25rem;column-gap:.5rem;padding:.5rem .1rem;border-bottom:1px solid var(--rule-solid)}
   .inv-row .nm{font-size:.8rem;grid-column:1;grid-row:1}
   .inv-row .n{font-size:.76rem;grid-column:2;grid-row:1;text-align:right}
   .inv-row .track{grid-column:1/-1;grid-row:2}
   .inv-row .last{grid-column:1/-1;grid-row:3;text-align:left;font-size:.68rem}

   table.matrix th,table.matrix td{padding:.4rem .45rem;font-size:.74rem}
   .intent-card{font-size:.78rem;padding:.5rem .7rem}
   .ev{grid-template-columns:1fr;row-gap:.15rem}
   .ev .ts{justify-self:start}
   .spawn .breakdown{gap:.6rem 1rem;font-size:.76rem}
 }
</style></head>
<body>
  <p class="eyebrow">JCEE-vocab-questions · 代理人監看台</p>
  <h1>誰在做什麼</h1>
  <p class="sub">十四隻代理人的分工關係與現在的資料流。<b id="at">—</b> 更新，每 6 秒重抓一次。</p>

  <h2>分工與資料流</h2>
  <figure>
    <p class="scroll-hint">← 左右滑動看全圖 →</p>
    <div class="diagram-scroll">
    <svg id="diagram" viewBox="0 0 960 480" role="img"
      aria-label="六位領域專家為設計與評估兩棒提供意見；五棒循環（構思、設計、建置、評估、修正）依序推進；
      每棒完成後把事件寫進黑板；wp-manager讀黑板與規格後向主線建議下一步；mutator獨立於循環外，向設計棒提出挑戰性提案">
      <defs>
        <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="#5a6470"/>
        </marker>
        <marker id="arr-accent" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="#cb4b16"/>
        </marker>
        <pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse">
          <circle cx="10" cy="10" r="0.8" fill="rgba(34,64,94,0.10)"/>
        </pattern>
      </defs>
      <rect width="960" height="480" fill="#fdfdfb"/>
      <rect width="960" height="480" fill="url(#dots)" opacity="0.6"/>

      <!-- 泳道分隔與標籤 -->
      <g font-family="Geist Mono,monospace" font-size="10" letter-spacing="0.1em" fill="#8a929c">
        <line x1="0" y1="112" x2="960" y2="112" stroke="rgba(34,64,94,0.14)"/>
        <line x1="0" y1="228" x2="960" y2="228" stroke="rgba(34,64,94,0.14)"/>
        <line x1="0" y1="316" x2="960" y2="316" stroke="rgba(34,64,94,0.14)"/>
        <text x="16" y="30">領域專家</text>
        <text x="16" y="150">五棒循環</text>
        <text x="16" y="248">共用事件帳本</text>
        <text x="16" y="336">監督與突變</text>
      </g>

      <!-- Lane 0：六位領域專家 -->
      <g data-node="experts">
        <rect x="220" y="20" width="520" height="76" rx="10" fill="#ffffff" stroke="#5a6470" stroke-width="1.4"/>
        <text x="480" y="44" text-anchor="middle" font-family="Geist,'Noto Sans TC'" font-size="13" font-weight="600" fill="#22405e">六位領域專家</text>
        <text x="480" y="63" text-anchor="middle" font-family="Geist Mono,monospace" font-size="9.5" fill="#5a6470">learning-scientist · assessment-expert · game-designer</text>
        <text x="480" y="77" text-anchor="middle" font-family="Geist Mono,monospace" font-size="9.5" fill="#5a6470">ux-designer · english-teacher · red-team-critic</text>
        <line x1="400" y1="96" x2="330" y2="126" stroke="#5a6470" stroke-dasharray="3 3" marker-end="url(#arr)"/>
        <line x1="560" y1="96" x2="700" y2="126" stroke="#5a6470" stroke-dasharray="3 3" marker-end="url(#arr)"/>
        <rect x="290" y="100" width="60" height="16" rx="3" fill="#fdfdfb"/>
        <text x="320" y="112" text-anchor="middle" font-family="Geist Mono,monospace" font-size="8.5" fill="#8a929c">審查意見</text>
      </g>

      <!-- Lane 1：五棒循環 -->
      <g font-family="Geist,'Noto Sans TC'" font-size="13" font-weight="600" text-anchor="middle" fill="#22405e">
        <g data-node="ideator">
          <rect x="40" y="128" width="150" height="60" rx="8" fill="#ffffff" stroke="#5a6470" stroke-width="1.4"/>
          <text x="115" y="153">構思</text>
          <text x="115" y="171" font-family="Geist Mono,monospace" font-size="9" font-weight="400" fill="#8a929c">cycle-ideator</text>
        </g>
        <g data-node="designer">
          <rect x="230" y="128" width="150" height="60" rx="8" fill="#ffffff" stroke="#cb4b16" stroke-width="1.8"/>
          <text x="305" y="153">設計</text>
          <text x="305" y="171" font-family="Geist Mono,monospace" font-size="9" font-weight="400" fill="#8a929c">cycle-designer</text>
        </g>
        <g data-node="builder">
          <rect x="420" y="128" width="150" height="60" rx="8" fill="#ffffff" stroke="#5a6470" stroke-width="1.4"/>
          <text x="495" y="153">建置</text>
          <text x="495" y="171" font-family="Geist Mono,monospace" font-size="9" font-weight="400" fill="#8a929c">cycle-builder</text>
        </g>
        <g data-node="evaluator">
          <rect x="610" y="128" width="150" height="60" rx="8" fill="#ffffff" stroke="#cb4b16" stroke-width="1.8"/>
          <text x="685" y="153">評估</text>
          <text x="685" y="171" font-family="Geist Mono,monospace" font-size="9" font-weight="400" fill="#8a929c">cycle-evaluator</text>
        </g>
        <g data-node="fixer">
          <rect x="770" y="128" width="150" height="60" rx="8" fill="#ffffff" stroke="#5a6470" stroke-width="1.4"/>
          <text x="845" y="153">修正</text>
          <text x="845" y="171" font-family="Geist Mono,monospace" font-size="9" font-weight="400" fill="#8a929c">cycle-fixer</text>
        </g>
      </g>
      <line x1="190" y1="158" x2="228" y2="158" stroke="#5a6470" marker-end="url(#arr)"/>
      <line x1="380" y1="158" x2="418" y2="158" stroke="#5a6470" marker-end="url(#arr)"/>
      <line x1="570" y1="158" x2="608" y2="158" stroke="#5a6470" marker-end="url(#arr)"/>
      <line x1="760" y1="158" x2="768" y2="158" stroke="#5a6470" marker-end="url(#arr)"/>
      <path d="M 845,126 C 845,100 305,100 305,126" fill="none" stroke="#8a929c" stroke-dasharray="3 3" marker-end="url(#arr)"/>
      <text x="575" y="104" text-anchor="middle" font-family="Geist Mono,monospace" font-size="8.5" fill="#8a929c">要改設計才退回</text>

      <!-- Lane 2：黑板 -->
      <g data-node="blackboard">
        <rect x="40" y="240" width="880" height="60" rx="8" fill="#ffffff" stroke="#5a6470" stroke-width="1.4"/>
        <text x="480" y="266" text-anchor="middle" font-family="Geist,'Noto Sans TC'" font-size="13" font-weight="600" fill="#22405e">黑板　_runlog.jsonl</text>
        <text x="480" y="284" text-anchor="middle" font-family="Geist Mono,monospace" font-size="9.5" fill="#5a6470">只增不改 · 誰都能讀 · 不准互相呼叫，只准留言</text>
      </g>
      <line x1="115" y1="188" x2="115" y2="238" stroke="#5a6470" marker-end="url(#arr)"/>
      <line x1="305" y1="188" x2="305" y2="238" stroke="#5a6470" marker-end="url(#arr)"/>
      <line x1="495" y1="188" x2="495" y2="238" stroke="#5a6470" marker-end="url(#arr)"/>
      <line x1="685" y1="188" x2="685" y2="238" stroke="#5a6470" marker-end="url(#arr)"/>
      <line x1="845" y1="188" x2="845" y2="238" stroke="#5a6470" marker-end="url(#arr)"/>

      <!-- Lane 3：wp-manager / 主線 / mutator -->
      <g data-node="wp-manager">
        <rect x="150" y="330" width="190" height="72" rx="8" fill="#ffffff" stroke="#cb4b16" stroke-width="1.8"/>
        <text x="245" y="358" text-anchor="middle" font-family="Geist,'Noto Sans TC'" font-size="13" font-weight="600" fill="#22405e">wp-manager</text>
        <text x="245" y="376" text-anchor="middle" font-family="Geist Mono,monospace" font-size="9" fill="#5a6470">讀黑板 · 建議下一步</text>
        <text x="245" y="390" text-anchor="middle" font-family="Geist Mono,monospace" font-size="9" fill="#8a929c">無 Agent 工具</text>
      </g>
      <line x1="480" y1="300" x2="245" y2="328" stroke="#5a6470" marker-end="url(#arr)"/>

      <g data-node="main">
        <rect x="410" y="330" width="180" height="72" rx="8" fill="#f2f5f9" stroke="#22405e" stroke-width="1.6"/>
        <text x="500" y="358" text-anchor="middle" font-family="Geist,'Noto Sans TC'" font-size="13" font-weight="600" fill="#22405e">主線</text>
        <text x="500" y="376" text-anchor="middle" font-family="Geist Mono,monospace" font-size="9" fill="#5a6470">實際 spawn 的一方</text>
      </g>
      <line x1="340" y1="360" x2="408" y2="360" stroke="#cb4b16" stroke-width="1.6" marker-end="url(#arr-accent)"/>
      <text x="375" y="349" text-anchor="middle" font-family="Geist Mono,monospace" font-size="8" fill="#cb4b16">建議</text>
      <path d="M 500,328 C 500,220 115,220 115,190" fill="none" stroke="#8a929c" stroke-dasharray="3 3" marker-end="url(#arr)"/>

      <g data-node="mutator">
        <rect x="650" y="330" width="180" height="72" rx="8" fill="#ffffff" stroke="#5a6470" stroke-width="1.4" stroke-dasharray="5 3"/>
        <text x="740" y="358" text-anchor="middle" font-family="Geist,'Noto Sans TC'" font-size="13" font-weight="600" fill="#22405e">mutator</text>
        <text x="740" y="376" text-anchor="middle" font-family="Geist Mono,monospace" font-size="9" fill="#5a6470">只提案，不動手</text>
        <text x="740" y="390" text-anchor="middle" font-family="Geist Mono,monospace" font-size="9" fill="#8a929c">outcome=proposed</text>
      </g>
      <path d="M 700,328 C 700,240 400,158 382,150" fill="none" stroke="#8a929c" stroke-dasharray="3 3" marker-end="url(#arr)"/>
      <text x="560" y="215" text-anchor="middle" font-family="Geist Mono,monospace" font-size="8" fill="#8a929c">挑戰已定案決策</text>

      <!-- 現正活動指示（JS 動態插入） -->
      <g id="live-badge" style="display:none">
        <circle r="5" fill="#cb4b16"><animate attributeName="r" values="5;7;5" dur="1.6s" repeatCount="indefinite"/></circle>
      </g>
    </svg>
    </div>
    <figcaption id="diagram-caption">六位領域專家在設計、評估兩棒插話；每棒完成寫進黑板；<code>wp-manager</code> 讀黑板向主線建議下一步；<code>mutator</code> 獨立在外挑戰已定案決策。橘框＝目前最新一筆事件所在的位置。</figcaption>
  </figure>

  <h2>工作包進度 <small>docs/PLAN.md</small></h2>
  <div class="wp-track" id="wp"></div>
  <div class="wp-legend">
    <span><i class="sw done"></i>已完成</span>
    <span><i class="sw doing"></i>進行中</span>
    <span><i class="sw todo"></i>未開始</span>
  </div>

  <h2>知識庫累積量 <small>kb/*.md，14 隻代理人全列</small></h2>
  <div class="kb-rows" id="kb"></div>

  <h2>工具庫 <small>誰拿了什麼工具，frontmatter tools: 欄位</small></h2>
  <div class="matrix-wrap"><table class="matrix" id="matrix"></table></div>

  <h2>觸發統計 <small>黑板全量聚合，非逐次工具呼叫（那要解析逐字稿，暫未做）</small></h2>
  <div class="inv-rows" id="inv"></div>

  <h2>意圖對帳 <small>intent_ledger.py：黑板上還沒結案的球</small></h2>
  <div class="intent-grid">
    <div class="intent-col"><h3>needs_human 未結案</h3><div id="intent-nh"></div></div>
    <div class="intent-col"><h3>proposed 待批</h3><div id="intent-pr"></div></div>
  </div>

  <h2>Spawn 預算 <small>全機共用，公路車／課程管理與備課同一個帳本</small></h2>
  <div class="spawn" id="spawn"></div>

  <h2>黑板最新動態</h2>
  <div class="feed" id="feed"></div>

  <footer>E:\Downloads\JCEE-vocab-questions · 只接受本機與 Tailscale 來源 · 樣式沿用 social-echo-chamber-research 監控前台</footer>

<script>
const STAGE_OF = {
  "cycle-ideator":"ideator","cycle-designer":"designer","cycle-builder":"builder",
  "cycle-evaluator":"evaluator","cycle-fixer":"fixer","wp-manager":"wp-manager","mutator":"mutator"
};
const EXPERTS = new Set(["english-teacher","learning-scientist","assessment-expert","game-designer","ux-designer","red-team-critic"]);
function esc(s){return (s||"").replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}
function nodeOf(agent){ if(EXPERTS.has(agent)) return "experts"; return STAGE_OF[agent] || null; }

let lastActive = null;
function highlight(agent, ts){
  if(lastActive){
    const prev = document.querySelector(`[data-node="${lastActive}"] rect`);
    if(prev) prev.removeAttribute("filter");
  }
  const id = nodeOf(agent);
  const badge = document.getElementById('live-badge');
  if(!id){ badge.style.display='none'; return; }
  const g = document.querySelector(`[data-node="${id}"]`);
  if(!g){ badge.style.display='none'; return; }
  const box = g.querySelector('rect');
  const x = parseFloat(box.getAttribute('x'))+parseFloat(box.getAttribute('width'))-10;
  const y = parseFloat(box.getAttribute('y'))+10;
  badge.setAttribute('transform', `translate(${x},${y})`);
  badge.style.display='block';
  lastActive = id;
}

async function tick(){
  let r; try{ r = await fetch('/api/state'); }catch(e){ return; }
  if(!r.ok) return;
  const d = await r.json();
  document.getElementById('at').textContent = (d.at||'').replace('T',' ').slice(0,19);

  document.getElementById('wp').innerHTML = (d.wp||[]).map((w,i)=>{
    const cls = w.icon==='✅'?'done':(w.icon==='🟨'?'doing':'');
    return `<div class="wp-seg ${cls}"><div class="num">${String(i+1).padStart(2,'0')}</div><div class="t">${esc(w.title)}</div></div>`;
  }).join('') || '<div class="empty">讀不到 docs/PLAN.md</div>';

  const sp = d.spawn||{total:0,by_line:{}};
  const pct = Math.min(100, (sp.total/8)*100);
  document.getElementById('spawn').innerHTML =
    `<div class="line1">今日全機 <b>${sp.total}</b> / 8（共用池，超過會被 guard-subagent-budget.py 擋）</div>
     <div class="bar"><i style="width:${pct}%"></i></div>
     <div class="breakdown">${Object.entries(sp.by_line).map(([k,v])=>`<span><b>${esc(k)}</b> ${v}</span>`).join('')||'（今日尚無紀錄）'}</div>`;

  const kbs = d.kb||[];
  const max = Math.max(1, ...kbs.map(k=>k.lines));
  document.getElementById('kb').innerHTML = kbs.map(k=>{
    const w = Math.round((k.lines/max)*100);
    return `<div class="kb-row ${k.lines===0?'zero':''}">
      <div class="nm">${esc(k.agent)}</div>
      <div class="track"><div class="fill" style="width:${w}%"></div></div>
      <div class="n">${k.lines}${k.revoked?` <b>·${k.revoked}推翻</b>`:''}</div></div>`;
  }).join('') || '<div class="empty">讀不到代理人清單</div>';

  const allTools = d.all_tools||[];
  const mx = document.getElementById('matrix');
  mx.innerHTML = `<thead><tr><th>代理人</th>${allTools.map(t=>`<th>${esc(t)}</th>`).join('')}</tr></thead>
    <tbody>${(d.tools||[]).map(r=>{
      const set = new Set(r.tools);
      return `<tr><td class="nm">${esc(r.agent)}${r.unrestricted?'<span class="unrestricted">未寫=全開</span>':''}</td>
        ${allTools.map(t=>`<td class="${set.has(t)?'yes':'no'}">${set.has(t)?'●':'·'}</td>`).join('')}</tr>`;
    }).join('')}</tbody>`;

  const invs = d.invocations||[];
  const maxN = Math.max(1, ...invs.map(i=>i.n));
  document.getElementById('inv').innerHTML = invs.map(i=>{
    const w = Math.round((i.n/maxN)*100);
    return `<div class="inv-row"><div class="nm">${esc(i.agent)}</div>
      <div class="track"><div class="fill" style="width:${w}%"></div></div>
      <div class="n">${i.n} 次</div>
      <div class="last">${esc((i.last_ts||'').replace('T',' ').slice(0,16))}</div></div>`;
  }).join('') || '<div class="empty">黑板還沒有任何一列可統計</div>';

  const intent = d.intent||{needs_human_未結案:[],proposed_未結案:[]};
  document.getElementById('intent-nh').innerHTML = (intent.needs_human_未結案||[]).map(x=>
    `<div class="intent-card"><span class="who">${esc(x.agent)}</span><span class="age">${x.球在人手上幾小時}h</span>
     <span class="txt">${esc(x.task||'')}</span></div>`
  ).join('') || '<div class="empty">無</div>';
  document.getElementById('intent-pr').innerHTML = (intent.proposed_未結案||[]).map(x=>
    `<div class="intent-card"><span class="who">${esc(x.agent)}</span><span class="age">${x.待批幾小時}h</span>
     <span class="txt">${esc(x.proposal||'')}</span></div>`
  ).join('') || '<div class="empty">無</div>';

  document.getElementById('feed').innerHTML = (d.feed||[]).map(e=>{
    const cls = e.outcome==='proposed'?'proposed':(e.outcome==='ok'?'ok':'blocked');
    return `<div class="ev">
      <span class="agent">${esc(e.agent)}<span class="pill ${cls}">${esc(e.outcome||'?')}</span></span>
      <span class="task">${esc(e.task||'')}</span>
      <span class="ts">${esc((e.ts||'').replace('T',' ').slice(0,16))}</span></div>`;
  }).join('') || '<div class="empty">黑板還沒有任何一列</div>';

  highlight(d.latest_agent, d.latest_ts);
}
tick(); setInterval(tick, 6000);
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _guard(self):
        ip = self.client_address[0]
        if allowed(ip):
            return True
        self._send(403, json.dumps({"err": "forbidden from %s" % ip}))
        return False

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if not self._guard():
            return
        p = urllib.parse.urlparse(self.path).path
        if p == "/api/state":
            self._send(200, json.dumps(state(), ensure_ascii=False))
        elif p == "/" or p == "/index.html":
            self._send(200, PAGE, "text/html; charset=utf-8")
        else:
            self._send(404, json.dumps({"err": "not found"}))


def _tailscale_ip():
    try:
        exe = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"),
                            "Tailscale", "tailscale.exe")
        out = subprocess.run([exe, "ip", "-4"], capture_output=True, text=True, timeout=5)
        return out.stdout.strip().splitlines()[0] if out.returncode == 0 else ""
    except Exception:
        return ""


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    tsip = _tailscale_ip()
    print("代理人監看台啟動於 :%d" % PORT)
    print("本機：      http://127.0.0.1:%d" % PORT)
    if tsip:
        print("Tailscale： http://%s:%d  ← 手機用這個" % (tsip, PORT))
    else:
        print("（讀不到 Tailscale IP，跑 `tailscale ip -4` 手動查）")
    print("只接受本機與 Tailscale（100.64.0.0/10），其他來源 403。Ctrl+C 結束")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
