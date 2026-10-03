#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
grab_video.py：把一條影片連結變成 Claude 看得懂的「素材包」（前三步自動化）。

  1. yt-dlp 抓元資料、平台字幕（有的話）、720p 影片
  2. ffmpeg 抽關鍵幀、拼縮圖總表、分離 16kHz 單聲道音軌
  3. 沒字幕時用 faster-whisper 在本機轉錄
  產出 brief.md（交接單）+ transcript.txt + frames/ + sheets/，Claude 讀這些就能分析。

用法：
  python scripts/grab_video.py <URL>
  python scripts/grab_video.py <URL> --interval 2      抽幀間隔秒數（預設短片 2、長片 8）
  python scripts/grab_video.py <URL> --model medium    Whisper 模型 tiny/base/small/medium/large-v3
  python scripts/grab_video.py <URL> --lang zh         指定語言（預設自動偵測）
  python scripts/grab_video.py <URL> --cookies chrome  要登入才看得到的影片，從瀏覽器借 Cookie
  python scripts/grab_video.py <URL> --out work/xxx    自訂輸出資料夾
  python scripts/grab_video.py --doctor                只做環境健檢
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bootstrap  # noqa: E402  先補齊相依，再 import 重套件

# ---------- 凍結契約 FROZEN v1.0：brief.md 的四層標題與順序 ----------
# 下游（SKILL.md 的報告模板、使用者的既有 brief）都依賴這四個字串，改了就破壞相容。
EVIDENCE_LAYERS = ("證據層 1：元資料", "證據層 2：", "證據層 3：畫面", "證據層 4：社群")
NO_SPEECH_LINE = "（Whisper 未偵測到任何口說。全片可能只有配樂，資訊在畫面字卡上，請看 sheets/）"
LANG_PREF = ["zh-Hant", "zh-TW", "zh-Hans", "zh", "en", "ja"]
SUB_LANGS = "zh-Hant,zh-Hans,zh-TW,zh,en-orig,ja-orig,zh-orig,en,ja"  # 千萬別用 .*，YouTube 會給 180 種翻譯然後 429


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, encoding="utf-8", errors="replace", **kw)


def tool_cmd(exe: str) -> list[str]:
    """bootstrap 可能回傳 'python -m yt_dlp' 這種替身，拆成 list。"""
    return shlex.split(exe, posix=False) if " -m " in exe else [exe]


def safe_name(s: str) -> str:
    return re.sub(r"[^\w\-]+", "_", s)[:40]


def fmt_ts(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    return f"{m:02d}:{s:02d}"


# ---------- 1. yt-dlp ----------

def fetch_info(ytdlp: str, url: str, cookies: str | None) -> dict:
    cmd = [*tool_cmd(ytdlp), "--dump-json", "--no-warnings", url]
    if cookies:
        cmd += ["--cookies-from-browser", cookies]
    r = run(cmd, capture_output=True)
    if r.returncode != 0:
        sys.exit(f"[ERROR] yt-dlp 抓不到資訊：\n{r.stderr.strip()}\n"
                 "常見原因：連結打錯、影片要登入（試 --cookies chrome）、yt-dlp 太舊（pip install -U yt-dlp）")
    return json.loads(r.stdout)


def download(ytdlp: str, url: str, out: Path, cookies: str | None) -> Path:
    video = out / "video.mp4"
    if video.exists():
        print(f"[skip] 影片已存在：{video.name}")
        return video
    cmd = [
        *tool_cmd(ytdlp), "--no-warnings",
        "-f", "bv*[height<=720]+ba/b[height<=720]/b",
        "--merge-output-format", "mp4",
        "--write-subs", "--write-auto-subs", "--sub-langs", SUB_LANGS,
        "--sub-format", "srt/vtt/best", "--convert-subs", "srt",
        "--ignore-errors",  # 字幕抓失敗不要連影片一起放棄
        "-o", str(out / "video.%(ext)s"),
        url,
    ]
    if cookies:
        cmd += ["--cookies-from-browser", cookies]
    print("[*] 下載影片與字幕 …")
    r = run(cmd)
    if r.returncode != 0 or not video.exists():
        sys.exit("[ERROR] 影片下載失敗")
    return video


# ---------- 2. ffmpeg ----------

def extract_frames(ffmpeg: str, video: Path, out: Path, interval: float) -> int:
    frames = out / "frames"
    if frames.exists() and any(frames.glob("*.jpg")):
        return len(list(frames.glob("*.jpg")))
    frames.mkdir(exist_ok=True)
    print(f"[*] 每 {interval} 秒抽一張關鍵幀 …")
    run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
         "-vf", f"fps=1/{interval},scale=-2:720", "-q:v", "3", str(frames / "f_%03d.jpg")], check=True)
    return len(list(frames.glob("*.jpg")))


