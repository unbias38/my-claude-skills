#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bootstrap：video-research 的相依自動安裝。
分顆粒 ensure_*，偵測缺哪個裝哪個、裝過秒跳過；對使用者透明，不要求手動 pip。
三樣相依：yt-dlp（下載）、ffmpeg（抽幀與分音軌）、faster-whisper（本機轉錄）。
每個 ensure 回傳「可用的執行檔路徑或 True」，裝不了回傳 None，由呼叫端走降級。
"""
from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

IS_WIN = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"

# winget 裝的工具不一定在目前 shell 的 PATH 裡，給備援路徑
_WINGET_PKGS = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Packages"


def _have_py(mod: str) -> bool:
    return importlib.util.find_spec(mod) is not None


def _pip(*pkgs: str) -> None:
    subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", "-q", *pkgs], check=True)


def _run_quiet(cmd: list[str]) -> bool:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=900).returncode == 0
    except Exception:
        return False


def _find_in_winget(glob: str, exe: str) -> str | None:
    if not IS_WIN or not _WINGET_PKGS.exists():
        return None
    for d in _WINGET_PKGS.glob(glob):
        for p in d.rglob(exe):
            return str(p)
    return None


# ---------- yt-dlp ----------

def ensure_ytdlp(log=print) -> str | None:
    """回傳 yt-dlp 可執行路徑。優先 PATH，其次 winget 路徑，最後 pip 安裝（跨平台最穩）。"""
    exe = shutil.which("yt-dlp")
    if exe:
        return exe
    exe = _find_in_winget("yt-dlp.yt-dlp_*", "yt-dlp.exe")
    if exe:
        return exe
    log("[bootstrap] 沒找到 yt-dlp，用 pip 安裝（約 30 秒）…")
    try:
        _pip("yt-dlp")
    except Exception as e:
        log(f"[bootstrap] pip 安裝 yt-dlp 失敗：{e}")
        return None
    exe = shutil.which("yt-dlp")
    if exe:
        return exe
    # pip 裝好但 Scripts 不在 PATH：用 python -m yt_dlp 當替身
    if _have_py("yt_dlp"):
        return f"{sys.executable} -m yt_dlp"
    return None


# ---------- ffmpeg ----------

def ensure_ffmpeg(log=print) -> str | None:
    """回傳 ffmpeg 可執行路徑。PATH → winget 路徑 → 系統套件管理器 → pip imageio-ffmpeg（內附二進位）。"""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    exe = _find_in_winget("*FFmpeg*", "ffmpeg.exe")
    if exe:
        return exe
    if IS_WIN and shutil.which("winget"):
        log("[bootstrap] 沒找到 ffmpeg，用 winget 安裝（約 1 到 3 分鐘）…")
        _run_quiet(["winget", "install", "--id", "Gyan.FFmpeg", "-e", "--accept-source-agreements",
                    "--accept-package-agreements", "--silent"])
        exe = _find_in_winget("*FFmpeg*", "ffmpeg.exe") or shutil.which("ffmpeg")
        if exe:
            return exe
    elif IS_MAC and shutil.which("brew"):
        log("[bootstrap] 沒找到 ffmpeg，用 brew 安裝…")
        _run_quiet(["brew", "install", "ffmpeg"])
        exe = shutil.which("ffmpeg")
        if exe:
            return exe
    log("[bootstrap] 改用 pip 的 imageio-ffmpeg（內附 ffmpeg 二進位）…")
    try:
        if not _have_py("imageio_ffmpeg"):
            _pip("imageio-ffmpeg")
        import imageio_ffmpeg  # type: ignore
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:
        log(f"[bootstrap] ffmpeg 全部安裝途徑失敗：{e}")
        return None


# ---------- faster-whisper ----------

def ensure_whisper(log=print) -> bool:
    """確保 faster-whisper 可 import。模型檔第一次用時才會下載（small 約 500MB）。"""
    if _have_py("faster_whisper"):
        return True
    log("[bootstrap] 沒找到 faster-whisper，用 pip 安裝（約 1 分鐘）…")
    try:
        _pip("faster-whisper")
    except Exception as e:
        log(f"[bootstrap] pip 安裝 faster-whisper 失敗：{e}")
        return False
    return _have_py("faster_whisper")


def doctor(log=print) -> dict:
    """環境健檢：回報三樣相依各自狀態，不安裝。"""
    status = {
        "yt-dlp": shutil.which("yt-dlp") or _find_in_winget("yt-dlp.yt-dlp_*", "yt-dlp.exe") or ("python -m yt_dlp" if _have_py("yt_dlp") else None),
        "ffmpeg": shutil.which("ffmpeg") or _find_in_winget("*FFmpeg*", "ffmpeg.exe"),
        "faster-whisper": _have_py("faster_whisper"),
    }
    for k, v in status.items():
        log(f"  {'OK ' if v else '缺 '} {k}: {v if v else '未安裝（跑主腳本時會自動裝）'}")
    return status


if __name__ == "__main__":
    doctor()
