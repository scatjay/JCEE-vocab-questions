# JCEE Vocab Game — 完整建置計畫

> 建立：2026-09-13 深夜｜**最後更新：2026-09-14（WP-8 教學決策層完成五位專家審查與 cycle-designer 裁決定案：
> 精熟判定改為「3次跨場次獨立事件＋跨站分級用語」、KC 鍵值拆分「內容/考點」與「答題行為」兩個維度、
> 政策4(到期複習)vs政策6(新舊比例)寫成明確優先序算法、難度公式補 tie-break 與冷啟動切換點、
> 新增 WP-8 Phase 0 資料層 schema 補丁（`progress/{uid}/kc/{kcId}`、`progress/{uid}/recentAttempts`、`wrongItems.repairHistory`）、
> WP-9 補上色彩/彈窗/冷卻機制與 floor-hit 對 streak 的處理。裁決全文與未採納意見見 `docs/cycle/wp8-2-design.md`）**｜
> **2026-09-14 追加**：`mutator` 用 Leveled Commitment Contracts 框架突變提案精熟判定（政策8），`cycle-designer` 裁決採納方案A（答錯扣點代替歸零、精熟可被撤銷），schema 新增 `demotedAt`，驗收標準第7條同步修訂、新增第15、16條，第13條紅線驗收範圍同步擴大。裁決全文見 `docs/cycle/MUTATIONS.md` #1。｜
> **2026-09-14 再追加**：WP-9候選A文案經`red-team-critic`第二輪真身覆核v2不通過，`cycle-designer`裁決修訂為v3（見`docs/cycle/wp9-2-design.md`）；WP-8政策5／§7待決事項#7經`assessment-expert`真身複審，`cycle-designer`裁決維持現行線性難度公式、不換logistic/Rasch，新增display-guard機械驗收（第17條）（見§5政策5、`docs/cycle/wp8-2-design.md`「2026-09-14 v2追記」）。｜
> 基準 commit：`f0fb953`
> 用途：**派工用的工程文件**。之後的 session（含 Sonnet）接手時，先讀這一份，再挑工作包做。
> 文件裡的行號取自上述 commit，動到原站檔案前請先 grep 確認位置沒有位移。

---

## 0. 這份文件怎麼用

- 每個工作包（WP-n）都是**可獨立派工**的單位，寫明了：目標／前置條件／做法／驗收標準。
- 接手時：① 讀 §1 紅線 ② 讀 §2 現況 ③ 確認 §7 有沒有新答案 ④ 挑一個前置條件已滿足的 WP 開工。
- 做完一個 WP，更新本文件該 WP 的狀態標記（`⬜ 未開始` → `🟨 進行中` → `✅ 完成`），並在 commit 訊息裡註明 WP 編號。
- 不要一次開很多工作包。站台改造類（WP-2）可以分站平行，其餘請依 §8 的順序。

---

## 1. 專案定位與紅線

### 🎯 北極星目標（2026-09-13 楊老師定，晚於本文件初版）

> **從高一高二開始，每天 15–30 分鐘，能完整攻克這些題目。**

算術與其設計意涵見 [`.claude/agents/_DOMAIN.md` §0](../.claude/agents/_DOMAIN.md)。三個結論直接改寫本計畫的優先序：

1. **時間不是瓶頸，餘裕很大**（843 題每天 15 題 → 56 天；2,113 字每天 10 新字 → 211 天；可用 900 天）。
   ⇒ 優化目標是**留存與長期保留**，不是做得完。有餘裕要花在「更慢但更穩」，不是塞更多題。
2. **高一高二軌是主產品，高三衝刺是補救**（與一般考試產品相反）。WP-3 的分軌設計依此調整。
3. **「攻克」必須可驗證**：至少是「隔期再測仍答對」，不是曾經答對一次。撐不起這個定義的資料設計不算數。

