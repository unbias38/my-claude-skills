# 凍結紀錄

## v1.0 ｜ 2026-10-03 ｜ 已鎖定

鎖了什麼（都在 `scripts/grab_video.py` 頂部）：

- `EVIDENCE_LAYERS`：brief.md 四層標題字串「證據層 1：元資料」「證據層 2：」「證據層 3：畫面」「證據層 4：社群」。報告模板與使用者既有素材包都依賴這四個字串。
- `NO_SPEECH_LINE`：無口說時寫進 transcript 與 brief 的標記句。下游靠它判斷「這支沒旁白」。
- `LANG_PREF` 與 `pick_subtitle` 的優先順序：人工字幕（中英日偏好）＞ 影片語言 -orig ＞ en-orig ＞ 其他 -orig ＞ 其他。改了會讓 YouTube 選到機翻字幕。
- `SUB_LANGS`：只抓中英日。改成萬用字元會被 YouTube 429。

定版依據：四支實跑素材包（work/facebook_4246300608944671、youtube_4fBjEnkgrTA、bilibili_BV1b9ad6xEnD、bilibili_BV1kSaR6gEwg）皆通過。

回歸守門：`tests/test_grab.py` 把以上四項寫成斷言。

要調整 → 另開 v1.1 或 v2.0，不動本版。
