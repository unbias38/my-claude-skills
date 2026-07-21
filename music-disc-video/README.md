# music-disc-video

把一首歌做成「旋轉碟片 + 跟著唱的歌詞」的視覺作品。

產出兩種東西：

- **單一 HTML 檔** —— 雙擊就播。圖片和音樂都內嵌在裡面，複製到隨身碟、傳給別人都不會破圖沒聲音。
- **MP4 影片** —— 可以直接上傳 YouTube、IG、抖音。

畫面由五層組成：滿版背景 → 旋轉的圓形碟片（中心是真的透明孔，不是蓋白圓）→ 方形封面 → 跟著唱的歌詞 → 音訊頻譜。

六套版面：橫式 16:9、直式 9:16、正方形 1:1，每種各有「有歌詞」和「純音樂」兩版。

---

## 安裝

需要 Python 3.9 以上，以及兩個套件：

```bash
pip install numpy pillow
```

還需要 **ffmpeg**（處理影音）。最簡單的裝法不需要系統管理員權限：

```bash
pip install imageio-ffmpeg
```

（或用系統的方式：Windows `winget install ffmpeg`、macOS `brew install ffmpeg`、Linux `sudo apt install ffmpeg`）

中文字型會自動尋找系統內建的（Windows 微軟正黑體 / macOS 蘋方 / Linux 思源黑體）。
Linux 如果沒有中文字型：`sudo apt install fonts-noto-cjk`

裝完先檢查：

```bash
python3 scripts/env.py
```

---

## 快速上手

**1. 建一個資料夾，放進三樣東西**

```
我的歌/
├── cover.png     封面圖（正方形最好）
├── song.mp3      音樂
└── lyrics.txt    歌詞
```

**2. 寫一個 `project.json` 放在同一個資料夾**

```json
{
  "title":    "歌名",
  "subtitle": "英文副標，不要就留空字串",
  "art":      "cover.png",
  "audio":    "song.mp3",
  "lyrics":   "lyrics.txt",
  "layout":   "16x9",
  "out_prefix": "musicdisk"
}
```

**3. 歌詞沒有時間軸的話，先對時**

