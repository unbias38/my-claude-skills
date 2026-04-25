# My Claude Skills

自製的 Claude Skills 收藏。想到有用的就加進來。

## Skills

| Skill | 說明 |
|---|---|
| [hackmd-note](./hackmd-note) | 寫充分運用 HackMD 語法的筆記（色塊、收合、mermaid、簡報模式等 36 類語法） |
| [humanizer-zh-tw](./humanizer-zh-tw) | 去除 AI 寫作痕跡，基於 24 種模式 + 50 分制評分。繁中版，衍生自 blader/humanizer → op7418/Humanizer-zh |
| [survey-design](./survey-design) | 設計符合發表水準的學術問卷，基於 COSMIN/Dillman 方法論。24 項自評量表 + 自動修正迴圈，產出問卷、編碼簿、專家評定表 |
| [teaching-handbook](./teaching-handbook) | 把 Word (.docx) 或 Markdown (.md) 教學講義轉成「側邊欄導航風格」的高畫質網頁。保留 Word 原圖與文字顏色，自動生成目錄、Scroll Spy、字體縮放、程式碼複製按鈕 |
| [paper-language-pass](./paper-language-pass) | 學術論文（.docx/.md/.tex）投稿前語言層 polish。6 個平行 subagent（一致性／時態／hedging／散文／連貫／摘要）各自掃全篇但只專注一維度，產出嚴重度排序的編號清單，等你決定哪些要修才動檔。Venue-agnostic，依使用者提供的期刊規則（abstract 是否允許 citation、tense 慣例、拼字、字數限制等）自動校準 |

## 安裝

把想用的 skill 資料夾複製到 Claude 的 skills 目錄：

**macOS / Linux：**

```bash
git clone https://github.com/unbias38/my-claude-skills.git
cp -r my-claude-skills/hackmd-note ~/.claude/skills/
```

**Windows (Git Bash)：**

```bash
git clone https://github.com/unbias38/my-claude-skills.git
cp -r my-claude-skills/hackmd-note "$HOME/.claude/skills/"
```

**Windows (PowerShell)：**

```powershell
git clone https://github.com/unbias38/my-claude-skills.git
Copy-Item -Recurse my-claude-skills/hackmd-note "$env:USERPROFILE/.claude/skills/"
```

安裝完重啟 Claude Code 即可使用。

## 只想安裝單一 skill？

用 git sparse-checkout 只抓你要的：

```bash
git clone --filter=blob:none --sparse https://github.com/unbias38/my-claude-skills.git
cd my-claude-skills
git sparse-checkout set hackmd-note
```

## 觸發方式

各 skill 的觸發條件寫在各自的 `SKILL.md` 裡，Claude 會自動判斷何時啟用。

例如 `hackmd-note` 會在你提到 HackMD、hackmd 筆記，或要求產生 HackMD 格式輸出時自動觸發。

## 授權

本 repo 採用 [MIT License](./LICENSE)，Copyright (c) 2026 九月筍 (unbias38)。

**關於衍生 skill**：部分 skill 是第三方開源專案的衍生版本，會在該 skill 的子資料夾另外保留一份 `LICENSE`，完整列出上游著作權以符合原作者授權條款。例如：

- [`humanizer-zh-tw/LICENSE`](./humanizer-zh-tw/LICENSE) — 衍生自 [blader/humanizer](https://github.com/blader/humanizer)（Siqi Chen）經由 [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh)（歸藏），全部 MIT 授權
