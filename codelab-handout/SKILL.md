---
name: codelab-handout
description: >
  Convert lecture content into Google Codelabs-style single-file HTML
  handouts. Strongly opinionated visual design (Google blue, Codelabs
  aesthetic, per-step duration markers, sticky sidebar TOC, font/width/
  theme toggles, code copy buttons). Triggers ONLY when the user
  explicitly mentions "codelab" / "Codelabs" — e.g. "做成 codelab 樣子的
  網頁", "轉成 codelab 講義", "Codelabs-style handout", "codelab-handout",
  "Google Codelabs 風的講義". For generic "convert docx/md/pptx to a web
  page" without the codelab keyword, use teaching-handbook instead. This
  skill is for users who want the specific Codelabs look-and-feel,
  including time-budgeted step structure (5–8 sections, each with
  Duration). Accepts markdown directly; for docx/pdf/pptx, convert via
  markitdown first. The build script enforces output saved OUTSIDE the
  skill folder.
---

# codelab-handout

把上課內容（口述、docx、pdf、pptx、md）轉成 Google Codelabs 風格的單檔 HTML 講義。學生雙擊就能開，左側 sticky 目錄、每章節時間標記、明暗主題、三段字級。

> `<SKILL_DIR>` 代表本 `SKILL.md` 所在的資料夾。腳本路徑為 `<SKILL_DIR>/scripts/build.py`、範本為 `<SKILL_DIR>/assets/template.html`。

## 範圍邊界

本 skill 只產 Codelabs 風格的強意見視覺設計；要忠實保留原檔樣式（Word 顏色、原圖）請用 `teaching-handbook`。

**不要這樣修**：
- ~~拿掉 build.py 的 skill 資料夾輸出守門~~ — repo 會被產出物弄髒
- ~~在 build.py 裡寫死內容改寫規則~~ — 內容語感是步驟 2 LLM 的工作（腳本苦力 / LLM 判斷分工）

## 步驟 1：依輸入類型準備 markdown

| 輸入 | 處理方式 |
|------|---------|
| 口述大綱／主題 | 直接寫 markdown（格式見步驟 2）|
| 現有 markdown | 跳過寫作，直接到步驟 3 |
| docx / pdf | 先轉成 markdown 再整理結構：用 markitdown CLI（`pip install "markitdown[all]"`）或已安裝的 markitdown skill；沒有 markitdown 時，docx 可退 pandoc／mammoth、pdf 退 pymupdf |
| pptx | 同上（markitdown CLI 或 skill）；沒有時退 python-pptx 解析，再轉 markdown |

## 步驟 2：撰寫 markdown

**語感**：講義要口語化，像老師上課的口氣（用比喻、「我們來……」、blockquote 標小提醒、適度幽默但不裝年輕）。不確定語感時讀 `<SKILL_DIR>/references/example_input.md`。

**格式規範**：

````markdown
---
title: 講義標題
duration: 60          # 選填，總分鐘數
authors: 講師名字     # 選填
---

## 章節一：標題
Duration: 5

內容文字。每個 `##` 會變成一個獨立區塊與目錄項。

```python
print("程式碼區塊會自動加複製按鈕")
```

> 💡 引言會渲染成有底色的提示框
````

**章節設計原則**：

- 每個 `##` 是一個完整步驟，學員看完一個 `##` 應該可以喘口氣
- 5–8 個章節最理想（多了側邊欄擁擠）
- `Duration` 用整數分鐘
- 首章節寫「今天要做什麼」、尾章節寫「你帶走了什麼」

## 步驟 3：執行 build.py

> ⚠️ **成品不能輸出到 skill 資料夾**。`scripts/build.py` 會主動擋下。輸入也不要放在 skill 資料夾，建議輸入跟輸出都放在使用者專案目錄或 `~/Documents/`。

```bash
python3 <SKILL_DIR>/scripts/build.py 輸入路徑/講義.md -o 輸出路徑/講義.html
```

（Windows 用 `python` 取代 `python3`，下同）

範例：

```bash
python3 <SKILL_DIR>/scripts/build.py ~/Documents/lecture.md -o ~/Documents/lecture.html
```

依賴：Python 3.10+、`markdown` 套件。缺套件時腳本會提示安裝指令。

## 步驟 4：請使用者預覽

依使用者作業系統提供開啟指令：

- **Windows**：`start <檔案絕對路徑>` 或 `explorer.exe <檔案絕對路徑>`
- **macOS**：`open <檔案絕對路徑>`
- **Linux**：`xdg-open <檔案絕對路徑>`
- **WSL**（要在 Windows 瀏覽器開）：`explorer.exe "$(wslpath -w <輸出檔>)"`

## 主題色客製

把 `<SKILL_DIR>/assets/template.html` **複製到你的專案目錄**修改，再用 `--template` 指定；**不要直接改 skill 資料夾內的檔案**（之後更新 skill 會衝突）。

```bash
python3 <SKILL_DIR>/scripts/build.py 講義.md -o 講義.html --template 你的專案/my-template.html
```

要改的是範本開頭的 `:root` CSS 變數：`--accent` 是主色（預設 Google 藍 `#1A73E8`）、`--accent-bg` 是主色淺底、`--sidebar-w` 是側邊欄寬度。
