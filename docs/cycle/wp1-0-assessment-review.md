# WP-1 波次0 審查 — assessment-expert（真身）

> 審查對象：`game/engine.js`（commit fa0b6a8 引入，約190行）。這是 WP-1 正式跑五棒循環之前的 ad-hoc v0 草稿，
> 尚未掛進任何一站（`wordwheel.html` 內 grep `JG.` 零筆），也早於 2026-09-14 WP-8 裁決（`docs/cycle/wp8-2-design.md`）。
> 我的任務不是要不要重寫，是把落差列清楚，交給 `cycle-designer` 收斂進正式 WP-1 派工。

## 我讀了什麼

- `.claude/agents/assessment-expert.md`（本代理人定義）、`.claude/agents/_DOMAIN.md`（領域簡報，特別 §5 評估層級）
- `docs/PLAN.md` §3.2（原始資料模型 schema）、§3.3（安全模型/已知風險）、§4（各站掛勾點盤點）、
  §5 WP-1（做法與驗收）、§5 WP-8（Phase 0 資料層補丁全文，政策1到9，驗收標準13/14項）
- `docs/cycle/wp8-2-design.md`（WP-8 裁決全文，含我自己上一輪模擬版意見被採納/不採納的段落）
- `docs/cycle/wp8-2-review-assessment-expert.md`（我自己上一輪模擬版產出，作對照基準）
- `game/engine.js` 全文（190行）逐行讀完；另確認 `game/engine.css` 不存在（engine.js L169 有動態載入它，
  這是功能性 bug 不是評測問題，不在我的範圍，記一筆給接手 WP-1 建置的人）；確認 `wordwheel.html` 沒有任何 JG 呼叫。

## 現有v0草稿 vs 規格的落差（逐條，含檔案行號）

### A. 對照 §3.2 原始 schema（WP-8 裁決前就該有的東西，落差跟 WP-8 無關）

1. **`progress/{uid}.stations/{stationId}`（attempted/correct/lastAt/msPerItem）完全沒有寫**。
   engine.js L142-144 的 `update()` 只寫 `xp`、`level`、`streak` 三個欄位。
   影響：WP-4 番茄鐘明確要「同時記錄真實 msPerItem 進 progress.stations」（PLAN §5 WP-4）
   才能把估時從保守猜測換成個人中位數；這個節點不存在，WP-4 那條 measure-first 設計會直接卡住。
   `session.items` 裡雖然每筆有 `at`（L96），但沒有任何地方計算相鄰題目的耗時差。

2. **`progress/{uid}.track`（junior/senior）從未被寫入或讀出**。engine.js 完全沒有 track 相關程式碼。
   WP-3 的年級分軌切換（打底 vs 衝刺、不同推薦順序與文案）需要這個欄位，目前無處可存。

3. **`progress/{uid}.badges` 只被讀不被寫**：L67 `this.local.badges = remote.badges || {}` 只在載入時鏡射遠端值，
   但整份程式碼裡沒有任何地方會產生新徽章或把 badges 寫回 RTDB。目前這是個純讀取的死欄位。

4. **wrongItems 的修復判定完全只信任本機 localStorage，從未從遠端 wrongItems/{uid} 拉回來對帳**：
   `_loadRemoteIfNeeded()`（L58-72）只同步 xp、streak、badges，沒有讀 wrongItems 節點。
   換裝置或清過 localStorage 之後，`this.local.wrong` 是空的，代表：
   (a) 之前在別的裝置答錯的題目，這次答對不會被算成「修好」（漏發 +15，也漏標 repairedAt）；
   (b) 這題會被當「從未錯過」對待，跟遠端 wrongItems 真正的狀態不一致。
   這直接影響「修好舊錯題」這個宣稱的正確性，不是效度問題，是資料來源不一致的問題。

### B. 對照 WP-8 Phase 0 補丁（PLAN §5 WP-8 Phase 0，docs/PLAN.md L409-438）

