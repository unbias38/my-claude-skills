# 平台差異（實跑紀錄，2026-10-03）

| | YouTube（含 Shorts） | Bilibili | Facebook Reels |
|---|---|---|---|
| 不登入能拿到 | 標題、作者、觀看、讚、標籤、自動字幕、720p | 標題、作者、觀看、讚、留言數、標籤、720p | 標題、作者、觀看、文案、720p |
| 拿不到 | 留言需另抓 | 留言只給零星幾則 | 讚數、留言數、留言 |
| 字幕 | 幾乎都有自動字幕，原語言帶 -orig | 部分有 CC 或 AI 字幕，多數沒有 | 幾乎沒有 |
| 口說層走法 | 平台字幕，跳過 Whisper | 多數走 Whisper | 一定走 Whisper |
| 一支 1 到 4 分鐘影片耗時 | 約 15 秒 | 70 秒到 2 分半 | 約 60 秒 |
| 專屬坑 | 字幕語言用萬用字元會被 429；非 -orig 的字幕全是機翻 | 匿名留言限流；部分影片要 Cookie | 下載器偶爾壞要等 yt-dlp 更新；Reels 大字卡多，抽幀要密 |

## YouTube 字幕的規則

- 自動字幕檔名帶 `-orig` 的才是「真正聽到的語言」，其他全是機器翻譯，品質很差（serum 譯成「血清」）。
- YouTube 現在有自動配音，一支影片會冒出 21 種 `xx-orig`，腳本用元資料的 `language` 欄位挑，不靠檔名順序。
- 腳本只抓中英日。千萬別改成 `.*`，YouTube 會給 180 種翻譯然後回 429，而且字幕失敗會連影片一起放棄（腳本已加 `--ignore-errors`）。

## Bilibili

- 沒有獨立的「短影音」網址，直式短片就是普通 BV 號投稿，App 裡才會進豎屏流。腳本一律當普通影片處理，依長度自動決定抽幀密度。
- 動態裡的短影片網址是 t.bilibili.com 開頭，yt-dlp 的 BiliBiliDynamic 下載器支援。
- 部分影片要登入，yt-dlp 可吃 `--cookies-from-browser`。

## Facebook

- Reels 不登入抓得到影片與基本元資料，但社群訊號全空。
- 標題字串裡的「10K views · 413 reactions」是抓取當下的快照，可能和 view_count 欄位不一致，報告裡擇一並註明。
- 短影音常有大字卡而非口說，抽幀密度要比長片高（腳本對三分鐘內的影片自動用 2 秒）。

## 留言抓法（三平台通用）

```
yt-dlp --skip-download --write-comments -o "c.%(ext)s" <URL>
```

產出 `c.info.json`，裡面 `comments` 陣列有 author、text、like_count。未登入通常只給個位數幾則、讚數顯示 0，報告裡要說明不代表整體。要全貌加 `--cookies-from-browser chrome`，但要先徵得使用者同意。
