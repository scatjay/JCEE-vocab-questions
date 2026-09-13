# JCEE Vocab Game — 完整建置計畫

> 建立：2026-09-13 深夜｜**最後更新：2026-09-14 00:15（補 WP-8/9、北極星目標、代理人循環對接）**｜基準 commit：`f0fb953`
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

**首頁另連到 6 個獨立 repo**（作文 `essay-prompts`、學測克漏字 `grammar-cloze-test`、指考克漏字
`zhikao-cloze-test`、文意選填 `passage-completion`、篇章結構 `discourse-structure`、混合題 `mixed-format`）。
那些**不在本 repo 內**，目前不動；未來若要納入，是另一輪 fork 與 §1 紅線的重新確認。

---

## 5. 工作包

### ⬜ WP-1 遊戲化核心引擎 ＋ 資料層
**前置**：無（可立即開工）
**目標**：一份共用引擎，加上 RTDB progress/sessions/wrongItems 的結構與規則，並在**一個**站（`wordwheel.html`）跑通端到端。

**做法**
1. 建 `game/engine.js`（ES module，無外部相依），公開 API 極小：
   ```js
   JG.init({ station })            // 讀 auth 狀態、載入 progress、畫 HUD
   JG.answer({ correct, qid, category, deepLink })
   JG.sessionStart({ mode })  /  JG.sessionEnd()
   ```
2. 建 `game/engine.css`：HUD 浮動徽章（等級／XP 條／連續天數）。
   HUD 刻意用**自成一格的深色＋琥珀色**，不要去配合各站不同的配色（各站色系不一，配不完，
   HUD 本來就該讀起來像疊在內容上的一層）。
3. 計分規則（已定案，見 §6）：答對 +10、答錯 +2、**修好舊錯題 +15**。
4. 等級曲線：`需要的累計XP(n) = round(100 * n^1.4)`，前幾級刻意好升。
5. 連續天數：以**台北時區**日界計算，當日完成 ≥3 題才算數。
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
- canvas-confetti 只在**升級**與**修好錯題**時觸發，不要每答對一題就放（會廉價）。

**驗收**：無資料的新帳號進來畫面不是空殼（顯示引導而非空圖）；有資料時圖表數字與 RTDB 對得上。

---

### ⬜ WP-4 番茄鐘 ＋ 碎片時間
**前置**：WP-2（需要真實的每題耗時數據來估題數）、WP-3
**目標**：兩種「時間先決」的練習入口。

**設計**
- **碎片時間（3 分鐘）**：首頁一顆大按鈕，**零設定**。取題優先序：
  ① `cards` 今日到期 ② `wrongItems` 未修復且 missCount 高 ③ 隨機新題。
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
- 學生端在 Hub 顯示「老師的話」，並記 `studentSeenAt`（讓老師知道學生看了沒）。
- 報表上明確標示數據為學生自陳（見 §3.3）。

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

### ⬜ WP-8 教學決策層（**這是「智能」的所在**）
**前置**：WP-2（要有分類過的作答資料）
**目標**：回答一個問題——**給這個學生、現在、下一題是什麼**。
番茄鐘、碎片時間、AI 家教都只是這一層的外殼；沒有這一層，那些只是隨機出題加計時器。

> 本工作包是 2026-09-14 補上的。初版計畫漏了它——領域簡報 §1 的三個模型裡，
> 領域模型（原站題目自帶）與學習者模型（WP-1）都有，**教學決策是空白**。

**政策組成**
1. **題目難度 `d`**：優先用大考中心官方答對率（`d = 1 − 答對率`，原站多數題目都有，這是罕見資產）；
   沒有的用站內累積作答估；都沒有給中位數並標記為估計值。
2. **學生對該 KC 的能力 `θ`**：該 KC 的加權近期正確率。冷啟動用該年級先驗。
3. **難度targeting**：預測成功率 `p = clamp(0.5 + (θ − d))`，選 `|p − 0.85|` 最小的候選
   （期望難度，見領域簡報 §2）。
   🔴 **公式要能用一句話解釋**——`assessment-expert` 會要求，解釋不了的模型不准上。
4. **到期複習優先於新題**：`cards/` 的 SRS 直接沿用；非卡片站用簡單間隔表
   （1／3／7／21／60 天），答錯退一階。
