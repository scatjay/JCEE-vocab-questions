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

## 2026-09-14（第二輪，第一次真的跑團隊健檢的「休假候選」與「突變頻率」兩項新裝檢查）

### 本專案的實測

- **黑板 2 列不是「其他人跑完沒寫」的協定違反**：對照 git log 時間序，`_runlog.jsonl` 寫入協定是
  commit `c9417ce`（"接上管理師＋黑板架構...12隻代理人補寫黑板協定"）才加進各代理人定義檔，
  時間點晚於 WP-8 五份審查（`e5e7ddf`／`6fffab2`）。⇒ **那幾份審查沒留黑板列是預期行為，
  不是沉默違規**——下次看到「黑板列數遠少於 docs/cycle/ 產出數」不用直接判定違規，
  先比對 git log 的 commit 時間序跟協定加入的時間點。
- **KB 機制本身有系統性落差，不是六位領域專家偷懶**：`kb/` 目錄目前只有 `README.md` 與
  `wp-manager.md` 兩個檔——包括 `assessment-expert` 這兩輪都真的跑過兩次實質審查
  （WP-8、WP-1 v0），也完全沒有寫出 `kb/assessment-expert.md`。逐檔 grep 14 隻代理人定義檔的
  「寫黑板」收尾段落後發現：**只有 `wp-manager`／`mutator`／`red-team-critic`／`game-designer`
  四隻的定義檔裡有「完成後追加自己 KB」的明文指示**；其餘 10 隻（`assessment-expert`／
  `cycle-designer`／`cycle-builder`／`cycle-evaluator`／`cycle-fixer`／`cycle-ideator`／
  `english-teacher`／`learning-scientist`／`ux-designer`／`student-tester`）的「動工前」段落
  都有「先讀自己的 KB」，但收尾的「寫黑板」段落只寫黑板列、完全沒提回寫 KB。
  ⇒ 這解釋了「休假候選」這項檢查這一輪注定查不到任何候選——不是因為六位專家還沒觀察到
  ≥3 筆值得記錄的東西，是因為**多數代理人的定義檔本身沒有指示它們寫**。
  這是「脫節」等級的落差：`kb/README.md` 明訂全部 14 隻角色（含流程角色）都該累積 KB，
  但只有 4 隻的定義檔真的照做。
- **mutator 是本輪新增，尚未被呼叫過一次**（黑板無列、`kb/mutator.md` 不存在），
  不算「該跑卻沉默」，是還沒排到它的第一輪。

### 我的判斷

- 上述 KB 回寫落差**不建議我自己動手改 10 個代理人定義檔**——那是代理人定義檔的「內容本體」，
  不屬於 tools/model/紅線這種安全邊界（可以直接列 diff），但也不是 PLAN.md 的事實性狀態
  （可以直接同步），落在紅線「不自己建立或刪除代理人定義檔，除非主線明確同意」的精神範圍內
  （雖然字面只講建立/刪除，修改內容一樣需要主線同意）。⇒ 這輪只回報，附建議 diff 範本，
  不動手；下次主線同意後才補。
- 下次團隊健檢遇到「KB 是空的」不要直接跳到「這隻代理人沒在累積判斷」的結論——
  先查該代理人定義檔本身有沒有寫「跑完要回寫 KB」，很可能是機制沒接上，不是代理人沒做。

## 2026-09-14（同一輪，WP-1 收斂判斷）

### 我的判斷（本輪新增，尚待下一輪驗證對錯）

- WP-1 對照 §9 表格，必要審查者只有 `assessment-expert`（無需 red-team-critic 或全體五位專家），
  這一項已經在 `docs/cycle/wp1-0-assessment-review.md` 完成，且審查內容具體到函式/行號，
  不是空泛意見。⇒ WP-1 的「審查」棒次已走完，**不需要再找別的專家補審**，
  下一步是 `cycle-designer` 把這份審查收斂成 `docs/cycle/wp1-2-design.md`（含 §7 待決事項#10
  的排工決定：assessment-expert 已建議跟 Phase 0 補丁併一輪，這是工程排程判斷，
  不是需要楊老師裁示的政策問題，`cycle-designer` 有空間直接採納)。
- 黑板上 assessment-expert 那筆 `needs_human: true` 目前還沒有人接手處理——這是本輪唯一
  積壓的 `needs_human` 項目，且正好是「下一步找誰」的答案本身（cycle-designer），
  不是另一個獨立卡點。

## 2026-09-14

2026-09-14第三輪：第一次用Contract Net公告+授予格式。判斷：WP-1設計(wp1-2-design.md)已收斂完成、13條驗收標準逐條可驗，唯一必要審查者assessment-expert已審過，直接可交cycle-builder施工，不需再等——這驗證了第一輪"審查完成不需補審"的判斷模式可以連續套用到"設計完成不需補設計"。本輪新發現：WP-9的red-team-critic主審從未進行過(黑板全文搜尋零筆)，但WP-9的設計內容(§5 WP-9全節)已经由game-designer/ux-designer在WP-8審查那輪一併看過並經cycle-designer裁決寫入PLAN.md，這代表red-team-critic主審的前置條件(有東西可審)已滿足，且這個任務跟cycle-builder做WP-1完全沒有資料依賴——是這輪認得出的第二個獨立候選，不是硬湊數。mutator查了一輪：目前§6沒有任何決策符合"反覆修訂2次以上、框架從未被質疑"的門檻(精熟判定/tie-break都只修訂過一次)，判斷這輪不排mutator，不勉強找一個弱理由湊批次。共用池只剩3(17/20)，批次上限=min(3-5,3)=3，這輪公告2個沒有頂到上限，是因為只有2個真正獨立且front-condition滿足的任務，不是為了省用量刻意少報。

## 2026-09-14

第一次執行「突變討論與追蹤」健檢。mutator第一次真實任務（挑戰WP-8政策8精熟判定，用Leveled
Commitment框架）品質判斷：框架選用準確、後設分析（consecutiveSpacedCorrect歸零/masteredAt無
撤銷是兩處全有全無承諾）核對PLAN.md原文後成立，不是套框架硬找問題。但我發現mutator自己的
方案A文件有內部矛盾未被自己抓到：(1)宣稱"不需要新欄位"但同時要求"記錄撤銷事件"，而masteredAt
現行是單一ms|null無history，撤銷後"曾精熟過"的痕跡會消失——這是方案A文件本身的邏輯漏洞，不是
我雞蛋裡挑骨頭；(2)方案A沒提到PLAN.md §5 WP-8驗收第7條（已定案的機械驗收文字，測試"歸零重算"）
會被方案A的"扣點"行為打臉、需要同步改寫。教訓：mutator產出的裁決建議雖然框架分析紮實，但
"代價很小、不動schema"這類自我宣稱，需要我逐條回頭核對它列的驗收/schema原文才能抓到真正的
連動遺漏——不能只看它的論證邏輯內部自洽就照單全收。這類「宣稱不動schema但功能本身隱含需要
新欄位」的落差，下次審mutator或cycle-designer提案時應該固定檢查一遍。另外首次確認：mutator
工具箱的"上次用過"欄位它自己因為沒有Edit工具而留空，我補上了——這是我跨代理人視角職權範圍
內該做、且mutator在完成報告裡主動提到的缺口，往後mutator每次用完框架大概率都要靠我來補這欄。
