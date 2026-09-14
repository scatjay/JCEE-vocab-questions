# WP-9 底線偵測與誠實路由 — 收斂後正式設計（cycle-designer，2026-09-14）

> 輸入：`red-team-critic` 主審（2026-09-14 07:47:35，黑板列＋`.claude/agents/kb/red-team-critic.md`）、
> `docs/PLAN.md` §5 WP-9 全節（L530-579）、`docs/cycle/wp8-2-design.md`（game-designer/ux-designer 對 WP-9 的既有裁決）、
> `docs/cycle/wp8-2-review-english-teacher.md`（降階內容適切性審查）、
> `docs/cycle/wp1-2-design.md` ＋ 實際已建置的 `game/engine.js`（commit `4f8fb99`，2026-09-14 07:54）。
> 本文件裁決 red-team-critic 提出的四個發現，並把 WP-9 收斂成可直接交 `cycle-builder` 施工的規格。

## 要解決什麼（一句話）

把 red-team-critic 主審找到的「1 致命＋3 嚴重」問題逐一裁決，補齊 WP-9 規格裡真正缺的具體內容
（安全網文案、滾動視窗讀取介面、roots 深連結、streak 補丁排序），讓 WP-9 從「還不能進 build」
變成「可以進 build，但有一項內容需要楊老師先給答案」。

---

## 沿用既有的什麼

- `docs/PLAN.md` §5 WP-9 既有的機制決策（色彩用 `--teal`、不用彈窗、一步到位 deepLink、冷卻機制、
  floor-hit 當天 streak 不歸零）——這些是 game-designer／ux-designer 上一輪已裁定的定案，本文件不重開，
  只在「冷卻機制」與「streak 補丁」兩點補上紅隊發現的實作缺口。
- `game/engine.js`（WP-1 已建置，非草稿）：
  - `JG.forceStreakCredit({reason})`（L128-149）——floor-hit 當天 streak 不歸零需要的入口**已經存在**，
    不需要另外設計或等待補丁，見裁決 4。
  - `progress/{uid}/recentAttempts`（append，上限 30，`sessionEnd()` 內寫入，L257-299）——
    WP-9 讀滾動視窗需要的資料**已經在寫**，見裁決 2。
  - `wordwheel.html` 已接上 `JG.init`／`JG.answer({kcId:...})`／`JG.sessionEnd()`（L253、279-293、311）。
- `evaluateKcEvent`／`computeAnswerGain`（`game/kc-logic.js`）的「純函式、不碰 RTDB/DOM，供
  cycle-evaluator 直接單元測試」這個模式——WP-9 的觸底判定邏輯沿用同一種寫法（見下方介面契約）。
- `roots/index.html` 既有的資料結構（`DATA.groups[].items[]`、`section id="g"+gi`、`state.q`/`state.lv`/`state.examOnly`）
  ——不重寫這個頁面，只在既有 `fetch(...).then(...)` 之後追加一段讀 URL 參數的邏輯（見裁決 3）。

---

## red-team-critic 四個發現逐一裁決

### 發現 1（致命）：安全網「指向外部資源」沒有具體內容

**裁決：不由我單方面拍板最終文案，但本輪就定出一個可以現在上線的保守版本，並把「要不要加碼」列成明確待決問題（附具體選項，不是空手丟回去）。**

理由：這是本專案目前唯一一處「內容涉及未成年學生的真實求助路徑」的地方，其他 WP-9 決策
（色彩、彈窗、冷卻）都是機制層，出錯頂多是體驗不好；這一條若捏造轉介內容或方向不對，
影響的是真實學生在真實困境下會不會被引導到合適的地方——這正是 `_DOMAIN.md` §3 動機紅線
「不做同儕排名」「用官方答對率校準情緒」等條目背後同一種顧慮的更高風險版本，而且我作為
AI 沒有能力代替楊老師承擔「該不該讓系統對學生建議撥打校外專線」這種判斷的後果。

**三個候選文案（供楊老師挑選或修改，不是三選一之外沒有別的可能）**：

