# Codelabs 風講義產生器 / codelab-handout

一個 Claude Code skill —— 把上課內容（口述大綱、docx、pdf、pptx、markdown）轉成 **Google Codelabs 風格**的單檔 HTML 講義。學生拿到檔案雙擊就能開：左側 sticky 目錄、每章節時間標記、明暗主題切換、三段字級、程式碼一鍵複製。

## 為什麼需要它

上課講義用 Word 發，學生要嘛沒裝 Office、要嘛排版跑掉。Google Codelabs 那種「一步一步帶著做、每步標時間」的網頁很適合教學，但自己刻一個很花時間。這個 skill 讓你只要準備好內容，Claude 就幫你產出一個**單一 HTML 檔**——不用架網站、不用網路，傳給學生直接開。

## 它做什麼

1. 依你的輸入類型準備 markdown：
   - 口述大綱／主題 → Claude 直接幫你寫成講義 markdown（口語化、像老師上課的口氣）
   - 現有 markdown → 直接進轉檔
   - docx / pdf / pptx → 先用 markitdown 等工具轉成 markdown 再整理
2. 跑 `scripts/build.py`，把 markdown 轉成 Codelabs 風 HTML
3. 給你對應作業系統的預覽指令，讓你馬上打開看

產出的網頁功能（全部內建在單一 HTML 裡）：

| 功能 | 說明 |
|------|------|
| 左側 sticky 目錄 | 每個 `##` 章節一個項目，做到哪跳到哪 |
| 章節時間標記 | `Duration: 5` 會顯示成「5 分鐘」，頂部顯示總章節數與總時長 |
| 明暗主題 | 一鍵切換 light / dark |
| 三段字級 | 小／中／大字體切換 |
| 三段版面寬度 | 窄（舒服閱讀）／中／滿屏 |
| 程式碼複製按鈕 | 每個程式碼區塊自動加複製鈕 |
| 上一步／下一步 | 每章節底部有導覽連結，頂部有閱讀進度條 |

## 怎麼觸發

**觸發詞是「codelab」**——一定要明講，例如：

```
把這份講義做成 codelab 樣子的網頁
幫我把 lecture.md 轉成 codelab 講義
做一份 Google Codelabs 風的講義
```

### 跟 teaching-handbook 的分工

| 你想要的 | 用哪個 skill |
|----------|--------------|
| Codelabs 的強意見視覺設計（Google 藍、時間標記、步驟式結構） | **codelab-handout**（本 skill） |
| 忠實保留原檔樣式（Word 顏色、原圖）的一般「轉網頁」 | `teaching-handbook` |

一句話：**要 Codelabs 那個味道才來這裡**；只說「幫我把 docx 轉成網頁」而沒提 codelab，不會觸發本 skill。

## 講義的 markdown 格式

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

章節設計原則：5–8 個 `##` 最理想、`Duration` 用整數分鐘、首章寫「今天要做什麼」、尾章寫「你帶走了什麼」。完整示範見 `references/example_input.md`。

## 安裝

### 1. 把 skill 放到 Claude Code 能找到的位置

```
~/.claude/skills/codelab-handout/            # 全域可用
# 或
<專案>/.claude/skills/codelab-handout/       # 只在該專案啟用
```

整個資料夾複製過去即可。詳細安裝指令（含 Windows）見 [repo 根目錄 README](../README.md#安裝)。

### 2. 安裝 Python 依賴 ⚙️

轉檔腳本需要 Python 3.10+ 和 `markdown` 套件：

```bash
pip install markdown
```

沒裝的話腳本會直接提示你安裝指令。另外，如果輸入是 docx / pdf / pptx，建議加裝 markitdown：

```bash
pip install "markitdown[all]"   # 選用：docx/pdf/pptx 轉 markdown 用
```

## 怎麼用（直接跑腳本）

不透過 Claude 也可以自己跑：

```bash
python3 <skill路徑>/scripts/build.py ~/Documents/講義.md -o ~/Documents/講義.html
```

（Windows 用 `python` 取代 `python3`）

> ⚠️ **成品不能輸出到 skill 資料夾內**——`build.py` 會主動擋下並報錯，避免產出物弄髒 repo。輸入跟輸出都放在你的專案目錄或 `~/Documents/` 就對了。

## 主題色客製

想換掉預設的 Google 藍？把 `assets/template.html` **複製到你的專案目錄**修改（不要直接改 skill 資料夾裡的檔案），再用 `--template` 指定：

```bash
python3 <skill路徑>/scripts/build.py 講義.md -o 講義.html --template 你的專案/my-template.html
```

要改的是範本開頭的 `:root` CSS 變數：

| 變數 | 意義 | 預設值 |
|------|------|--------|
| `--accent` | 主色 | Google 藍 `#1A73E8` |
| `--accent-bg` | 主色淺底 | `#e8f0fe` |
| `--sidebar-w` | 側邊欄寬度 | `260px` |

## 檔案結構

```
codelab-handout/
├── SKILL.md                       ← Claude 讀的工作流定義
├── README.md                      ← 你正在讀這份
├── scripts/
│   └── build.py                   ← markdown → Codelabs 風 HTML 轉檔腳本
├── assets/
│   └── template.html              ← 內建 HTML 範本（Codelabs 風格 CSS/JS 全在這）
└── references/
    └── example_input.md           ← 講義 markdown 完整示範（含語感範例）
```

## 設計原則

- **腳本苦力、LLM 判斷**：`build.py` 只管格式轉換，內容語感（口語化、比喻、章節安排）是 Claude 的工作，不在腳本裡寫死改寫規則。
- **產出物不進 skill 資料夾**：腳本內建守門，避免 HTML 成品汙染要分享到 GitHub 的 repo。
- **單檔即全部**：CSS / JS 全部內嵌，學生拿到一個 HTML 檔就能離線使用。

## 授權

MIT（見 repo 根目錄 [LICENSE](../LICENSE)）。
