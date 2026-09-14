# cycle-fixer 知識庫

> 這份是 cycle-fixer 自己跨輪累積的判斷，不是黑板的複本。照 `.claude/agents/kb/README.md`
> 的規則：標日期、區分「有定論的研究」／「本專案的實測」／「我的判斷」，
> 被推翻的往下移標「已被 YYYY-MM-DD 推翻」，不刪除。


## 2026-09-14

【根因分類帳，第1筆】2026-09-14 修 wordwheel.html showFloorHit() 降階按鈕原地鬼打牆bug
（student-tester情境C發現）。根因分類：資料層缺口（DATA無跨字族難度分級）＋單站部署與多站降階
路由設計假設不一致（docs/PLAN.md §5「wordwheel.html是段考範圍」是相對於未建置的學測級站而言，
不是wordwheel內部字族之間的分級；但觸底偵測目前只在wordwheel內部觸發，導致「降階路由回
wordwheel.html」這句話套在已經在wordwheel裡觸底的學生身上語意空洞）。本次判斷：不回退設計
（cycle-designer已經在wp9-2-design.md把Phase1-3裁決為可進build，這個bug是build階段的接線疏漏，
不是設計層新問題），採用「最小可行修正」（隨機切字族+開啟onlyExam篩選+誠實改按鈕文案），
把「真正的跨字族難度分級」與「單站vs多站降階語意」列為殘留限制記錄在wp9-2-design.md供
cycle-designer下一輪判斷，不自己動手改設計文件本身的§5定案文字。
【判斷，未經驗證】這類「承諾在文案裡但程式邏輯沒有真正實作」的bug，可能是這個團隊（文案由
cycle-designer裁決、UI由cycle-builder施工）常見的接縫——文案定案的語意（降階）沒有被翻譯成
具體的程式碼行為驗收標準（wp9-2-design.md驗收標準清單裡沒有一條是「驗證按鈕真的換了難度/字族」），
之後如果同類bug再出現≥2次，值得回報wp-manager建議在設計文件的驗收標準模板裡強制加一條
「UI文案的每個動詞承諾都要對應一條可驗的行為斷言」。
【本專案實測】專案沒有puppeteer/jsdom，重驗DOM互動類bug時改用「抽取<script type=module>內容+
node --check驗語法＋抽取DATA字面量用eval跑純邏輯模擬」的做法可行（此次抽取DATA用
html.indexOf('const DATA = ')到下一個const宣告前最後一個分號，因為整個DATA字面量在檔案裡是
單行、且內部字串含中文與跳脫字元，直接regex比對容易失敗）。
