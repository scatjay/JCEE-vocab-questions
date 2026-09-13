#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""intent_ledger.py —— 意圖對帳（JCEE 縮小版）：黑板上還開著、沒人結案的球有哪些。

    python intent_ledger.py            印報告
    python intent_ledger.py --json     給機器讀（monitor server／wp-manager 用）

## 這支跟公路車線 intent_ledger.py 的關係（先講清楚，不要照抄）

公路車那支做的是**三方交叉**：`_coach_registry.json`（24 小時跑的 daemon/crawler，
有「歸誰／容忍幾小時／逾時怎樣」三欄契約）× 黑板 × `closes`——因為它的「崗位」
是會**silently 停掉**的背景常駐行程，需要「逾時多久算異常」這種契約才問得出
「該派工」跟「契約缺口」兩區。

JCEE 沒有這種東西。這條線的代理人全部是**被呼叫才存在**的子代理，沒有一個
會在背景 24 小時跑然後突然停掉——沒有「daemon 死了」這件事,所以沒有 A 區
（逾時派工）跟 C 區（契約缺口）能問的資料;也沒有 B1/B2 需要的「這個崗位現在
正不正常」的獨立健康檢查（公路車讀 `coach_registry.py` 的 liveness,JCEE 沒有
對應的東西）。硬套三欄契約會是編造出「容忍幾小時」這種沒有根據的數字。

⇒ 這支縮小到公路車那支唯一在 JCEE 也有真實資料支撐的部分：
   **黑板上 `needs_human` 與 `outcome=proposed` 兩類「球還在人手上」的列，
   有哪些還沒被 `closes` 結掉**。這件事黑板本身的資料就答得出來，不需要編造
   任何契約欄位。若之後 JCEE 也長出「常駐流程」（例如 WP-8 的 Cloud Function
   `jcee-tutor`),再回頭比照公路車那支加 A/C 區,現在加是無中生有。

## 為什麼還是值得做（即使縮水了)

`wp-manager.md` 的 prompt 裡本來就要求它「手動掃一遍黑板找 needs_human 積壓、
proposed 清單」——那是每次呼叫都要重新讀完整份黑板去人工算一次。公路車線
自己的教訓（見它的 intent_ledger.py 檔頭)是:寫成契約只是紀錄(L3),要變成
「該動的時候真的有人算出結論」(L1),需要一個固定會被跑、會給出結論的讀者。
這支就是那個讀者——給 wp-manager 用,也給 monitor server 的面板用。
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import sys

try:
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                           # noqa: BLE001
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, ".claude", "agents", "_runlog.jsonl")
_TZ8 = datetime.timezone(datetime.timedelta(hours=8))


def _now():
    return datetime.datetime.now(_TZ8)


def _parse_ts(s):
    if not s:
        return None
    try:
        d = datetime.datetime.fromisoformat(str(s))
        return d.replace(tzinfo=_TZ8) if d.tzinfo is None else d
    except Exception:                                       # noqa: BLE001
        return None


def _age_h(ts, now):
    d = _parse_ts(ts)
    return None if d is None else (now - d).total_seconds() / 3600.0


def load_board():
    """🔴 fail-closed：檔案不存在就明講量不到，不要回空清單假裝『沒有積壓』。"""
    if not os.path.isfile(BOARD):
        raise RuntimeError(
            "找不到黑板 %s —— 這不是『沒有積壓』，是量不到。" % BOARD)
    rows = []
    for i, ln in enumerate(io.open(BOARD, encoding="utf-8", errors="replace"), 1):
        ln = ln.strip()
        if not ln:
            continue
        try:
            rows.append(json.loads(ln))
        except Exception as e:                              # noqa: BLE001
            print("⚠ 黑板第 %d 列解析失敗，已跳過：%s" % (i, str(e)[:80]))
    return rows


def closed_ts(board):
    """所有被後續列 closes 指到的 ts（規格見 mcp-governance/docs/AGENT_BLACKBOARD.md §3.1）。"""
    out = set()
    for r in board:
        for t in (r.get("closes") or []):
            out.add(str(t))
    return out


def build(board):
    now = _now()
    closed = closed_ts(board)
    needs_human, proposed = [], []

    for h in board:
        if str(h.get("ts")) in closed:
            continue
        age = round(_age_h(h.get("ts"), now) or 0, 1)
        if h.get("needs_human"):
            needs_human.append({"ts": h.get("ts"), "agent": h.get("agent"),
                                 "task": h.get("task"), "summary": h.get("summary"),
                                 "球在人手上幾小時": age})
        if str(h.get("outcome")) == "proposed":
            proposed.append({"ts": h.get("ts"), "agent": h.get("agent"),
                              "task": h.get("task"),
                              "proposal": (str(h.get("proposal") or ""))[:160],
                              "待批幾小時": age})

    needs_human.sort(key=lambda x: -x["球在人手上幾小時"])
    proposed.sort(key=lambda x: -x["待批幾小時"])
    return {"ts": now.isoformat(timespec="seconds"),
            "needs_human_未結案": needs_human,
            "proposed_未結案": proposed}


def report(res, n_board):
    print("== JCEE 意圖對帳（黑板 × closes，縮小版）%s ==" % res["ts"][:19])
    print("黑板 %d 列\n" % n_board)

    nh = res["needs_human_未結案"]
    print("── needs_human 未結案（球在人/主線手上）%d 件" % len(nh))
    for x in nh:
        print("   ✋ %s %s「%s」　%.0fh" %
              (str(x["ts"])[:19], x["agent"], (x["task"] or "")[:42],
               x["球在人手上幾小時"]))
        if x.get("summary"):
            print("      %s" % x["summary"][:100])
    if not nh:
        print("   （無）")

    pr = res["proposed_未結案"]
    print("\n── proposed 未結案（提案待批）%d 件" % len(pr))
    for x in pr:
        print("   💡 %s %s　待批 %.0fh" % (str(x["ts"])[:19], x["agent"], x["待批幾小時"]))
        print("      %s" % (x["proposal"] or "(空)"))
    if not pr:
        print("   （無）")

    print("\n── 這份對帳沒有涵蓋什麼")
    print("   · 沒有『逾時該派工』區——JCEE 沒有常駐 daemon，沒有契約可比對。")
    print("   · 不判斷 proposed 執行了沒——那要讀懂語意，機器判不出來，由人/代理人決定。")
    print("   · 只讀本線黑板，不跨線。")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true", help="只印 JSON")
    a = ap.parse_args()

    try:
        board = load_board()
    except RuntimeError as e:
        print("🔴 %s" % e)
        return 2

    res = build(board)
    if a.json:
        res["n_board_rows"] = len(board)
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        report(res, len(board))
    return 0


if __name__ == "__main__":
    sys.exit(main())
