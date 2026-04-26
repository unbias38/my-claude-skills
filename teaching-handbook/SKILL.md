---
name: teaching-handbook
description: 將 Word (.docx)、Markdown (.md) 或 PowerPoint (.pptx) 教學講義轉成「側邊欄導航風格」的高畫質 HTML 網頁。使用時機：使用者說「上架教材」「上架講義」「教材轉網頁」「講義轉網頁」「轉成側邊欄導航風格」「轉成側邊欄網頁」「把這份 .docx/.md/.pptx 轉 HTML」，或提供 .docx/.md/.pptx 檔案並要求產出教學網頁時。產出包含固定側邊欄目錄、Scroll Spy、字體縮放、程式碼複製按鈕、自動保留 Word 文字顏色等互動功能。
---

# teaching-handbook

把 `.docx` / `.md` / `.pptx` 教學講義轉成側邊欄風格的教學網頁。

## 範圍邊界（重要）

本 skill **只負責機械轉檔**（Stage 1）：把原檔的文字、圖、結構**忠實搬到** HTML，不改寫、不美化、不重組。

**內容理解 / 改寫 / 美化（Stage 2）不在本 skill 範圍**。原因：每份簡報的領域、讀者、風格差異太大，強行寫死自動規則只會把大部分簡報搞砸。Stage 2 由使用者**在跑完轉檔後**另起對話、依當份簡報的具體需求請 Claude 處理。

未來的 Claude / 維護者：**不要試圖把美化規則寫進這個 skill**。詳情見 wiki notes `pptx-stage2-thoughts.md`（如果存在於使用者的 wiki）。

## 硬規則（不可違反）

1. **必須使用原始檔**（`.docx` / `.md` / `.pptx`），不接受先轉過的 `.htm` / `.html`（否則圖片會糊）。
2. **不要改寫 `scripts/` 下的 Python 邏輯**，直接呼叫即可。
3. **輸出檔名以輸入檔名為基底**（例如 `我的講義.docx` → `我的講義.html`），不要預設 `index.html`，避免覆蓋專案主頁。
4. 若目標輸出檔已存在，先向使用者確認再覆蓋。

## 依套件

第一次使用時執行一次即可：

```bash
uv add mammoth beautifulsoup4 markdown python-pptx
```

## 執行 SOP

### 步驟 1：確認輸入檔

- 使用者提供 `.docx` → 走 `docx_converter.py`
- 使用者提供 `.md` → 走 `md_converter.py`
- 使用者提供 `.pptx` → 走 `pptx_converter.py`
- 其他副檔名 → 停下來問使用者

### 步驟 2：確認參數（都有預設值，可略）

- `--title`：瀏覽器分頁標題（預設 `教學手冊`，md 預設 `Document`）
- `--sidebar-title`：側邊欄標題（docx 預設 `教學手冊導航`；pptx 預設 `投影片目錄`）
- `--no-notes`（僅 pptx）：不納入講者備註。**預設納入**。
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

PPTX：
```bash
uv run .claude/skills/teaching-handbook/scripts/pptx_converter.py "<input.pptx>" --title "<標題>" --sidebar-title "<側邊欄標題>"
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
    ├── pptx_converter.py         ← .pptx 入口
    ├── style_injector.py         ← 核心樣式 + 導航 + 複製按鈕引擎（上游、不動）
    └── _polish.py                ← 共用 helper：sidebar 搜尋框 + 圖片 lazy load
```

`style_injector.py` 自成一體，三個 converter 皆透過 `import style_injector` 呼叫它。
`_polish.py` 是 converter-side 的共用增強，與 `style_injector.py` 無關（後者保持原樣）。

## 三個 converter 共享的功能（透過 `_polish.py`）

下列功能無論 docx / md / pptx 都會生效：

- **圖片 `loading="lazy"`**：所有 `<img>` 自動帶 lazy 屬性，大檔載入快
- **Sidebar 重建**：清空 `style_injector.py` 生成的 nav，**用文件中所有 H1/H2/H3 重建**（按文件順序）。修復「`1. 章節`」「純中文標題」等不符合上游 regex 的 heading 被 sidebar 漏掉的問題
- **Sidebar 即時搜尋**：在重建後的 `#sidebar-nav` 上方注入 `<input id="th-search">`，輸入即時過濾目錄項

