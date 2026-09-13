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
（尚無）
