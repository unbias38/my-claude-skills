# HackMD 語法參考 — 核心

> 本文件語法內容整理自 HackMD 官方功能介紹與教學筆記（https://hackmd.io/features-tw ），
> 僅作為語法參考重排，非官方文件。

## 目錄

- 1. YAML Metadata（前言區）
- 2. 標題
- 3. 標籤
- 4. 目錄
- 5. 文字格式
- 6. 文字顏色
- 7. Emoji
- 8. 引用區塊
- 9. 清單
- 10. 連結
- 11. 圖片
- 12. 表格
- 13. 程式碼
- 14. 分隔線
- 15. 註腳
- 16. 定義清單
- 17. 縮寫
- 18. 印刷字元自動轉換
- 19. 色塊強調（Admonition）
- 20. GitHub Alert 警示區塊
- 21. 收合區塊（Spoiler）
- 22. 嵌入外部內容
- 23. 嵌入 HackMD 筆記
- 24. 數學式（MathJax / LaTeX）
- 34. 不換行空白與 HTML 元素
- 35. 支援的圖表語言總覽
- 36. HackMD 專屬語法速查表

（§25–33 圖表語言細節、樂譜、書本／簡報模式見 syntax-advanced.md）

---

## 1. YAML Metadata（前言區）

在筆記最上方使用 YAML 格式設定筆記屬性：

```yaml
---
title: 筆記標題
description: 筆記描述
image: https://example.com/image.png
tags: 功能, 教學
robots: noindex, nofollow
lang: zh-tw
dir: ltr
breaks: true
GA: UA-XXXXXXXX-X
disqus: disqus_id
slideOptions:
  transition: slide
  theme: solarized
---
```

| 欄位 | 說明 |
| --- | --- |
| `title` | 筆記標題 |
| `description` | 筆記描述（連結預覽用） |
| `image` | 預設圖片（連結預覽用） |
| `tags` | 筆記標籤 |
| `robots` | 搜尋引擎機器人 meta |
| `lang` | 瀏覽器顯示語言 |
| `dir` | 文字方向（`ltr` / `rtl`） |
| `breaks` | 是否啟用換行 |
| `GA` | Google Analytics 追蹤碼 |
| `disqus` | Disqus 留言區 ID |
| `slideOptions` | 簡報模式選項 |

---

## 2. 標題

### `#` 語法

```markdown
# h1 標題
## h2 標題
### h3 標題
#### h4 標題
##### h5 標題
###### h6 標題
```

### 替代語法

```markdown
一級標題
===

二級標題
---
```

`===` 等同 `# 標題`，`---` 等同 `## 標題`。

---

## 3. 標籤

```markdown
###### tags: `功能` `酷` `更新`
```

---

## 4. 目錄

```markdown
[TOC]
```

自動產生目錄，支援到第三層標題。

---

## 5. 文字格式

### 粗體

```markdown
**粗體文字**
__粗體文字__
```

### 斜體

```markdown
*斜體文字*
_斜體文字_
```

### 刪除線

```markdown
~~刪除線文字~~
```

### 底線

```markdown
++底線文字++
```

### 螢光標記

```markdown
==標記文字==
```

### 上標

```markdown
19^th^
```

### 下標

```markdown
H~2~O
```

### 旁註標記（Ruby Annotation）

```markdown
{旁註標記|注音或拼音}
```

小字會顯示在主文字上方，常用於 CJK 注音標記。

---

## 6. 文字顏色

### 方法一：`<font>` 標籤

```html
<font color="#f00">紅色文字</font>
<font color="#1936C9">藍色文字</font>
<font color="#F7A004">橘色文字</font>
```

色碼支援三位（`#f00`）或六位（`#FF0000`）十六進位格式。

### 方法二：CSS class

```html
<style>
.blue { color: blue; }
.orange { color: orange; }
</style>

<span class="blue">藍色文字</span>
<span class="orange">橘色文字</span>
```

適合重複使用相同顏色時。

---

## 7. Emoji

### 代碼輸入

輸入 `:` 觸發自動搜尋：

```markdown
:smiley:
:point_right:
:bouquet:
:bell:
:tada:
:fire:
:mega:
:zap:
```

### 直接貼上

可從任何地方複製 emoji 直接貼入筆記。

> Emoji 搜尋工具：https://hackmdio.github.io/emoji-datasource-finder/

