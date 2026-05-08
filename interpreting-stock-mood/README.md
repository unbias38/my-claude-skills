# 股票溝通師 / Interpreting Stock Mood

一個 Claude Code skill，把「跟寵物溝通」的玄學風格套到股票分析上 —— 從股價、新聞、PTT、Yahoo 留言、三大法人、Google Trends 萃取客觀特徵，結合技術指標（MA / RSI / MACD / 布林 / KD / 量價）解讀「股票心情」，產出擬人化獨白 + 情緒推測 + 行動建議 + 技術摘要 + 多維熱度交叉驗證五區塊報告，並可一鍵產出含 7 張圖的 DOCX 報告。

> ⚠️ **本工具僅為技術面解讀與娛樂用途，非投資建議。** 投資決策請自行評估並承擔風險。

## 靈感來源

本 skill 的「擬人化溝通師」風格靈感來自 **[寵物溝通師（GitHub: @ChatGPT3a01）](https://github.com/ChatGPT3a01)** 的作品 —— 用幽默的「我幫你問了 XXX 哦」「他偷偷跟我說……」這種對寵物的口吻替動物代言。本 skill 把同樣的敘事框架搬到股市，但**內核必須是真實技術指標**：每一句擬人化台詞背後都對應一個可驗證的數字（例如「他說飛得很高」=「60 日漲 X%」），不為了好笑捏造數字。

## 它做什麼

跟 Claude 講「我想問 XXX 股票最近怎樣」就會觸發。Claude 會自動：

1. 識別股票代號（台股 4 位數自動補 `.TW`、辨識 ETF / 槓桿 ETF / 美股）
2. 若提問模糊，反問 4 題（部位 / 方向 / 金額 / 時間範圍）
3. 跑 `analyze_stock.py` 抓股價、新聞、PTT 提及率、Yahoo 留言累計、TWSE 三大法人、Google Trends（容錯，任一失敗不中斷）
4. 計算技術指標 + 警訊（爆量長黑、跌破均線、量價背離、死叉、超買拉回）
5. 產出五區塊 Markdown 報告
6. 詢問是否要產出 DOCX 含圖完整版

### 提問範例

**1. 模糊提問 → 觸發反問**
> 「幫我問 2330 最近怎麼了？」

Claude 會先反問你的持倉 / 方向 / 金額 / 時間，再進行分析。適合純粹好奇、還沒決定要不要進場時。

**2. 清楚提問 → 直接分析**
> 「我手上 0050 持有 3 年，平均成本 130，現在想加碼，他現在是好時機嗎？」

包含持倉狀態（已持有）+ 成本 + 想做什麼（加碼）+ 標的，Claude 直接進入五區塊報告。

**3. 槓桿 ETF（容易踩坑）**
> 「我手上 00631L 正二抱了兩週漲了 8%，他還能再抱嗎？」

Claude 會用「正二, 正 2, 00631L」多別名抓 PTT 熱度，並提醒槓桿 ETF 的波動放大特性。**注意**：「正二」≠「0050」，這兩個 ETF 行為完全不同。

**4. 美股 / 黑話**
> 「解讀一下 NVDA 最近的心情」
> 「航海王最近狀況怎樣？」

NVDA 直接識別。「航海王」是黑話（指航運三雄 2603 / 2609 / 2615），Claude 會反問你問的是哪一隻而不是亂猜。其他常見黑話（護國神山、蘋概股、AI 概念、銅板股…）的辨識規則見 `references/aliases.md`。

## 安裝

### 1. 把 skill 放到 Claude Code 能找到的位置

```
~/.claude/skills/interpreting-stock-mood/    # 全域可用
# 或
<專案>/.claude/skills/interpreting-stock-mood/    # 只在該專案啟用
```

整個資料夾複製過去即可。Claude Code 會讀 `SKILL.md` 的 frontmatter 自動辨識觸發條件。

### 2. 安裝 Python 依賴

```bash
pip install yfinance matplotlib numpy python-docx
# 選用：抓 Google Trends 熱度
pip install pytrends
```

| 套件 | 必要？ | 用途 |
|---|---|---|
| `yfinance` | ✅ 必要 | 抓股價、新聞 |
| `matplotlib` | ✅ 必要 | 畫 7 張技術圖（DOCX 用） |
| `numpy` | ✅ 必要 | 技術指標計算 |
| `python-docx` | ✅ 必要 | 產出 DOCX 報告 |
| `pytrends` | 🟡 選用 | Google Trends 熱度（沒裝就跳過該維度） |

PTT / Yahoo / TWSE 三大法人都用 Python 標準庫的 `urllib.request`，**不需要額外裝套件**。

### 3. 字型（已內建，不用動）

`assets/fonts/NotoSansTC.ttf` 已附上，matplotlib 會自動載入用來顯示中文 —— 任何 OS 都不會出現方塊豆腐。授權 SIL OFL-1.1，詳見 `assets/fonts/NOTICE.md`。

## 怎麼用

### 方法 A：在 Claude Code 對話裡（推薦）

直接跟 Claude 講：

```
幫我問 2330 最近怎麼了
解讀一下 NVDA 的心情
我手上長榮 2603 平均成本 100，現在 130 該不該停利？
```

只要出現觸發詞（股票溝通、股票心情、股票翻譯、stock mood、解析股票…）或股票代號 + 提問，Claude 就會自動觸發本 skill。

### 方法 B：直接跑腳本（不透過 Claude）

從你想存報告的目錄底下跑，DOCX 會落在 `<cwd>/reports/`：

```bash
# 1. 抓特徵 + 技術指標（輸出 JSON 到 stdout）
python /path/to/skill/scripts/analyze_stock.py 2330 "台積電,台積,TSMC"

# 2. 產 DOCX 報告（含 7 張圖 + 模板自動生成的擬人化文字）
python /path/to/skill/scripts/generate_report.py 2330 "台積電,台積,TSMC"

# 3. 指定輸出目錄
python /path/to/skill/scripts/generate_report.py 2330 "台積電" --output-dir ~/Documents/stock-reports
```

第二個參數是**別名清單**（逗號分隔），用於 PTT 標題搜尋 —— 多傳幾個命中率高很多，避免誤判 PTT 冷清。常見台股 / 美股 / 槓桿 ETF 的建議別名見 `references/aliases.md`。

**輸出位置**：DOCX 預設輸出到 `<當前工作目錄>/reports/<symbol>_<YYYYMMDD>_<HHMM>.docx`，**不會寫進 skill 資料夾**（避免污染全域共享的 skill 目錄）。可用 `--output-dir` 覆蓋。

## 輸出範例（五區塊）

```
🎧 股票溝通分析報告

🎤 他想說什麼（先聽他講話）
> 我幫你問了 2330 哦 ──
> 他說他最近飛得很高，60 天漲了 27%，每天有點頭暈……
> 他偷偷跟我說，三大法人合計買超 540 萬股，他覺得有人挺他。
> 他要我提醒：「我現在站在 60 日高點區，追進來的請有準備」

📊 市場情緒推測（信心度：medium）
✅ 建議行動（扣回使用者持倉/時間）
🔬 技術與情緒特徵摘要（表格）
🌐 多維熱度交叉驗證（散戶 / 媒體 / 市場 / 法人四維對照）
📌 一句話總結
⚠️ 非投資建議
```

完整範例見 `examples/usage_example.md`。

## 檔案結構

```
interpreting-stock-mood/
├── SKILL.md                      ← Claude 讀的工作流定義
├── README.md                     ← 你正在讀這份
├── scripts/
│   ├── analyze_stock.py          ← 抓資料 + 算技術指標（輸出 JSON）
│   └── generate_report.py        ← 產 DOCX 報告
├── references/
│   ├── aliases.md                ← 台股/美股別名表 + 黑話辨識 + 槓桿 ETF
│   ├── asset_traits.md           ← 各類資產脾氣（權值股、ETF、航運…）
│   └── technical_emotion_mapping.md  ← 技術指標 → 市場情緒對應通則
├── examples/
│   └── usage_example.md          ← 完整使用範例
└── assets/fonts/
    ├── NotoSansTC.ttf            ← 圖表中文字型
    └── NOTICE.md                 ← 字型授權
```

## 設計原則

- **解讀，不是預測**：科學上沒有方法能準確預測股價。所有輸出都是「依據近期技術特徵推測」，禁止「他明天會漲」這種斷言。
- **透明 > 隱藏**：資料源失敗時標「⚠️ 抓取失敗（未納入判讀）」，**不會**把「沒抓到」當成「真的冷清」誤導使用者。
- **不給目標價 / 止損價**：只說「跌破 60 日線（1,952 元）值得留意」這種相對位置 + 對照價格的描述。
- **強制免責**：每次完整輸出都附「非投資建議」字樣。

## 已知限制

- 三大法人資料**僅台股**（TWSE 來源），美股無對應資料
- PTT 的關鍵字搜尋有命中率問題 —— 槓桿 ETF（00631L 等）特別需要傳「正二」「正 2」雙寫法
- pytrends 偶爾被 Google 擋（429 / 連線失敗），抓不到就完全省略該維度
- yfinance 對台股新聞覆蓋有限，多為英文標題

## 授權

- 程式碼：MIT（如需正式散布請自行加 LICENSE 檔）
- NotoSansTC 字型：SIL Open Font License 1.1（詳見 `assets/fonts/NOTICE.md`）
- 資料來源：yfinance / PTT / Yahoo 股市 / TWSE / Google Trends，請遵守各自的使用條款
