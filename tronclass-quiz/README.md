# TronClass 小考出題 / tronclass-quiz

一個 Claude Code skill：依講義與課本習題出題，產生可以直接匯入 TronClass（暢課）的考卷。

## 它做什麼

| 考試 | 產出 | 題型 |
|---|---|---|
| 各章小考、多章合考 | `.xls`（TronClass「導入題庫官方範本」格式）＋題目圖 PNG | 單選題 |
| 期中考 | 一份 `.docx`（TronClass Word 匯入測驗） | 選擇＋文字填空＋計算題組，公式用 LaTeX，全部自動批改 |

出題規則寫在 `SKILL.md`，重點是讓學生「考前只看講義就能準備」：

- 講義題只用講義上現成的隨堂小測驗與牛刀小試，不另外出新題
- 課本題的答案要能在講義內容頁查到
- 題目自足，不寫「圖 1.2」「公式 2.7」這種要翻書的字眼
- 考觀念，不考年代、人名、事件名稱
- 不出有爭議的題目，不用「以上皆是」這類組合選項
- 答案 A～D 平均、同一字母最多連續 2 題，配分是整數且剛好 100

## 怎麼觸發

```
出 CH2 小考
把這份講義的習題做成 TronClass 題庫
出期中考題，範圍 CH1～CH3
```

## 需要另外安裝

```bash
pip install python-pptx xlwt python-docx matplotlib openpyxl
```

題目圖的中文字型預設用 Windows 的 Microsoft JhengHei（`C:\Windows\Fonts\msjh.ttc`），其他系統請換成自己的中文字型。

## 檔案

```
tronclass-quiz/
├── SKILL.md                          出題規則與流程
├── scripts/
│   ├── extract_handout.py            從講義 PPTX 抽隨堂小測驗、牛刀小試
│   └── build_quiz.py                 題目 JSON → TronClass 匯入用 .xls（題目 JSON 格式寫在檔頭）
├── references/
│   ├── midterm-word.md               期中考的題目組成與 Word 匯入格式（實測結果）
│   └── example_build_word_import_test.py   Word 匯入測試卷產製腳本
└── assets/
    ├── 導入題庫官方範本.xls            TronClass Excel 匯入官方範本
    └── exam-word-import-zh-tw.docx   TronClass Word 匯入官方範本
```

`extract_handout.py` 是照作者自己的講義版型寫的（答案形狀名稱 `Ans{k}Letter`、「牛刀小試」標籤）；講義格式不同時，Claude 會改用 python-pptx 直接讀。

含真實考題的範例檔（題目 JSON、期中考產製腳本）沒有放進這個公開版本。

## 授權

MIT，見 repo 根目錄的 [LICENSE](../LICENSE)。`assets/` 內兩份範本是 TronClass 平台提供的匯入範本，原樣收錄。