---

## 8. 引用區塊

### 基本引用

```markdown
> 這是引用區塊
>> 巢狀引用
>>> 更深層的巢狀引用
```

### 帶署名的引用

```markdown
> 這是我的留言
> [name=使用者名稱] [time=Sun, Jun 28, 2015 9:59 PM] [color=#907bf7]
```

| 標記 | 說明 |
| --- | --- |
| `[name=名稱]` | 署名 |
| `[time=時間]` | 時間戳記 |
| `[color=色碼]` | 引用區塊顏色 |

---

## 9. 清單

### 無序清單

```markdown
- 項目一
- 項目二
  - 子項目（縮排兩個空白）
    - 更深子項目
```

標記符號可用 `-`、`+` 或 `*`，不同符號會強制建立新的清單。

### 有序清單

```markdown
1. 第一項
2. 第二項
3. 第三項
```

也可以全部用 `1.`，會自動編號：

```markdown
1. foo
1. bar
1. baz
```

可從任意數字開始：

```markdown
57. foo
1. bar
```

### 待辦清單（Checkbox）

```markdown
- [ ] 未完成
- [x] 已完成
  - [ ] 巢狀未完成
  - [x] 巢狀已完成
```

---

## 10. 連結

### 基本連結

```markdown
[連結文字](https://hackmd.io)
```

### 帶標題的連結

```markdown
[連結文字](https://hackmd.io "滑鼠懸停顯示的標題")
```

### 自動連結

```markdown
https://hackmd.io
```

直接貼上網址會自動轉為可點擊連結。

### 參照式連結

```markdown
[連結標籤]: https://hackmd.io "HackMD"

點擊 [連結標籤] 前往。
```

---

## 11. 圖片

### 基本圖片

```markdown
![替代文字](https://example.com/image.png)
```

### 帶標題的圖片

```markdown
![替代文字](https://example.com/image.png "圖片標題")
```

### 參照式圖片

```markdown
![替代文字][img-id]

[img-id]: https://example.com/image.png "圖片標題"
```

### 調整圖片大小

**百分比縮放：**（`=` 前須有空格）

```markdown
![](https://example.com/image.png =50%x)
```

**固定像素寬度：**

```markdown
![](https://example.com/image.png =200x)
```

**固定寬高：**

```markdown
![](https://example.com/image.png =200x200)
```

### 圖片對齊（HTML）

**置中：**

```html
<div style="text-align: center;">
  <img src="https://example.com/image.png">
</div>
```

**靠右：**

```html
<div style="text-align: right;">
  <img src="https://example.com/image.png">
</div>
```

### 支援格式

`png`、`jpg`、`gif`、`bmp`、`tif`

---

## 12. 表格

### 基本表格

```markdown
| 欄位一 | 欄位二 | 欄位三 |
| ------ | ------ | ------ |
| 資料   | 資料   | 資料   |
| 資料   | 資料   | 資料   |
```

### 對齊方式

```markdown
| 靠左對齊 | 置中對齊 | 靠右對齊 |
|:-------- |:--------:| --------:|
| 左       | 中       | 右       |
```

| 語法 | 對齊 |
| --- | --- |
| `:------` | 靠左 |
| `:------:` | 置中 |
| `------:` | 靠右 |

### 表格快捷鍵

| 快捷鍵 | 功能 |
| --- | --- |
| <kbd>Shift</kbd>+<kbd>Ctrl</kbd>+<kbd>Left</kbd> | 靠左對齊 |
| <kbd>Shift</kbd>+<kbd>Ctrl</kbd>+<kbd>Right</kbd> | 靠右對齊 |
| <kbd>Shift</kbd>+<kbd>Ctrl</kbd>+<kbd>Up</kbd> | 置中對齊 |
| <kbd>Shift</kbd>+<kbd>Ctrl</kbd>+<kbd>Down</kbd> | 取消對齊 |

> 從 Excel 複製表格時，開啟「Smart Paste」功能即可自動轉換為 Markdown 表格。

---

## 13. 程式碼

### 行內程式碼

```markdown
行內 `console.log()` 程式碼
```

### 縮排程式碼區塊

    // 四個空格縮排
    line 1 of code
    line 2 of code

### 程式碼區塊（無高亮）

````markdown
```
function hello() {
  return "world";
}
```
````

