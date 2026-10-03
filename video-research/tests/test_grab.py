#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回歸測試：video-research。執行：python tests/test_grab.py
不需重相依（不跑 yt-dlp、ffmpeg、Whisper）：純邏輯、凍結契約、自動安裝分支、驗證器守則。"""
import os
import subprocess
import sys
import tempfile
import types
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")
sys.path.insert(0, SCRIPTS)

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}")


import grab_video as g  # noqa: E402
import bootstrap  # noqa: E402

print("1) 凍結契約")
check("四層標題字串", g.EVIDENCE_LAYERS == ("證據層 1：元資料", "證據層 2：", "證據層 3：畫面", "證據層 4：社群"))
check("無口說標記句", g.NO_SPEECH_LINE.startswith("（Whisper 未偵測到任何口說"))
check("字幕語言不含萬用字元", ".*" not in g.SUB_LANGS and "zh-Hant" in g.SUB_LANGS)
check("LANG_PREF 繁中優先", g.LANG_PREF[0] == "zh-Hant")

print("2) 字幕優先順序（pick_subtitle）")
P = lambda n: Path(f"video.{n}.srt")  # noqa: E731
found = {k: P(k) for k in ["zh-Hant", "en-orig", "ja-orig", "en", "ja"]}
check("YouTube 英文影片：選 en-orig 不選機翻 zh-Hant",
      g.pick_subtitle(found, {"language": "en-US", "subtitles": {}}).name == "video.en-orig.srt")
check("有人工繁中字幕時優先人工",
      g.pick_subtitle(found, {"language": "en-US", "subtitles": {"zh-Hant": []}}).name == "video.zh-Hant.srt")
check("日文影片選 ja-orig",
      g.pick_subtitle(found, {"language": "ja", "subtitles": {}}).name == "video.ja-orig.srt")
check("沒有 -orig 時退回 LANG_PREF",
      g.pick_subtitle({"en": P("en"), "ja": P("ja")}, {"language": "fr", "subtitles": {}}).name == "video.en.srt")
check("沒有字幕回 None", g.pick_subtitle({}, {}) is None)

print("3) 純邏輯")
check("fmt_ts", g.fmt_ts(272) == "04:32" and g.fmt_ts(5.9) == "00:05")
check("safe_name 去除特殊字元", g.safe_name("BV1b9ad6xEnD/") == "BV1b9ad6xEnD_")
srt = "1\n00:00:00,000 --> 00:00:05,239\nUm, hi guys.\n\n2\n00:00:05,239 --> 00:00:07,259\n<i>>> [music]</i>\n\n3\n00:01:02,000 --> 00:01:04,000\nUm, hi guys.\n"
lines = g.srt_to_lines(srt)
check("srt_to_lines 時間碼與去標籤", lines[0] == "[00:00] Um, hi guys." and lines[1] == "[00:05] >> [music]")
check("srt_to_lines 連續重複行去重，不同時間重複保留", len(lines) == 3)
check("mark_no_speech 空→標記句", g.mark_no_speech([]) == [g.NO_SPEECH_LINE])
check("mark_no_speech 非空→原樣", g.mark_no_speech(["[00:00] hi"]) == ["[00:00] hi"])
check("tool_cmd 處理 python -m 替身", g.tool_cmd("C:/py/python.exe -m yt_dlp")[-2:] == ["-m", "yt_dlp"])
check("tool_cmd 單一執行檔", g.tool_cmd("C:/x/yt-dlp.exe") == ["C:/x/yt-dlp.exe"])

print("4) brief.md 產出（不需相依）")
with tempfile.TemporaryDirectory() as td:
    out = Path(td)
    info = {"title": "T", "duration": 70, "subtitles": {}, "automatic_captions": {"en-orig": [], "zh-Hant": []},
            "language": "en-US", "tags": ["a"], "description": "desc"}
    g.write_brief(out, info, [g.NO_SPEECH_LINE], "Whisper 轉錄（small）", 0, 2, 0, ["ffmpeg 不可用"])
    b = (out / "brief.md").read_text(encoding="utf-8")
    check("四層標題都在", all(h in b for h in g.EVIDENCE_LAYERS))
    check("降級提示寫進 brief", "降級提示" in b and "ffmpeg 不可用" in b)
    check("無畫面層時明講", "ffmpeg 不可用，本次沒有畫面層" in b)
    check("自動字幕摘要含影片語言", "影片語言：en-US" in b)

print("5) 自動安裝分支（攔截，不真的裝）")
calls = []
bootstrap._pip = lambda *p: calls.append(p)
bootstrap.subprocess = types.SimpleNamespace(run=lambda *a, **k: types.SimpleNamespace(returncode=1))
bootstrap.shutil = types.SimpleNamespace(which=lambda n: None)
bootstrap._find_in_winget = lambda *a: None
bootstrap._have_py = lambda m: True
calls.clear()
check("faster-whisper 已在→不重裝", bootstrap.ensure_whisper(log=lambda *a: None) is True and calls == [])
bootstrap._have_py = lambda m: False
calls.clear()
bootstrap.ensure_whisper(log=lambda *a: None)
check("faster-whisper 缺→嘗試 pip", calls == [("faster-whisper",)])
calls.clear()
bootstrap._have_py = lambda m: m == "yt_dlp"
r = bootstrap.ensure_ytdlp(log=lambda *a: None)
check("yt-dlp 缺→pip 後用 python -m 替身", calls == [("yt-dlp",)] and r and r.endswith("-m yt_dlp"))
bootstrap.shutil = types.SimpleNamespace(which=lambda n: "/usr/bin/yt-dlp" if n == "yt-dlp" else None)
calls.clear()
check("yt-dlp 在 PATH→不裝", bootstrap.ensure_ytdlp(log=lambda *a: None) == "/usr/bin/yt-dlp" and calls == [])

print("6) 驗證器守則（validate_punct）")
vp = os.path.join(SCRIPTS, "validate_punct.py")
with tempfile.TemporaryDirectory() as td:
    clean = Path(td) / "clean.md"
    clean.write_text("# 標題\n\n這是乾淨的句子，全形標點。數字 1,000 之間半形沒問題。\n", encoding="utf-8")
    dirty = Path(td) / "dirty.md"
    dirty.write_text("這是髒的句子,半形逗號夾中文。\n", encoding="utf-8")
    dash = Path(td) / "dash.md"
    dash.write_text("這裡有破折號——不行。\n", encoding="utf-8")
    rc = lambda p: subprocess.run([sys.executable, vp, str(p)], capture_output=True).returncode  # noqa: E731
    check("乾淨檔通過", rc(clean) == 0)
    check("半形標點夾中文被擋", rc(dirty) != 0)
    check("破折號被擋", rc(dash) != 0)
    skill_md = Path(HERE) / ".." / "SKILL.md"
    check("SKILL.md 本身通過驗證器", rc(skill_md) == 0)
    for ref in (Path(HERE) / ".." / "references").glob("*.md"):
        check(f"references/{ref.name} 通過驗證器", rc(ref) == 0)

print(f"\n結果：{PASS} passed, {FAIL} failed")
sys.exit(0 if FAIL == 0 else 1)
