# WP-1 遊戲化核心引擎＋資料層 — 正式設計（cycle-designer，2026-09-14）

> 輸入：`docs/cycle/wp1-0-assessment-review.md`（`assessment-expert` 真身，WP-1 依 §9 表格的唯一必要審查者，
> 已完成、具體到函式與行號）＋ `docs/PLAN.md` §3.2/§5 WP-1/§5 WP-8 Phase 0/§7 待決事項#10 ＋ `game/engine.js`（v0 草稿，190行）。
> 本文件把審查結果收斂成可直接交 `cycle-builder` 施工的規格。**不寫實作程式碼**，只定介面、schema、分階段、驗收標準。

---

## 要解決什麼（一句話）

把 `game/engine.js` 這份 v0 草稿，補成同時滿足 §3.2 原始資料模型**與** WP-8 裁決新增的 Phase 0
三個節點（`progress/kc`、`progress/recentAttempts`、`wrongItems.repairHistory`）的正式 WP-1 交付，
並修掉「修好舊錯題 +15 可被同題同場次無腦刷分」這個已知且現在被程式碼證實存在的漏洞。

---

## 沿用既有的什麼

**完全不重寫，逐項確認 v0 草稿裡已經做對、可以直接留用的部分：**

- Firebase 初始化、`onAuthStateChanged` 掛勾、未登入靜默降級成純 localStorage 的整體架構（L1-50、L133）—— 這是 WP-1 驗收標準「未登入時 JG 靜默降級」的既有實作，不動。
- `xpForLevel`/`levelFromXp` 等級曲線公式（`round(100*n^1.4)`，L26-31）——與 §5 WP-1 做法第4點定案的公式一致，不動。
- `taipeiDay()` 台北時區日界計算（L20-24）——正確，不動。
- `_bumpStreak()` 的**整體邏輯骨架**（換日判斷、`todayCount`、`current`/`longest`，L102-124）——沿用，只在
  Phase 2 加一個新的呼叫入口（`forceStreakCredit`，見下）給 WP-9 掛，不改動既有換日/計數邏輯本身。
- `sessionStart`/`session` 記憶體物件（`{mode, station, startedAt, attempted, correct, items:[]}`，L74-76）——沿用，
  `items` 陣列本來就逐題記錄在記憶體，Phase 2 只是把它落地成更多節點，不改變記憶體結構。
- `_injectHudOnce`/`_renderHud`（L159-187）與其操作的 class 名稱（`.jg-lv`/`.jg-xp`/`.jg-streak`/`.jg-toast`/`.ok`）
  ——HUD 顯示邏輯不動，只補齊目前不存在的 `engine.css` 檔案本身（見分階段 Phase 1）。
- RTDB 規則的「先 GET 全份 → 合併 → PUT 回去 → 驗證四個命名空間都在」流程（§5 WP-1 做法第7點）——沿用，
  Phase 0 新節點按此文的判斷（見「介面契約 › 權限」）大機率不需要改規則文字本身，但建置時仍要照這個流程走一次去**驗證**（不是假設）。
- `cards/` 既有 SRS、`gsat`/`zhikao` 既有深連結與 `randomTen()`——本 WP 不碰，維持 §4 盤點的現狀。
- WP-8 裁決文件（`docs/cycle/wp8-2-design.md`）裡已經定案的政策文字本身（KC 鍵值格式、精熟判定三次獨立事件規則、
  難度公式、每日排隊演算法）——**這些是 WP-8 的政策內容，WP-1 只負責把支撐這些政策運算所需的資料正確寫進 RTDB**，
  不在本文件重新裁決政策，只裁決「資料層怎麼把這些政策要用的欄位如實記下來」。

---

## 介面契約（函式/資料/路徑/權限）

### A. `JG.answer(...)` 簽章擴充（向下相容）