| | 文案 | 優點 | 缺點/風險 |
|---|---|---|---|
| A（保守／學業導向） | 「這個系統目前的題目都超出你現在能穩定練習的範圍。去找你的英文老師，讓他知道你卡在這裡——他會比系統更清楚接下來怎麼幫你。」 | 不需要系統知道任何個資／學校配置；不把「單字太難」跟「心理狀態」掛勾，避免不成比例的框架；「老師」是每個學生都有的通用角色。 | 若學生剛好跟老師關係疏離、求助不到人，這句話可能落空、沒有真正的兜底。 |
| B（含全國性求助專線） | 「這一段真的超出這個系統現在能幫你的範圍。你可以跟你的導師聊聊，也可以打 1980（張老師專線，免費、不留紀錄）聊聊。」 | 提供一個不需要透過師生關係就能自己撥打的管道，覆蓋「沒有可信任大人」的情境。 | 1980 張老師專線的定位是情緒／心理輔導，用在「單字太難」這種**學業**情境上可能造成錯位框架——學生可能被嚇到，以為系統認為他有心理問題；這是需要楊老師（作為對學生負責的一方）判斷是否適當的倫理決定，不該由 AI 逕自決定要不要把課業困難跟心理熱線綁在一起。 |
| C（分層，兩者都給但不互相暗示因果） | 先顯示 A 的內容；下方用較小字級另起一行：「如果你現在心情不好、想找人聊聊，也可以打 1980（張老師專線）。」 | 兼顧兩種情境，且用「分成兩句獨立的話」降低錯位框架風險。 | 文案變長；仍然涉及「要不要主動提供心理支持資源」這個需要楊老師拍板的判斷；且這兩句都還沒被 `red-team-critic`/`english-teacher` 針對**逐字文案**本身審查過（他們之前審的是政策與機制層，見下方風險小節）。 |

**本輪定案（可以現在進 build 的部分）**：v1 上線用 **候選 A**。理由：它已經滿足 red-team
「必須指向具體資源、不能是抽象詞」的要求（「去找你的英文老師」是具體、可執行、不涉及未經
確認的敏感內容的動作），且完全不涉及需要監護人／專業判斷的倫理風險，可以現在定案不必等待。

**列為需要楊老師決定、不擋 v1 上線的問題**：是否要疊加 B／C 這類校外心理支持資源。
在楊老師明確回答前，系統**只用候選 A**，不得因為工程師覺得「A 感覺不夠」就自行加碼 B/C 的內容
——這條本身也是本文件的裁決，見下方「需要人決定的問題」。

**額外要求（呼應 red-team 發現 1 裡的另一半，關鍵字黑名單不足以保證文案安全）**：
候選 A／未來若楊老師選 B/C，**逐字文案本身在上線前必須至少過一次 `red-team-critic` 或
`english-teacher` 的真身審查**（不是關鍵字黑名單，是真的讀語感），因為黑名單只能擋「加油」
「再試一次」這種最白目的字面，擋不住委婉包裝的責備語氣或被動語態。這條寫進下方驗收標準第 3 條。

---

### 發現 2（嚴重）：wordwheel 未接 `recentAttempts`，觸底/脫離觸底判定量不到

**裁決：WP-1 建置（commit `4f8fb99`，時間晚於 red-team 審查）已經把「寫入」這一半解決了；
但「讀取」這一半——WP-9 偵測邏輯需要的即時滾動視窗介面——目前完全不存在，這是真正該歸類為
WP-9 自己要交付的新介面，不是重開 WP-1 或 WP-2。**

**已核實（本輪重新 grep，不是照抄 red-team 舊發現）**：
- `wordwheel.html` L284-293 現在確實呼叫 `JG.answer({..., kcId:\`wordwheel:${d.k}\`, ...})`。
- `game/engine.js` L257-299 `sessionEnd()` 確實把每題寫進 `progress/{uid}/recentAttempts`（append，
  上限 30，含 `station`／`correct`／`sessionId`）。
- **紅隊原本擔心的「學生在被降階的地方怎麼答都不會被系統看見」這個風險已經解決**：
  `recentAttempts` 每一筆都帶 `station` 欄位，不是只記觸發時的那一站；因此在 wordwheel（降階目的地）
  答對的題目，會被記進同一份 `recentAttempts`，可以被拿來計算「冷卻期外連續答對 ≥5 題脫離觸底」。

