# 子代理規則 — JCEE-vocab-questions

> 這份是**給子代理的**，不是給主 session 的（主 session 讀 `.claude/agents/_DOMAIN.md` 與 `docs/PLAN.md`）。
> 由 `SubagentStart` hook 注入。
>
> 🔴 **刻意精簡**：不含稱呼、日文附中譯、Karpathy 四原則、measure-first 觸發詞、
> 專案路由表、記憶索引——那些對一個做單一任務的子代理沒有意義，
> 而**每次 spawn 都要付它們的 token**。

## 紅線（違反即造成實害，每條都要附 Why）

> 只寫「在這條線工作才成立、且看輸出就能判斷有沒有遵守」的規則。
> 全域紅線不重複（不全碟遞迴、不印 secret、不 `git add .`、破壞性操作先驗證目標…）。

R-1. **不得改動原站既有的解析／分類／題目內容**，本 fork 只加系統層（登入、遊戲化、家教、報表）；
     必要的站內修改僅限「插入計分掛勾」這類最小侵入式改動。
     Why：原站解析／中譯／分類／標註著作權屬原作者所有，非商業使用限定（`docs/PLAN.md` §1 第1、2條）；
     改了內容本身等於製造版權爭議與失真教材，兩者都是無法回頭的錯。

R-2. **學生個資（email／UID／練習紀錄）不進 git、不進 commit**，只存 Firebase RTDB。
     Why：`docs/PLAN.md` §1 第3條，個資落 repo 是不可逆的洩漏（公開 repo 更是如此）。

R-3. **共用資源是 Firebase 專案 `gen-lang-client-0929530380`**（與同專案下 `isu0821`／`whgm`／`nacs0914`
     三個命名空間共用，本專案用 `jceeVocabGame` 節點）。改 RTDB 規則前必須「先 GET 全份規則 →
     本機合併 → PUT 回去 → 驗證四個命名空間都還在」，**絕不整份覆蓋上傳**。
     Why：一次覆蓋會讓另外三個不相干專案的使用者當場斷線，且不會立刻被發現。

R-4. **AI 家教（WP-5）不做開放式聊天，只能引用站上既有解析，不自行生成新的文法解釋**。
     Why：避免幻覺、避免產出與原作競爭的衍生內容（`docs/PLAN.md` §1 第4條、`_DOMAIN.md` §6）。

R-5. **「攻克」「精熟」兩詞在 WP-8 Phase 0 資料層補丁通過驗收前，不得出現在任何使用者可見畫面**
     （學生端／老師報表／AI 家教建議卡）。內部欄位 `masteredAt` 可以先寫，呈現文字不行。
     Why：現有 `progress`／`sessions`／`wrongItems` 三張表撐不起這兩個詞的判定，見
     `docs/cycle/wp8-2-design.md`——講出去就是對使用者做了資料撐不起的宣稱。

R-N. **你是子代理：不得再 spawn 子代理**（深度＝能力，你是葉子）。
     寫檔只准在你被授權的路徑內（`docs/`、`game/`，且依你自己的 `## 紅線` 段落再收）。
     Why：不是規矩而已，是機械擋著——`guard-subagent-budget.py` 的 `MAX_DEPTH=1`
     會直接拒絕（2026-09-13 全機實測：某線管理師四次呼叫、三個不同對象，全被同一句擋下）。
     連管理師也一樣，所以管理師的 frontmatter 裡沒有 `Agent`。

R-T. 🔴 **你沒有時鐘：不准自己編 `ts`。**
     你收不到主 session 的 `[CURRENT-TIME]` 注入，所以你不知道現在幾點。
     寫黑板一律用 `python board_tool.py write ...`（見下方工具庫），它會自動取真時間、
     組好完整schema、原子寫入——**不要再手動跑 `python -c` 取時間戳或手動組 JSON**，
     那是這支工具存在之前的舊做法。

     Why：2026-09-13 全機實測，編出來的 `ts` 會讓黑板出現逆序或未來時間；
     黑板的活性判斷、STALE、斷路器全部建立在 `ts` 上，`ts` 是編的，那些判斷就都是編的，
     而且看起來跟正確的一模一樣。`board_tool.py` 就是為了讓這件事不再靠人記得而寫的。

## 你多半不准做的事

- 動 `docs/PLAN.md` 的 WP-1~7、WP-9 既有本體文字——除非你的崗位明文授權（例：`cycle-designer`
  在 WP-8 裁決範圍內，也只能動 WP-8/WP-9 與必要的表格，不能順手重寫其他章節）。
- `git add .` / `git add -A` / `--no-verify` / 全碟遞迴搜尋。
- 印出任何機密（`env`、`cat .env*`、`rclone config show`、token、Firebase service account 金鑰）。
- **對不確定的事回報「已完成」。做不到就說做不到，並說缺什麼。**
- 引入 React／Tailwind／打包工具——本專案是純 vanilla 靜態站，這是硬約束（`docs/PLAN.md` §3.1）。

## Tools（這條線的入口，別自己重造）

🔴 **動工前先看自己的工具箱 `.claude/agents/toolbox/<你自己的name>.md`**——
這是從全隊共用的 `TOOLS.md` 裡篩出跟你有關的子集，加上你自己用出來的心得，
不用每次都去讀 `TOOLS.md` 全文。工具箱跟 `kb/<name>.md` 是平行結構：kb記判斷力，
toolbox記工具用法，兩個都只增不改。`TOOLS.md` 本身是治理權威，工具箱是個人筆記，
兩者對不上時以 `TOOLS.md` 為準。那份清單本身有生命週期，你可以參與：

```
python E:/Downloads/mcp-governance/tools/agents_census.py     # 代理人登錄與守衛對帳（中央正本，別複製）
python board_tool.py write ...                                  # 寫黑板／讀寫自己的KB，見上方R-T
python intent_ledger.py --json                                 # 黑板上還沒結案的球（wp-manager用）
git log --oneline -20                                          # 最近做了什麼
curl -s -o /dev/null -w "%{http_code}" <url>                    # 驗證頁面/deepLink 是否 200
```

**你可以提案發明/改善/停用工具，但不能自己動手寫**（跟改代理人定義檔同一條邊界——
提案由 `board_tool.py write --outcome proposed --proposal "..."` 送出，是否真的建置由主線決定）：
- 發現某個重複性判斷每次都要人工重做一次 ⇒ 提案發明一支工具，描述輸入輸出。
- 某個工具用起來卡住、少個欄位 ⇒ 用 `--friction` 記下來（不是 `residual_risk`——
  friction是「卡住但自己繞過去了」）。
- 某個工具長期沒人在 `evidence`/`friction` 提到 ⇒ 提案標記停用，說明為什麼。
詳細規則見 `TOOLS.md`「工具生態治理」一節。

主要資料在 Firebase RTDB `jceeVocabGame/*`（唯讀查詢用 Admin SDK／REST，沒有本機可寫的測試指令，
新建/修改規則走 R-3 的合併流程）；規格正本是 `docs/PLAN.md`；各 WP 的審查/設計產物在 `docs/cycle/`。
