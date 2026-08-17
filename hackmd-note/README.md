# HackMD 筆記寫手 / hackmd-note

一個 Claude Code skill —— 讓 Claude 用 HackMD 擴充版 Markdown 的完整語法（色塊、收合區塊、圖表、嵌入、簡報模式…）幫你「寫出」一份排版豐富的 HackMD 筆記內容，你只要複製貼上到 hackmd.io 就能用。

## 為什麼需要它

HackMD 支援的語法遠比一般 Markdown 多——`:::info` 色塊、`:::spoiler` 收合、`{%youtube%}` 嵌入、mermaid 圖表、數學式、簡報模式……但 Claude 平常寫筆記只會用到最基本的標題和條列。這個 skill 附上一份完整的 HackMD 語法參考，讓 Claude 寫筆記時知道有哪些工具可以用、什麼時候該用哪個，產出的筆記直接貼進 HackMD 就是漂亮的成品。

## 它做什麼

當你請 Claude 寫 HackMD 筆記時，它會：

1. 先讀內建的語法參考（`references/syntax-core.md`；需要圖表、樂譜、簡報或書本模式時再讀 `syntax-advanced.md`）
2. 依內容挑選合適的語法，例如：

| 情境 | 會用的語法 |
| --- | --- |
| 重點提醒、警告 | `:::info` / `:::warning` / `:::danger` / `:::success` 色塊 |
| 補充細節不想佔版面 | `:::spoiler` 收合區塊 |
| 關鍵詞強調 | `==螢光標記==`、`++底線++` |
| 結構化比較 | 表格 |
| 筆記有 4 個以上章節 | `[TOC]` 自動目錄 |
| 流程、關係視覺化 | mermaid / flow / sequence / graphviz 圖表 |
| 公式 | MathJax 數學式 |
| 影片、PDF、設計稿 | `{%youtube%}` / `{%pdf%}` / `{%figma%}` 嵌入 |

3. 用清楚的標題結構、短段落、標籤（`` ###### tags: `tag` ``）組織內容
4. 若你指定簡報或書本模式，會改用對應的 `---` / `----` / `===` 結構
5. 最後把整份筆記包成**一個可直接複製的區塊**交給你

語言會跟著你走——你用中文問，預設就產出繁體中文筆記。

## 怎麼觸發

跟 Claude 說類似這些話：

```
幫我寫一份 HackMD 筆記，主題是今天的會議紀錄
把這篇文章整理成 hackmd 筆記
幫我做一份 HackMD 簡報，介紹我們的新功能
這份筆記要放到 HackMD，幫我加上 info 色塊和目錄
```

只要提到「HackMD」「hackmd 筆記」，或要求用 HackMD 特有功能（`:::info` 色塊、spoiler、`{%youtube%}` 嵌入、簡報、書本模式），就會觸發。

## 範圍邊界（重要）

這個 skill **只負責寫出筆記內容**，不會動到你的 HackMD 帳號：

- 不發表、不上傳到 hackmd.io，也不呼叫任何 HackMD API 或 MCP 工具
- 不列出、更新、刪除你既有的 HackMD 筆記
- 若你要「寫完直接發表」，它會先產好草稿，再交給環境裡的發表工具（若有）處理

## 安裝

把資料夾複製到 Claude Code 的 skills 目錄即可，零依賴、不用裝任何東西：

```
~/.claude/skills/hackmd-note/            # 全域可用
# 或
<專案>/.claude/skills/hackmd-note/       # 只在該專案啟用
```

裝完重啟 Claude Code。詳細安裝指令（含 Windows）見 [repo 根目錄 README](../README.md#安裝)。

## 檔案結構

```
hackmd-note/
├── SKILL.md                        ← Claude 讀的工作流定義（觸發條件 + 寫作準則）
├── README.md                       ← 你正在讀這份
└── references/
    ├── syntax-core.md              ← 核心語法參考（文字格式/色塊/嵌入/數學式…）
    └── syntax-advanced.md          ← 進階語法參考（圖表/樂譜/書本/簡報模式）
```

語法參考整理自 [HackMD 官方功能介紹](https://hackmd.io/features-tw)，僅作為語法重排，非官方文件。

## 授權

MIT（見 repo 根目錄 [LICENSE](../LICENSE)）。
