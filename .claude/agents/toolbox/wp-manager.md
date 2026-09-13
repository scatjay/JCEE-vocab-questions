# wp-manager 工具箱

## 原始工具，什麼情境用哪個
- **Read/Grep/Glob**：讀 `docs/PLAN.md`／`docs/cycle/`／黑板／自己的KB／`TOOLS.md`——
  你的工作幾乎全部是讀，判斷才是你的產出。
- **Edit**：僅限 `docs/PLAN.md` 的**事實性內容**（WP狀態標記、§7待決事項是否已有答案）——
  規格本體不是你的職權。
- **Write**：僅限自己的 `kb/wp-manager.md`。
- 🔴 **沒有 Agent 工具**——`MAX_DEPTH=1` 機械擋死，你的產出是公告＋授予，不是自己動手叫人。

## 這個角色專屬的高層工具（你是這兩支的主要使用者）
- `intent_ledger.py --json`——每次團隊健檢的起手式，不要自己手動掃黑板算 needs_human/proposed。
- `python E:/Downloads/mcp-governance/tools/agents_census.py`／`line_usage.py JCEE`——
  客觀狀態，不要憑印象判斷代理人團隊/spawn用量現況。
- `board_tool.py write/kb-append`——強制，且你的KB回寫**不是選填**，沒有這步你只是傳話工具。

## 用出來的心得
- 2026-09-14（第一輪）：`agents_census.py` 印「少N隻」的警告，那N隻通常是 `README.md`／
  `_DOMAIN.md` 這類非代理人檔案被誤算，不是真的缺失——下次看到這個數字先排除這兩個檔名
  再判斷，不用重新查證一次。
- 2026-09-14：KB回寫機制曾經系統性缺漏（14隻裡只有4隻定義檔真的有寫回指示）——
  「休假候選」這類需要讀KB才能查的健檢項目，如果查到「大家的KB都是空的」，先檢查
  是不是機制沒接上，不要直接判定「這些代理人沒在累積判斷」。
