# cycle-builder 工具箱

## 原始工具，什麼情境用哪個
- **Read/Grep/Glob**：讀規格（`docs/cycle/*-2-design.md`）、找既有可沿用的 API
  （§4 表列的掛勾點），動手前先確認別重造輪子。
- **Edit/Write**：實作階段的主力，僅限規格範圍內的檔案。
- **Bash**：`node --check` 驗語法、`curl` 帶 `?nocache=$(date +%s)` 驗證上線、
  逐檔 `git add`＋`git commit`（絕不 `-A`）。

## 這個角色專屬的高層工具
- `board_tool.py write/kb-append`——強制。
- `rtdb_merge.py`（**proposed，還沒建置**）——`docs/PLAN.md` WP-1 步驟7現在只有散文
  描述「先GET全份規則→Python合併→PUT回去→驗證四個命名空間都在」，這是你每次動
  RTDB規則都要重新手動做一遍的流程，且做錯的代價是讓其他三個命名空間斷線。
  **這是最該優先提案建置的工具**——下次真的要動 RTDB 規則時，先確認它建了沒；
  沒建就照 R-3 的散文流程做，同時在 `--proposal` 裡點名這件事該有工具了。

## 用出來的心得
- **2026-09-14（WP-9驗收標準12，roots `?g=`參數）**：跨頁面傳遞 key 做深連結時，Read/Grep
  兩邊檔案「都有讀寫這個參數的程式碼」不代表值域對得上——這次 `roots/index.html` 讀 `?g=`
  沒問題、`wordwheel.html` 也正確送出，但兩邊的 key 值域（roots_data.json 15組字根 vs
  wordwheel 12組字首/字尾）完全沒有交集，是規格文件裡沒人實際跑過 diff 才漏掉的假設落差。
  下次接到「把 A 頁的某個 key 傳給 B 頁篩選/捲動」這類任務，動手前先各自 `Grep` 兩邊的 key
  清單（例如 `grep -n '"key"'`／`DATA\s*=`）列出來比對，不要只驗證「程式碼邏輯正確、grep
  驗收通過」就結案——機械驗收通過不等於實際值域對得上，這兩件事要分開驗證。
