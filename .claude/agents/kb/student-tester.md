# student-tester 知識庫

> 這份是 student-tester 自己跨輪累積的判斷，不是黑板的複本。照 `.claude/agents/kb/README.md`
> 的規則：標日期、區分「有定論的研究」／「本專案的實測」／「我的判斷」，
> 被推翻的往下移標「已被 YYYY-MM-DD 推翻」，不刪除。


## 2026-09-14

【2026-09-14 首次執行｜情境C走查】WP-9 機制本身讀碼通過，但接線範圍是本輪最大發現，優先度高於文案措辭。

## 本專案的實測（讀碼證實，非揣測）
1. WP-9（evaluateFloorState/showFloorHit/floorState）目前只接在 wordwheel.html（`wordwheel.html` L226-352）。
   `gsat/index.html`（984行，學測單字843題主站）grep `JG.\|floor` 完全零匹配——情境C學生若從首頁
   最顯眼的「學測單字」卡片（`index.html` L245，主要card，非quicknav小字）進去，系統目前**沒有任何
   底線偵測**，會一路答到猜測水準也不會停。這是WP-9「這個WP就是為了情境C存在」的目標，但目前的
   建置範圍構造性地碰不到情境C最可能先踩到的那個站。
2. wordwheel.html 觸底畫面的主要按鈕「回到單字輪重新開始（段考範圍）」(`wordwheel.html` L243-244)
   onclick 只是 `setMode('quiz')`——不重設 `cur`（word family索引），實際效果是重刷「剛剛讓他觸底的
   同一個字族、同一個題型難度」，不是導向真正更簡單的內容。搭配 `evaluateFloorState`
   規則3（一旦active，之後每題不是exit就是trigger_short，見`docs/cycle/wp9-2-design.md`L347-352）：
   點下這顆主按鈕後，學生要在同樣讓他觸底的內容上連續答對5題才能脫離，否則每答一題就再看到一次
   截斷畫面——按鈕文字承諾的「降階」跟實際發生的事不一致。
3. roots深連結：`wordwheel.html` DATA[].k（如re-、-tion/-sion、con-/com-）與roots_data.json的15個
   groups[].key（tain/ten、pon/pos、spond/spons、vers/vert、fer、spec/spect、speci、ced/cess、
   cap/capt、-ceive、princip-、tend/tens/tent、lect/leg/lig、leg/legis、lig）**完全沒有交集**
   （`docs/cycle/wp9-2-design.md` 驗收標準12v3已自述此發現，本輪逐字核對 roots_data.json 確認為真，
   非文件自己猜測）。`?g=`永遠findIndex=-1，學生點「看字根表」進去看到的必然是245字未篩選全清單，
   不是對應到他剛卡關那個字族的篩選結果。
4. 觸底文案（v3，`wordwheel.html` L225）已核實通過三輪真身審查修訂，全文純中文、無需解碼英文，
   對「連基礎英文閱讀都吃力但中文閱讀正常」的情境C學生應該可讀——這一條文案本身做得紮實，
   問題在接線範圍與按鈕行為，不在文案語感。

## 我的判斷（無法只靠讀碼驗證，需真人測試）
- 情境C學生在wordwheel的parse/sense/infer/fake題型（例：「reform 怎麼拆？」四個選項都是精細的
  中文構詞辨析如「re 再+form 形狀」vs「re 回+form 表格」）很可能落在≤30%或連8題錯，因為這題型
  要求的不是單字量而是中文構詞分析的精讀能力——這一步只是合理推測，需要真人數據。
- 首頁（index.html）本身是一面高密度純文字牆（含答對率、鑑別度等術語），情境C學生能不能撐過
  「找到該去哪一站」這一步本身就是問題，這比WP-9內部設計更早發生，屬於WP-9範圍外但值得記錄。

## 已被推翻
（無，這是本代理人第一次執行）