5. **`progress/{uid}/kc/{kcId}` 整個節點不存在**。engine.js 從頭到尾沒有 kcId/contentKey 的計算邏輯；
   `answer({correct, qid, category, deepLink})`（L78）裡的 category 只是原樣存進 wrongItems 和 session 內存 items，
   從未依政策1（kcId = station:contentKey 組合）做任何轉換或彙總。沒有這個節點，theta（KC能力估計）、
   consecutiveSpacedCorrect、masteredAt、crossStationVerified 全部無從計算，WP-8 整個政策引擎沒有地基。

6. **`progress/{uid}/recentAttempts`（append，上限30筆）不存在**。目前逐題紀錄只活在記憶體裡的
   `this.session.items`（L44、L75），`sessionEnd()`（L126-157）只把彙總數字（attempted/correct/durationSec）
   push 進 sessions/{uid}/{sessionId}，逐題明細從未落地成獨立、可被 WP-9 直接讀取的滾動陣列。
   WP-9「最近20題正確率」若照 Phase 0 設計是要直接讀 recentAttempts、不重掃 sessions 全表；
   這個節點不存在，WP-9 目前只能回頭重掃 sessions（而 sessions 本身也只存彙總數字，不含逐題陣列，見下一條）。

7. **wrongItems repairHistory 不存在，現有的 repairedAt 寫法是單值覆寫不是歷史陣列**：
   現有 sessionEnd() L151-154 的寫法（只用 update 蓋掉單一 repairedAt 值）跟 Phase 0 規格要求的
   `repairHistory: [{repairedAt, sessionId}]` 陣列語意不同。若同一題被修好又忘記又修好，
   只留得下最後一次的時間，等於歷史被覆蓋掉。Phase 0 規格明確要求 repairedAt 只作為
   repairHistory 最後一筆的鏡像值（PLAN §5 WP-8 L433-437），現有寫法連鏡像都稱不上，是唯一真相。

8. **「修好+15」的判定沒有任何時間間隔或跨場次檢查，允許無腦刷分，這正是 PLAN 自己已經標記的
   已知待補丁，現在對照程式碼確認它就是這樣寫的**：
   answer() L78-100 判斷 `wasWrongBefore = !!(this.local.wrong && this.local.wrong[qid])`（L83），
   只要同一個 session 裡先答錯一題、緊接著同一題再答一次且答對，就立刻拿 +15（L84），
   完全沒有檢查這次作答的 session 是否等於上次錯誤的 session、也沒有檢查時間間隔。
   這不只是「將來要補」，是現在就存在、且第一次有人拿它做端到端測試就會被發現的計分漏洞。

9. **JG.answer 的介面沒有 followedRecommendation 欄位**：現有簽名是
   `answer({ correct, qid, category, deepLink })`（L78），WP-8 裁決要求新增可選欄位
   followedRecommendation（省略預設 false，向下相容），答對且為 true 時疊加 +2 XP 一致性加成
   （PLAN §5 WP-1 L233-235、WP-8 L493-496）。這個欄位完全不存在，計分邏輯（L84）
   也沒有對應的加總邏輯。這是純加法的介面擴充，不會動到既有呼叫者，風險低，但目前是零。

10. **沒有 sessionId 可用，會卡住第5-7條的補丁怎麼實作**：sessionEnd() L137 用
    push(ref(db, ...)) 建立 session 記錄，但從未取用 push() 回傳值的 key。
    Phase 0 的 kc.recentWindow、recentAttempts、repairHistory 全部需要每筆記錄帶 sessionId
    才能判斷「是否為獨立事件（不同 session）」（政策8）。目前連 sessionId 這個值本身
    在寫入當下都拿不到，是補丁能不能落地的前置技術缺口，不只是欄位沒加而已。

### C. 對照 WP-9（間接關聯，不是 WP-9 本身的設計，是 WP-1 要留的介面缺口）