def contact_sheets(ffmpeg: str, video: Path, out: Path, every: float = 3, cols: int = 4, rows: int = 4) -> int:
    """每 every 秒一格、每張 cols×rows 格的縮圖總表，左上角印時間碼。長片或無口說的影片先看這個。"""
    sheets = out / "sheets"
    if sheets.exists() and any(sheets.glob("*.jpg")):
        return len(list(sheets.glob("*.jpg")))
    sheets.mkdir(exist_ok=True)
    print(f"[*] 每 {every} 秒一格拼縮圖總表（{cols}x{rows}）…")
    vf = (f"fps=1/{every},scale=480:-2,"
          f"drawtext=text='%{{pts\\:hms}}':x=8:y=8:fontsize=22:fontcolor=yellow:box=1:boxcolor=black@0.6,"
          f"tile={cols}x{rows}")
    r = run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
             "-vf", vf, "-q:v", "3", str(sheets / "s_%02d.jpg")])
    if r.returncode != 0:  # 有些 ffmpeg 版本沒有 drawtext（缺字型庫），退一步不印時間碼
        vf = f"fps=1/{every},scale=480:-2,tile={cols}x{rows}"
        run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
             "-vf", vf, "-q:v", "3", str(sheets / "s_%02d.jpg")], check=True)
    return len(list(sheets.glob("*.jpg")))


def extract_audio(ffmpeg: str, video: Path, out: Path) -> Path:
    audio = out / "audio.wav"
    if audio.exists():
        return audio
    print("[*] 分離音軌 …")
    run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
         "-vn", "-ac", "1", "-ar", "16000", str(audio)], check=True)
    return audio


# ---------- 3. 字幕 / 轉錄 ----------

def pick_subtitle(found: dict[str, Path], info: dict) -> Path | None:
    """挑最合用的字幕。
    1. 上傳者自己上的字幕（manual），依中英日偏好
    2. 影片語言的原語言自動字幕（檔名帶 -orig）。這才是真的聽到的話
    3. 英文 -orig，再其他 -orig
    4. 其他全是機器翻譯，品質很差，最後才用
    """
    if not found:
        return None
    manual = set((info.get("subtitles") or {}).keys())
    for lang in LANG_PREF:
        if lang in manual and lang in found:
            return found[lang]
    spoken = (info.get("language") or "").split("-")[0]
    for lang in [f"{spoken}-orig", "en-orig"] + [k for k in found if k.endswith("-orig")]:
        if lang in found:
            return found[lang]
    for lang in LANG_PREF:
        if lang in found:
            return found[lang]
    return next(iter(found.values()))


def existing_subtitle(out: Path, info: dict) -> Path | None:
    found = {p.name[len("video."):-len(".srt")]: p for p in out.glob("video.*.srt")}
    return pick_subtitle(found, info)


