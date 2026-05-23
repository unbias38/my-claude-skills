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

## 步驟 1：依輸入類型準備 markdown

| 輸入 | 處理方式 |
|------|---------|
| 口述大綱／主題 | 直接寫 markdown（格式見步驟 2）|
| 現有 markdown | 跳過寫作，直接到步驟 3 |
| docx / pdf | 先用 `markitdown` skill 轉成 markdown，再整理結構 |
| pptx | 用 `markitdown` 或 python-pptx 解析，再轉 markdown |

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
- **WSL**（要在 Windows 瀏覽器開）：`\\wsl.localhost\<distro><檔案絕對路徑>`

## 主題色客製

改 `<SKILL_DIR>/assets/template.html` 開頭的 `:root` CSS 變數即可。`--accent` 是主色（預設 Google 藍 `#1A73E8`）、`--accent-bg` 是主色淺底、`--sidebar-w` 是側邊欄寬度。