11. **`_bumpStreak()`（L102-124）沒有任何機制可以標記「今天沒滿3題是因為系統自己判斷該停（floor-hit），
    不是學生沒回來」**。PLAN §5 WP-1 L245-246 已經寫明這是已知待補丁（streak 需配合 WP-9 改動），
    現有程式碼裡連一個可以掛這個例外的旗標欄位都沒有。這不是要我現在設計 WP-9 的判斷邏輯
    （那是 learning-scientist/game-designer 的範圍），但資料介面要先留得下這個訊號，
    WP-1 若現在完全不留位置，WP-9 上線時會被迫回頭改 WP-1。

12. **streak 記帳邏輯本身的可稽核性偏弱**：`_countedYesterday`、`_prevDayCount` 這兩個內部欄位
    只在 `_bumpStreak()` 內部使用、從未在建構子或別處初始化，邏輯分支多層，難以一眼確認「連續N天」
    這個數字在各種邊界情況（例如跨兩天以上沒登入、同一天多次呼叫）下是否正確。
    這個數字若進了老師報表就是「留存」這一層的核心指標（_DOMAIN.md §5 使用層級），
    在標成「可信」之前，建議先補一組邊界情況的單元測試（不是我寫，是移交建置端）。

## 對WP-8 Phase 0補丁的具體建議（怎麼補、補在哪個函式/欄位）

1. 先解決 sessionId 缺口：`sessionEnd()` 內把 `push(...)` 的回傳值存起來取 key，
   在整個 `sessionEnd()` 函式一開始就決定好 sessionId，讓後續所有 Phase 0 節點的寫入共用同一個值。

2. 在 `answer()` 新增 kcId/contentKey 的計算，但計算規則不該內建在 engine.js 裡：
   政策1定義 contentKey 依站別而不同（gsat/zhikao 用 headword、wordwheel 用字族、cards/translate/class
   用既有題型分類）。這是呼叫端（adapter）該算好、餵給 JG.answer 的東西，不是 engine 自己反推。
   建議 JG.answer 簽名新增 kcId（呼叫端算好整串組合值傳進來），
   engine 內部只負責用它去更新 progress/{uid}/kc/{kcId} 節點，不含業務判斷。
   category/errorMode（政策2的行為分類）應保持獨立欄位，不可混進 kcId，現有 category 參數
   語意含糊（目前拿它同時當 wrongItems 的分類用），建議拆成兩個明確參數避免未來誤用。

3. `sessionEnd()` 逐題迴圈（現有 L145-155）需要同時做三件事，不是只改 wrongItems 那段：
   (a) push 進 progress/{uid}/recentAttempts（保上限30筆，可用 get 現有陣列後裁切，或改用
   固定大小佇列寫法，避免每次都整包讀寫）；
   (b) 更新 progress/{uid}/kc/{it.kcId}：attempted/correct 累加、recentWindow 追加（上限10筆）、
   依政策8判斷是否為「距上次作答大於等於7天且不同session」的獨立事件來決定
   consecutiveSpacedCorrect 是否遞增/歸零、進而判斷 masteredAt/crossStationVerified；
   這段判斷邏輯建議獨立成一個純函式，方便對照驗收標準5-7、11、14單獨測試，不要塞進
   sessionEnd 這個已經很擠的函式裡；
   (c) wrongItems 的 repairHistory 改成陣列 append（現有 L153 的單值 update 要整段換掉），
   同時把 repairedAt 維持為 repairHistory 最後一筆的鏡像值（向下相容）。

4. 修好判定必須先解決本文第8條指出的「同場次刷分」漏洞，這個修法本身就需要 repairHistory/sessionId
   才能做：answer()（L84）目前 wasWrongBefore 判斷完全基於本機 this.local.wrong[qid] 是否存在；
   建議判定改為讀 wrongItems/{uid}/{qid} 的 lastMissAt 與目前 sessionId、時間，
   確認上一次錯誤與這一次答對不在同一個 session（至少）、或依 PLAN 決議是否也要求時間間隔，
   這條的最終規則本身待 §7 待決事項第10項排工時定案，這裡只確認現有程式碼完全沒做這件事。