執行時機：converter 在 body 末端塞 `<script>`，於 `window.load` 後執行（此時 `style_injector.py` 已跑完，nav 已被它的 regex 邏輯填好）。

**為什麼放在 `_polish.py` 而非 `style_injector.py`**：硬規則 #2 不動上游 `style_injector.py`。converter-side 增強統一抽到 `_polish.py`。

### 為什麼是「清空重建」而非「補登」

上游 `style_injector.py` sidebar JS 用 regex `^(\d+(\.\d+)?)(\s|$) || ^[A-Z](\s|$)` 過濾 H2/H3。對下列常見情境**全部會誤殺**：

- markdown 標題「`1. 章節`」（digit + dot + space，regex 在 dot 後 require digit，失敗）
- 純中文 H2 / H3（既無數字也無大寫字母前綴）
- docx heading 用中文起頭

如果只「補登被漏的」，當 H1（永遠通過）和 H2（中文，被漏）交錯時，**順序會錯**（既有 H1 在前，後補的 H2 全部塞最後）。所以必須**清空 nav 整個重建**，按 `querySelectorAll('h1, h2, h3')` 的 document order 全列。

**ID 兼容性**：`style_injector.py` 給通過 regex 的 heading assign `id="section-N"`，scroll-spy IntersectionObserver 用這些 ID 對應 nav-link。重建邏輯**重用既有 id**（若 heading 已有 id 則保留），新加的 heading assign `th-section-N`。Observer 端比對 `href === '#' + id`，新舊 ID 都對得上 → scroll-spy 正常。

**順序保證**：document order 由 `querySelectorAll` 保證，重建後 sidebar 順序 = 文件順序，與單純 append 在 H1/H2/H3 交錯文件的順序錯亂問題隔絕。

**驗證**（2026-04-25）：
- `LSpe2.md`（1 H1 + 15 H2 + 7 H3 共 23 個 heading）：之前 sidebar 1 條，現在 23 條 ✅
- `防災宣導_SROI.docx`（10 H1）：10 條 → 10 條，無 regression ✅
- `金融大數據_v0.pptx`（10 H2 「01 - 標題」）：10 條 → 10 條，無 regression ✅

**不要這樣修**：~~改 `style_injector.py` 的 regex 一勞永逸~~ — 違反硬規則 #2。`_polish.py` 的清空重建是正確的繞道方式。

## pptx 轉換原則

- **每張投影片 = 一個 `<h2>` 章節**（側邊欄自動列出）
- **章節分隔投影片 → `<h1>`**（無內容、無 bullets、≤1 圖、或 layout 名稱含 `section header`／`title slide`／`chapter`）
- 投影片標題空白 → 用 `Slide N` 標示
- 投影片內文 → `<ul>`（短）或 `<p>`（長）
- 投影片內嵌圖片 → 以 base64 data URI 內嵌、`loading="lazy"`、80×80 縮圖橫排
- 講者備註 → **預設納入**（教學型 pptx 常把真正內容放在備註）；用 `--no-notes` 可關閉
- Sidebar 自動加搜尋框（輸入即時過濾目錄項）
- 不做投影片轉圖、不還原版面 —— 這是重排器，不是螢幕截圖器
- 動畫、轉場、嵌入影片會丟失（pptx → HTML 的必然代價）

## pptx 採坑紀錄（2026-04-25 實測 12 頁簡報）

下面是「為什麼 `pptx_converter.py` 看起來怪怪的」的解答。**未來除錯前先讀完，避免把對的東西改壞。**

### 1. 標題會被強制加 `01 - ` 前綴 — 這是故意的

**現象**：`pptx_converter.py` 的 `_render_slide_html` 會把 `投影片標題` 改成 `01 - 投影片標題` 才送進 HTML。

**原因**：上游 `style_injector.py` 第 430 行 sidebar nav 生成 JS 用 regex 過濾 h2/h3 標題：

```js
const match = text.match(/^(\d+(\.\d+)?)(\s|$)/) || text.match(/^[A-Z](\s|$)/);
if (match || header.tagName === 'H1') { /* add to sidebar */ }
```

只接受「數字 + 空白開頭」（如 `1 章` `1.1 節`）或「單一大寫字母 + 空白開頭」（如 `A 概論`）。**純中文標題全部被略過 → sidebar 變空白**。