**但發現一個 red-team 沒抓到、比他原本描述更精確的新缺口（本輪讀 `engine.js` 原始碼才發現）**：
`progress/recentAttempts` **只在 `sessionEnd()` 時才寫入**，`this.session.items`（當下這一場作答的
逐題記錄）在場次結束前只存在記憶體裡、沒有任何公開方法可以讀取。也就是說：如果觸底偵測要在
「同一場次進行中、每答一題就檢查一次最近 20 題」，現在的介面完全讀不到「這一場目前為止已經答的題」，
只能讀到「上一場（或更早）留下的最新 30 筆」——若學生在同一場連續作答超過 20 題，`recentAttempts`
在這場結束前會是**過期的**，偵測會漏看剛發生的连续失败。

**裁決：這是 WP-9 build 任務裡必須新增的公開介面，寫進本文件的介面契約，不是留白**（見下）。

---

### 發現 3（嚴重）：roots 深連結未實作，被誤放進 §7 軟性待決事項

**裁決：升級為 WP-9 build 的硬性阻斷前置條件（blocking gate），不再是「待人工瀏覽器確認」的軟性項目。**

理由：本輪直接完整讀了 `roots/index.html`（205 行，非截斷），可以**不靠人工瀏覽器**、單純從程式碼
就確定結論，不需要停在「待確認」：
- 全檔沒有任何 `location.hash`、`URLSearchParams`、`hashchange` 相關程式碼。
- 頁面上唯一的錨點（`<a href="#g"+gi>`）是在 `fetch('roots_data.json')` **非同步**完成、`render()`
  跑完之後才被動態建立的（L92-159）；也就是說，若使用者一開始就帶著 `#g3` 這樣的網址進站，
  `<section id="g3">` 在瀏覽器解析初始 HTML 的當下根本還不存在——現代瀏覽器不會在內容於頁面
  載入後才非同步出現時，回頭重新捲動到那個片段（除非頁面自己額外處理）。
  ⇒ **這不是「可能有 bug、需要人在瀏覽器點點看確認」，而是程式碼裡確定沒有這段邏輯**，
  `docs/cycle/wp8-2-design.md` 待決事項 #2 把它列成「需要人工在瀏覽器實測確認」是可以本輪關掉的——
  不需要瀏覽器，讀碼就能定案：**目前不支援**。

`red-team-critic` 說得對：這件事被放進 §7「軟性待人工確認」等於把一條**已知會讓 WP-9 自己的紅線
「路由目的地不能是空殼」直接失敗**的技術缺口，降級成了可以延後處理的小事。一個「一步到位」按鈕
把學生導去 `roots/index.html`（不帶查詢參數）等於丟給他一個空白搜尋框——這正是 WP-9 §5 定案文字
自己禁止的事。

**具體要補的介面契約（本文件定義，供 cycle-builder 施工，屬於 WP-9 build 範圍內的小補丁，
不是另開一張 WP-2/roots 的票——邏輯跟 WP-8 Phase 0 併入同一輪的判斷一致：同一個人一次做完，
不拆票增加協調成本）**：

```js
// 追加在 roots/index.html 現有 fetch('roots_data.json').then(d=>{ ... render(); }) 內、render() 之後：
const params = new URLSearchParams(location.search);
const lv = params.get('lv');          // 例："1,2" → 預設勾選第1、2級
if (lv) {
  lv.split(',').forEach(n => { const i = parseInt(n, 10); if (i) state.lv.add(i); });
  render(); // 依新的 state.lv 重繪，並同步 lv 篩選按鈕的 aria-pressed
}
const g = params.get('g');            // 例："re-" → 對應 DATA.groups 裡 key===g 的那個家族
if (g) {
  const gi = DATA.groups.findIndex(x => x.key === g);
  if (gi >= 0) document.getElementById('g'+gi)?.scrollIntoView({behavior:'smooth', block:'start'});
}
```

用 **query string**（`?lv=1,2` / `?g=re-`）而不是 `location.hash`——因為這個頁面的內容是 `fetch` 完成後
才動態建立，`hash` 依賴瀏覽器原生錨點捲動（在動態內容場景下不可靠），`URLSearchParams` 讀取完全
由頁面自己的 JS 控制時機，不受這個限制。WP-9 路由連結因此要組成
`../roots/index.html?lv=1,2`（依降階當下這名學生的年級/程度給預設级別；若判�is不出程度，
不帶 `lv` 參數，讓學生看到完整清單而不是誤篩選掉他該看的內容——**寧可不篩選也不要篩錯**）。

