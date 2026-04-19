---
name: teaching-handbook
description: 將 Word (.docx) 或 Markdown (.md) 教學講義轉成「側邊欄導航風格」的高畫質 HTML 網頁。使用時機：使用者說「上架教材」「上架講義」「教材轉網頁」「講義轉網頁」「轉成側邊欄導航風格」「轉成側邊欄網頁」「把這份 .docx/.md 轉 HTML」，或提供 .docx/.md 檔案並要求產出教學網頁時。產出包含固定側邊欄目錄、Scroll Spy、字體縮放、程式碼複製按鈕、自動保留 Word 文字顏色等互動功能。
---

# teaching-handbook

把 `.docx` / `.md` 教學講義轉成側邊欄風格的教學網頁。

## 硬規則（不可違反）

1. **必須使用 `.docx` 原始檔**，不接受先轉過的 `.htm` / `.html`（否則圖片會糊）。
2. **不要改寫 `scripts/` 下的 Python 邏輯**，直接呼叫即可。
3. **輸出檔名以輸入檔名為基底**（例如 `我的講義.docx` → `我的講義.html`），不要預設 `index.html`，避免覆蓋專案主頁。
4. 若目標輸出檔已存在，先向使用者確認再覆蓋。

## 依套件

第一次使用時執行一次即可：

```bash
uv add mammoth beautifulsoup4 markdown
```

## 執行 SOP

### 步驟 1：確認輸入檔

- 使用者提供 `.docx` → 走 `docx_converter.py`
- 使用者提供 `.md` → 走 `md_converter.py`
- 其他副檔名 → 停下來問使用者

### 步驟 2：確認參數（都有預設值，可略）

- `--title`：瀏覽器分頁標題（預設 `教學手冊`，md 預設 `Document`）
- `--sidebar-title`：側邊欄標題（僅 docx 支援，預設 `教學手冊導航`）
- 輸出檔名：省略則自動用輸入檔名 + `.html`

使用者若沒主動提，**直接用預設值**，不要反覆追問。

### 步驟 3：執行轉換

DOCX：
```bash
uv run .claude/skills/teaching-handbook/scripts/docx_converter.py "<input.docx>" --title "<標題>" --sidebar-title "<側邊欄標題>"
```

Markdown：
```bash
uv run .claude/skills/teaching-handbook/scripts/md_converter.py "<input.md>" --title "<標題>"
```

### 步驟 4：回報結果

告訴使用者輸出檔路徑，讓他可以打開檢查。不用自行開啟瀏覽器。

## 產出的網頁功能

- 左側 280px 固定側邊欄，自動從 `h1/h2/h3` 生成目錄（Scroll Spy 高亮目前章節）
- `<<` 收折按鈕：側邊欄縮成 60px，主區域擴展到 1400px
- `A- / 100% / A+` 字體縮放（預設 1.15x）
- 程式碼區塊（單格表格或 `<pre>`）自動加「複製」按鈕
- 圖片響應式（`max-width: 100%`），保留 Word 原始高畫質

## 檔案結構

```
.claude/skills/teaching-handbook/
├── SKILL.md                      ← 本文件
└── scripts/
    ├── docx_converter.py         ← .docx 入口
    ├── md_converter.py           ← .md 入口
    └── style_injector.py         ← 核心樣式 + 導航 + 複製按鈕引擎
```

`style_injector.py` 自成一體，`docx_converter.py` 與 `md_converter.py` 皆透過 `import style_injector` 呼叫它。
