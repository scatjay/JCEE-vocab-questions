#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""board_tool.py —— 把「取真時間／寫黑板／讀寫自己的KB」這幾組被 14 隻代理人各自
用散文描述、各自手打 Bash 的原始操作，聚合成幾個可靠的高層指令。

## 為什麼要這支（2026-09-14）

現況：每隻代理人的 prompt 裡都重複寫著同一段——「跑
`python -c "import datetime;print(...)"` 取真時間」「照這個 schema 手動組 JSON
append 進 `_runlog.jsonl`」。這是把同一組低階操作（Bash＋手動拼字串＋檔案 I/O）
用文字複製 14 次，而不是聚合成一個工具——後果不是理論上的：其他線已經實測過
「代理人自己編時間戳」造成黑板逆序、「手動組 JSON」漏欄位這些問題（見
mcp-governance/docs/AGENT_BLACKBOARD.md 的 R-T 與相關事故記錄）。

這支不做任何新判斷，只是把「怎麼正確做這件事」從十四份散文說明，收斂成一個
被測過、行為一致的指令。代理人的判斷力（寫什麼 summary、evidence 有哪些）
還是代理人自己的事，這支只管「怎麼落地不出錯」。

## 指令

    python board_tool.py ts
        印出真時間（ISO 8601，含時區），取代手打的 `python -c "import datetime..."`。

    python board_tool.py write --agent NAME --task TEXT --outcome OUTCOME
        [--summary TEXT] [--evidence A,B,C] [--residual A,B,C]
        [--needs-human] [--proposal TEXT] [--closes TS1,TS2] [--friction A,B,C]
        組好完整 schema 的一列（ts 自動取真時間，不需要也不接受手動指定），
        append 進 `.claude/agents/_runlog.jsonl`（原子寫入，不會留下寫一半的殘檔）。
        outcome 必須是 ok/blocked/failed/incomplete/proposed 之一，寫錯直接報錯，
        不會靜默存進一個黑板讀者看不懂的值。

    python board_tool.py kb-read AGENT
        印出 `.claude/agents/kb/AGENT.md` 的內容；檔案不存在就印出這是第一次執行、
        照 kb/README.md 的格式新建，不要假裝讀到了什麼。

    python board_tool.py kb-append AGENT --text TEXT [--section "## 標題"]
        把 TEXT 追加進 `.claude/agents/kb/AGENT.md`（檔案不存在就先建立含標準檔頭的新檔）。
        只增不改：這支不提供「修改/刪除舊條目」的指令，被推翻的舊結論照 kb/README.md
        的規則自己在新增內容裡寫「已被 YYYY-MM-DD 推翻」，不要指望這支幫你改歷史。
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

try:
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                           # noqa: BLE001
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(HERE, ".claude", "agents")
BOARD = os.path.join(AGENTS_DIR, "_runlog.jsonl")
KB_DIR = os.path.join(AGENTS_DIR, "kb")
LINE_NAME = "JCEE-vocab-questions"
VALID_OUTCOMES = ("ok", "blocked", "failed", "incomplete", "proposed")

KB_HEADER = """# {agent} 知識庫

> 這份是 {agent} 自己跨輪累積的判斷，不是黑板的複本。照 `.claude/agents/kb/README.md`
> 的規則：標日期、區分「有定論的研究」／「本專案的實測」／「我的判斷」，
> 被推翻的往下移標「已被 YYYY-MM-DD 推翻」，不刪除。

"""


def _now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def cmd_ts(_args):
    print(_now_iso())


def _split_csv(s):
    return [x.strip() for x in s.split(",") if x.strip()] if s else []


def cmd_write(args):
    if args.outcome not in VALID_OUTCOMES:
        print("🔴 --outcome 必須是 %s 之一，收到 %r" % ("/".join(VALID_OUTCOMES), args.outcome))
        return 2
    if args.outcome == "proposed" and not args.proposal:
        print("🔴 outcome=proposed 必須附 --proposal（提案內容），不能是空的。")
        return 2

    entry = {
        "ts": _now_iso(),
        "line": LINE_NAME,
        "agent": args.agent,
        "task": args.task,
        "outcome": args.outcome,
        "summary": args.summary or "",
        "evidence": _split_csv(args.evidence),
        "residual_risk": _split_csv(args.residual),
        "needs_human": bool(args.needs_human),
        "proposal": args.proposal or None,
        "closes": _split_csv(args.closes),
        "friction": _split_csv(args.friction),
    }

    os.makedirs(os.path.dirname(BOARD), exist_ok=True)
    # 原子寫入的單位是「一整列」，用 append 模式即可——多個 writer 併發時，
    # os 對單次 write() 的行級 append 在同一顆碟上不會交錯成半列（跟 control_server.py
    # 的 _atomic 處理『整檔覆寫』是不同情境，這裡是純 append，風險本來就低很多）。
    with open(BOARD, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print("✅ 已寫入黑板：%s %s outcome=%s" % (entry["ts"], args.agent, args.outcome))
    return 0


def cmd_kb_read(args):
    p = os.path.join(KB_DIR, args.agent + ".md")
    if not os.path.exists(p):
        print("（%s 還沒有知識庫檔案——這是第一次執行，讀完這輪就用 kb-append 建立它，"
              "照 kb/README.md 的規則區分「有定論的研究」/「本專案的實測」/「我的判斷」）"
              % args.agent)
        return 0
    with open(p, encoding="utf-8", errors="replace") as f:
        print(f.read())
    return 0


def cmd_kb_append(args):
    p = os.path.join(KB_DIR, args.agent + ".md")
    os.makedirs(KB_DIR, exist_ok=True)
    is_new = not os.path.exists(p)
    today = datetime.date.today().isoformat()
    section = args.section or ("## %s" % today)
    with open(p, "a", encoding="utf-8") as f:
        if is_new:
            f.write(KB_HEADER.format(agent=args.agent))
        f.write("\n%s\n\n%s\n" % (section, args.text))
    print("✅ 已追加進 %s（%s）" % (p, "新建" if is_new else "既有檔案"))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ts", help="印出真時間，取代手打的 python -c 時間戳指令")

    w = sub.add_parser("write", help="組好schema寫進黑板")
    w.add_argument("--agent", required=True)
    w.add_argument("--task", required=True)
    w.add_argument("--outcome", required=True, choices=VALID_OUTCOMES)
    w.add_argument("--summary", default="")
    w.add_argument("--evidence", default="", help="逗號分隔")
    w.add_argument("--residual", default="", help="逗號分隔")
    w.add_argument("--needs-human", action="store_true")
    w.add_argument("--proposal", default="")
    w.add_argument("--closes", default="", help="逗號分隔的 ts")
    w.add_argument("--friction", default="", help="逗號分隔")

    r = sub.add_parser("kb-read", help="讀自己的知識庫")
    r.add_argument("agent")

    a = sub.add_parser("kb-append", help="追加自己的知識庫（只增不改）")
    a.add_argument("agent")
    a.add_argument("--text", required=True)
    a.add_argument("--section", default="")

    args = ap.parse_args()
    fn = {"ts": cmd_ts, "write": cmd_write, "kb-read": cmd_kb_read,
          "kb-append": cmd_kb_append}[args.cmd]
    return fn(args) or 0


if __name__ == "__main__":
    sys.exit(main())