---

### 發現 4（嚴重）：floor-hit 當天 streak 補丁跟 WP-9 上線順序沒鎖死

**裁決：這個補丁在紅隊審查**之後**、本輪讀碼查證前，已經被 WP-1 實際建置完成——不需要再新增
一條「等 WP-1 補丁」的阻斷條件，因為依賴的東西已經存在。這是本次收斂裡最好的消息。**

**已核實**（`game/engine.js` L128-149）：`JG.forceStreakCredit({reason})` 已經實作，效果如契約所述：
把當天 `todayCount` 灌到 ≥3（等同正常完成 3 題的效果），不改變 XP／`recentAttempts`／`wrongItems`，
只動 `streak` 這一個節點。這正是 `docs/cycle/wp8-2-design.md` 當時要求的「留得住訊號的入口」。

**仍然要保留的**（不是新阻斷條件，是既有驗收標準要照跑）：`docs/PLAN.md` §5 WP-9 驗收標準
「造『當天觸發 floor-hit 且只完成 2 題』的假學生，驗證當日 streak 仍計為完成、不歸零」這一條
（L578）到目前為止還沒有人實際跑過（`cycle-builder` 的收尾紀錄裡列的是 WP-1 自己 13 條驗收，
不包含這條——這條屬於 WP-9 的驗收范圍，要等 WP-9 build 時才會被觸發呼叫並驗證）。
本文件把它保留在下方驗收標準清單裡，不需要另外訂「等 WP-1」的阻斷順序，因為 WP-1 那一半已完成。

---

## 介面契約（函式/資料/路徑/權限）

### A. 新增資料節點：`progress/{uid}/floorState`

```jsonc
progress/{uid}/floorState: {
  active: bool,                          // 目前是否處於觸底狀態（尚未脫離）
  firstTriggeredAt: ms,                  // 目前這次觸底事件第一次觸發的時間
  lastTriggeredAt: ms,                   // 最近一次「重複觸發」的時間（用於24小時冷卻判斷）
  consecutiveCorrectSinceTrigger: number,// 觸發後，跨任意站累計的連續答對數（見下方純函式）
  triggerCount: number                   // 累計觸發次數（老師報表要看得到，對應 §5 原文「資料記 floorHit」）
}
```

沿用既有權限模型（同 `docs/cycle/wp1-2-design.md` 介面契約 F 的假設與但書）：
`floorState` 是 `progress/{uid}` 底下的子欄位，若現行 RTDB 規則是物件層級授權則自動繼承；
若規則是逐欄位白名單，建置時要用「先 GET 全份規則→合併→PUT 回去→驗證」流程補上這個欄位，
**這只是假設不是已驗證事實**，跟 WP-1 當時的但書一致，不重複驗證前不能假設一定不用改規則。

### B. `game/engine.js` 新增公開方法：`JG.getRecentWindow(n = 20)`

```js
// 回傳最近 n 筆作答（合併「本場尚未 flush 的 session.items」與「上次 sessionEnd 已寫入 RTDB 的
// progress/recentAttempts 快取」），依時間新到舊排序後取前 n 筆。
// 這是 WP-9 觸底偵測要用的讀取介面——目前完全不存在，是本文件新增的介面契約，不是沿用。
JG.getRecentWindow(n = 20)
  -> Array<{ at: ms, station: string, kcId: string, correct: bool, sessionId: string }>
```

**實作要求（供 cycle-builder 施工，不是留白）**：
1. `_loadRemoteIfNeeded()` 需要新增一次 `get(ref(db, \`${NS}/progress/${uid}/recentAttempts\`))`，
   把結果快取進 `this.local.recentAttempts`（跟現有 `xp`/`streak`/`wrong` 同一套「遠端為準」邏輯）。
2. `getRecentWindow(n)` 合併 `this.local.recentAttempts`（持久化過的）與
   `this.session ? this.session.items.map(...) : []`（本場進行中、尚未寫入 RTDB 的），
   兩者依 `at` 排序後取最後 n 筆——這樣一場連續作答超過 20 題時，視窗看到的永遠是真正最近的
   20 題，不會漏看剛發生在同一場的連續失敗。
