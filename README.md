# JCEE Vocab Game（測試中）

這個 repo 是 [staresto-create/JCEE-vocab-questions](https://github.com/staresto-create/JCEE-vocab-questions) 的 fork，
原站是 [staresto-create ZZSH 老師的高中英文自學題庫](https://staresto-create.github.io/JCEE-vocab-questions/)。

## 原作與授權

- 歷屆學測／指考考古題本身：依中華民國著作權法第 9 條第 1 項第 5 款，不得為著作權之標的，任何人均得自由利用。
- 原站自撰的解析、中譯、分類、標註與編排：著作權屬 **staresto-create ZZSH** 所有，非商業使用、需註明出處。
- 本 fork 目前僅新增「登入與審核閘門」等系統架構，**未改動、未重製原站的解析／分類內容**。
- 任何後續要用於商業用途的規劃，前提是取得原作者本人授權，本 repo 目前的開發不涉及該方向。

## 這個 fork 目前加了什麼

- `/gate/` — Google 登入 + 楊老師人工審核閘門（Firebase Auth + Realtime Database，`jceeVocabGame` 獨立命名空間，
  與同一 Firebase 專案下其他專案的資料互不相通）。
  - `gate/login.html` — 學員登入頁，Google 登入後若未審核會停在等待畫面，審核通過即時解鎖。
  - `gate/admin.html` — 審核後台，僅 `scatjay@gmail.com` 可用（同時由 RTDB 安全規則強制，不是只靠前端隱藏）。
- `/play/` — 之後遊戲化練習系統（XP／連續紀錄／番茄鐘／碎片時間／AI 個人化家教建議）的入口，目前是建置中的佔位頁。

## 尚未完成（設計/建置中，不在今晚範圍）

- 遊戲化引擎（XP、等級、連續紀錄、徽章）
- 番茄鐘衝刺模式／碎片時間快速練習／高一高二（基礎）vs 高三（衝刺）分軌
- Chart.js 學習儀表板
- AI 個人化家教建議（Vertex Gemini，讀取練習數據＋題目既有解析，非開放式聊天機器人）
- 真人老師依報表與學生討論的機制
- 系統維運的子代理人（subagent）規劃

## 部署

GitHub Pages，同一 repo 的 `main` 分支。閘門頁尚未串進首頁 `index.html` 的導覽，測試期間直接開 `gate/login.html`。