```js
JG.answer({
  correct,                    // boolean，必填，既有
  qid,                        // string，必填，既有——該站題目的既有唯一識別（各站格式不同，adapter 自己組）
  category,                   // string，選填，既有——wrongItems 的自由文字分類，語意不變，不作為 KC 鍵值
  deepLink,                   // string，選填，既有

  kcId,                       // string，選填但強烈建議必填——WP-8 政策1的完整鍵值 `${station}:${contentKey}`，
                               // 由呼叫端（各站 adapter）依政策1規則算好整串傳入，engine 不做業務判斷。
                               // 省略時 engine 退化用 `${this.station}:${qid}` 頂替，並 console.warn 一次
                               // （不中斷、不擋畫面，但代表這一題暫時自成一個 KC，精熟判定會失真——
                               //  這是刻意的「寧可繼續運作也不要整站掛掉」的降級，不是允許長期省略）。

  errorMode,                  // string，選填——WP-8 政策2的「答題行為分類」屬性（如 wordwheel 的 t 值：
                               // parse/pos/sense/infer/fake）。只存成該次作答的屬性，絕不進 kcId、
                               // 絕不影響精熟判定與排程。

  followedRecommendation = false,  // boolean，選填，WP-8 一致性加成——省略時視為 false，向下相容。
})
// 回傳不變：{ gained, level }
```

**計分規則（修訂，取代現有 L83-88 的判定）**：

- base：答對 +10、答錯 +2（不變）。
- **+15 判定改寫**：`correct && wasWrongBefore` 時，不再只看 `this.local.wrong[qid]` 是否存在，
  改為：該題最近一次「未修復」的答錯事件（`wrongItems/{uid}/{qid}.lastMissAt` 對應的 `sessionId`）
  與**本次事件的 `sessionId`（見下方 B）不同**，才給 +15；若相同（同一場次內先錯後對），
  這次答對只算一般的 +10（不是 +2——這題本來就答對了，不該被當「答錯」計分，只是不給修復加成）。
  🔴 這是本文件裁決要寫死的規則，對應交辦事項第2點。
- **一致性加成**：`correct && followedRecommendation === true` 時，在上面算出的 base 之上疊加 +2。
  兩個加成（+15 修復／+2 一致性）互相獨立，可以同時成立（該題剛好是系統建議的到期複習題）。

### B. sessionId：所有 Phase 2 節點共用同一個值

`sessionEnd()` 一開始就要決定 `sessionId`，取代現有「push 完全不留 key」的寫法：

```js
const sessionRef = push(ref(db, `${NS}/sessions/${uid}`));   // 先要 key，不先寫內容
const sessionId = sessionRef.key;
await set(sessionRef, { station, mode, startedAt, endedAt, attempted, correct, durationSec });
```

這個 `sessionId` 之後在同一個 `sessionEnd()` 呼叫裡，寫進：`progress/kc/{kcId}.lastTestedSessionId`、
`progress/kc/{kcId}.recentWindow[].sessionId`、`progress/recentAttempts[].sessionId`、
`wrongItems/{itemKey}.repairHistory[].sessionId`——**同一個字串，不得各自重算**。

### C. 資料模型（RTDB `jceeVocabGame/`，本 WP 交付範圍）

```jsonc
progress/{uid}: {
  xp, level,                          // 既有，不變
  track: "junior" | "senior",         // 補上讀寫路徑（見下方 API），預設值不在寫入時決定
  streak: { current, longest, lastActiveDay, todayCount },  // 既有，補 forceStreakCredit 入口
  stations/{stationId}: {
    attempted, correct, lastAt,       // 補上：sessionEnd() 逐站累加
    msPerItem                         // 補上：站層級「累計平均」，見下方說明，不是個人中位數（WP-4 的事）
  },
  kc/{kcId}: {                        // 🔴 WP-8 Phase 0 新節點，本 WP 交付
    attempted, correct,
    recentWindow: [{ at, correct, itemId, sessionId, station }],  // 上限10筆，新的推入、超額砍最舊
    consecutiveSpacedCorrect,         // 只在「獨立事件」規則成立時遞增，否則歸零
    lastTestedAt, lastTestedSessionId,
    masteredAt,                       // ms | null
    crossStationVerified              // bool
  },
  recentAttempts: [{ at, station, kcId, correct, sessionId }]  // 🔴 append，上限30筆，供 WP-9 直接讀
  // badges 節點：本 WP 不新增寫入邏輯（見「風險與取捨」），維持現狀只讀不寫
}

wrongItems/{uid}/{itemKey}: {
  station, qid, deepLink, category,   // 既有，不變
  missCount, lastMissAt,              // 既有，不變
  repairedAt,                         // 既有欄位保留，語意改為「repairHistory 最後一筆的鏡像值」
  repairHistory: [{ repairedAt, sessionId }]   // 🔴 新增，取代單值覆寫
}
```