3. 未登入時（`this.user===null`）只用 `this.session.items`（沒有遠端可併），這跟既有「未登入靜默
   降級成純 localStorage」的整體架構一致，不需要新設計降級路徑。

### C. 純函式：`evaluateFloorState`（新檔或併入 `game/kc-logic.js`，不碰 RTDB/DOM）

```js
// 輸入：window 是 JG.getRecentWindow(20) 的回傳值（依 at 升冪排序）、prevFloorState 是現有
// progress/floorState（不存在時視為 {active:false, firstTriggeredAt:null, lastTriggeredAt:null,
// consecutiveCorrectSinceTrigger:0, triggerCount:0}）、now 預設 Date.now()。
// 輸出：{ floorState: 新的節點內容, action: 'trigger_full' | 'trigger_short' | 'exit' | 'none' }
function evaluateFloorState(prevFloorState, window, now = Date.now()) -> { floorState, action }
```

**規則（把 §5 原文「連續 8 題錯」「≤30%」「冷卻窗口」翻成可測試的判斷式，這是本文件對原文
唯一模糊地帶的具體化，不是新政策）**：

1. `isFloorCondition = (window.length>=20 && correctCount(window)/window.length <= 0.30) || last8AllWrong(window)`
   （`last8AllWrong` 只在 `window` 末 8 筆都存在且都 `correct===false` 時成立，`window.length<8` 時一律 false）。
2. 若 `!prevFloorState.active`：
   - 若 `isFloorCondition` 為 true：這是新一輪觸發。
     - 若 `prevFloorState.lastTriggeredAt===null` 或 `now - prevFloorState.lastTriggeredAt >= 24*3600*1000`
       → `action='trigger_full'`（完整文案，含裁決 1 定案的候選 A 文字＋路由按鈕）。
     - 否則（24 小時內曾觸發過、這次是提早又掉回去）→ `action='trigger_short'`（只顯示簡短路由按鈕）。
     - 兩種情況都要更新：`active=true`、`lastTriggeredAt=now`、
       `firstTriggeredAt=prevFloorState.firstTriggeredAt||now`、`consecutiveCorrectSinceTrigger=0`、
       `triggerCount+=1`。
   - 若 `isFloorCondition` 為 false → `action='none'`，`floorState` 不變。
3. 若 `prevFloorState.active`（已經在觸底狀態裡）：
   - 逐筆處理 `lastTriggeredAt` 之後發生的作答（跨任意站，呼應裁決 2）：答對則
     `consecutiveCorrectSinceTrigger += 1`；答錯則歸零。
   - 若 `consecutiveCorrectSinceTrigger >= 5` → `action='exit'`，`active=false`
     （`lastTriggeredAt`／`triggerCount` 保留原值，供下次判斷 24 小時冷卻用）。
   - 否則（尚未脫離）→ `action='trigger_short'`（同一次觸底事件裡的重複進入，只顯示簡短版）。

### D. 呼叫時機（各站 adapter，仿照 `wordwheel.html` 現有接線方式）

在每次 `JG.answer(...)` 呼叫**之後**，緊接著呼叫：
```js
const { floorState, action } = evaluateFloorState(cachedFloorState, JG.getRecentWindow(20));
// action==='trigger_full' → 顯示裁決1候選A的完整文案 + roots/wordwheel路由按鈕，停止出題
// action==='trigger_short' → 只顯示簡短路由按鈕，不重播文案，停止出題
// action==='exit' → 恢復正常出題流程
// action==='none' → 無事發生
// 無論哪種 action !== 'none'，都要把 floorState 寫回 progress/{uid}/floorState（沿用§3.3權限模型）
```
`cachedFloorState` 由呼叫端在頁面載入時 `get()` 一次 `progress/{uid}/floorState` 取得，跟現有
`_loadRemoteIfNeeded()` 的模式一致（是否併入 engine.js 內部或留給各站 adapter 自己讀，
交 `cycle-builder` 施工時決定，本文件只定「必須讀取既有值、不能每次都當作從零開始」這個行為）。

### E. `roots/index.html` 查詢參數（見發現 3，重複列在此處供施工時對照）

