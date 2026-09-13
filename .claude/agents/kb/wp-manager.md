# wp-manager 知識庫

> 這份是管理師自己跨輪累積的判斷，不是黑板（`_runlog.jsonl`）的複本。
> 黑板記「發生了什麼」，這裡記「我看出了什麼規律」。照 `kb/README.md` 的規則：
> 標日期、區分「本專案的實測」／「我的判斷」，被推翻的往下移標「已被 YYYY-MM-DD 推翻」，不刪除。

## 2026-09-14（第一輪，管理師剛接線，由主線代為補寫第一筆——之後由 wp-manager 自己追加）

### 本專案的實測

- `agents_census.py` 對本線印出「定義16隻/載入14隻，少2隻」是**假陽性**：那2隻是 `README.md`
  與 `_DOMAIN.md`，本來就不是代理人定義（無 frontmatter 是預期行為，不是缺失）。
  **下次看到這個數字不用重查一次，直接排除這兩個檔名就對得起來。**
- `game/engine.js` 存在（commit fa0b6a8），但是 WP-1 正式五棒循環**之前**的 ad-hoc v0 草稿：
  沒有掛進任何一站（`wordwheel.html` 裡沒有 `JG.` 呼叫）、也沒有 WP-8 裁決新增的 Phase 0
  補丁（`recentAttempts`／`repairHistory`／`followedRecommendation` 都 grep 不到）。
  ⇒ WP-5 §5 的狀態標記「⬜未開始」雖然字面精準，但容易被誤讀成「空白起跑」，實際上是「有舊債」。
- WP-8 五位專家審查裡，只有 `learning-scientist`（v2）與 `english-teacher` 是**真身** subagent_type
  執行；`assessment-expert`／`game-designer`／`ux-designer` 三份是上一個 session 因為平台限制
  用 general-purpose 模擬產出的。這個區分容易在後續輪次被忽略、誤讀成「五位真專家都審過了」。

### 我的判斷（事後驗證：對了）

- 2026-09-14 第一輪判斷：WP-1 該優先，且第一步不是重寫引擎，是先找 `assessment-expert`
  審查現有 v0 草稿跟 WP-8 Phase 0 補丁的落差。
  **驗證結果：assessment-expert 跑完後確認判斷正確**——`game/engine.js` 的「修好+15」判定
  完全沒有跨場次檢查（可被同一題故意先錯、下一秒重考就拿分鑽掉），且 `progress/{uid}/kc/{kcId}`
  與 `recentAttempts` 這兩個 WP-8 政策引擎的地基節點完全不存在。這兩件事必須跟 Phase 0
  補丁一起排進 WP-1 正式派工，不能只補 schema 不修判定邏輯（見 `docs/cycle/wp1-0-assessment-review.md`）。
  ⇒ 「先審查既有草稿再決定要不要重寫」這個判斷模式，下次遇到類似情況（有舊草稿、規格後來又修訂過）
  可以直接沿用，不用重新推導。

### 待觀察

- 這是第一輪，還沒有「我的建議被推翻」的案例可記錄。下一輪如果 `cycle-designer` 收斂
  `wp1-0-assessment-review.md` 時對優先序有不同判斷，要回來補這一節。