### 指定語言（語法高亮）

````markdown
```javascript
var foo = function (bar) {
  return bar++;
};
```
````

### 顯示行號

語言名稱後加 `=`：

````markdown
```javascript=
var s = "JavaScript syntax highlighting";
alert(s);
```
````

### 指定起始行號

````markdown
```javascript=101
var s = "從第 101 行開始";
alert(s);
```
````

### 延續上一個區塊的行號

````markdown
```javascript=+
var s = "延續前一個區塊的行號";
alert(s);
```
````

### 自動換行

以 `!` 作為語言標識：

````markdown
```!
這是一段很長很長的文字，會自動換行而不會超出程式碼區塊的範圍。
```
````

---

## 14. 分隔線

三種寫法，效果相同：

```markdown
---
***
___
```

---

## 15. 註腳

### 基本註腳

```markdown
這裡有一個註腳[^1]。

[^1]: 這是註腳內容。
```

### 具名標籤註腳

```markdown
研究主題是圖書館裡哪種書最常被偷[^Schwitzgebel]。

[^Schwitzgebel]: Schwitzgebel 2009; Schwitzgebel and Rust 2014.
```

### 多段落註腳

```markdown
[^long]: 第一段落內容。

    第二段落須縮排四個空白。
```

### 行內註腳

```markdown
行內註腳^[直接在此寫註腳內容]
```

> **注意：** 註腳標籤不能包含空白，建議使用 `-`、`_` 或 CamelCase。自動依出現順序編號。

---

## 16. 定義清單

### 寬鬆格式

```markdown
名詞 1

:   定義 1

名詞 2

:   定義 2a

    定義 2 的第二段落
```

### 緊湊格式

```markdown
名詞 1
  ~ 定義 1

名詞 2
  ~ 定義 2a
  ~ 定義 2b
```

---

## 17. 縮寫

```markdown
這是 HTML 的範例。

*[HTML]: Hyper Text Markup Language
```

定義後，文中獨立出現的 `HTML` 會自動加上懸停提示。不影響嵌在其他文字中的情況（如 `xxxHTMLyyy`）。

---

## 18. 印刷字元自動轉換

```markdown
(c) (C)       → ©
(r) (R)       → ®
(tm) (TM)     → ™
(p) (P)       → §
+-            → ±
測試...       → 測試…（省略號）
--            → —（破折號）
"雙引號"      → 「智慧雙引號」
'單引號'      → 「智慧單引號」
```

---

## 19. 色塊強調（Admonition）

### 四種色塊

```markdown
:::success
成功 — 綠色色塊 :tada:
:::

:::info
資訊 — 藍色色塊 :mega:
:::

:::warning
警告 — 黃色色塊 :zap:
:::

:::danger
危險 — 紅色色塊 :fire:
:::
```

### 巢狀色塊

外層用四個冒號 `::::`，內層用三個 `:::`：

```markdown
::::info
外層藍色色塊
:::danger
內層紅色色塊
:::
外層繼續
::::
```

---

## 20. GitHub Alert 警示區塊

```markdown
> [!NOTE]備註
> 備註內容

> [!TIP]小提醒
> 提示內容

> [!IMPORTANT]重要
> 重要資訊

> [!WARNING]注意
> 警告內容

> [!CAUTION]危險
> 危險提醒
```

`[!TYPE]` 後可直接加上自訂標題文字。

---

## 21. 收合區塊（Spoiler）

### 預設標題

```markdown
:::spoiler
收合的內容，預設標題為「詳細資料」
:::
```

### 自訂標題

```markdown
:::spoiler 點擊展開
隱藏的內容
:::
```

### 預設展開

```markdown
:::spoiler {state="open"} 預設展開的標題
一開始就顯示的內容
:::
```

---

## 22. 嵌入外部內容

### YouTube

```markdown
{%youtube 影片ID %}
```

影片 ID 取自 URL 中 `v=` 後的字串。

### Vimeo

```markdown
{%vimeo 124148255 %}
```

### GitHub Gist

```markdown
{%gist schacon/4277 %}
```

### SlideShare

```markdown
{%slideshare briansolis/26-disruptive-technology-trends-2016-2018-56796196 %}
```

### Speakerdeck

```markdown
{%speakerdeck sugarenia/xxlcss-how-to-scale-css-and-keep-your-sanity %}
```