`?lv=<comma-separated levels>`、`?g=<group key>` —— 內容見上方發現 3 的程式碼片段。

---

## 分階段

**Phase 1 — 資料與讀取介面（本文件新增部分，無使用者可見畫面）**
1. `progress/{uid}/floorState` 節點與權限驗證（介面契約 A）。
2. `JG.getRecentWindow(n)`（介面契約 B），含 `_loadRemoteIfNeeded()` 補讀 `recentAttempts`。
3. `evaluateFloorState` 純函式（介面契約 C），連同單元測試（比照 `kc-logic.js` 的驗法）。

**Phase 2 — roots 深連結補丁（見發現 3，獨立、無依賴，可與 Phase 1 平行）**
1. `roots/index.html` 追加 `?lv=`/`?g=` 讀取（介面契約 E）。

**Phase 3 — 觸底 UI 與路由（依賴 Phase 1、2 都完成）**
1. 候選 A 文案（或楊老師選定/修改後的版本）寫成畫面：教學決策層每一站 adapter 在
   `action==='trigger_full'|'trigger_short'` 時替換 `qstem`／清空選項（沿用 wordwheel「這一輪做完了」模式）。
2. 路由按鈕：主要按鈕 deepLink 到 `wordwheel.html`（段考範圍）；次要文字連結到
   `../roots/index.html?lv=...`（字根表，附「這是理解工具，不是必修進度，不勉強」提醒文字）；
   若楊老師已決定加入候選 B/C，這裡再加一行外部資源連結/電話。
3. `action==='trigger_full'` 時額外呼叫 `JG.forceStreakCredit({reason:'floorHit'})`。
4. 端到端跑下方全部驗收標準。

**Phase 4 — 文案審查（不需要工程，但是上線前的硬性步驟）**
候選 A（或楊老師選定版本）的逐字文案，交 `red-team-critic` 或 `english-teacher` 做一次真身審查
（不是關鍵字黑名單），確認語氣真的不責備、真的讀得懂（対象是低閱讀能力學生）。

---

## 🔴 驗收標準（每條都要寫「怎麼驗」）

**沿用 §5 原文既有的（正面，怎麼驗：造假學生跑過 Phase 1-3）**
1.（正）假學生連續亂答，系統在第 20 題前觸發並停止出題。怎麼驗：造一組 `correct:false` 序列餵給
   `evaluateFloorState`（或端到端跑 `JG.answer`+偵測呼叫），在第 8 題（連續 8 錯規則）或第 20 題內
   （≤30% 規則）得到 `action==='trigger_full'`。
2.（正）觸發後路由指向站內實際存在的頁面。怎麼驗：`curl` `wordwheel.html` 與
   `roots/index.html?lv=1,2` 均回傳 200。
3.（負，本文件新增，取代原本只靠關鍵字黑名單的版本）觸發訊息（候選 A 或楊老師選定版本）
   同時通過**兩層**檢查才算過：(a) 機械關鍵字黑名單（不含「加油」「再試一次」「不要放棄」）；
   (b) `red-team-critic` 或 `english-teacher` 對逐字文案的真身審查通過（不是模擬、不是黑名單）。
   **只過 (a) 沒過 (b) 不算通過**——這是呼應 red-team 發現 1 指出「黑名單是必要不充分條件」的直接修正。
4.（負，沿用）正常學生（約 70% 正確率）連續 100 題不得誤觸發。怎麼驗：造 70% 正確率的假序列
   跑 `evaluateFloorState`，全程 `action` 不應出現 `'trigger_full'`/`'trigger_short'`。
5.（負，沿用+精確化）同一假學生 24 小時內連續觸發 3 次，驗證只有第一次 `action==='trigger_full'`，
   第 2、3 次 `action==='trigger_short'`。怎麼驗：直接呼叫 `evaluateFloorState` 三次，
   餵入時間戳分別間隔 <24hr，斷言 `action` 序列為 `['trigger_full','trigger_short','trigger_short']`。
6.（正，沿用）造「當天觸發 floor-hit 且只完成 2 題」的假學生，驗證當日 streak 仍計為完成、不歸零。
   怎麼驗：呼叫 `JG.forceStreakCredit({reason:'floorHit'})` 後讀 `progress/{uid}/streak.todayCount`
   應 ≥3、`current` 未因為只答 2 題而被判斷為斷掉。