### D. 新增/擴充的公開方法

```js
JG.setTrack(track)              // "junior" | "senior"，寫 progress/{uid}.track，即時寫（低頻，不等 sessionEnd）
                                 // 讀取端（WP-3）：欄位不存在時，UI 顯示層自己預設 "junior"（北極星主線），
                                 // engine 不在未設定時主動寫入預設值，避免每個新帳號白白多一次寫入。

JG.forceStreakCredit({ reason }) // 給 WP-9 floor-hit 掛的入口。效果：把「今日已完成」的判定強制視為 true
                                 // （如同今天已達 todayCount>=3 的效果），但不改變 session.attempted/correct、
                                 // 不給 XP、不寫 wrongItems/kc/recentAttempts——純粹只影響 streak 這一個節點。
                                 // 本 WP 只交付這個「留得住訊號」的入口本身；何時呼叫它、
                                 // floor-hit 判定邏輯，屬於 WP-9 範圍，這裡不設計。
```

### E. 內部純函式（供 cycle-evaluator 對照驗收標準 5–7 單獨測試，不是公開 API）

```js
// 純函式，輸入輸出都是資料，不碰 RTDB/DOM——方便單獨測試政策8的判定
function evaluateKcEvent(prevKcRecord, event /* {at, correct, sessionId, station, itemId} */) -> newKcRecord
```

規則（照抄 `wp8-2-design.md` 政策7/8 定案文字，本 WP 只負責把它寫成程式碼，不重新裁決）：
距上次作答 ≥7 天 **且** 與 `lastTestedSessionId` 不同，才算「獨立事件」；獨立事件且答對 →
`consecutiveSpacedCorrect += 1`；獨立事件但答錯，或非獨立事件時答錯 → 歸零；`consecutiveSpacedCorrect`
達 3 時寫 `masteredAt`，並依「這 3 次是否曾出現在不同站」決定 `crossStationVerified`。
同一 session 內同一 KC 被答第二次不算獨立事件，但 `attempted`/`correct`/`recentWindow` 仍照常累加。

### F. 權限（沿用 §3.3，不需要新規則文字——但要驗證）

`progress/{uid}/kc/*`、`progress/{uid}/recentAttempts`、`wrongItems/{uid}/{itemKey}/repairHistory`
都是既有頂層節點（`progress/{uid}`、`wrongItems/{uid}`）底下的**子欄位**。若現行 RTDB 規則是
「整個 `progress/{uid}` 物件層級」授權（§3.3 表格的粒度就是這樣寫的），子欄位會自動繼承、**不需要改規則文字**。
🔴 這只是設計假設，不是已驗證事實——本 repo 沒有規則檔案落在 git（規則活在 Firebase 專案本身），
建置時必須照 WP-1 做法第7點「先 GET 全份規則」實際看一次：若規則裡對 `progress/{uid}` 有
逐欄位 `.validate`（白名單式，拒絕未列出的子鍵），就必須在同一次 GET→合併→PUT 流程裡把新欄位加進白名單，
不能假設「沿用」就一定不用動規則。

---

## 分階段

### Phase 1 — 補齊 §3.2 原始 schema 缺口 ＋ 修既有 bug（跟 WP-8 無關，v0 草稿本來就該做但沒做）

