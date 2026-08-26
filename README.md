# My Claude Skills

自製的 Claude Skills 收藏。想到有用的就加進來。

## Skills

| Skill | 說明 |
|---|---|
| [hackmd-note](./hackmd-note) | 寫充分運用 HackMD 語法的筆記（色塊、收合、mermaid、簡報模式等 36 類語法）。只產內容，不發表。 |
| [humanizer-zh-tw](./humanizer-zh-tw) | 去除 AI 寫作痕跡，基於 24 種模式 + 50 分制評分。繁中版，衍生自 blader/humanizer → op7418/Humanizer-zh。 |
| [survey-design](./survey-design) | 設計符合發表水準的學術問卷，基於 COSMIN/Dillman 方法論。24 項自評量表 + 自動修正迴圈，產出問卷、編碼簿、專家評定表。 |
| [teaching-handbook](./teaching-handbook) ⚙️ | 把 Word (.docx)、Markdown (.md) 或 PowerPoint (.pptx) 教學講義轉成「側邊欄導航風格」的高畫質網頁。忠實機械轉檔：保留 Word 原圖與文字顏色，自動生成目錄、Scroll Spy、程式碼複製按鈕。 |
| [paper-language-pass](./paper-language-pass) | 英文學術論文（.docx/.md/.tex）投稿前語言層潤稿：8 個平行 subagent 各掃一個維度，等使用者核可才動檔。Pass 8 用全文密度數字判定 AI 味（誇示形容詞、自創術語、em-dash 密度等 8 類）。中文稿請用 humanizer-zh-tw。 |
| [tw-naming](./tw-naming) | 繁體中文（台灣語境）姓名 skill：取名 / 評估 / 改名三模式，以康熙筆劃為三才五格基準。整合 breezyreeds 康熙筆劃 CSV + johnwu1114 繁體字庫 + wikiversity 生肖字根規則。 |
| [interpreting-stock-mood](./interpreting-stock-mood) | 股票溝通師：擬人化獨白搭配 MA/RSI/MACD 等客觀技術指標解讀股票心情。自動抓股價、PTT、Yahoo 留言、三大法人、新聞（yfinance + Google News RSS 雙來源容錯）與 Google Trends（選用），強制「非投資建議」免責，可選產出 DOCX。 |
| [codelab-handout](./codelab-handout) ⚙️ | 把上課內容轉成 Google Codelabs 風格的單檔 HTML 講義（藍色主題、章節時間預算、sticky 目錄）。觸發詞要明說 "codelab"；一般轉網頁請用 teaching-handbook（忠實轉檔 vs 強意見設計的分工）。 |
| [music-disc-video](./music-disc-video) ⚙️ | 把「封面圖 + mp3 + 歌詞」做成旋轉碟片配同步滾動歌詞的視覺，輸出雙擊即播的單檔 HTML 和／或 MP4。六套版面（16:9 / 9:16 / 1:1，各有含歌詞與純音樂版）。歌詞吃 .srt / .lrc / 純文字，沒有時間軸會產生敲拍對時工具。 |
| [learn-notes](./learn-notes) | 專案內學習筆記系統（LEARN.md 目錄 + learns/ 逐日筆記），為非工程師設計：白話 + 比喻的筆記風格、支援 Obsidian 雙括號連結、「複習」時自動查目錄帶你回顧。說「做筆記」「更新 LEARN」「複習」就觸發。 |
| [course-handout](./course-handout) | 把「分部驟跟著做」的實作課做成學員能自己操作到底的互動講義網頁（Artifact）：單元收合、提示詞一鍵複製、可打勾驗收清單（含預期錯誤）、術語浮動說明、五色畫筆、結業證書（2,500 種頭銜、可下載 PNG）、Markdown 下載。四種起點：有專案、只有主題、只有程式碼（逆向反推提示詞）、非 AI 課。閱讀型講義請用 codelab-handout。 |

⚙️ = 除了複製資料夾之外**還要另外安裝東西**才能跑，見該 skill 的 README。

## 安裝