7.（正，本文件新增，對應發現 2 的介面契約 B）造一場作答 25 題的假 session（超過視窗大小 20），
   驗證 `JG.getRecentWindow(20)` 回傳的是**這場最新的 20 筆**（不是上一場結束時寫入 RTDB 的舊 30 筆），
   即使本場尚未呼叫 `sessionEnd()`。怎麼驗：檢查回傳陣列第 1 筆的 `at` 等於本場第 6 題的時間戳
   （25 題裡的第 6~25 題）。
8.（正，本文件新增，對應發現 2「降階後答對要能算數」）造「觸發 floor-hit 後，學生在 `wordwheel`
   （非原本觸發時的那一站）連續答對 5 題」的假序列，驗證第 5 題後 `action==='exit'`、
   `floorState.active` 變回 `false`。怎麼驗：`window` 陣列裡混入不同 `station` 值餵給
   `evaluateFloorState`，確認判定不看 `station` 是否跟觸發時相同。
9.（負，本文件新增）同一序列裡若第 3、4 題答對、第 5 題答錯才第 6 題起才連續答對 5 題，
   驗證 `consecutiveCorrectSinceTrigger` 在第 5 題答錯時歸零，不會用「先前累積的 2＋後面 3」湊出脫離。
10.（正，本文件新增，對應發現 3）`roots/index.html?lv=1,2` 帶查詢參數進站，驗證頁面渲染後
    `state.lv` 內容為 `{1,2}`、且第 1/2 級篩選按鈕 `aria-pressed` 顯示為 `true`（不需要學生自己點）。
    怎麼驗：這條需要瀏覽器（無頭瀏覽器或人工）跑一次，讀 DOM 屬性；純 `curl` 驗不到 JS 執行後的狀態，
    只能驗證 HTTP 200，這條驗收本身**依賴瀏覽器環境**，跟驗收 2 的 `curl` 是分開的兩件事。
11.（負，紅線，沿用 WP-8 Phase 0 精神）在 Phase 0（`progress/kc`）驗收通過前，
    grep WP-9 相關新檔案／文案模板，搜尋「攻克」「精熟」字樣——不得出現（跟 WP-1/WP-8 用同一條紅線）。

---

## 風險與已接受的取捨

- **候選 A 文案假設「學生有一個可以求助的英文老師/導師」**：接受此限制，因為候選 B/C 的加碼
  需要楊老師先做倫理判斷，見「需要人決定的問題」；在那之前，候選 A 是能做到的最好版本，
  不是完美版本。
- **`?lv=`/`?g=` 是本文件新設計的介面，尚未經 `ux-designer`／`game-designer` 對這個新增 UI 行為
  （篩選按鈕會不會自動改變、閃爍感受）審查**：接受，因為這是小範圍、機械性的查詢參數讀取，
  不改變 `roots/index.html` 既有的視覺／互動設計本身，風險遠低於這頁面原本設計決策的範疇；
  若真人測試發現「自動勾選篩選」讓學生困惑（不知道為什麼進來就篩過），再回頭調整成
  「篩選預設關閉、只捲動到對應段落」的更保守版本。
- **`evaluateFloorState` 的「連續 8 題錯」與「≤30%」兩條規則同時存在、以 OR 連接**：接受這個組合，
  因為兩條各自處理不同情境（8 連錯抓「突然掉進完全不會的題」，≤30% 抓「持續低於猜測水準但
  不是每題都連續錯」），這是 §5 原文本來就寫的兩條規則，本文件只是把它們的優先關係
  用 OR 明確寫死，沒有新增判斷邏輯。
- **未採用 red-team KB 建議的 `floor_sim.py` 專用模擬腳本作為本輪交付項目**：接受，理由見下方
  「沒有採納」小節——這是好建議但屬於 `cycle-evaluator` 的驗收工具，不是設計文件本身要生產的東西。

---

## 🔴 沒有採納誰的建議、為什麼