1. 修 `sessionEnd()`：改用 `push()` 先取 `sessionRef.key` 再 `set()`，取得可重用的 `sessionId`（介面契約 B）。
2. 補 `progress/{uid}.stations/{stationId}`：`sessionEnd()` 逐站累加 `attempted`/`correct`/`lastAt`；
   `msPerItem` 用「累計平均」寫法：`newMs = round((oldMs*oldAttempted + thisSessionMsTotal) / (oldAttempted+thisAttempted))`，
   `thisSessionMsTotal` 從 `session.items[].at` 相鄰差值加總（第一題用 `at[0]-startedAt`）。
   🔴 這只是站層級粗估平均，不是個人中位數——WP-4 要中位數時，自己從 `progress/recentAttempts`
   （本 WP 交付、含 `at`/`station`）算，本 WP 不用為了「將來要中位數」多存整份分布。
3. 補 `JG.setTrack()`（介面契約 D），本 WP 只交付寫入路徑，UI 切換屬於 WP-3。
4. **不補** `progress/{uid}.badges` 的寫入邏輯——原因見「風險與已接受的取捨」，這是刻意不做，不是漏做。
5. 補 `_loadRemoteIfNeeded()`：新增 `get(ref(db, \`${NS}/wrongItems/${uid}\`))`，把遠端 `wrongItems` 併入
   `this.local.wrong`（遠端為準，跟現有 xp/streak/badges 的「遠端是真相來源」邏輯一致），解決換裝置/清快取後
   「修好」判定失真的問題（assessment-expert 審查第4/7條）。
6. 建立 `game/engine.css`（現在完全不存在，HUD 樣式載入 404，是純工程缺陷，順手修掉）：
   至少涵蓋 `#jg-hud`、`.jg-lv`、`.jg-xp`、`.jg-streak`、`.jg-toast`、`.jg-toast.ok` 這幾個既有 class，
   深色底＋琥珀色（§5 WP-1 做法第2點的既定要求，本文件不重新設計配色細節，交 cycle-builder 抓色碼）。

### Phase 2 — WP-8 Phase 0 資料層補丁（本 WP 交付範圍，依 §5 WP-8 Phase 0 定案文字實作）

1. `JG.answer()` 簽章擴充：`kcId`/`errorMode`/`followedRecommendation`（介面契約 A），改寫 +15 判定邏輯。
2. `sessionEnd()` 逐題迴圈新增三件事（在 Phase 1 第1點的 `sessionId` 基礎上）：
   - push 進 `progress/recentAttempts`，寫入前檢查長度、超過30筆砍最舊（讀現有陣列裁切，或維護
     一個固定長度佇列寫法——實作細節交 cycle-builder，本文件只定「上限30、append、超額砍最舊」這個行為）。
   - 呼叫 `evaluateKcEvent`（介面契約 E）算出新的 `progress/kc/{kcId}` 內容並寫回。
   - 若該題 `correct===true` 且屬於「修復」（+15 判定成立），把 `wrongItems/{itemKey}.repairHistory`
     用 append 方式加一筆 `{repairedAt, sessionId}`，並同步更新 `repairedAt` 鏡像值＝這筆的 `repairedAt`。
3. `evaluateKcEvent` 寫成獨立、不碰 RTDB/DOM 的純函式（介面契約 E），方便驗收標準 5–7 單獨呼叫測試。

### Phase 3 — `wordwheel.html` adapter ＋ 端到端驗收

1. 在 `ask()` 的 `b.onclick` 內（現有 L279-293，`const ok=oi===q.a;` 之後）插入
   `JG.answer({ correct: ok, qid: \`${d.k}#${pool[qi]}\`, category: q.t, kcId: \`wordwheel:${d.k}\`, errorMode: q.t, deepLink: \`../wordwheel.html#${d.k}\` })`。
   🔴 `qid` 用「字族+池內索引」組成——這一站目前沒有題目自帶穩定 id 欄位，這是 cycle-builder 施工時
   需要跟 `game-designer`/`assessment-expert` 之外自己確認的細節（本文件只定「必須唯一、必須穩定」這個要求，
   不保證這個具體組法在資料改版後仍穩定，是已知的小風險，見風險小節）。