把想用的 skill 資料夾複製到 Claude 的 skills 目錄：

**macOS / Linux：**

```bash
git clone https://github.com/unbias38/my-claude-skills.git
mkdir -p ~/.claude/skills
cp -r my-claude-skills/hackmd-note ~/.claude/skills/
```

**Windows (Git Bash)：**

```bash
git clone https://github.com/unbias38/my-claude-skills.git
mkdir -p "$HOME/.claude/skills"
cp -r my-claude-skills/hackmd-note "$HOME/.claude/skills/"
```

**Windows (PowerShell)：**

```powershell
git clone https://github.com/unbias38/my-claude-skills.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
Copy-Item -Recurse my-claude-skills/hackmd-note "$env:USERPROFILE/.claude/skills/"
```

> ⚠️ **`mkdir` 那行不能省。** `~/.claude/skills/` 不存在時，`cp -r` 和 `Copy-Item`
> 都不會報錯，而是把 skill 資料夾本身變成 `skills`——你會得到
> `~/.claude/skills/SKILL.md` 而不是 `~/.claude/skills/hackmd-note/SKILL.md`，
> skill 靜默不載入。

安裝完重啟 Claude Code 即可使用。裝好的樣子應該是
`~/.claude/skills/<skill 名稱>/SKILL.md`。

> 標了 ⚙️ 的 skill 還需要額外的環境（詳見各 skill 資料夾的 README）：
> - `music-disc-video` 要 `pip install numpy pillow imageio-ffmpeg`，裝完跑
>   `python3 music-disc-video/scripts/env.py` 會逐項告訴你缺什麼
> - `teaching-handbook` 要安裝 [uv](https://docs.astral.sh/uv/)（Python 套件由 `uv run` 自動處理）
> - `codelab-handout` 要 Python 3.10+ 和 `pip install markdown`

### 一鍵安裝全部

**macOS / Linux / Git Bash：**

```bash
mkdir -p ~/.claude/skills
for d in my-claude-skills/*/; do cp -r "$d" ~/.claude/skills/; done
```

**Windows (PowerShell)：**

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
Get-ChildItem my-claude-skills -Directory | Copy-Item -Recurse -Destination "$env:USERPROFILE/.claude/skills/"
```

## 只想安裝單一 skill？

用 git sparse-checkout 只抓你要的：

```bash
git clone --filter=blob:none --sparse https://github.com/unbias38/my-claude-skills.git
cd my-claude-skills
git sparse-checkout set hackmd-note
mkdir -p ~/.claude/skills
cp -r hackmd-note ~/.claude/skills/
```

## 觸發方式

各 skill 的觸發條件寫在各自的 `SKILL.md` 裡，Claude 會自動判斷何時啟用。

例如 `hackmd-note` 會在你提到 HackMD、hackmd 筆記，或要求產生 HackMD 格式輸出時自動觸發。

## 授權

本 repo 採用 [MIT License](./LICENSE)，Copyright (c) 2026 九月筍 (unbias38)。

**關於衍生 skill**：部分 skill 是第三方開源專案的衍生版本，會在該 skill 的子資料夾另外保留一份 `LICENSE`，完整列出上游著作權以符合原作者授權條款。例如：

- [`humanizer-zh-tw/LICENSE`](./humanizer-zh-tw/LICENSE) — 衍生自 [blader/humanizer](https://github.com/blader/humanizer)（Siqi Chen）經由 [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh)（歸藏），全部 MIT 授權
- [`tw-naming/LICENSE`](./tw-naming/LICENSE) — 整合 [breezyreeds/kangxi-strokecount](https://github.com/breezyreeds/kangxi-strokecount)（MIT, Kawai Lo）+ [johnwu1114/chinese-name](https://github.com/johnwu1114/chinese-name)（**upstream 無 LICENSE**，使用前請見該 skill 的 README License Caveat 段落）+ [zh.wikiversity 生肖姓名學](https://zh.wikiversity.org/wiki/生肖姓名學)（CC BY-SA 4.0）
