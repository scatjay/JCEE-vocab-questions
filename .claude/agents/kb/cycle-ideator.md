# cycle-ideator 知識庫

> 這份是 cycle-ideator 自己跨輪累積的判斷，不是黑板的複本。照 `.claude/agents/kb/README.md`
> 的規則：標日期、區分「有定論的研究」／「本專案的實測」／「我的判斷」，
> 被推翻的往下移標「已被 YYYY-MM-DD 推翻」，不刪除。


## 2026-09-14

2026-09-14（第一次真正跑動：五個遊戲玩法方向提案，見 docs/cycle/gameplay-diversity-1-options.md）本專案的硬約束清單（供未來構思參考，這輪盤點PLAN.md/_DOMAIN.md/game-designer KB後整理，不是我自己的實測）：
1) 【紅線】不做同儕排名——_DOMAIN.md §3明文，且_SHARED_language_learning_gamification.md已用Mogavi et al.(2022)全文的S2-1第一手證詞與「跟风行为」发现佐证：連「非正式的社交可見性」（不只是正式排行榜）都要推演风险，這比字面紅線更寬。
2) 【工程約束】無建置流程、純vanilla、13個獨立HTML檔——PLAN.md §3.1明講不得引入React/Tailwind/打包工具，外部套件只能CDN直載UMD版；任何提案若隱含「需要框架化改造」直接不成立，不必等設計棒才發現。
3) 【資料層約束】gsat/zhikao(838题选择题库)目前完全沒有KC精熟追蹤資料（WP-2尚未對它們掛勾，只有wordwheel透過WP-1真正接了engine）——提案若假設「所有站都有θ/KC資料可用」是錯的假設，要先查WP-2/WP-8的實際掛勾進度而非照抄wordwheel那條線的資料前提。
4) 【內容類型約束】translate站是自評式開放作答(gradeGood/gradeBad由學生自己按，機器不判分，實測見translate/index.html L940-950)——任何精熟判定/連續正確類機制的「客觀對錯」前提在這裡不成立，需要結構上不同的機制（自我前後對照，而非θ驅動）。
5) 【已佔用的機制線】"精熟地圖+鎖定每日3題來源"已經是docs/cycle/PLAYTEST.md收斂中的既有提案，構思棒新提案不能是它的换皮（同樣是KC continuous/predefined goal可視化），要主動检查新提案的目標結構軸（ephemeral/predefined/continuous/collection四種在game-designer.md已有明確定義可以拿來檢查互斥性）。
6) 【新資產尚未變成玩法】gsat/zhikao帶官方答對率/鑑別度是本站獨有資產，目前只在AI家教話術層被提及，尚未真的做成學生可體驗的機制——這是個具體的"文件裡寫了但沒做出來"缺口，不是憑空想像的痛點。