def srt_to_lines(text: str) -> list[str]:
    lines, last = [], None
    for block in re.split(r"\n\s*\n", text.strip()):
        rows = block.strip().splitlines()
        if len(rows) < 2:
            continue
        ts_row = rows[1] if "-->" in rows[1] else rows[0]
        m = re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->", ts_row)
        if not m:
            continue
        start = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3])
        body = " ".join(r for r in rows[1:] if "-->" not in r).strip()
        body = re.sub(r"<[^>]+>", "", body)
        if body and body != last:
            lines.append(f"[{fmt_ts(start)}] {body}")
            last = body
    return lines


def transcribe(audio: Path, model: str, lang: str | None, hint: str) -> list[str]:
    from faster_whisper import WhisperModel  # bootstrap.ensure_whisper 已先補齊
    print(f"[*] faster-whisper {model} 轉錄中（CPU，約需口說時長的一半）…")
    t = time.time()
    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, info = m.transcribe(str(audio), language=lang, beam_size=5, vad_filter=True,
                              initial_prompt=hint or None)
    lines = [f"[{fmt_ts(s.start)}] {s.text.strip()}" for s in segs if s.text.strip()]
    print(f"[OK] 轉錄完成，語言 {info.language}，{len(lines)} 段，{time.time() - t:.0f} 秒")
    return mark_no_speech(lines)


def mark_no_speech(lines: list[str]) -> list[str]:
    """Whisper 一句都沒聽到，多半是純配樂影片；明講，不假裝轉錄成功。"""
    if not lines:
        print("[!] Whisper 一句都沒聽到：這支影片很可能只有配樂、沒有口說。內容全在畫面上，請看 sheets/")
        return [NO_SPEECH_LINE]
    return lines


# ---------- 4. brief.md ----------

def write_brief(out: Path, info: dict, lines: list[str], source: str,
                n_frames: int, interval: float, n_sheets: int, degraded: list[str]) -> None:
    subs = ", ".join(sorted((info.get("subtitles") or {}).keys())) or "無"
    auto_keys = sorted((info.get("automatic_captions") or {}).keys())
    autosubs = (f"{len(auto_keys)} 種，影片語言：{info.get('language') or '未標示'}（非原語言者皆為機器翻譯，別用）"
                if auto_keys else "無")
    dur = info.get("duration") or 0
    rows = [
        ("來源", info.get("webpage_url") or info.get("original_url", "")),
        ("平台", info.get("extractor_key", "")),
        ("標題", info.get("title", "")),
        ("作者", info.get("uploader") or info.get("channel", "")),
        ("上傳日", info.get("upload_date", "")),
        ("長度", f"{fmt_ts(dur)}（{dur:.0f} 秒）"),
        ("觀看", info.get("view_count")),
        ("讚", info.get("like_count")),
        ("留言數", info.get("comment_count")),
        ("人工字幕", subs),
        ("自動字幕", autosubs),
        ("標籤", " ".join(f"#{t}" for t in (info.get("tags") or [])[:15])),
    ]
    md = ["# 影片分析素材包", "",
          "> 由 video-research 的 grab_video.py 自動產出。Claude 分析時請讀本檔＋ sheets/ 縮圖總表，",
          "> 產出報告請照「證據分層」：元資料／口說或字幕／畫面／社群。", ""]
    if degraded:
        md += ["> **降級提示**：" + "；".join(degraded), ""]
    md += [f"## {EVIDENCE_LAYERS[0]}", "", "| 欄位 | 值 |", "|------|-----|"]
    md += [f"| {k} | {v if v not in (None, '') else '（無）'} |" for k, v in rows]
    desc = (info.get("description") or "").strip()
    if desc:
        md += ["", "**文案：**", "", *(f"> {l}" for l in desc.splitlines())]
    md += ["", f"## {EVIDENCE_LAYERS[1]}{source}", ""]
    md += lines or ["（無）"]
    md += ["", f"## {EVIDENCE_LAYERS[2]}", ""]
    if n_frames:
        md += [f"frames/ 共 {n_frames} 張，每 {interval} 秒一張。第 N 張約在第 (N-1)×{interval} 秒。"]
    if n_sheets:
        md += [f"sheets/ 共 {n_sheets} 張縮圖總表（每格左上角有時間碼）。先看總表掌握全貌，",
               "再對需要讀小字的時間點抽單張全解析度幀：",
               "`ffmpeg -ss 00:01:24 -i video.mp4 -frames:v 1 -q:v 2 keyframes/k_000124.jpg`"]
    if not n_frames and not n_sheets:
        md += ["（ffmpeg 不可用，本次沒有畫面層）"]
    md += ["", f"## {EVIDENCE_LAYERS[3]}", "",
           "留言需另外抓取：`yt-dlp --skip-download --write-comments -o c.%(ext)s <URL>`，",
           "未登入通常只給零星幾則，要看全貌需 --cookies-from-browser。", ""]
    (out / "brief.md").write_text("\n".join(md), encoding="utf-8")