5. answer() 簽名新增 kcId（見上）與 followedRecommendation（預設 false），
   計分那行（L84）改為 base 分數算完後，再疊加一致性加成：答對且 followedRecommendation 為真才加 2 分。
   純加法，向下相容，風險低。

6. 本文第1-4條（§A，跟WP-8無關的原始 schema 缺口）建議跟 Phase 0 補丁一起補，不要拆成兩輪：
   progress/{uid}.stations/{stationId}、.track、.badges 的寫入邏輯，跟 Phase 0 新節點都是同一個
   sessionEnd()/_loadRemoteIfNeeded() 要動的範圍，此時不順手補，WP-4/WP-3 會各自再回頭改一次 WP-1。

7. `_loadRemoteIfNeeded()`（L58-72）應該同時拉回 wrongItems/{uid}，讓本機 this.local.wrong 在登入時
   跟遠端對帳，而不是只信任本機鏡像，這是本文第4條指出的資料一致性缺口，不修的話「修好舊錯題」
   這個宣稱在跨裝置情境下會不穩定。

## 最重要的一件事

現有 `answer()` 裡「修好舊錯題 +15」的判定，現在就能被無腦刷分（同一題故意先錯、下一秒重考拿+15，
沒有任何時間或跨場次檢查），而且它已經被 PLAN 自己標成已知待補丁，這不是我這輪的新發現，
是我拿程式碼對照文件之後確認「PLAN 裡寫的擔心，程式碼裡真的是這樣寫」。
在 WP-1 正式跑五棒循環之前，這一條必須跟 Phase 0 的 repairHistory/sessionId 補丁一起排工，
不能只做 schema、不改 answer() 裡的判定邏輯，否則 schema 補了、漏洞還在，等於白補。
其次重要的是：progress/{uid}/kc/{kcId} 與 recentAttempts 兩個節點完全不存在，
這代表整個 WP-8 政策引擎現在沒有地基可以蓋，這兩個節點的寫入邏輯應視為 WP-1 正式循環的
交付範圍（而不是留給 WP-8 自己去補 WP-1 的資料層），因為 WP-1 的工作包名稱本身就叫
「遊戲化核心引擎 ＋ 資料層」。

## 交給誰

- 上述「怎麼補」的具體函式拆解（第2、3點提到的純函式化建議）需要 cycle-designer 收斂進正式 WP-1
  派工清單，決定 Phase 0 節點的寫入究竟算 WP-1 交付還是另開一張補丁票（PLAN §7 待決事項第10項
  目前寫的是「需要楊老師決定」，我這輪只確認技術上該怎麼接，沒有權限替楊老師做這個排工決定）。
- kcId/contentKey 由呼叫端（各站 adapter）計算或由 engine 內建計算，這是介面設計取捨，
  涉及 WP-2 各站 adapter 怎麼寫，建議 cycle-designer 跟負責 WP-2 派工的角色一起定。
- streak 記帳邏輯（本文第11、12條）的邊界情況正確性與 WP-9 floor-hit 的介面留位，
  機制設計本身仍是 game-designer/learning-scientist 的範圍，我只確認「資料介面現在留不住這個訊號」。
- engine.css 檔案不存在（HUD 樣式載入會失敗）是純工程缺陷，不在我的範圍，留給接手 WP-1 建置的人。
- 難度公式要不要換成 logistic/Rasch（PLAN §7 待決事項第7項，點名要我真身重新審查）不在這次任務範圍內，
  這次任務限定審查 game/engine.js 這份 WP-1 草稿，難度公式屬於 WP-8 政策5，
  待 wp-manager 或 cycle-designer 另外排一輪 WP-8 政策5 的真身複審再處理。
