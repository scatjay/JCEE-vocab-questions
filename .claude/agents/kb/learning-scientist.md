# learning-scientist 知識庫

> 這份是 learning-scientist 自己跨輪累積的判斷，不是黑板的複本。照 `.claude/agents/kb/README.md`
> 的規則：標日期、區分「有定論的研究」／「本專案的實測」／「我的判斷」，
> 被推翻的往下移標「已被 YYYY-MM-DD 推翻」，不刪除。


## 2026-09-14

第一次真身任務：審查 docs/PLAN.md §5 WP-8（教學決策層政策1-9）＋ game/kc-logic.js 實作 ＋ docs/cycle/wp8-2-design.md／MUTATIONS.md#1 既有裁決。以下區分三類，供下次任務接續。

**有定論的研究（已查證，非猜測出處）**
- Cepeda, Vul, Rohrer, Wixted & Pashler (2008)，Psychological Science 19(11)，spacing effect大型後設分析（317個實驗、839筆評估）：最佳間隔（gap）佔「最終測驗延遲（retention interval）」的比例，隨延遲拉長而下降——約1週延遲時最佳gap佔20-40%，1年延遲時降到5-10%；但「絕對天數」仍隨延遲拉長而增加，不是固定值。這篇是WebSearch驗證過標題/作者/年份/期刊/核心數字，非逐字讀全文，標記為「僅摘要/二手整理層級的確認」，不是我逐段讀過原始論文。
- Wilson, Shenhav, Straccia et al. (2019)，Nature Communications 10:4646，「The Eighty Five Percent Rule for optimal learning」：85%最佳訓練正確率的結論來自二元分類任務（binary classification）與梯度下降類學習演算法的模擬/機器學習實驗，不是人類課堂verbal/vocabulary recall的直接實證。同樣經WebSearch確認標題/作者/期刊/核心結論存在，未讀全文，標記「僅摘要」。**重要限定**：本專案領域簡報§2把「~85%」當設計原則沿用是合理方向（desirable difficulty文獻的一般共識——太易無成長太難只剩挫折），但把85%當成precise universal constant（而非70-90%這種區間性共識）套用到四選一單字題，超出這篇論文實際驗證過的任務類型，算是「合理外推但非同一domain驗證」，下次遇到有人把85%當成鐵律逐位小數比對時要提醒這個限定。

**本專案的實測（讀碼證實，非猜測）**
- WP-8政策8的`crossStationVerified`（「精熟」vs「此站已穩定」用語分級的判定依據）在目前的kcId schema下**結構性不可能為true**：政策1定義`kcId=${station}:${contentKey}`，且`game/engine.js`（`JG.init({station:"wordwheel"})`、`${this.station}:${qid}`fallback）與`game/kc-logic.js`的`stationsInStreak`機制證實，同一個kcId記錄只會收到「同一個station」寫入的事件（因為station本身就是key的一部分），所以`new Set(stationsInStreak).size>=2`在真實系統裡永遠不會發生——`crossStationVerified`永遠是false，「攻克」這個詞的顯示條件（政策8：`crossStationVerified:true`）在目前schema下**永遠不可達**。這不是我的猜測，是直接讀`docs/PLAN.md`政策1定義＋`game/engine.js`第208-220行＋`game/kc-logic.js`第38-74行三處交叉核對出的邏輯矛盾，且驗收標準第6條（PLAN.md §5第534行）要求測「若其中一次在不同站」——這種輸入在單一kcId記錄下不可能自然發生，只能靠手工餵給`evaluateKcEvent`這個純函式的假造測資通過單元測試（測到函式本身邏輯自洽，但驗證不到「真實系統會不會產生這種輸入」，這是單元測試沒觸及整合層級bug的典型案例）。下次任何人審WP-8/WP-2 KC相關產物，先查這個bug有沒有被回頭修（修法：把跨站可比對的KC改成不含station前綴的共用contentKey命名空間，讓多個站的事件能寫進同一筆KC記錄，station本身當成event的屬性留著即可，recentWindow本來就已經存了每筆event的station，不需要新欄位）。

**我的判斷（無定論證據，僅供本專案暫時參考）**
- KC_SPACED_MS固定7天（`game/kc-logic.js`第5-6行，`WP-8政策8`）沒有專屬研究支撐這個具體數字，讀起來像是工程上選的「一週」整數，且PLAN.md政策8全文沒有像政策5交錯規則那樣附「初始值，之後依真實資料調整」的但書——這是不一致的誠實度標示，我認為該補上同等但書。更根本的問題：北極星是900天的長期保留目標，但精熟判定只要求「3次獨立事件、每次間隔≥7天」，這個門檻可以完全在SRS梯度表（1/3/7/21/60天）最短的那一端就湊滿3次（例如第8/16/24天各測一次），從未在21天或60天的間隔驗證過retention——依Cepeda et al. 2008的比例關係，這種短間隔證據不足以代表「撐得到900天後的學測」這種長期保留，跟politique 4（SRS本身會拉長間隔）的設計精神其實矛盾但沒人明說。這是我的判斷，建議：精熟判定的3次獨立事件裡，至少要有1次發生在較長間隔（例如≥21天），而不是任何≥7天都算數，讓"精熟"更貼近北極星真正在乎的長程保留而非短期複習存活。
- 政策5交錯規則（同KC連續≤2題、間隔≥3題不同KC）的數字本身合理且已誠實標記為可調整，但操作定義的「同KC」＝「不同單字/字族」，跟交錯練習文獻（如Rohrer相關研究，我僅有印象、未逐篇查證，標記僅供參考）真正測的「不同題型/不同解題策略」是不同的顆粒度——本專案目前的每日排隊演算法(政策4+6)沒有明文要求跨站/跨題型混合，只保證跨單字混合，交錯效益可能比文獻預期的弱。這是我的判斷，非有定論證據，下次有真實資料時該檢查「同單字不同站/題型交錯」跟「同站不同單字交錯」對留存率有沒有差異。