# ---------- main ----------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", nargs="?")
    ap.add_argument("--interval", type=float, default=None)
    ap.add_argument("--model", default="small")
    ap.add_argument("--lang", default=None)
    ap.add_argument("--cookies", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--force-whisper", action="store_true")
    ap.add_argument("--doctor", action="store_true", help="只做環境健檢")
    args = ap.parse_args()

    if args.doctor or not args.url:
        print("[環境健檢]")
        bootstrap.doctor()
        if not args.url:
            sys.exit(0 if args.doctor else "請給影片連結")
        return

    degraded: list[str] = []
    ytdlp = bootstrap.ensure_ytdlp()
    if not ytdlp:
        sys.exit("[ERROR] yt-dlp 裝不起來，沒有它什麼都抓不到。請手動：pip install yt-dlp")
    ffmpeg = bootstrap.ensure_ffmpeg()
    if not ffmpeg:
        degraded.append("ffmpeg 不可用，沒有畫面層與轉錄（只剩元資料與平台字幕）")

    print("[*] 抓取元資料 …")
    info = fetch_info(ytdlp, args.url, args.cookies)
    plat = safe_name(info.get("extractor_key", "video")).lower()
    out = Path(args.out) if args.out else Path("work") / f"{plat}_{safe_name(str(info.get('id', 'x')))}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    dur = float(info.get("duration") or 0)
    print(f"    {info.get('title', '')[:60]}  |  {fmt_ts(dur)}  |  → {out}")

    video = download(ytdlp, args.url, out, args.cookies)
    interval = args.interval or (2 if dur <= 180 else 8)
    n_frames = n_sheets = 0
    if ffmpeg:
        n_frames = extract_frames(ffmpeg, video, out, interval)
        n_sheets = contact_sheets(ffmpeg, video, out, every=3 if dur <= 600 else 10)

    srt = existing_subtitle(out, info)
    if srt and not args.force_whisper:
        print(f"[OK] 平台字幕：{srt.name}，略過 Whisper")
        lines = srt_to_lines(srt.read_text(encoding="utf-8", errors="replace"))
        source = f"平台字幕（{srt.name}）"
    elif ffmpeg and bootstrap.ensure_whisper():
        audio = extract_audio(ffmpeg, video, out)
        hint = " ".join(filter(None, [info.get("title", "")[:80], (info.get("description") or "")[:120]]))
        lines = transcribe(audio, args.model, args.lang, hint)
        source = f"Whisper 轉錄（{args.model}，專有名詞可能需校正）"
    else:
        degraded.append("無字幕且 Whisper 不可用，本次沒有口說層")
        lines, source = ["（無字幕，且本機轉錄不可用）"], "口說（不可用）"
    (out / "transcript.txt").write_text("\n".join(lines), encoding="utf-8")

    write_brief(out, info, lines, source, n_frames, interval, n_sheets, degraded)
    print(f"\n[DONE] 素材包：{out}")
    if degraded:
        print("[!] 降級：" + "；".join(degraded))
    print(f"       請 Claude 讀 {out / 'brief.md'} 與 sheets/ 來分析")


if __name__ == "__main__":
    main()
