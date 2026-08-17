# 教材上架器 / teaching-handbook

一個 Claude Code skill —— 把 Word（`.docx`）、Markdown（`.md`）或 PowerPoint（`.pptx`）教學講義，一鍵轉成「側邊欄導航風格」的單檔 HTML 教學網頁：左邊固定目錄、右邊內文，附 Scroll Spy、目錄搜尋、字體縮放、程式碼複製按鈕，圖片保留原始高畫質。

## 為什麼需要它

講義寫在 Word 或簡報裡，想放上網讓學生看，通常得手動另存 HTML —— 結果圖片糊掉、沒有目錄、手機上難讀。這個 skill 直接吃**原始檔**，產出一個可以直接開的教學網頁，不用碰任何程式碼。

## 它做什麼（以及不做什麼）

本 skill 走**忠實機械轉檔**路線：把原檔的文字、圖片、結構原封不動搬進 HTML，**不改寫、不美化、不重組內容**。

- 想要轉完再潤稿或美化？轉檔完成後**另起對話**請 Claude 處理即可，本 skill 不越界。
- 想要 **codelab / Codelabs 風格**（強意見視覺重設計）？那是姊妹 skill `codelab-handout` 的工作，兩者分工是「忠實轉檔 vs 強意見設計」。

### 產出的網頁有什麼

| 功能 | 說明 |
|---|---|
| 固定側邊欄目錄 | 左側 280px，自動從 H1/H2/H3 生成，含 Scroll Spy 高亮目前章節 |
| 目錄即時搜尋 | 目錄上方有搜尋框，輸入即過濾章節 |
| 側邊欄收折 | `<<` 按鈕縮成 60px，閱讀區擴到 1400px |
| 字體縮放 | `A- / 100% / A+`（預設 1.15x） |
| 程式碼複製按鈕 | 程式碼區塊自動加「複製」 |
| 高畫質圖片 | 響應式、lazy load，保留 Word 原圖畫質 |
| 保留文字顏色 | Word 裡標的紅字藍字會原樣保留（docx） |

### PPTX 的特別處理

- 每張投影片變成一個章節（側邊欄自動列出）；章節分隔頁自動變成大標題
- **講者備註預設會納入**（教學簡報常把真正內容寫在備註），不要可加 `--no-notes`
- 投影片裡的裝飾小圖示會排成 80×80 縮圖列，避免版面被圖海淹沒
- 這是「重排器」不是「截圖器」：動畫、轉場、嵌入影片會丟失

## 怎麼觸發

把檔案丟給 Claude，說類似這些話：

```
上架教材
把這份講義轉成側邊欄網頁
幫我把 我的講義.docx 轉成教學網頁
把 simple.md 教材轉網頁
這份 .pptx 上架講義
```

標題、側邊欄名稱都有預設值，不講也能直接轉。輸出檔名跟著輸入檔走（`我的講義.docx` → `我的講義.html`），不會覆蓋你專案的 `index.html`。

## 安裝

### 1. 複製資料夾

把整個資料夾放到 Claude Code 的 skills 目錄：

```
~/.claude/skills/teaching-handbook/            # 全域可用
# 或
<專案>/.claude/skills/teaching-handbook/       # 只在該專案啟用
```

詳細安裝指令（含 Windows）見 [repo 根目錄 README](../README.md#安裝)。

### 2. 安裝 uv（唯一前置需求）

腳本用 `uv run` 執行，Python 套件依賴（mammoth、python-docx、python-pptx、markdown、beautifulsoup4）寫在各腳本的 inline metadata（PEP 723）裡，`uv` 會**自動安裝**，不用手動 `pip install` 任何東西。

沒有 uv 的話：

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 怎麼用（直接跑腳本也行）

不透過 Claude 也能手動轉：

```bash
# Word
uv run scripts/docx_converter.py "我的講義.docx" --title "課程名稱" --sidebar-title "課程導航"

# Markdown
uv run scripts/md_converter.py "講義.md" --title "課程名稱"

# PowerPoint（--no-notes 可排除講者備註）
uv run scripts/pptx_converter.py "簡報.pptx" --title "課程名稱" --sidebar-title "投影片目錄"
```

**注意**：一定要餵原始檔（`.docx` / `.md` / `.pptx`），不要餵 Word 先另存的 `.htm`，否則圖片會糊。

## 檔案結構

```
teaching-handbook/
├── SKILL.md                  ← Claude 讀的工作流定義（含 pptx 採坑紀錄）
├── README.md                 ← 你正在讀這份
└── scripts/
    ├── docx_converter.py     ← .docx 入口（含 Word 文字顏色保留）
    ├── md_converter.py       ← .md 入口
    ├── pptx_converter.py     ← .pptx 入口（含章節偵測、備註納入）
    ├── style_injector.py     ← 核心樣式 + 導航 + 複製按鈕引擎（上游、不動）
    └── _polish.py            ← 共用增強：目錄重建 + 搜尋框 + 圖片 lazy load
```

## 設計原則

- **只做 Stage 1（機械轉檔）**：內容理解與美化屬於下游，每份教材需求不同，寫死自動美化規則只會搞砸大多數檔案。
- **不動上游引擎**：`style_injector.py` 保持原樣，所有修補（例如中文標題被目錄漏掉的問題）都在 `_polish.py` 這層繞道解決。
- **不覆蓋既有檔案**：目標輸出檔已存在時，會先問過你再覆蓋。

## 已知限制

- pptx 的動畫、轉場、嵌入影片無法保留（HTML 的必然代價）
- pptx 不還原投影片版面，走「內容重排」路線；若你的簡報「圖才是主角」（如設計作品集），本 skill 不適合
- EMF / WMF / TIFF 格式的內嵌圖片會跳過（瀏覽器不支援）

## 授權

MIT（見 repo 根目錄 [LICENSE](../LICENSE)）。