最快的方式是請 Gemini 代勞：到 [Google AI Studio](https://aistudio.google.com/) 上傳音檔
（或直接貼 YouTube 連結），要它輸出 **SRT 格式**、**每句獨立一條**、**逐句對應不要用區間概括**。
存成 `.srt` 放回資料夾即可，標準 SRT 本來就讀得進來。完整 prompt 見 SKILL.md 步驟 2。
模型抓的時間點會有些微偏移，在第 5 步的網頁版聽一遍、手改幾句就好。

沒辦法用上述方法的話，就自己敲：

```bash
python3 scripts/timetap.py 我的歌
```

會產生「敲拍對時.html」。打開它，按空白鍵播放，之後**每唱到一句新歌詞就敲一下空白鍵**。
敲錯按 Backspace 退回、點清單任一句可以從那裡重來。標完按「匯出歌詞檔」，
把下載到的檔案放回資料夾，並把 `project.json` 的 `lyrics` 改成新檔名。

**4. 準備（自動調校 + 挑主色）**

```bash
python3 scripts/prepare.py 我的歌
```

它會自動決定字級和背景暗度，並產生 `_主色候選.png`（三個候選主色畫在真實背景上）。
挑好之後：

```bash
python3 scripts/prepare.py 我的歌 --accent 2
```

**5. 出網頁版來看**

```bash
python3 scripts/build_html.py 我的歌
```

雙擊產生出來的 `musicdisk.html` 就能播。

**6. 滿意之後出影片**

```bash
python3 scripts/render_video.py 我的歌 --start 60 --end 90   # 先出 30 秒試片
python3 scripts/render_video.py 我的歌                        # 全長
```

四分鐘的歌大約要跑 13 分鐘。

---

## 六套版面

`project.json` 的 `layout` 改成下面任一個：

| 值 | 尺寸 | 適合 |
|---|---|---|
| `16x9` | 1920×1080 | YouTube、電腦螢幕、上課投影 |
| `9x16` | 1080×1920 | IG Reels、抖音、YouTube Shorts |
| `1x1` | 1080×1080 | IG 貼文 |
| `16x9-solo` | 1920×1080 | 純音樂版（無歌詞，碟片放大置中） |
| `9x16-solo` | 1080×1920 | 純音樂直式 |
| `1x1-solo` | 1080×1080 | 純音樂方形 |

純音樂版不需要 `lyrics` 欄位。字級和遮罩會依各版面的空間自動重算。

---

## 想微調

在 `project.json` 加 `overrides`，重跑 build_html.py 或 render_video.py。
**網頁和影片讀同一份設定，改一次兩邊都會變。**

```json
"overrides": {
  "disc":       { "period": 16.0 },
  "colors":     { "accent": "#7FD4FF" },
  "lyrics":     { "size": 34, "zoom": 1.24 },
  "background": { "mask_base": 0.62, "mask_side": 0.5 },
  "video_progress": null
}
```

| 設定 | 意思 |
|---|---|
| `disc.period` | 碟片轉一圈幾秒。數字越大轉越慢（預設 12） |
| `colors.accent` | 主色。歌詞高亮、頻譜、播放鍵、進度條都會跟著變 |
| `lyrics.size` | 歌詞字級 |
| `lyrics.zoom` | 當前句放大幾倍（預設 1.18） |
| `background.mask_base` | 背景整體壓暗程度，0～1 |
| `background.mask_side` | 歌詞那一側再額外壓暗多少 |
| `video_progress` | 設成 `null` 就不畫影片底部那條進度線 |

---

## 歌詞格式

四種都吃，會自動判斷：

```
單行式    1 00:00:17,500 --> 00:00:22,000 過往早已變的平淡。

標準 SRT  1
          00:00:17,500 --> 00:00:22,000
          過往早已變的平淡。

LRC       [00:17.50]過往早已變的平淡。

純文字    過往早已變的平淡。          ← 沒有時間，用 timetap.py 對時
```

LRC 裡「只有時間、沒有文字」的那一行代表「上一句唱完了」，
會被轉成間奏（那段時間高亮會收掉）。

---

## 檔案結構

```
music-disc-video/
├── SKILL.md              給 AI 助理讀的工作流
├── README.md             這份
├── layouts/              六套版面設定（所有座標與顏色的唯一來源）
│   ├── 16x9.json           手寫的原始版面
│   ├── _generate.py        其餘五套由這支產生（要改請改它，別改產物）
│   └── ...
├── assets/
│   ├── template.html       網頁版模板
│   └── timetap.html        敲拍對時工具的模板
├── scripts/
│   ├── env.py              環境自我檢查（字型、ffmpeg 自動尋找）
│   ├── layout.py           讀版面設定、把比例換算成像素
│   ├── lyrics.py           歌詞解析（四種格式）
│   ├── spectrum.py         事先算好整首歌的頻譜
│   ├── autotune.py         自動決定字級、遮罩濃度、候選主色
│   ├── prepare.py          ① 準備
│   ├── timetap.py          產生敲拍對時網頁
│   ├── build_html.py       ② 出網頁
│   ├── render_video.py     ③ 出影片
│   └── webshot.py          把網頁在指定秒數拍成圖（預覽／測試用）
└── tests/
    ├── make_fixture.py     產生合成測試素材（無版權疑慮）
    ├── regress.py          回歸測試：六套版面逐像素比對
    └── fixture/ baseline/
```

---

## 開發者注意

第一次用要先建立自己的基準（repo 裡不附）：

```bash
python3 tests/regress.py --bless
```

之後改完程式一定要跑：

```bash
python3 tests/regress.py
```

它會用合成素材把六套版面各畫 12 格（網頁 6 格 + 影片 6 格），跟基準逐像素比對。
只有在「刻意改了外觀而且確認新的比較好」時才用 `--bless` 重新定基準。

基準之所以不附在 repo 裡：比對的是整張圖的 SHA，Pillow 版本、系統字型、
Chrome 版本任一不同就會有微小像素差異，別台機器的基準一定對不上。
基準要在自己的環境產生才有意義。

四條不能違背的設計原則、以及開發過程踩過的七個坑，都寫在 `SKILL.md` 最後兩節。
動手改之前請先讀那兩段 —— 每一條都是實際踩過才寫下來的。

---

## 參考來源

點子來自 bilibili UP 主 **hopiy_046** 的影片《用 codex 搞定音樂碟片動畫》。

本專案的實作、版面設計與程式碼皆為獨立撰寫。
