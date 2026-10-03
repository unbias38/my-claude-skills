# video-research：本機影片研究員

丟一條影片連結（Bilibili、YouTube 含 Shorts、Facebook Reels、Instagram、TikTok，或任何 yt-dlp 支援的網站），在自己電腦上把影片變成「元資料＋逐字稿或字幕＋縮圖總表」素材包，再由 Claude 寫出標明證據來源的分析報告。

- 不用 API 金鑰、不上傳影片、零成本。
- 腳本只負責收集證據，分析交給對話裡的 Claude，長片不會撞 token 上限。
- 報告固定四層：元資料、口說、畫面、社群。每個判斷都指回某一層證據。

## 安裝

把本資料夾複製到 `~/.claude/skills/video-research/`，重啟 Claude Code 即可。

相依（yt-dlp、ffmpeg、faster-whisper）**第一次跑時自動安裝**，不用手動 pip。想先看環境狀態：

```
python ~/.claude/skills/video-research/scripts/grab_video.py --doctor
```

需要 Python 3.10 以上。第一次轉錄會下載 Whisper small 模型（約 500MB）。Windows 以外的系統，ffmpeg 會嘗試 brew 或 pip 內附版本，尚未實測。

## 用法

對 Claude 說：

- 「幫我看看這支在講什麼 https://…」
- 「這支業配在推什麼？可信嗎 https://…」
- 「整理這個 UP 主的重點 https://…」

Claude 會跑腳本、讀素材包、寫報告到 `work/<平台>_<影片ID>/report.md`，對話裡只給一句話結論和重點。

手動跑腳本：

```
python ~/.claude/skills/video-research/scripts/grab_video.py <URL>
python ~/.claude/skills/video-research/scripts/grab_video.py <URL> --cookies chrome   # 要登入的影片
python ~/.claude/skills/video-research/scripts/grab_video.py <URL> --model medium     # 專有名詞多
```

## 平台差異（實測）

| | YouTube | Bilibili | Facebook Reels |
|---|---|---|---|
| 字幕 | 有原語言自動字幕，跳過 Whisper | 多數無，走 Whisper | 無，走 Whisper |
| 不登入拿到 | 觀看、讚、標籤 | 觀看、讚、留言數 | 觀看、文案 |
| 1 到 4 分鐘影片耗時 | 約 15 秒 | 1 到 2.5 分鐘 | 約 1 分鐘 |

純 CPU 跑 Whisper small，約需口說時長的一半。

## 能力邊界

- Claude 聽不到聲音，只能靠轉錄文字；語氣、音樂風格不在範圍。
- 畫面與聲音的毫秒級同步做不到，要這種精度請切片段交給原生影片模型。
- 要登入的影片與完整留言，需使用者明示後才借用瀏覽器 Cookie。
- 不驗證影片宣稱，不確定一律標「（需查證）」。

缺相依時逐級降級（沒 Whisper 只出字幕加截圖，沒 ffmpeg 只出元資料），每一級都在交接單上明講。

## 測試

```
python tests/test_grab.py
```

31 條回歸測試，不需真的下載影片。凍結項見 `FROZEN.md`。