2. 在頁面載入時呼叫 `JG.init({station:"wordwheel"})`、在「這一輪做完了」（現有 L252 分支）呼叫 `JG.sessionEnd()`。
3. 照 WP-1 做法第7點流程，實際 GET 一次現行 RTDB 規則、確認介面契約 F 的假設（子欄位自動繼承或需要補白名單）、
   合併新增內容、PUT 回去、驗證四個命名空間（`jceeVocabGame`／`isu0821`／`whgm`／`nacs0914`）都還在。
4. 端到端跑本文件下方驗收標準全部項目。

**排工說明（對應 §7 待決事項#10）**：`assessment-expert` 已明確建議「跨場次判定要跟 Phase 0 補丁一起做，
不要拆兩輪」，這是工程排程判斷（同一組函式、同一組 schema 欄位、同一次 code review），
本文件**直接採納定案**：Phase 1／2／3 都在同一輪 WP-1 建置裡完成，不拆成「先上 WP-1 舊版、之後再補 WP-8 patch」
兩張票。§7 待決事項#10 視為本文件已回答，不需要另外等楊老師裁示（性質是工程排程，不是產品政策）。

---

## 🔴 驗收標準（每條都要寫「怎麼驗」）

**沿用 §5 WP-1 原始驗收（正面，怎麼驗：建一個測試帳號，跑過 Phase 3 的 wordwheel adapter）**

1.（正）測試帳號答 5 題（含至少 1 題刻意先答錯再對），RTDB 對應 `progress/{uid}`／`sessions/{uid}/*`／
   `wrongItems/{uid}/*` 三處都出現資料，且 `progress.xp` 等於 5 題各自 gained 加總、`sessions` 該筆
   `attempted`/`correct` 與實際一致。怎麼驗：`curl` RTDB REST（帶測試帳號 ID token）逐一 GET 三個路徑核對數字。
2.（正）關閉分頁重開（同帳號），HUD 顯示的等級/XP/連續天數與 RTDB 現值一致。怎麼驗：重整頁面，
   比對畫面文字與同一時間點 `curl` GET `progress/{uid}` 的值。
3.（負）用第二個測試帳號登入，`curl` GET `progress/{uid-第一帳號}` 應該被規則拒絕（403 或空結果）。
4.（負）未登入（不做任何登入動作）直接進 `wordwheel.html` 答題，畫面不報錯、`JG` 正常記本地分數，
   RTDB 完全沒有新資料寫入（`curl` 確認該路徑仍是答題前的狀態）。

**針對本文件新增設計的驗收（對應交辦事項2、3、4、5，正/負皆有）**

5.（負，+15 跨場次修復判定，這是本次任務點名要驗的核心項）造一個假學生：先答錯 qid=X，
   **同一個 sessionId 內**10秒後重新作答同一題 X 並答對。怎麼驗：不呼叫 `sessionEnd()`／`sessionStart()`
   之間直接連續兩次 `JG.answer` 打同一 qid；驗證第二次的 `gained` 是 **10**（不是 15），
   且 `wrongItems/{uid}/X.repairHistory` 這次**沒有**新增一筆（因為判定不成立）。
6.（正，對照組）同一 qid 在**不同** session（呼叫 `sessionEnd()` 結束前一場、`sessionStart()` 開新場）
   答對，驗證 `gained===15`，且 `repairHistory` 新增一筆、`repairedAt` 鏡像值同步更新為這筆的值。
7.（正，一致性加成）`followedRecommendation:true` 且答對時，`gained` 比同條件下 `followedRecommendation` 省略/false
   時多 2（例如：一般答對10→12、修復15→17）。怎麼驗：同一起始狀態各跑一次帶/不帶這個欄位的呼叫，比對 `gained`。
8.（正，向下相容）呼叫 `JG.answer` 完全省略 `kcId`/`errorMode`/`followedRecommendation` 三個新欄位，
   不報錯、`gained`/`level` 行為與擴充前一致；`progress/kc` 仍會寫入（用退化的 `${station}:${qid}` 鍵值），
   但 console 出現一次警告（不算失敗，只是確認降級路徑真的走得通，不是靜默壞掉）。