5. **交錯**：同一 KC 連續不超過 2 題（領域簡報 §2）。
6. **新舊比例**：穩定期約 **30% 新 / 70% 複習**（北極星說時間有餘裕 ⇒ 偏複習）；
   頭兩週可拉高新題比例先建立內容廣度。
7. **精熟判定**：同一 KC 在**間隔 ≥7 天後**再測連續 2 次答對 → 標記精熟，之後只在長間隔出現。
   這同時是「攻克」的操作型定義（北極星結論 3）。
8. 🔴 **每一題都要帶得出「為什麼給你這題」的一句話**，存進資料。
   AI 家教與老師報表都靠它；解釋不出來的推薦，學生沒理由信。

**驗收**
- 造強／中／弱三種假學生，policy 選出的題目難度分布**明顯不同**（列出三組的難度中位數）。
- 任取連續 10 題，同一 KC 不超過 2 題連續。
- 每個決策都取得出那句理由，且理由與實際選題依據一致（抽查 10 筆）。
- **負面**：能力貼近亂猜的假學生，policy **不回傳題目**，回傳觸底訊號（交給 WP-9）。

---

### ⬜ WP-9 底線偵測與誠實路由（M 型化）
**前置**：WP-8
**目標**：系統發現自己幫不上這個學生時，**誠實說出來並指路，而不是繼續餵他失敗**。

> 來源：`red-team-critic` 常設挑戰 1。初版計畫的七個工作包**沒有任何一個涵蓋這件事**。
> 這是內容層的問題，不是演算法調得出來的——題庫最低階仍是學測級。

**設計**
- **偵測**：滾動視窗（最近 20 題）正確率 ≤ 亂猜水準（四選一 25%）加誤差，取 **≤30%**；
  或連續 8 題錯。
- **觸發後停止出題**。不要再給下一題。
- **訊息**：不責備、不假裝、不用「加油／再試一次」把他推回去。
  講清楚「這一段對你現在太難，這不是你的問題，是這個題庫的最低階就是學測級」。
- **降階路由（只用站上真實存在的東西，不編造）**：
  - `wordwheel.html` 是**段考範圍**（L1–L3 課本、U9–U12 核心字彙），**不是學測級**
    ——這是站內真實存在的較低一階入口。
  - `roots/` 字根家族表是查閱表、視覺化、不需作答，可無壓力探索。
  - 要誠實說明：這兩個也不是「基礎英文」課程。
- **連降階都撐不住時**：誠實說這個系統幫不上，指向外部資源。**不要把人留下來反覆失敗。**
- 資料記 `floorHit`，老師報表要看得到（這是老師最該知道的事之一）。

**驗收**
- 假學生連續亂答，系統在第 20 題前觸發並停止出題。
- 觸發訊息通過關鍵字檢查：不含「加油」「再試一次」「不要放棄」這類把責任推回學生的話。
- 觸發後給的路由指向站內**實際存在**的頁面（`curl` 驗證 200）。
- **負面**：正常學生（約 70% 正確率）連續 100 題**不得誤觸發**。

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
| **「攻克」＝間隔 ≥7 天後再測連續 2 次答對** | 曾經答對一次不叫學會；這是可驗證的操作型定義 |
| **難度 targeting 公式必須一句話解釋得完** | 解釋不了的模型，學生不會信、老師不敢用、我們也查不出錯 |
| **偵測到觸底就停止出題，不用鼓勵話術推回去** | 反覆失敗會讓學生確認「我就是不行」，比沒有系統更糟 |
| **每一題都要帶「為什麼給你這題」的一句話** | 推薦講不出理由就只是隨機出題的包裝 |

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
| **WP-8 教學決策** | **全體五位專家** | A、B、E | 這是系統的大腦，每個角度都會被它影響 |
| **WP-9 底線偵測** | **`red-team-critic`（主審）**、`english-teacher` | **C（不可省略）** | 這個 WP 就是為了情境 C 存在的 |

### 🔴 真人測試不可省略

`student-tester` 是模擬的，只抓得到明顯的牆。
**WP-4、WP-5、WP-9 上線前必須有真人學生測過**，題目用 `student-tester` 產出的
「這個情境最需要真人測試的問題」那份清單。特別是 WP-9——那一段的對象正是最不該被我們猜測的人。
