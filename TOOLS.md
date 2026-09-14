# 工具庫（誰都該先看一眼再動手）

> 動工前先掃一眼這份清單，有沒有現成工具可以用，**不要重造輪子**。
> 這份清單本身也有生命週期——見下方「工具生態治理」。
> 即時版（含當下的黑板觸發統計）可以看監看台 `agent_monitor_server.py` 的「工具庫」「觸發統計」兩塊，
> 這份文件是給**代理人自己讀**的靜態參考，監看台是給**楊老師看即時狀態**用的，兩者不同用途。

## 第一層：原始工具（Claude Code 平台內建，14 隻現況，2026-09-14 普查）

| 代理人 | Read | Grep | Glob | Bash | Write | Edit | WebSearch | WebFetch |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `assessment-expert` | ● | ● | ● | ● |  |  | ● | ● |
| `cycle-builder` | ● | ● | ● | ● | ● | ● |  |  |
| `cycle-designer` | ● | ● | ● | ● | ● |  |  |  |
| `cycle-evaluator` | ● | ● | ● | ● |  |  |  |  |
| `cycle-fixer` | ● | ● | ● | ● | ● | ● |  |  |
| `cycle-ideator` | ● | ● | ● | ● |  |  | ● | ● |
| `english-teacher` | ● | ● | ● | ● |  |  | ● | ● |
| `game-designer` | ● | ● | ● | ● |  |  | ● | ● |
| `learning-scientist` | ● | ● | ● | ● |  |  | ● | ● |
| `mutator` | ● | ● | ● | ● | ●（限自己的提案檔/kb） |  | ● | ● |
| `red-team-critic` | ● | ● | ● | ● |  |  | ● | ● |
| `student-tester` | ● | ● | ● | ● |  |  |  |  |
| `ux-designer` | ● | ● | ● | ● |  |  | ● | ● |
| `wp-manager` | ● | ● | ● | ● | ●（僅PLAN.md事實性內容/自己的kb） | ●（同左） |  |  |

沒有任何一隻拿到 `Agent` 工具——這不是遺漏，是 `MAX_DEPTH=1` 機械擋死的結果（見各檔紅線）。
只有 `cycle-evaluator`／`student-tester` 沒有 Write/Edit（權責分離：只能發現/模擬，不能動手）；
只有需要對外查證據的六位領域專家＋`cycle-ideator`／`mutator` 拿到 WebSearch/WebFetch。

## 第二層：這條線自己聚合出來的高層工具
|---|---|---|---|---|
| `board_tool.py` | 寫黑板一列／讀寫自己的KB，自動取真時間、組好schema、原子寫入 | 全部14隻代理人 | ✅ active | 任何任務完成後（寫黑板是強制的，不是選填） |
| `intent_ledger.py` | 對帳黑板上還沒結案的 `needs_human`／`proposed` | `wp-manager` | ✅ active | 團隊健檢、判斷現在球在誰手上 |
| `agent_monitor_server.py` | 給楊老師看的監看台（網頁，含Tailscale） | 楊老師本人（不是代理人用） | ✅ active | 人要看現況時，不是代理人任務流程的一部分 |
| `rtdb_merge.py` | 安全合併RTDB規則（GET全份→合併→PUT→驗證命名空間） | `cycle-builder`（規劃中） | 💡 proposed | WP-1步驟7目前只有散文描述，這支還沒真的存在 |
| `claim_audit.py` | 掃描指定詞（例：攻克/精熟）有沒有出現、資料撐不撐得住 | `assessment-expert`（規劃中） | 💡 proposed | 尚未建置 |
| `xp_sim.py` | 模擬計分規則在不同學生策略下的產出，抓鑽漏洞空間 | `game-designer`（規劃中） | 💡 proposed | 尚未建置 |
| `interleave_check.py` | 判定一串KC序列是否符合交錯規則 | `learning-scientist`（規劃中） | 💡 proposed | 尚未建置 |
| `floor_sim.py` | 模擬假學生跑WP-9底線偵測，量誤觸發率 | `cycle-evaluator`（規劃中，2026-09-14由red-team-critic提案改由cycle-designer裁決指派給cycle-evaluator——見`docs/cycle/wp9-2-design.md`「沒有採納」小節：寫模擬腳本屬驗收職權，不是紅隊審查職權） | 💡 proposed | 尚未建置；WP-9 Phase 3施工完成後，`cycle-evaluator`可直接照`evaluateFloorState`純函式介面契約寫這支或等效單元測試 |

## 工具生態治理（固定循環，不是一次性建置）

**沒有獨立的「工具循環」——治理疊在既有的黑板機制與 `wp-manager` 每次被呼叫的健檢上**，
理由：另開一套平行機制，會變成第二套需要維護、又容易跟黑板本尊漂移的系統（這個專案已經
在別的地方吃過「同一件事兩套邏輯講不同話」的虧，見 `docs/cycle/*` 的教訓）。

三個動作，任何代理人都能做，走既有的 `board_tool.py`：

1. **發明**：發現一個重複性、可以獨立驗證的判斷（不是「我覺得可以」而是「這件事每次都要
   人工重做一次」），`outcome=proposed`＋`--proposal` 描述這支工具該做什麼、誰會用、
   輸入輸出長什麼樣——寫法比照上表 `proposed` 那五列。
2. **改善**：工具用起來卡住、輸出格式不好用、少了個欄位，用 `--friction` 記下來
   （**不是**`residual_risk`——friction是「卡住但我自己繞過去了」，residual_risk是「還沒解決」）。
   friction 累積到一定次數，代表這支工具該回頭改了。
3. **停用**：一支工具長期沒有任何代理人在 `evidence` 或 `friction` 裡提到它——代表沒人在用，
   `outcome=proposed` 建議標記 `status=deprecated` 並說明為什麼。

**`wp-manager` 的團隊健檢每輪都要多看一項「工具生態」**（見它自己的 prompt）：
掃黑板的 `friction` 欄位跟工具相關的 `proposed` 提案，判斷這份清單裡哪支該升級成 active、
哪支累積夠多 friction 該回頭改、哪支長期沒人用該建議停用——**這份清單本身要跟著回報跟著改**，
不是寫一次就不動了。

## 誰能真的動手建/改/停用工具

跟代理人定義檔的邊界欄位是同一條紅線：**發明/改善/停用都是提案，不是代理人自己動手**——
除了 `board_tool.py`/`intent_ledger.py` 本身允許被讀取/呼叫（那是使用，不是修改）之外，
新增或修改工具原始碼是主線的職權（跟修改代理人定義檔同一個道理：邊界欄位一旦被順手改鬆，
錯誤不會當場報錯）。代理人負責**提案跟使用**，不負責**自己動手寫新工具**。