- **`red-team-critic` 建議把「連降階都撐不住時」的兜底路由本輪直接定出唯一版本，未完全採納**：
  只在「保守版本可以本輪定案」這部分採納（候選 A 定為 v1 預設），但「是否要疊加校外心理支持資源」
  刻意**沒有**由本文件單方面決定，因為那涉及對未成年學生的求助路徑判斷，是需要楊老師本人承擔的
  倫理決定，不是我可以代答的技術問題。**若楊老師回覆選 B 或 C，會直接改採納，不需要再開一輪設計。**
- **`red-team-critic` 建議把 `roots` hash 深連結列為「待人工瀏覽器實測」，未採納他保留在 §7 軟性
  待決事項的分類**：本文件裁決升級為 build 的硬性阻斷前置條件（見發現 3），理由是本輪已經靠讀碼
  （非人工瀏覽器）就能確定「目前不支援」是事實而非猜測，不需要等瀏覽器實測才能定案要不要做——
  **只有「query string 這個具體做法是否是最佳方案」還留給 `ux-designer` 之後審查，不是「要不要做」本身還沒定。**
- **`red-team-critic` 建議建立 `floor_sim.py` 作為本輪機械驗收工具，未採納（不是不同意，是分工判斷）**：
  這個建議本身是對的、也會被用上——但寫模擬腳本、實際跑驗收，屬於 `cycle-evaluator` 的職權
  （對照本文件上方「怎麼驗」逐條去寫），不是 `cycle-designer` 產出設計文件時該交付的程式碼
  （紅線「不寫實作程式碼」）。**本文件已經把 `evaluateFloorState` 的純函式介面定義清楚，
  讓 `cycle-evaluator` 可以直接照著寫 `floor_sim.py` 或等效的單元測試，不需要重新設計判定邏輯。**
- **`red-team-critic` 隱含質疑「訊息文案只做關鍵字黑名單是否足夠」，部分未採納他原本可能期待
  的「這輪就把文案完全定案」**：本文件只把候選 A 定為 v1 預設，並新增「逐字文案必須過真身審查」
  這條硬性驗收（見驗收標準 3），但沒有宣稱這條驗收現在就已經跑過——**這是刻意留給 Phase 4，
  不在這份設計文件裡假裝已經做完。**

---

## 需要人決定的問題

1. 🔴 **是否要在觸底安全網文案裡加入校外心理支持資源（如 1980 張老師專線）？**
   本文件提供三個候選文案（見發現 1），v1 預設用候選 A（不含校外專線）。這是唯一一項
   **涉及未成年學生真實求助路徑、有倫理考量、我判斷不該由 AI 代答**的問題——請楊老師從
   候選 A/B/C 中選一個，或給出修改版本。在得到答案前，WP-9 可以用候選 A 進 build，
   不必整個 WP-9 卡住等這一項，但候選 A 之外的加碼在楊老師回答前不會出現在畫面上。
2. （沿用既有、未變動）§7 待決事項 #6：真人測試找得到低閱讀能力的學生嗎？找不到，WP-9
   只能標「未經驗證」上線。
3. （沿用既有、未變動）§7 待決事項 #9：字根表降階的先備條件門檻怎麼量化——本輪仍不處理，
   維持只加提醒文案的做法。
4. **候選 A（或楊老師選定版本）的逐字文案，建議下一輪明確排 `red-team-critic`／`english-teacher`
   做 Phase 4 的真身文案審查**——這不是「等答案才能問」的問題，是需要 `wp-manager` 之後排工排進去
   的一個步驟，本文件先點名，避免又被漏排。

---

## 這一版 WP-9 現在能不能進 build？

**可以，附帶條件**：Phase 1（資料/讀取介面）、Phase 2（roots 深連結）、Phase 3（UI/路由，用候選 A
文案）可以直接交 `cycle-builder` 施工並跑驗收標準 1、2、4-11；驗收標準 3 的 (b) 真身文案審查
（Phase 4）與「是否加碼 B/C」這兩件事，等楊老師回答問題 1 之後才能關閉，但不阻擋前面幾個 Phase
先動工——這是本文件對 red-team「還不能進 build」判定的具體修正：**擋住的只有一項內容決策，
不是整個工作包的機制與資料設計**，其餘三個嚴重問題（wordwheel 接線、roots 深連結、streak 補丁）
在本輪已經全部裁決/確認解決或給出可施工的具體介面。