**對策**：converter 端強制前綴 `f"{i:02d} - {title}"`（不動上游腳本，符合硬規則 #2）。

**不要這樣修**：~~改 `style_injector.py` 把 regex 放寬~~ — 違反硬規則 #2，且會影響 docx/md 流程。

### 2. 圖片預設縮成 80×80 縮圖橫排 — 這也是故意的

**現象**：投影片裡的圖片不是大圖內嵌，是 `<div class="pptx-thumbs">` 裡的 80×80 小方塊橫排。

**原因**：PowerPoint 教學簡報通常每張投影片埋 5–10 張 256×256 的**裝飾圖示**（流程箭頭、燈泡、章節標誌等）—— 不是「正文圖」。如果當大圖內嵌，每張佔約 300px 垂直空間，累積就一片空白海。實測 12 頁簡報共 32 張圖、所有都是 256×256，幾乎全是裝飾。

**對策**：用 flex + 80×80 縮圖排在標題下方，視覺上是一行 icons。

**不要這樣修**：~~改回每張一行的大圖呈現~~ — 會讓所有教學型 pptx 變成空白海。如果未來真遇到「圖才是主角」的 pptx（例如設計作品集），應該另開新 skill（如 `pptx-gallery`），別改這個。

### 3. 過濾純數字/單字母的短 bullet

**現象**：`_collect_body_paragraphs` 會跳過長度 ≤ 2 且為純數字或純字母的文字。

**原因**：PowerPoint 投影片底部常有頁碼（"2"、"3"）或裝飾編號，會被 python-pptx 當成一般文字框讀進來，污染 bullet 清單。

**不要這樣修**：~~移掉這個過濾~~ — 除非使用者明確表示需要保留頁碼。

---

### 教訓（給未來的我）

「LLM 按按鈕」型 skill 並非「加個檔就完事」。下游 `style_injector.py` 有**隱性假設**（標題要數字開頭、image 要適合大圖呈現），新加的 converter 必須學會這些假設才能對接。設計上的拗口都是有原因的，不要看到就想「優化」掉。

## pptx 大檔擴張（2026-04-25 加，因應 200+ 頁簡報）

為了讓大檔（50+ 頁）也好用，`pptx_converter.py` 內建三件事：

### 1. 章節偵測 → `<h1>`

`_is_chapter_slide()` 判斷規則：
- 投影片 layout 名稱含 `section header` / `section divider` / `title slide` / `chapter` → 是章節
- 或 投影片無 bullets、無 long paragraphs、且 ≤1 張圖 → 是章節

章節投影片用 `<h1>`（不加 `01 -` 前綴，因 H1 不需 regex 匹配）。`style_injector.py` 自動把 H1 列為 sidebar 頂層（level-1，含上方分隔線）—— **這是上游已經支援的功能，我們只是讓 pptx 能觸發它**。

**不要這樣修**：~~改用 H3 區分章節～~ — H3 受 regex 限制，且 sidebar 顯示太小看不出階層。

### 2. 圖片 `loading="lazy"`

每張 `<img>` 都有 `loading="lazy"` 屬性。瀏覽器只在 scroll 接近時才 decode 圖片。對 200 頁、500+ 圖的簡報，初次載入和記憶體使用都顯著降低。

### 3. Sidebar 即時搜尋框

converter 在 HTML body 末端注入一段 `<script>`，會在 `window.load` 後（等 `style_injector.py` 的 nav 生成完）：
- 在 `#sidebar-nav` 上方插入 `<input type="search" id="pptx-search">`
- 監聽 input 事件，即時過濾 `.nav-link` 的 `display`

**為什麼用 JS 注入而非靜態 HTML**：sidebar 容器是 `style_injector.py` 動態建構的、它的 nav-link 是另一段 JS 跑出來的。converter 沒辦法在編譯期把搜尋框塞進 sidebar，只能 runtime DOM 操作。retry-pattern（`setTimeout(init, 50)`）等 nav-link 出現才安裝，是必要的容錯。

**不要這樣修**：~~把搜尋框 HTML 寫死在 converter 輸出的 body 開頭~~ — 它會出現在主內容區而不是 sidebar，因為 style_injector 的 sidebar 是後加上去的獨立區塊。