### PDF（須使用 https）

```markdown
{%pdf https://example.com/document.pdf %}
```

### Figma

```markdown
{%figma figma分享連結 %}
```

### iframe

```html
<iframe width="100%" height="500" src="https://hackmd.io/features" frameborder="0"></iframe>
```

> 在編輯器中輸入 `{}` 可觸發嵌入自動完成。

---

## 23. 嵌入 HackMD 筆記

### 以筆記 ID 嵌入

```markdown
{%hackmd 筆記ID %}
```

### 以使用者路徑嵌入

```markdown
{%hackmd @使用者/筆記permalink %}
```

### 嵌入主題樣式

```markdown
{%hackmd @themes/dracula %}
{%hackmd @themes/notion %}
{%hackmd @themes/orangeheart %}
{%hackmd @debbylin/theme-matcha %}
```

利用 `<style>` 標籤定義 CSS，搭配嵌入功能可為筆記套用自訂主題。

---

## 24. 數學式（MathJax / LaTeX）

### 行內數學式

```markdown
滿足 $\Gamma(n) = (n-1)!\quad\forall n\in\mathbb N$ 的 Gamma 函數
```

`$` 前後不能有空格。

### 區塊數學式

```markdown
$$
x = {-b \pm \sqrt{b^2-4ac} \over 2a}
$$
```

```markdown
$$
\Gamma(z) = \int_0^\infty t^{z-1}e^{-t}dt\,.
$$
```

---

## 34. 不換行空白與 HTML 元素

### 不換行空白

```html
&nbsp;
```

### 鍵盤按鍵樣式

```html
<kbd>Ctrl</kbd>+<kbd>C</kbd>
```

### Font Awesome 圖示

```html
<i class="fa fa-file-text"></i>
<i class="fa fa-camera"></i>
<i class="fa fa-github"></i>
<i class="fa fa-pencil fa-fw"></i>
```

---

## 35. 支援的圖表語言總覽

| 語言標記 | 圖表類型 |
| --- | --- |
| `$...$` | 行內數學式（MathJax） |
| `$$...$$` | 區塊數學式（MathJax） |
| ` ```sequence ` | UML 時序圖 |
| ` ```flow ` | 流程圖（flow.js） |
| ` ```graphviz ` | Graphviz 有向圖 |
| ` ```mermaid ` + `graph` | Mermaid 流程圖 |
| ` ```mermaid ` + `pie` | Mermaid 圓餅圖 |
| ` ```mermaid ` + `gantt` | Mermaid 甘特圖 |
| ` ```markmap ` | 心智圖 |
| ` ```vega ` | Vega-Lite 資料視覺化 |
| ` ```abc ` | ABC 樂譜 |

---

## 36. HackMD 專屬語法速查表

| 語法 | 功能 |
| --- | --- |
| `{%hackmd noteID %}` | 嵌入 HackMD 筆記 |
| `{%youtube ID %}` | 嵌入 YouTube |
| `{%vimeo ID %}` | 嵌入 Vimeo |
| `{%gist user/id %}` | 嵌入 Gist |
| `{%slideshare path %}` | 嵌入 SlideShare |
| `{%speakerdeck path %}` | 嵌入 Speakerdeck |
| `{%pdf URL %}` | 嵌入 PDF |
| `{%figma URL %}` | 嵌入 Figma |
| `[TOC]` | 自動目錄 |
| `:::success/info/warning/danger` | 色塊強調 |
| `:::spoiler` | 收合區塊 |
| `> [!NOTE/TIP/IMPORTANT/WARNING/CAUTION]` | GitHub Alert |
| `[name=X] [time=X] [color=X]` | 引用署名 |
| `==文字==` | 螢光標記 |
| `++文字++` | 底線 |
| `^文字^` | 上標 |
| `~文字~` | 下標 |
| `{旁註\|標記}` | Ruby 旁註 |
| `^[行內註腳]` | 行內註腳 |
| `![](url =寬x高)` | 圖片尺寸 |
| `` ```lang= `` | 程式碼行號 |
| `` ```lang=101 `` | 指定起始行號 |
| `` ```lang=+ `` | 延續行號 |
| `` ```! `` | 自動換行程式碼 |
| `---` / `----` | 簡報分頁 / 子頁 |
| `<!-- .slide: -->` | 簡報單頁屬性 |