9.（正，schema）抽查 `progress/{uid}/recentAttempts`，寫超過30筆之後，陣列長度仍是30、且保留的是最新30筆
   （最舊的第1筆被丟棄）。怎麼驗：造31次連續作答，GET 該節點數陣列長度並比對第一筆的 `at` 是否為第2次那筆的時間。
10.（正，schema）抽查 `progress/{uid}/stations/{stationId}`，`attempted`/`correct` 累加正確，
    `lastAt` 等於最後一次作答時間，`msPerItem` 是正數且量級合理（同一站連續作答，值應落在秒等級，
    不是 0 或負數）。怎麼驗：GET 該節點跟手動加總 `session.items` 比對。
11.（正+負，精熟判定機械驗收，與 WP-8 驗收標準5/6/7 共用同一段程式邏輯——因為判定邏輯的實作就在 WP-1 這裡）
    直接呼叫本文件介面契約 E 的 `evaluateKcEvent` 純函式，餵入下列三組輸入分別驗證：
    (a) 三次同 sessionId → `masteredAt` 仍是 null；
    (b) 三次分屬三個不同 session、間隔 ≥7 天、都答對 → 第三次後 `masteredAt` 被設定；
    (c) 三次裡有一次答錯 → `consecutiveSpacedCorrect` 該次歸零、不會用「2次對1次」湊出 `masteredAt`。
    怎麼驗：這是純函式，不需要真的操作 RTDB，直接單元測試呼叫並斷言回傳值。
12.（負，Phase 0 紅線）在驗收標準5、6、9、10、11 全部通過前，grep `game/engine.js`、`game/engine.css`、
    `wordwheel.html` 搜尋「攻克」「精熟」字樣——不得出現。怎麼驗：`grep -rn "攻克\|精熟" game/ wordwheel.html`
    回傳空結果才算過。
13.（正，跨裝置一致性）測試帳號在裝置A答錯 qid=Y 並讓遠端 `wrongItems` 寫入成功；清空 localStorage
    模擬換裝置（或關掉再開瀏覽器 profile），重新登入同帳號後直接答對 qid=Y（不同 session），
    驗證 `gained===15`（因為 `_loadRemoteIfNeeded` 已把遠端 wrongItems 併回本機，不會誤判「從未錯過」）。
    怎麼驗：手動清 `localStorage.jceeGame_v1` 後重整頁面再作答，比對 gained 與 RTDB repairHistory 是否正確增加。

---

## 風險與已接受的取捨

- **`progress/{uid}.badges` 本 WP 不寫入邏輯，維持只讀不寫**：接受。目前沒有任何 WP 定義過「有哪些
  badgeId、什麼條件觸發」這個目錄本身——沒有目錄就沒有東西可寫，寫一個空殼寫入函式沒有意義。
  等 WP-3（儀表板呈現層）或後續某輪定義出具體 badge 目錄，再回頭補這段邏輯，這不是本 WP 的漏做。
- **`wordwheel` 的 `qid` 組法（字族+池內索引）不是題目自帶的穩定 id**：接受，但標記為小風險。
  若之後 `DATA` 內容改版重排順序，既有 `wrongItems` 記錄可能對錯題。這站目前確實沒有更好的欄位可用，
  且影響範圍有限（wordwheel 本來就是 WP-1 唯一要跑通端到端的站，其餘站在 WP-2 各自看有沒有更好的 id 欄位）。
- **RTDB 規則是否需要因 Phase 0 新欄位而修改，本文件只給出「大概率不用」的判斷，未實際驗證**：
  接受，因為本 repo 沒有規則檔案落地可查，只能在建置時實跑 GET 驗證（已寫進 Phase 3 第3點的施工步驟，
  不是不驗證，是驗證動作本身要等建置階段才有得跑）。