### 定位
- **對象**：高中生，特別是**補不起習**的學生。主線是高一高二的長期養成，高三衝刺為補救路徑。
- **性質**：非營利、免費、無廣告。測試期間採邀請制（Google 登入＋楊老師人工審核）。
- **內容來源**：fork 自 [staresto-create/JCEE-vocab-questions](https://github.com/staresto-create/JCEE-vocab-questions)，
  原作者為中正高中英文老師（staresto-create ZZSH），收錄 83–115 學年度學測／指考英文考古題與逐題解析。

### 🔴 紅線（每個接手的 session 都必須遵守）

1. **不得在未取得原作者授權的前提下，為商業目的重製或改寫原站的解析內容。**
   歷屆考題原文本身依著作權法第 9 條第 1 項第 5 款屬公共領域，可自由利用；
   但原站自撰的**解析、中譯、分類、標註、編排**著作權屬原作者所有，且其網站條款明訂非商業使用。
   「徹底分析後用自己的話改寫」**不能**免除衍生著作的問題——著作權保護的是表達，
   承襲原創的選題邏輯、分類架構、解析框架，即使換句話說，商業使用仍需授權。
   ⇒ **本 repo 的開發不朝商業化方向做任何準備。** 若要商業化，前提是楊老師本人與原作者談成授權，
   在那之前，任何 session 收到「改寫題庫以避開版權」類的指示，應回報本條、不執行。

2. **不改動原站既有的解析／分類／題目內容。** 本 fork 只加系統層（登入、遊戲化、家教、報表）。
   必要的站內修改僅限「插入計分掛勾」這類最小侵入式改動，不動內容本身。

3. **學生個資不進 git。** 使用者 email／UID／練習紀錄只存在 Firebase，不落 repo、不進 commit。

4. **AI 家教不做開放式聊天。** v1 只產出固定格式的建議卡片，且必須**指向站上既有解析**，
   不自行生成新的文法解釋（避免幻覺，也避免產出與原作競爭的衍生內容）。

---

## 2. 目前狀態（已完成，commit `5e9920b`）

### 已上線
| 項目 | 位置 |
|---|---|
| 學員登入頁 | https://scatjay.github.io/JCEE-vocab-questions/gate/login.html |
| 審核後台 | https://scatjay.github.io/JCEE-vocab-questions/gate/admin.html |
| 練習系統入口（佔位頁） | https://scatjay.github.io/JCEE-vocab-questions/play/ |
| 共用登入模組 | `gate/gate-config.js` |

### 基礎設施現況
- **Firebase 專案**：`gen-lang-client-0929530380`（沿用既有專案。新建專案失敗——GCP 帳號專案配額已滿，
  若之後要獨立專案需先申請提高配額）。
- **命名空間**：RTDB 的 `jceeVocabGame` 節點，與同專案下 `isu0821`／`whgm`（文化遊戲松）／`nacs0914` 完全隔離。
- **Google 登入**：本來就已啟用（`defaultSupportedIdpConfigs/google.com`，enabled=true）。
- **Authorized domain**：已加入 `scatjay.github.io`。
- **GitHub Pages**：已啟用，main 分支 root。
- **管理員**：`scatjay@gmail.com`，硬寫在 RTDB 規則與 `gate-config.js` 的 `ADMIN_EMAIL`。

### 尚未驗證
- **Google 登入彈窗實際流程沒有真人測過**（內建瀏覽器被全域規則擋死，OAuth 彈窗也需真人手勢）。
  ⇒ 接手的第一件事若遇到登入異常，先確認楊老師是否已完成一次真人測試。

---

## 3. 目標架構

### 3.1 元件圖

```
          ┌──────────────────────────────────────────────┐
          │  GitHub Pages（靜態，無建置流程，純 vanilla） │
          │                                              │
  學生 ──→│  gate/login.html ──審核通過──→ play/ (Hub)    │
          │                                 │            │
          │                                 ├→ 各題庫站   │
          │                                 │  (掛 engine)│
          │                                 └→ 儀表板     │
          │                                    (Chart.js) │
  楊老師 →│  gate/admin.html ──→ 審核／學生報表／討論註記  │
          └───────────────┬──────────────────────────────┘
                          │ Firebase JS SDK（ID token）
                          ▼
          ┌──────────────────────────────────────────────┐
          │ Firebase RTDB  jceeVocabGame/*                │
          │  users / progress / sessions / advice / reports│
          └───────────────┬──────────────────────────────┘
                          │ Admin SDK（service account）
                          ▼
          ┌──────────────────────────────────────────────┐
          │ Cloud Function `jcee-tutor`                    │
          │  驗 ID token → 查 approved → 讀 progress       │
          │  → Vertex Gemini (global endpoint) → 寫 advice │
          └──────────────────────────────────────────────┘
```

**關鍵限制**：原站是純 vanilla、無建置流程的靜態站。**不要引入 React／Tailwind／打包工具**——
會跟既有 13 個獨立 HTML 檔的架構打架，也讓 GitHub Pages 部署複雜化。
外部套件只用 CDN 直載的 UMD 版（Chart.js、canvas-confetti），其餘自己寫。

### 3.2 資料模型（RTDB，`jceeVocabGame/`）

```jsonc
users/{uid}: {                      // ✅ 已實作
  email, displayName, photoURL,
  approved: bool, requestedAt: ms, approvedAt: ms
}

progress/{uid}: {                   // WP-1
  xp: number,
  level: number,
  track: "junior" | "senior",       // 高一高二 / 高三，影響推薦與語氣
  streak: { current, longest, lastActiveDay },   // day = "YYYY-MM-DD"（台北時區）
  badges: { [badgeId]: earnedAtMs },
  stations/{stationId}: { attempted, correct, lastAt, msPerItem }
}

sessions/{uid}/{sessionId}: {       // WP-1，append-only
  station, mode,                    // mode: "free" | "pomodoro25" | "fragment3" | "mock"
  startedAt, endedAt, attempted, correct, durationSec
}

wrongItems/{uid}/{itemKey}: {       // WP-1，家教的主要證據來源
  station, qid, deepLink,           // deepLink 例：gsat/#q-<id>
  category,                         // 取自題目既有 metadata（見 §4）
  missCount, lastMissAt, repairedAt // repairedAt: 之後答對的時間
}

advice/{uid}/latest: {              // WP-5，只有 Cloud Function 寫得進去
  diagnosis, evidence[], nextAction, officialStat,
  generatedAt, model, basedOnSessionIds[]
}

reports/{uid}/{periodId}: {         // WP-6，periodId 例："2026-W38"
  generatedAt, stats{...}, aiSummary,
  teacherNote, teacherNoteAt,       // 只有 admin 寫得進去
  studentSeenAt
}
```

> **注意（2026-09-14）**：WP-8 裁決新增了三個節點（`progress/{uid}/kc/{kcId}`、`progress/{uid}/recentAttempts`、
> `wrongItems/{uid}/{itemKey}.repairHistory`），是對上面這份 schema 的**追加**，不改變既有欄位語意。
> 完整定義寫在 §5 WP-8 的「Phase 0」小節，正式建置時要同步把這三個節點補回這裡，本次裁決先不動這個區塊的文字。

### 3.3 安全模型

| 節點 | 學生本人 | 其他學生 | 楊老師(admin) | Cloud Function |
|---|---|---|---|---|
| `users/{uid}` | 建立一次（`!data.exists()`） | ✗ | 讀寫全部 | — |
| `progress/{uid}` | 讀寫自己 | ✗ | 讀全部 | 讀 |
| `sessions/{uid}/{sid}` | 只能新增（`!data.exists()`） | ✗ | 讀全部 | 讀 |
| `wrongItems/{uid}` | 讀寫自己 | ✗ | 讀全部 | 讀 |
| `advice/{uid}` | 只能讀 | ✗ | 讀全部 | 寫 |
| `reports/{uid}` | 讀自己、寫 `studentSeenAt` | ✗ | 讀寫全部 | 寫 |

**已知且接受的風險**：`progress` 由學生端自寫，技術上可用瀏覽器 console 竄改 XP／等級。
這是個人激勵工具，不是評量，**接受**。但因此：
- `sessions` 設計成 **append-only**（`!data.exists()`），保留時間軌跡，較難事後竄改；
- **給老師看的報表數字一律以 `sessions` 為準**，並在 UI 上標明「學生自陳數據」。
- 若哪天這些數字要用於任何實質評量，這個信任模型必須重做（改成 Function 代寫）。

---

## 4. 各站現況盤點（掛勾點）

這是今晚實際讀碼盤出來的。**各站的答題引擎各自獨立、命名不一致**，
沒有共用慣例可以「一次掛全部」——必須逐站寫 adapter。

| 站 | 檔案 | 型態 | 掛勾點（行號 @ `195cb6d`） | 既有 localStorage |
|---|---|---|---|---|
| 學測單字 | `gsat/index.html` | 四選一 | `selectAnswer(letter,q)` L783、`finishQuiz()` L910 | 錯題本 `LS_WRONG`、歷程 `LS_HISTORY` |
| 指考單字 | `zhikao/index.html` | 四選一（與 gsat 同構） | `selectAnswer` L752、`finishQuiz` L879 | 同上 |
| 單字記憶卡 | `cards/index.html` | 間隔複習卡 | `answer(chosen, correct)` L713 | `jcee_cards_v1`（自有 SRS） |
| 中翻英 | `translate/index.html` | 自評 | `gradeGood` L940／`gradeBad` L947、`finishSession()` L957 | 錯題本＋歷程 |
| 單字輪 | `wordwheel.html` | 五型構詞題 | `ask()` 內選項 handler（`.right`/`.wrong`） | 無 |
| 段考單字 | `class/index.html` | 拼寫輸入 | 自有 `STORE_KEY` 狀態機 | 有 |
| 字根家族表 | `roots/` | **純查閱表** | 無答題迴圈 | — |
| 複現字／簡寫表 | `repeats/`、`abbr/` | **純閱讀** | 無 | — |
| 篇章銜接 | `cohesion*.html`（11 檔） | 單元練習 | 未細讀 | 有 |
| 示範頁 | `demo/` | 閱讀 | 無 | — |

**可直接利用的既有能力**（不要重造）：
- `gsat`／`zhikao` 已有 `randomTen()`（L700／L671）與 **hash 深連結**（`#q-<id>` 與卷次 hash），
  番茄鐘／碎片時間的「出 N 題」可以直接深連結進去，不必自己寫選題器。
- `cards/` 已有完整 SRS（到期判斷、答錯重排），碎片時間模式應直接取它的「今日到期」清單。
- `gsat` 每題帶 `collocation`、`note`、`accuracyRate`、`discrimination`、`discriminationNote`；
  `wordwheel` 每題帶 `t`（parse／pos／sense／infer／fake）與 `why`。
  **這些就是 AI 家教的分類依據與證據來源**，不需要另外標註題目。
  🔴 **2026-09-14 補充**：`collocation` 是逐題自由文字（該題的搭配組合），不是可跨題共用的分類；
  `t` 是「答題行為」分類，不是「考點」分類——這兩者不能直接當同一層 KC 鍵值混用，
  詳見 §5 WP-8 政策1/2 的裁決文字。

**首頁另連到 6 個獨立 repo**（作文 `essay-prompts`、學測克漏字 `grammar-cloze-test`、指考克漏字
`zhikao-cloze-test`、文意選填 `passage-completion`、篇章結構 `discourse-structure`、混合題 `mixed-format`）。
那些**不在本 repo 內**，目前不動；未來若要納入，是另一輪 fork 與 §1 紅線的重新確認。

---

## 5. 工作包

### 🟨 WP-1 遊戲化核心引擎 ＋ 資料層 — 2026-09-14 Phase1-3已實作，驗收部分待真人/cycle-evaluator

> `cycle-builder` 已依 `docs/cycle/wp1-2-design.md` 完成施工（`game/engine.js`／`game/engine.css`／
> `game/kc-logic.js`／`wordwheel.html` adapter）。13條驗收標準裡 5/6/7/11(a)(b)(c) 已用 node
> 單元測試驗過；1-4/9/10/13 需要真實 RTDB 帳號＋瀏覽器端到端測試，本輪環境無法驗，
> 已標記 `needs_human`，留給真人或 `cycle-evaluator` 補驗。
**前置**：無（可立即開工）
**目標**：一份共用引擎，加上 RTDB progress/sessions/wrongItems 的結構與規則，並在**一個**站（`wordwheel.html`）跑通端到端。

**做法**
1. 建 `game/engine.js`（ES module，無外部相依），公開 API 極小：
   ```js
   JG.init({ station })            // 讀 auth 狀態、載入 progress、畫 HUD
   JG.answer({ correct, qid, category, deepLink })
   JG.sessionStart({ mode })  /  JG.sessionEnd()
   ```
   🔴 **2026-09-14 補充**（WP-8 裁決帶出的介面擴充，向下相容）：`JG.answer` 新增可選欄位
   `followedRecommendation: bool`（省略預設 `false`）——當該題來自 WP-8 建議且答對，額外 +2 XP
   一致性加成，疊加在下面第3點的 base 分數之上。見 §5 WP-8「XP 鑽漏洞裁決」小節。
2. 建 `game/engine.css`：HUD 浮動徽章（等級／XP 條／連續天數）。
   HUD 刻意用**自成一格的深色＋琥珀色**，不要去配合各站不同的配色（各站色系不一，配不完，
   HUD 本來就該讀起來像疊在內容上的一層）。
3. 計分規則（已定案，見 §6）：答對 +10、答錯 +2、**修好舊錯題 +15**。
   🔴 **2026-09-14 已知待補丁**（WP-8 審查發現，尚未排工）：「修好」判定目前沒有要求跨場次，
   可被「故意先錯、下一秒重考同一題拿+15」無腦刷分。修法與所需 schema（`wrongItems.repairHistory`）
   已在 §5 WP-8 Phase 0 定案，**計分邏輯本身的修改仍屬 WP-1 範圍**，待排工，見 §7 待決事項。
4. 等級曲線：`需要的累計XP(n) = round(100 * n^1.4)`，前幾級刻意好升。
5. 連續天數：以**台北時區**日界計算，當日完成 ≥3 題才算數。
   🔴 **2026-09-14 已知待補丁**：WP-9 底線偵測觸發（floor-hit）當天，若因系統判斷停止出題導致當天沒滿3題，
   streak 該日仍須視為已完成、不歸零。這條行為已在 §5 WP-9 定案，**streak 計算邏輯需要 WP-1 配合改動**，待排工。
6. 寫入策略：**session 結束時才寫 RTDB**（不要每題寫），localStorage 作即時鏡像。
7. RTDB 規則加上 §3.2／§3.3 的節點（**注意：合併進既有規則，不要覆蓋其他命名空間**——
   做法見本 repo 歷史或 `nacs0914` 的前例：先 GET 全份規則 → Python 合併 → PUT 回去 → 驗證四個命名空間都在）。
8. 在 `wordwheel.html` 插入 adapter（選項 handler 判定 `.right`/`.wrong` 之後呼叫 `JG.answer`）。

**驗收**
- 用一個測試帳號答 5 題，RTDB 出現 `progress`／`sessions`／`wrongItems` 三處資料，數字對得起來。
- 關掉分頁再開，HUD 顯示的等級／連續天數與 RTDB 一致。
- 用另一個帳號登入，讀不到前一個帳號的 `progress`（規則有效）。
- 未登入時 `JG` 靜默降級（存 localStorage、不報錯），不能讓原站在未登入時壞掉。

---

### ⬜ WP-2 其餘題庫站掛勾（可分站平行派工）
**前置**：WP-1 完成
**目標**：把 engine 掛進 `gsat`／`zhikao`／`cards`／`translate`／`class`。

**做法**：每站一個 adapter，**最小侵入**——在 §4 表列的掛勾點插 1–3 行 `JG.answer(...)`／`JG.sessionEnd(...)`，
不重寫原有邏輯、不動畫面。`category` 從該站題目既有欄位取（gsat 取 `collocation` 有無＋難度、
wordwheel 取 `t`、cards 取題型變體）。`deepLink` 用該站既有的 hash 格式。

> 🔴 **2026-09-14 提醒**：這裡的 `category` 是給 WP-2 掛勾用的粗分類，跟 §5 WP-8 定義的 **KC 鍵值**
> 是兩件事——WP-8 的 `kcId` 不能直接沿用這裡的 `category`，兩者的裁決見 WP-8 政策1/2。

**每站的驗收**：該站答題後 RTDB 數字正確累加；原站原有功能（錯題本、歷程、SRS）行為完全不變。

**不做**：`roots`／`repeats`／`abbr`／`demo`（純閱讀，無答題迴圈）；`cohesion*` 11 個檔先擱置，
要做之前先花一輪把它的結構讀清楚再評估（它與獨立 repo `discourse-structure` 的關係也要先釐清）。

---

### ⬜ WP-3 練習系統 Hub（`play/`）＋ 儀表板
**前置**：WP-1（有資料才畫得出圖）
**目標**：把 `play/index.html` 從佔位頁換成真正的入口。

**內容**
- 頂部：等級／XP／連續天數／今日進度；未達當日目標時給一句**不責備**的提示。
- **年級分軌切換**（junior／senior，存進 `progress.track`）。
  🔴 **junior 是預設與主線**（北極星結論 2）：設計、文案、預設值都以高一高二為準，
  senior 是補救路徑。不要做成「衝刺版加一個簡化模式」。
  - 高一高二「打底」：推薦順序 字根 → 單字輪 → 記憶卡；**不顯示學測倒數**（兩年後的倒數只會焦慮）；
    強調構詞與字詞搭配，因為這兩項會複利。
  - 高三「衝刺」：顯示倒數（原站首頁已有倒數邏輯可參考）；推薦順序偏向 單字題 → 錯題修復 → 模擬卷；
    以「本週修好幾題」為主要指標，不是練了幾題。
- 儀表板（Chart.js，cdnjs UMD）：各站正確率長條圖、近 14 天練習量、錯題分類分布。
  **圖要畫到位**：軸標、刻度標到真實數值、深淺色都要可讀（別只在淺色底下測）。
  🔴 **2026-09-14 提醒（下一輪 WP-3 設計時處理，本輪不裁決）**：`game-designer` 指出目前整份計畫只有
  XP/等級/streak 這些外在指標，缺「能力可見」（例如精熟徽章）；WP-8 這輪已產出 `masteredAt`／
  `crossStationVerified` 資料，WP-3 下一輪設計儀表板時應該把這批資料用上，不要只顯示等級數字。
- canvas-confetti 只在**升級**與**修好錯題**時觸發，不要每答對一題就放（會廉價）。

**驗收**：無資料的新帳號進來畫面不是空殼（顯示引導而非空圖）；有資料時圖表數字與 RTDB 對得上。

---

### ⬜ WP-4 番茄鐘 ＋ 碎片時間
**前置**：WP-2（需要真實的每題耗時數據來估題數）、WP-3
**目標**：兩種「時間先決」的練習入口。

**設計**
- **碎片時間（3 分鐘）**：首頁一顆大按鈕，**零設定**。取題優先序：
  ① `cards` 今日到期 ② `wrongItems` 未修復且 missCount 高 ③ 隨機新題。
  🔴 **2026-09-14 提醒**：WP-8 上線後，這裡的取題優先序應改由 WP-8 的每日排隊演算法（政策4+6合併版）
  直接決定，不要維持兩套各自獨立的優先序邏輯並存。
- **番茄鐘（25＋5）**：計時器狀態存 localStorage 並**跨頁存活**（練習發生在各題庫站，不在 Hub），
  由 engine 的 HUD 顯示剩餘時間，時間到提示休息。
- **題數估算要先量、不要猜**：v1 先用保守估計（單字四選一 ~25 秒／題、中翻英 ~120 秒／題），
  同時記錄真實 `msPerItem` 進 `progress.stations`，第二版改用該學生自己的中位數。
  ⇒ 這條是刻意的「measure-first」，不要在 v1 就宣稱時間估得準。
- 出題實作**優先走既有深連結**（§4），不要重寫選題器。

**驗收**：選 3 分鐘實際練完的時間落在 2–5 分鐘；番茄鐘切換頁面後計時不歸零。

---

### ⬜ WP-5 AI 個人化家教
**前置**：WP-2（要有足夠的作答數據與分類）
**目標**：每次 session 結束後，產出一張**具體、有證據、可執行**的建議卡。

**架構**
- Cloud Function `jcee-tutor`（Node 或 Python 皆可）：
  驗 Firebase ID token → 查 `users/{uid}.approved` → 讀 `progress`／`sessions`／`wrongItems`
  → 呼叫 Vertex Gemini → 寫 `advice/{uid}/latest`。
- Vertex 呼叫沿用本機既有模式（**不要重新研究**）：
  `POST https://aiplatform.googleapis.com/v1/projects/<proj>/locations/global/publishers/google/models/gemini-3.7-flash:generateContent`，
  `google.auth.default(scopes=['cloud-platform'])` ＋ `AuthorizedSession`，`responseMimeType: application/json`、低溫。
  參考實作：`E:\Downloads\課程管理與備課\_文官學院AI實作\_teacher_screening\screen_submissions.py`。
- **絕不把 service account 金鑰放進前端。** 前端只拿 ID token 呼叫 Function。

**建議卡的四個欄位（這是「家教做得好不好」的關鍵，不要簡化成一句鼓勵）**
1. `diagnosis` — 一句**具體**診斷，講模式不講分數。
   例：「你錯的 7 題裡有 5 題是字詞搭配，不是不認識那個字。」
2. `evidence[]` — 2–3 個**真實題目**，附 deepLink 直接跳回該題的**站上既有解析**。
   🔴 引用既有解析，不自己生成文法解釋。
   🔴 **2026-09-14 提醒（english-teacher 真身審查發現，下一輪找輸出樣本覆核）**：目前只有原則性要求，
   沒有機制強制檢查「引用是否存在、是否真的對應該題考點」，AI 在信心不足時可能自己補一句聽起來合理
   但其實自編的文法說明。這是 WP-5 上線前最優先要驗證的風險，不在本輪 WP-8 裁決範圍內處理。
3. `nextAction` — **一個**動作，且要合乎他現在有多少時間（讀 `sessions` 的典型時長）。
   例：「先花 5 分鐘把這 3 題的解析看完，再做同類型 5 題。」
4. `officialStat` — 有官方數據時拿來校準情緒。
   例：「這題全體考生答對率 23%，你錯了不奇怪——但它考的是搭配，值得弄懂。」

**語氣**：對象是補不起習的學生，**不製造焦慮、不說教、不比較排名**。
把「你不會」翻譯成「這一類還沒練夠」。

**成本與頻率**：session 結束才呼叫、且做 debounce（同一人 10 分鐘內最多一次）；快取在 `advice`。
Gemini Flash 這種量級成本極低，但仍應在 Function 內設每人每日上限。

**驗收**：造 3 種假數據（全對／集中錯搭配題／散錯），三次輸出的 `diagnosis` 明顯不同且說得中；
`evidence` 的 deepLink 點得進正確題目。

---

### ⬜ WP-6 真人老師報表與討論機制
**前置**：WP-5
**目標**：楊老師能依固定週期的報表，跟學生做實質討論。

**做法**
- `reports/{uid}/{periodId}`，periodId 用 ISO 週（`2026-W38`）。
- **v1 用「開啟時生成」，不架排程器**（省一整套 Cloud Scheduler 基礎設施）；
  週期性自動生成留到確定要用再做。
- 老師端（`gate/admin.html` 擴充或另開 `gate/reports.html`）：學生清單 → 單一學生報表 →
  練習時數／正確率趨勢／弱項分類／AI 建議歷史／反覆錯的題 → **老師寫討論註記**。
  🔴 **2026-09-14 新增**：`floorHit`（WP-9底線偵測）**跨多次session反覆觸發**時，要在學生清單/
  單一學生報表**顯著標示**（不是埋在一般統計裡）——這是WP-9安全網文案裁決（§7 #12）刻意
  留給人的判斷：系統不自動觸發外部資源建議，但要讓老師**看得到**這個學生反覆掙扎，
  由老師（有實際脈絡的人）決定要不要主動關心。這條資料需求會回頭要求`reports/{uid}`
  的schema包含`floorHit`次數與時間分布，本輪先記需求，細部欄位設計留給WP-6正式設計棒。
- 學生端在 Hub 顯示「老師的話」，並記 `studentSeenAt`（讓老師知道學生看了沒）。
- 報表上明確標示數據為學生自陳（見 §3.3）。
  🔴 **2026-09-14 提醒**：「精熟」／「攻克」字樣旁必須標**觀察次數**與**資料期間**、樣本數過小的 KC
  要明確標「資料不足，尚無法判斷」（不要顯示空白或 0%，會被誤讀成 0 分）；`crossStationVerified:false`
  時一律顯示「此站已穩定」而非「精熟」。細節見 §5 WP-8 政策7。

**驗收**：老師寫的註記，學生端看得到；學生看過之後老師端顯示已讀。

---

### ⬜ WP-7 系統代理人化
**前置**：WP-2 以後（有重複性工作才值得代理人化）
**目標**：把重複性維運工作固化成子代理人，沿用本機既有慣例。

**慣例**（照做，不要另立一套）
- 定義檔放對應專案的 `.claude/agents/*.md`；frontmatter 的 `description` 含 `<example>` 時**整串要單引號包住**。
- 收尾一律呼叫 `board.append(...)` 寫黑板（`_flipclass_rollcall/board.py`），
  **不要手動組 JSON**（`ts` 交給 board.py 產生）。
- 🔴 全機每日 spawn 上限 60（硬上限，不可用 override 突破），派工前先看用量。

**建議的代理人**
1. `jcee-station-instrumenter` — 把 engine 掛進某一站。**這隻最值得做**：WP-2 每站流程完全相同
   （讀作答函式 → 插 hook → 版本遞增 → push → curl 驗證 → 回報），正是代理人化的標準情境。
2. `jcee-gate-ops` — 整理審核佇列與異常登入給楊老師看。**不自動核准**（核准是人的決定）。
3. `jcee-tutor-tuner` — 家教提示詞調校與抽樣品質檢查（跑固定測試集、比對輸出、回報退步）。
4. **UI 微調直接用既有的 `worksheet-ui-tuner`**——它當初就寫成 repo 路徑作參數、不綁 nacs-worksheet，
   本 repo 可直接沿用。**不要再造一隻同功能的。**

---

### 🟨 WP-8 教學決策層（**這是「智能」的所在**）— 2026-09-14 五位專家審查＋裁決定案
**前置**：WP-2（要有分類過的作答資料）**＋ Phase 0 資料層補丁（見下，是政策7能不能成立的地基，必須先於政策引擎本身完成）**
**目標**：回答一個問題——**給這個學生、現在、下一題是什麼**。
番茄鐘、碎片時間、AI 家教都只是這一層的外殼；沒有這一層，那些只是隨機出題加計時器。

> 本工作包 2026-09-14 首版由五位專家（`learning-scientist` 真身、`assessment-expert`／`game-designer`／`ux-designer` 模擬、
> `english-teacher` 真身）審查，`cycle-designer` 裁決衝突後於同日修訂本節。
> **裁決理由、未採納的意見、待定事項全部寫在 `docs/cycle/wp8-2-design.md`，本節只放定案後的政策文字與驗收標準。**

#### Phase 0：資料層補丁（🔴 本輪新增，必須先做，否則政策7無法運作）

現有 `progress`／`sessions`／`wrongItems` 三張表**沒有一張能支撐「同一 KC 間隔 ≥7 天再測連續答對」的判定**——
`progress.stations` 只有站層級累計、沒有 KC 維度和時間序列；`sessions` 不記逐題；`wrongItems.repairedAt`
是單一值不是序列，答對從不留痕。這件事不解決，**「攻克」「精熟」這兩個詞在任何使用者可見畫面都不能出現。**

新增節點（追加在 §3.2 資料模型之上，不改變既有欄位語意；建置時比照 WP-1 做法第7點「先 GET 全份規則 →
合併 → PUT 回去 → 驗證」流程去追加，不要覆蓋其他命名空間）：

```jsonc
progress/{uid}/kc/{kcId}: {
  attempted: number,
  correct: number,
  recentWindow: [{ at: ms, correct: bool, itemId, sessionId, station }],  // 上限 10 筆
  consecutiveSpacedCorrect: number,   // 0–3；「獨立事件」規則成立時，答對+1(上限3)、答錯-1(下限0)，不整組歸零（2026-09-14 v2：採納mutator突變提案方案A，見 docs/cycle/MUTATIONS.md #1）
  lastTestedAt: ms,
  lastTestedSessionId: string,
  masteredAt: ms | null,        // consecutiveSpacedCorrect 最近一次由2升到3(達成/重新達成精熟門檻)的時間；一旦設定，之後即使被撤銷也不清空，保留「曾經精熟過」的歷史事實
  demotedAt: ms | null,         // 新增欄位。consecutiveSpacedCorrect 最近一次由3降到2(精熟後首次獨立事件答錯，即精熟被撤銷)的時間；重新達到3時清空為null
  crossStationVerified: bool    // 最近一次consecutiveSpacedCorrect達到3時，湊滿這3次的獨立答對事件是否分屬≥2個不同站（回溯 recentWindow 判定）
}

progress/{uid}/recentAttempts: [{ at: ms, station, kcId, correct: bool, sessionId }]
  // append，上限最新 30 筆——WP-9「最近20題」滾動窗口直接讀這裡，不必重掃 sessions 全表

wrongItems/{uid}/{itemKey}: {
  ...既有欄位不變,
  repairHistory: [{ repairedAt: ms, sessionId }]
  // 取代單一 repairedAt 語意；repairedAt 保留為 repairHistory 最後一筆的鏡像值，向下相容既有讀取程式碼
}
```

**KC 鍵值格式**：`kcId = ${station}:${contentKey}`（定義見政策1/2）。

**政策組成**

1. **知識成分歸因與 KC 鍵值定義**：`kcId = ${station}:${contentKey}`，`contentKey` 只取內容/考點維度：
   - gsat／zhikao：`contentKey` = 該題目標單字（headword）；`collocation` 欄位若存在，記為該次作答的屬性
     `hasCollocation` 與原文字串，不進鍵值本身（該欄位目前是逐題自由文字，還沒有可跨題共用的分類）。
   - wordwheel：`contentKey` = 該題所屬字族（`DATA[].k`，如 `re-`、`-tion / -sion`）。
   - cards／translate／class：沿用該站既有題型分類欄位；沒有的用單字本身。
2. **答題行為分類獨立於 KC 鍵值**：`t`（wordwheel 的 parse/pos/sense/infer/fake）與任何「答題行為/錯誤類型」欄位，
   一律記為每次作答的 `errorMode` 屬性，**不得**進入 KC 鍵值、不影響精熟判定與排程；
   用途是給 AI 家教與老師報表寫診斷語句（「你常見的錯誤型態是猜字義」），這是跟「這個 KC 穩不穩」不同的分析維度。
   🔴 兩者混用會讓歸因方向跟錯（`english-teacher` 真身審查發現，其餘四份審查都沒提到）。
3. **題目難度 `d`**：優先用大考中心官方答對率（`d = 1 − 答對率`，原站多數題目都有，這是罕見資產）；
   沒有的用站內累積作答估；都沒有給中位數並標記為估計值。
4. **學生對該 KC 的能力 `θ`**：該 KC 的加權近期正確率。冷啟動用該年級先驗，
   **直到該生在此 KC 累積作答數 ≥5 題後，先驗全面讓位給實測 θ**。
5. **難度targeting**：`p_raw = 0.5 + (θ − d)`；展示/防呆用 `p = clamp(p_raw, 0, 1)`。
   **排序鍵一律用 `p_raw`**（未 clamp 的原始差值）計算 `|p_raw − 0.85|` 最小者優先，
   clamp 後的 `p` 只用於對外顯示（避免呈現 >100% 或 <0% 的機率），不用於排序——
   避免 θ 與 d 差距大時多個候選同時撞頂/撞底、tie-break 退化成任意選。
   🔴 **公式要能用一句話解釋**——`assessment-expert` 會要求，解釋不了的模型不准上。
   **🔴 2026-09-14 已定案（`assessment-expert` 真身複審 §7 待決事項#7 後，`cycle-designer` 裁決採納）**：
   **維持現行線性公式，不換 logistic/Rasch**。理由：換模型解決的是「輸出跑出[0,1]」，但不解決
   「θ（個人小樣本、噪）跟 d（全國大樣本、穩）直接線性相加」這個真正的訊噪不對稱問題——這是
   兩個獨立問題，換曲線形狀對第二個問題沒有幫助；且公式失真最嚴重的區域（`|θ−d|>0.5`）跟
   選題排序鎖定的區域（`θ−d≈0.35` 附近，即 `|p_raw−0.85|` 最小）大致互斥，clamp 造成的失真在
   實際決策相關的選題範圍裡影響可忽略（**理論推導，未經真實資料驗證**）；已生效的 tie-break
   修正（排序鍵用 clamp 前的 `p_raw`）已解決本輪唯一真正會被使用者感受到的問題；logistic/Rasch
   的「一句話解釋」草稿本身比現行公式更難懂，違反本專案「一句話解釋得完」的紅線；真正的 Rasch
   需要校準資料，本專案目前 0 個真實學生資料，校準不了。**重新評估觸發條件**（已存入
   `docs/cycle/PARKED.md` 第 4 項）：(a) 累積到有真實學生複習資料可以校準參數，或 (b) 真人測試/
   實際資料顯示 `|θ−d|>0.5` 這個「理論上互斥」的假設不成立（例如低正確率學生的 θ 剛好落在跟排序
   決策相關的範圍內、clamp 失真真的被感受到）——任一條件滿足時，由 `assessment-expert`（真身）
   重新評估。**新增 display-guard 規則**：老師報表／任何使用者可見畫面，一律只能顯示 `clamp` 後的
   `p`（並標「系統估計，非精確機率」），永遠不能顯示未 clamp 的 `p_raw`（可能是 145% 或 -50% 這種
   荒謬數字）——比照現有防「攻克」字樣外洩的紅線機制，機械驗收見下方第 17 條。完整裁決全文見
   `docs/cycle/wp8-2-design.md`「2026-09-14 v2 追記」小節。
6. **每日排隊演算法（到期複習優先序 vs 新舊比例，合併政策，取代舊版政策4+6）**：
   ```
   每日排入 N 題：
   1. 到期複習集合 R（cards SRS 到期 ∪ 非卡片站簡單間隔表(1/3/7/21/60天，答錯退一階) ∪ wrongItems 未修復），
      依逾期天數與 missCount 排序。
   2. 複習配額上限 = ceil(0.7×N)；新題配額上限 = floor(0.3×N)。
      頭兩週複習/新題配額各改為 ceil(0.5×N)，兩週後切回 70/30。
   3. 若 |R| ≥ 複習配額上限：複習排滿配額上限，新題仍照配額出，新題保底至少 1 題（N≥2 時）。
   4. 若 |R| < 複習配額上限：複習全部排入，缺口轉給新題，但當日新題總數不得超過 ceil(0.5×N)；
      唯有 R 與新題候選都不足以填滿 N 的極端情況才允許超過，並標記 `queueFillMode:'shortage'`。
   5. 交錯規則（政策7）套用在最終排序後的整條隊列，不是分開排兩段再串接。
   ```
7. **交錯**：同一 KC 連續不超過 2 題；且**同一 KC 兩次出現之間至少間隔 3 題不同 KC**
   （初始值，之後依真實資料調整）。
8. **精熟判定（這同時是「攻克」的操作型定義，全計畫最重要的一段文字，2026-09-14 v2 修訂——採納`mutator`突變提案方案A，裁決見 `docs/cycle/MUTATIONS.md` #1）**：
   > `consecutiveSpacedCorrect`（範圍 0–3）是唯一驅動精熟狀態的計數器：
   > - **獨立事件**（定義不變）：距上次對此 KC 的作答 ≥7 天，且與上一次被計入的獨立事件不在同一個 `sessionId`。
   > - 每次獨立事件發生：**答對 `+1`（上限3，不再往上累加）；答錯 `-1`（下限0，不是整組歸零重算）**——一次失誤退一步，不作廢先前累積的證據。
   > - `consecutiveSpacedCorrect` 由 2 升到 3 的那一刻＝**達成精熟門檻**：`masteredAt` 設為該次事件時間；`demotedAt` 清空為 `null`；`crossStationVerified` 依湊滿這 3 次的獨立答對事件（回溯 `recentWindow`）判定——這 3 次分屬 ≥2 個不同站則 `true`，對外顯示「精熟」；否則 `false`，對外顯示「此站已穩定」（含該 KC 只存在單一站的情況）。
   > - `consecutiveSpacedCorrect` 由 3 降到 2 的那一刻（已達成精熟門檻的 KC，其後第一次獨立事件答錯）＝**精熟被撤銷**：`demotedAt` 設為該次事件時間；`masteredAt` **保留原值不清空**（歷史事實：曾經達到過精熟門檻，供老師報表/AI家教顯示「曾精熟後退步」）；對外顯示退回一般練習中的顯示，不得使用「攻克」「精熟」「此站已穩定」任一詞。
   > - 若之後 `consecutiveSpacedCorrect` 重新由 2 升到 3（重新達成）：`masteredAt` 更新為新的達成時間、`demotedAt` 清空為 `null`、`crossStationVerified` 依新一輪湊滿 3 次的獨立答對事件重新判定——可反覆發生，不限一次。
   > - 「攻克」一詞只能在 `consecutiveSpacedCorrect===3 且 crossStationVerified:true` 時使用；`consecutiveSpacedCorrect===3 且 crossStationVerified:false` 一律用「此站已穩定」；`consecutiveSpacedCorrect<3`（含剛被撤銷的狀態）一律不使用「攻克」「精熟」「此站已穩定」任一詞。
   > - 🔴 **在 Phase 0 資料層補丁通過驗收前，「攻克」「精熟」兩詞禁止出現在任何使用者可見畫面。**
9. 🔴 **每一題都要帶得出「為什麼給你這題」的一句話**（`reasonText`，掛在該次作答紀錄上），存進資料，
   **且必須呈現給學生本人**，不只是給老師報表/AI家教看：放在作答**之前**（題幹旁小徽章，預設收合，
   點/tap才展開），不放進答題後的解析資訊堆疊（會跟站內既有解析資訊混在一起、時間點也不同）。
   AI 家教與老師報表都靠它；解釋不出來的推薦，學生沒理由信。

**新增：WP-1 記分規則的一致性加成**（不改變既有 base，附加項，見 WP-1 做法第1點的介面擴充）：
`JG.answer` 新增可選欄位 `followedRecommendation: bool`（省略預設 `false`，向後相容）。
當該題來自 WP-8 建議、`followedRecommendation=true` 且答對，額外 +2 XP，疊加在既有 +10/+2/+15 之上——
用來抵消「挑軟柿子站刷 XP、迴避系統推薦的難站」這個誘因（`game-designer` 發現）。

**驗收**
1.（正）造強／中／弱三種假學生，policy 選出的題目難度分布明顯不同（列出三組 `p_raw` 中位數）。
2.（正）任取連續10題，同一 KC 不超過2題連續，且同一 KC 兩次出現間隔 ≥3 題不同 KC。
3.（正）每個決策都取得出那句理由（`reasonText`），且理由與實際選題依據一致（抽查10筆），
   並確認該理由被標記為「作答前呈現」而非只存 log。
4.（負）能力貼近亂猜的假學生，policy **不回傳題目**，回傳觸底訊號（交給 WP-9）。
5.（正，政策8機械驗收）造「同一天故意把同 KC 到期複習題連刷3次」的假學生，驗證系統**不會**標記
   `masteredAt`（因為3次都發生在同一 `sessionId`，不算獨立事件）。
6.（正，政策8機械驗收）造「同一 KC 間隔8天、9天、10天各答對一次、且三次分屬三個不同 session」的假學生：
   驗證第3次事件後 `masteredAt` 被設定；若三次都在同一站，驗證對外顯示為「此站已穩定」；
   若其中一次在不同站（且該 KC 確有跨站對應題），驗證顯示為「精熟」且 `crossStationVerified:true`。
7.（負，政策8機械驗收，2026-09-14 v2修訂：原「歸零重算」已依mutator突變提案方案A改為「扣點」，見MUTATIONS.md #1）造「四次獨立事件依序為：答對、答對、答錯、答對」的假學生，驗證 `consecutiveSpacedCorrect` 依序變化為 1→2→1→2（第三次答錯是扣1而非歸零到0），第4次事件後仍未達到3、`masteredAt`仍為null、不判定精熟；
    追加第5次獨立事件答對後 `consecutiveSpacedCorrect=3`，此時才設定 `masteredAt`——驗證「答錯不能整組作廢先前證據，但也不能3次裡對2次就湊數過關」同時成立。
8.（正，政策6機械驗收）造「到期複習題數本身超過70%配額」的假學生，驗證當日新題仍保底出現 ≥1 題（N≥2）。
9.（正，政策6機械驗收）造「到期複習不足70%配額」的假學生，驗證缺口由新題補滿，但當日新題總數不超過 ceil(0.5N)。
10.（正，政策6機械驗收）追蹤一個穩定期（非頭兩週）假學生連續30天出題記錄，統計新/複習題比例落在30/70附近（±10個百分點）。
11.（正+負，KC鍵值機械驗收）抽查10筆 KC 記錄，確認鍵值格式為 `${station}:${contentKey}`；
    **負面**：資料庫中不得出現任何一筆 KC 鍵值直接等於 `parse`／`pos`／`sense`／`infer`／`fake` 字串本身。
12.（正，schema驗收）抽查 `progress/{uid}/recentAttempts`，驗證筆數上限生效，且用它就能算出
    WP-9 的滾動20題正確率（不必重掃 `sessions` 全表）。
13.（負，紅線驗收，2026-09-14 v2擴大範圍）在 Phase 0 的第5、6、7、11、12、15、16 條通過前，grep 學生端頁面、老師報表模板、AI家教
    prompt 模板，搜尋「攻克」「精熟」字樣——**任何出現都判定為未通過驗收，不得上線**。
14.（正，tie-break機械驗收）造一個 θ 與 d 差距極大的假學生（例如 θ=0.95、d=0.05），使多個候選
    clamp 後的 `p` 同分；驗證排序改用 `p_raw` 作 tie-break，重跑同一輸入10次結果穩定不隨機。
15.（正+負，政策8機械驗收，新增，2026-09-14 v2：採納mutator突變提案方案A）造「已達成精熟門檻（`consecutiveSpacedCorrect=3`、`masteredAt`已設定）的KC，其後第一次獨立事件答錯」的假學生：驗證 `consecutiveSpacedCorrect` 降為2、`demotedAt` 被設定為該次事件時間、`masteredAt` 保留原值未被清空為null、對外顯示不得出現「攻克」「精熟」「此站已穩定」任一詞、老師報表/AI家教能區分「從未精熟」與「曾精熟現退步」兩種狀態（用`demotedAt`是否有值判斷，不要求特定文案字面）。
16.（正，政策8機械驗收，新增，2026-09-14 v2）延續上一題假學生，追加連續2次獨立事件皆答對：驗證 `consecutiveSpacedCorrect` 回到3、`demotedAt` 清空為null、`masteredAt` 更新為最新達成時間、`crossStationVerified` 依這輪湊滿3次的獨立答對事件重新判定（不沿用被撤銷前的舊值）。
17.（負，紅線驗收，新增，2026-09-14，回應assessment-expert真身複審display-guard建議）造 θ=0.95、d=0.05
    （`p_raw=1.4`）與 θ=0.05、d=0.95（`p_raw=-0.4`）兩組超出[0,1]範圍的假學生，檢查老師報表／學生端／
    AI家教建議卡三處畫面：(a) 正面：顯示的難度/機率數字必須等於 `clamp(p_raw,0,1)`（即100%與0%），
    且緊鄰標註「系統估計，非精確機率」；(b) 負面：grep 三處畫面模板原始碼，不得出現直接綁定/渲染
    未clamp的 `p_raw` 變數本身（例如渲染出140%、-40%這類荒謬數字）——任何一處違反都判定未通過驗收，
    不得上線。

---

### 🟨 WP-9 底線偵測與誠實路由（M 型化） — 2026-09-14 Phase 1-3 已建置，Phase 4文案審查進行中

> 見 `docs/cycle/wp9-2-design.md`。`red-team-critic` 主審找到1致命+3嚴重問題，其中2項已被
> WP-1施工意外解決（`recentAttempts`／`forceStreakCredit`已建置）；roots深連結缺口升級為
> build的硬性阻斷前置條件（已給補丁介面契約）；安全網「指向外部資源」文案定案候選A先進build，
> **候選B/C（要不要加碼校外心理支持資源）需要楊老師決定，見§7**。
> **2026-09-14 追加**：Phase 1-3 已由 `cycle-builder` 建置完成（`game/floor-logic.js`、
> `JG.getRecentWindow`/`getFloorState`/`setFloorState`、`wordwheel.html`/`roots/index.html`接線）；
> 驗收標準1/4/5/6/7/8/9/11本輪已用node直接驗證通過，標準2/10需瀏覽器環境、標準3(b)需真人
> 確認才能關閉。候選A文案同一時間經 `english-teacher` Phase 4真身審查判定v1不通過，
> `cycle-designer` 部分採納裁決為v2（已同步替換進UI），v2尚未跑過第二輪真身審查，
> 驗收標準3(b)仍未關閉。
**前置**：WP-8
**目標**：系統發現自己幫不上這個學生時，**誠實說出來並指路，而不是繼續餵他失敗**。

> 來源：`red-team-critic` 常設挑戰 1。初版計畫的七個工作包**沒有任何一個涵蓋這件事**。
> 這是內容層的問題，不是演算法調得出來的——題庫最低階仍是學測級。
> 🔴 **2026-09-14 補充**：`game-designer`（機制風險）與 `ux-designer`（UX 風險）在 WP-8 那輪審查裡
> 一併看了本節，`cycle-designer` 裁決後補上下面幾條；**訊息文案本身尚未經 `red-team-critic`（主審）審查**，
> 這是待定事項，不是本輪能關閉的缺口，見 `docs/cycle/wp8-2-design.md`「需要人決定的問題」。

**設計**
- **偵測**：滾動視窗（最近 20 題，讀 `progress/{uid}/recentAttempts`）正確率 ≤ 亂猜水準（四選一 25%）
  加誤差，取 **≤30%**；或連續 8 題錯。
- **觸發後停止出題**。不要再給下一題。
- **訊息**：不責備、不假裝、不用「加油／再試一次」把他推回去。
  講清楚「這一段對你現在太難，這不是你的問題，是這個題庫的最低階就是學測級」。
- **降階路由（只用站上真實存在的東西，不編造）**：
  - `wordwheel.html` 是**段考範圍**（L1–L3 課本、U9–U12 核心字彙），**不是學測級**
    ——這是站內真實存在的較低一階入口。
  - `roots/` 字根家族表是查閱表、視覺化、不需作答，可無壓力探索。
  - 要誠實說明：這兩個也不是「基礎英文」課程。
  - 🔴 導向字根表時附加一句提醒：「這是理解工具，不是必修進度，不勉強」——`english-teacher` 指出
    字根表對真正低閱讀能力（連基礎拼字規則、音節切分都不穩）的學生可能是多一層抽象，
    但量化的先備條件門檻沒有資料訂不出來，本輪不做行為攔阻，只加這句提醒（見 §7 待決事項）。
- **連降階都撐不住時**：誠實說這個系統幫不上，指向外部資源（**文案定案為候選A「去找你的英文老師」**，
  見 §7 #12——不加碼校外心理支持資源，理由與擱置條件見 `docs/cycle/PARKED.md` 第1項）。
  🔴 **2026-09-14 更新**：候選A逐字文案經 `english-teacher` Phase 4 審查後由 `cycle-designer` 裁決
  修訂為v2（原v1「超出你現在能穩定練習的範圍」被指出是委婉包裝的責備語氣、「這裡」指代不清），
  這裡的「去找你的英文老師」這個方向本身沒變，只是逐字措辭換了版本——**完整v2定案文字見
  `docs/cycle/wp9-2-design.md`「候選A」小節，此處不重複貼一份避免兩處各自漂移**。
  **不要把人留下來反覆失敗。**
- 🔴 **2026-09-14 新增：觸底後立刻安排信心重建，不只是轉去簡單題庫就結束**——「英文不好、
  正在掙扎」這個觀察本身是對的，系統該做的回應範圍在**教學/UX設計**，不是心理介入：
  降階後的**前1-2題**應優先選幾乎穩贏的內容（例如該生近期已經精熟的KC、或明顯低於他當前θ的題目），
  讓他先體驗到「我答對了」，而不是單純把他丟進一個新題庫繼續碰運氣。這條屬於 `game-designer`／
  `ux-designer` 職權，尚未寫進驗收標準，下一輪WP-9細部設計時要補。
- 資料記 `floorHit`，老師報表要看得到（這是老師最該知道的事之一）——**且反覆觸底（跨多次
  session，不是單一次）要在WP-6老師報表裡顯著呈現**，這是「學生反覆掙扎」這個觀察該被
  接住的正確位置：讓真正認識這個學生的老師決定要不要關心，不是系統自動觸發外部資源建議
  （見 §7 #12 的裁決理由）。
- 🔴 **色彩**：不沿用站內 `.wrong` 的錯誤紅/橘（學生連續看到多題紅色後，路由畫面再用同色系會被讀成
  「第9個懲罰」）——改用站內既有 `--teal`（代表答對/核心的正向色）當主色。
- 🔴 **不用彈窗**：比照 wordwheel 既有「這一輪做完了」直接替換 `qstem` 文字＋清空選項＋換按鈕文案的模式，
  不做需要主動關閉的 modal（額外的「關閉」動作對挫折學生是不必要的心理成本）。
- 🔴 **一步到位**：一顆主要按鈕直接 deepLink 到選定的降階站，次要選項用文字連結列在旁邊，
  不要求先「了解」再顯示選單再選（等於挫折學生要多點一次）。
- 🔴 **路由目的地不能是空殼**：連結必須帶預設篩選/錨點參數。**已解決（2026-09-14）**：
  `roots/index.html` 原本沒有 `location.hash` 捲動邏輯（讀碼確認，非待人工），已補上 `?lv=`/`?g=`
  query string 讀取（介面契約見 `docs/cycle/wp9-2-design.md`）；**但 2026-09-14 v3 這輪發現實際
  呼叫端（`wordwheel.html` 的 roots 連結）目前沒有真的送出這些參數**，是待補的建置缺口，見該文件
  驗收標準 12，不是本欄原本說的「待人工確認」那種未知狀態。
- 🔴 **重複觸發需要冷卻機制**：完整的「誠實告知＋降階」文案只在同一次觸底事件第一次觸發時完整播放；
  之後在冷卻窗口內（距上次觸發 <24 小時，或該生尚未在此之外連續答對 ≥5 題脫離觸底狀態）重複觸發時，
  只顯示簡短的降階按鈕，不重播完整文案——避免「連續被同一句話擋好幾天」變成聽起來像放棄他。
- 🔴 **floor-hit 當天 streak 不歸零**：觸發當天無論是否完成平常的 ≥3 題門檻，streak 該日視為已完成，
  不能因為被導去 `roots`/`wordwheel` 而斷掉（違反「斷掉的懲罰要溫和」紅線）——
  **這條需要 WP-1 的 streak 計算邏輯配合**，見 §7 待決事項與 WP-1 做法第5點。

**驗收**
- 假學生連續亂答，系統在第 20 題前觸發並停止出題。
- 觸發訊息通過關鍵字檢查：不含「加油」「再試一次」「不要放棄」這類把責任推回學生的話。
- 觸發後給的路由指向站內**實際存在**的頁面（`curl` 驗證 200）。
- **負面**：正常學生（約 70% 正確率）連續 100 題**不得誤觸發**。
- （新增，負面）同一假學生在 24 小時內連續觸發 3 次，驗證只有第一次顯示完整文案，第2、3次顯示簡短版。
- （新增，正面）造「當天觸發 floor-hit 且只完成 2 題」的假學生，驗證當日 streak 仍計為完成、不歸零。

---

## 6. 已定案的設計決策（不要重新討論）

| 決策 | 理由 |
|---|---|
| 純 vanilla，無建置流程 | 配合原站 13 個獨立 HTML 的架構；GitHub Pages 直接部署 |
| 外部套件只用 Chart.js＋canvas-confetti（CDN UMD） | 夠用且輕；不引入框架 |
| 沿用 `gen-lang-client-0929530380`＋獨立 namespace | GCP 專案配額已滿，新建失敗 |
| 管理員以 **email** 判定，不用 isAdmin 旗標 | 避免「第一個管理員要誰來設」的雞生蛋問題 |
| 答錯也給 XP（+2） | 對象是補不起習的學生，不能讓練習變成扣分體驗 |
| 修好舊錯題給最高分（+15） | 真正有效的是回頭修錯，不是刷題量 |
| AI 家教＝固定格式建議卡，非聊天機器人 | 安全可控、可被老師審閱、避免幻覺與衍生內容爭議 |
| 家教建議必須引用站上既有解析 | 品質、可信度、以及 §1 紅線 |
| 高一高二不顯示學測倒數 | 兩年後的倒數只會製造焦慮，不會帶出行為改變 |
| 報表數字以 append-only 的 `sessions` 為準 | `progress` 可被自己竄改（§3.3） |
| **高一高二軌是預設與主線，高三衝刺是補救** | 北極星算術：時間餘裕很大，瓶頸是留存不是進度 |
| **「攻克」＝間隔 ≥7 天且跨場次(不同session)的3次獨立正確事件，且至少1次跨站驗證(若該KC有跨站對應題)；否則對外顯示降級為「此站已穩定」** | 曾經答對一次不叫學會；四選一連續2次猜對機率約6.25%不算可忽略雜訊，n拉高到3並要求跨場次才是站得住的操作型定義（2026-09-14 五位專家審查後由 cycle-designer 修訂，取代舊版「連續2次答對」） |
| **KC 鍵值只取內容/考點維度，不得混用答題行為分類**（如 wordwheel 的 `t`） | 兩者是不同維度，混用會讓精熟判定與 AI 家教歸因方向跟錯（`english-teacher` 真身審查發現） |
| **難度targeting排序鍵改用 clamp 前的 `p_raw`，clamp 只留給呈現/防呆** | θ 與 d 差距大時 clamp 會讓多個候選同分，選題退化成任意選 |
| **難度公式維持現行線性 `p_raw=0.5+(θ−d)`，不換logistic/Rasch；老師報表/任何使用者可見畫面只能顯示clamp後的`p`並標「系統估計，非精確機率」，不得顯示`p_raw`** | 換模型解決不了θ與d訊噪不對稱的真正問題，且0個真實學生資料校準不了Rasch；display-guard比照既有防「攻克」外洩機制（`assessment-expert`真身複審，2026-09-14） |
| **到期複習(政策4)優先，但新題保底≥1題；複習不足時新題補滿但不超過當日50%** | 兩條規則本身沒寫優先序時，不同實作者會做出不一致行為 |
| **難度targeting公式必須一句話解釋得完** | 解釋不了的模型，學生不會信、老師不敢用、我們也查不出錯 |
| **偵測到觸底就停止出題，不用鼓勵話術推回去** | 反覆失敗會讓學生確認「我就是不行」，比沒有系統更糟 |
| **每一題都要帶「為什麼給你這題」的一句話，且要在作答前呈現給學生本人** | 推薦講不出理由就只是隨機出題的包裝；只存log不顯示會浪費「提取失敗後解釋最有效」的時機 |
| **攻克/精熟字樣在 Phase 0 資料層補丁通過驗收前，不得出現在任何使用者可見畫面** | 地基（逐次時間序列）還沒補齊前，這兩個詞沒有資料支撐（`assessment-expert` 審查發現） |
| **WP-9 路由畫面色彩用 `--teal`、不用彈窗、floor-hit 當天 streak 不歸零** | 避免機制（懲罰/驚擾）跟文案（誠實但不放棄）互相打臉（`game-designer`／`ux-designer` 審查發現） |

---

## 7. 待楊老師決定（開工前最好先有答案）

| # | 問題 | 卡住哪個 WP | 為什麼要先決定 |
|---|---|---|---|
| 1 | **測試對象是誰？**（她自己的學生／原作者的學生／少數測試者） | 🔴 **WP-1** | 決定資料模型要不要加「班級／群組」層。之後再加會動到 schema 與規則 |
| 2 | **要不要告訴原作者？** | WP-6 之前 | 禮貌問題、產品問題（她可能願意一起做），也是未來授權對話的自然起點 |
| 3 | **報表頻率？**（每週／每兩週／段考前後） | WP-6 | 決定要不要架排程器，或維持「開啟時生成」 |
| 4 | **AI 家教的語氣**：像老師（穩、指方向）還是像學長姐（近、會共感）？ | WP-5 | 直接寫進提示詞 |
| 5 | **`play/` 要不要串進原站首頁導覽？** | 任何對外開放前 | 目前刻意沒串（測試期間靠直接網址進入） |
| 6 | **真人測試找得到學生嗎？** | 🔴 **WP-9** | WP-9 的對象是低閱讀能力的學生。若找不到真人測，這個 WP 只能標為「未經驗證」上線，不能宣稱有效 |
| 7 | ~~難度公式要不要換成 logistic/Rasch 模型？~~ **已由 `assessment-expert` 真身複審定案（2026-09-14）：維持現行線性公式，不換 logistic/Rasch**——理由、重新評估觸發條件、新增 display-guard 規則見 §5 政策5與 `docs/cycle/wp8-2-design.md`「2026-09-14 v2 追記」小節。 | WP-8 政策5 | 保留列於此供追溯；不再是待決事項 |
| 8 | ~~`roots/index.html` 是否有 `location.hash` 自動捲動邏輯？~~ **已由 `cycle-designer` 讀完整檔（205行）定案回答（2026-09-14）：沒有，目前不支援**——非同步fetch後才建立section id，無hash/query處理。已升級為build的硬性阻斷前置條件，並給出補丁介面契約（`?lv=`/`?g=` query string + scrollIntoView），見 `docs/cycle/wp9-2-design.md`。 | WP-9 路由驗收 | 保留列於此供追溯；不再是待決事項——這是讀碼就能證偽的客觀問題，不需要真人瀏覽器實測 |
| 9 | **字根表降階的先備條件門檻怎麼量化？** | WP-9 | 沒有心理計量資料或真人測試前訂不出來，本輪先不做行為攔阻，只加提醒文案，這是刻意留白 |
| 10 | ~~WP-1「修好舊錯題+15」的跨場次判定補丁，併入哪一輪派工？~~ **已由 `cycle-designer` 裁決回答（2026-09-14，見 `docs/cycle/wp1-2-design.md`）：併入同一輪 WP-1 建置（Phase 1/2/3 一次做完，不拆票），性質屬工程排程判斷，不需另外等楊老師裁示。** | WP-1（設計已定案，待 `cycle-builder` 施工） | 保留列於此供追溯；不再是待決事項 |
| 11 | ~~WP-9 訊息文案本身還沒被 `red-team-critic`（主審）看過~~ **已完成（2026-09-14）**：`red-team-critic` 主審找到1致命+3嚴重，`cycle-designer` 已收斂處理，見 `docs/cycle/wp9-2-design.md`。 | WP-9 | 保留列於此供追溯；不再是待決事項 |
| 12 | ~~WP-9 安全網文案：連降階都撐不住時，要不要加碼校外心理支持資源？~~ **楊老師 2026-09-14 已決定：維持候選A，不採用B/C**——系統唯一能觀察到的訊號是答題正確率，撐不起「這個學生需要心理支持」的推論，把學業困難跳接成心理健康議題是範圍蔓延，且可能對單純英文不好的學生造成不準確的標籤與驚嚇。**這不是「這個觀察不重要」，是路由到別的地方**：真正該接住「學生反覆掙扎」這個觀察的，是WP-6老師報表（見下方新增設計）+人（真正認識學生的老師）判斷要不要關心，不是系統自動觸發熱線建議。**已存入 `docs/cycle/PARKED.md` 第1項**，附明確的重新觸發條件（WP-6反覆觸底訊號上線後可回頭再議），不是直接丟棄。 | WP-9 | 保留列於此供追溯；不再是待決事項 |

問題 1 現行預設（未獲答覆前）：**無群組層、單一扁平使用者清單**，楊老師是唯一管理者。

---

## 8. 派工建議順序

```
WP-1（引擎＋資料層＋wordwheel 跑通）      ← 先做這個，它定義了後面全部的介面
  ├─→ WP-2（其餘站掛勾）  ※ 可分站平行
  │      └─→ WP-8（教學決策層）★ 智能的所在，WP-4/5 都是它的外殼
  │             ├─→ WP-9（底線偵測與誠實路由）★ M 型化，紅隊常設挑戰 1
  │             ├─→ WP-4（番茄鐘／碎片時間）
  │             └─→ WP-5（AI 家教）
  │                    └─→ WP-6（老師報表與討論）
  └─→ WP-3（Hub＋儀表板）  ※ 只需 WP-1，可與 WP-2 平行

WP-7（代理人化）：等 WP-2 開始重複第 2、3 站時再做，那時才看得出該固化什麼
```

⚠ **WP-4／WP-5 的前置從 WP-2 改成 WP-8**（2026-09-14 修正）。
初版把番茄鐘與 AI 家教直接接在 WP-2 後面，等於在沒有教學決策層的情況下做它們的外殼——
那會做出「隨機出題＋計時器」和「講得漂亮但推薦沒有依據的家教」。

**一次只推進一條主線。** 這份計畫的總量是數週的工程，不是一個晚上。

---

## 9. 每個工作包怎麼跑（與代理人團隊對接）

本文件說的是**要建什麼**（WP-1～WP-9）；
[`.claude/agents/README.md`](../.claude/agents/README.md) 說的是**怎麼建**（五棒循環＋11 隻代理人）。
兩者的關係是：**每個工作包各自跑一輪循環**。

```
挑一個 WP
  → 1 構思（方向未定才需要；已寫在本文件的 WP 可跳過）  cycle-ideator
  → 2 設計  相關專家＋red-team-critic 平行發言 → cycle-designer 裁決衝突、產出規格與驗收標準
  → 人確認
  → 3 開發  cycle-builder（只做規格範圍內的事）
  → 4 評估  cycle-evaluator（實跑驗收標準）＋ 相關專家 ＋ student-tester 走查
  → 5 修正  cycle-fixer（只修被點名的）
  → 要改設計的退回第 2 棒
```

### 各 WP 的必要審查者（不是每個 WP 都要全員出動）

| WP | 必要專家 | 必要測試情境 | 為什麼 |
|---|---|---|---|
| WP-1 引擎 | `assessment-expert` | — | 資料結構決定了日後能不能宣稱「攻克」 |
| WP-2 各站掛勾 | — | — | 機械性工作，交 `cycle-builder`＋`cycle-evaluator` 即可 |
| WP-3 Hub／儀表板 | `ux-designer`、`assessment-expert` | A、D | 儀表板上每個詞都是一個宣稱；首次使用不能是空殼 |
| WP-4 番茄鐘／碎片 | `ux-designer`、`game-designer` | D、E | 3 分鐘模式的進入成本；會不會被鑽 |
| **WP-5 AI 家教** | **`english-teacher`（不可省略）**、`learning-scientist` | B、C | **英文內容錯誤是致命的**；且要驗證它沒有自行生成解釋 |
| WP-6 老師報表 | `assessment-expert`、`red-team-critic` | — | 失真的數字會被老師拿去質問學生 |
| **WP-8 教學決策** | **全體五位專家** | A、B、E | 這是系統的大腦，每個角度都會被它影響。**2026-09-14 已完成第一輪裁決，見 `docs/cycle/wp8-2-design.md`** |
| **WP-9 底線偵測** | **`red-team-critic`（主審）**、`english-teacher` | **C（不可省略）** | 這個 WP 就是為了情境 C 存在的。**2026-09-14：`english-teacher`、`red-team-critic` 皆已審，`cycle-designer` 已收斂，Phase 1-3 可交 cycle-builder，Phase 4文案待楊老師決定§7#12才能關閉** |

### 🔴 真人測試不可省略

`student-tester` 是模擬的，只抓得到明顯的牆。
**WP-4、WP-5、WP-9 上線前必須有真人學生測過**，題目用 `student-tester` 產出的
「這個情境最需要真人測試的問題」那份清單。特別是 WP-9——那一段的對象正是最不該被我們猜測的人。
