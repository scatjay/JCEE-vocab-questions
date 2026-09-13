# assessment-expert 工具箱

## 原始工具，什麼情境用哪個
- **Read/Grep/Glob**：查資料模型現況（`docs/PLAN.md` §3.2）撐不撐得起某個宣稱、
  找現有欄位有沒有留逐次時間序列。
- **Bash**：跑 `board_tool.py`／`intent_ledger.py`（見下）；沒有可執行的統計驗證指令
  （這個角色的判斷多半是「這個schema夠不夠」而不是「跑出一個數字」）。
- **WebSearch/WebFetch**：查心理計量方法（BKT/IRT/簡單正確率）在小樣本下的實證，
  補進自己的 `kb/assessment-expert.md`，不是每次任務都要查。

## 這個角色專屬的高層工具
- `board_tool.py write/kb-append`——跟其他人一樣，強制。
- `claim_audit.py`（**proposed，還沒建置**）——本該是這個角色最常用的工具：
  給一組詞（攻克/精熟/掌握度）＋要檢查的檔案，回報詞出現在哪、資料撐不撐得住。
  在它建好之前，這件事目前靠手動 grep + 讀 schema 定義，慢但可行。
  **如果這次任務又手動做了一遍這個判斷，這是提案發明它的具體理由，寫進 `--proposal`。**

## 用出來的心得
（尚無——第一次接上工具箱，跑過幾輪後才會有東西）