- **`msPerItem` 是站層級累計平均，不是個人分布**：接受，因為 WP-4 要的中位數可以從
  `progress/recentAttempts`（本 WP 已交付、含時間戳）事後算，不需要本 WP 額外存整份分布徒增資料量。
- **`+15` 跨場次判定只看 sessionId 是否相同，不額外要求最短時間間隔**：接受，維持交辦事項原文字面要求
  （「不在同一個 sessionId 才算數」），不額外加時間門檻。原因：session 邊界本身已經是一個自然的行為門檻
  （要先結束/開新場才能繞過），額外加時間門檻是設計加碼、不是交辦要求；若之後實測發現「開新分頁製造新
  session 但幾秒內完成」仍能鑽漏洞，再回頭加時間門檻（見下方未採納意見）。
- **各站 `qid`/`kcId` 由 adapter 各自計算，WP-1 只提供退化路徑**：接受此設計取捨（見介面契約A），
  好處是 engine 保持薄、業務規則不外洩進共用引擎；代價是每個 WP-2 adapter 都要正確算出 kcId，
  算錯不會報錯只會讓精熟判定失真——這是 WP-2 施工時要特別注意驗證的地方，不是本 WP 能完全防呆的。

---

## 🔴 沒有採納誰的建議、為什麼

- **`assessment-expert` 建議把 §A 四項缺口（stations/track/badges/wrongItems對帳）全部跟 Phase 0 一起補**，
  **部分採納、部分未採納**：`stations`／`track`／`wrongItems對帳` 三項採納（見 Phase 1）；
  **`badges` 寫入邏輯未採納**——不是不同意她的判斷，是這件事現在做不了：沒有任何一份現存文件定義過
  badge 目錄（有哪些 badgeId、觸發條件），寫入邏輯無從寫起。**若之後 WP-3 或任何一輪定義出 badge 目錄，
  這條建議會立刻變成可執行、應該回頭採納。**
- **`assessment-expert` 建議「+15 跨場次判定是否也要求時間間隔」留給排工時定案**——本文件裁決**不加時間間隔**，
  只用 sessionId 是否相同判定，因為交辦事項原文字面就是「不在同一個 sessionId 才算數」，沒有要求時間門檻；
  這不是駁回她的建議（她原文是「待定」不是「一定要加」），是本文件把這個待定關掉、選擇最貼近交辦文字的最小規則。
  **若之後真人測試/濫用觀察發現「開新 session 但幾秒內完成」仍能繞過，會回頭加最短時間間隔門檻。**
- **`assessment-expert` 建議 kcId 由 adapter 算好整串傳入、category/errorMode 拆成兩個明確參數**：
  **全部採納**，已寫進介面契約A（`kcId`/`errorMode` 為新欄位，`category` 保留既有語意不變、不強迫改名）——
  這裡刻意保留 `category` 舊名而非她建議的完全拆開重構，理由是 `category` 目前已被 wrongItems 既有讀取路徑
  使用，保留舊名可以不動到既有欄位語意，只是新增兩個獨立欄位，風險比重構舊欄位低。
- **本文件沒有встреча其他專家的衝突意見需要裁決**：WP-1 依 §9 表格只需要 `assessment-expert` 一位必要審查者，
  這輪沒有 `learning-scientist`/`game-designer`/`ux-designer`/`red-team-critic` 的 WP-1 專屬意見輸入，
  上一輪 WP-8 裁決裡涉及 WP-1 介面的部分（`followedRecommendation`、KC 鍵值格式）已經是那輪裁決過的定案，
  本文件只是原樣把那些定案轉譯成 WP-1 的函式簽章，不重新開一次裁決。

---

## 需要人決定的問題

無新增。§7 待決事項#10（本文件已裁決採納「併入同一輪」）與其餘既有待決事項（#1 群組層、#7 難度公式模型、
#8 roots hash 捲動、#9 字根表門檻、#11 WP-9 主審）都不在本文件範圍內，維持 `docs/PLAN.md` §7 現狀，
本文件不重複列出、也不要求楊老師針對 WP-1 本身另做任何決定。
