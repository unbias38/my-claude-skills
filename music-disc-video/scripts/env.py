"""
env.py —— 找出這台電腦上的「中文字型」和「ffmpeg」在哪裡。

為什麼需要這支？
    原本的程式把路徑寫死成 /mnt/c/Windows/Fonts/msjh.ttc，
    那只有「Windows + WSL」這種組合才對。換一台 Mac 或純 Linux 就直接壞掉。
    要能把 skill 分享給別人，就得改成「自己去找」。

    這就像寫食譜時不要寫「鹽在流理台左邊第三格」，
    而要寫「找到鹽罐」——每個人的廚房擺法不一樣。

找不到的時候會給出清楚的安裝指示，而不是丟一個看不懂的錯誤。
"""

import os
import platform
import shutil
import subprocess
import sys

# 允許使用者用環境變數強制指定，優先於自動偵測
ENV_FONT_REG  = "MUSICDISK_FONT_REGULAR"
ENV_FONT_BOLD = "MUSICDISK_FONT_BOLD"
ENV_FFMPEG    = "MUSICDISK_FFMPEG"


# =============================================================================
# 中文字型
# =============================================================================
# 依「優先順序」排列的候選字型。每一組是 (一般體, 粗體)。
# 粗體找不到時會退回用一般體，字會細一點但不會壞掉。
FONT_CANDIDATES = [
    # --- Windows（含 WSL 直接借用 Windows 的字型）---
    ("C:/Windows/Fonts/msjh.ttc",   "C:/Windows/Fonts/msjhbd.ttc"),    # 微軟正黑體（繁體）
    ("/mnt/c/Windows/Fonts/msjh.ttc", "/mnt/c/Windows/Fonts/msjhbd.ttc"),
    ("C:/Windows/Fonts/msyh.ttc",   "C:/Windows/Fonts/msyhbd.ttc"),    # 微軟雅黑（簡體）
    ("/mnt/c/Windows/Fonts/msyh.ttc", "/mnt/c/Windows/Fonts/msyhbd.ttc"),
    # --- macOS ---
    ("/System/Library/Fonts/PingFang.ttc", None),                      # 蘋方
    ("/System/Library/Fonts/STHeiti Medium.ttc", None),
    ("/Library/Fonts/Arial Unicode.ttf", None),
    # --- Linux ---
    ("/usr/share/fonts/opentype/noto/NotoSansCJKtc-Regular.otf",
     "/usr/share/fonts/opentype/noto/NotoSansCJKtc-Bold.otf"),
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
     "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    ("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
     "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"),
    ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", None),
]

FONT_HELP = """
找不到能顯示中文的字型。請照你的系統擇一處理：

  Windows      系統內建微軟正黑體，正常情況不會發生。
               若你在 WSL 裡執行，請確認 /mnt/c/Windows/Fonts 讀得到。
  macOS        系統內建蘋方字型，正常情況不會發生。
  Linux        請安裝思源黑體：
                   sudo apt install fonts-noto-cjk        （Ubuntu / Debian）
                   sudo dnf install google-noto-sans-cjk-fonts   （Fedora）

或者你也可以直接指定字型檔位置（換成你自己的路徑）：
    export MUSICDISK_FONT_REGULAR=/path/to/YourFont.ttf
    export MUSICDISK_FONT_BOLD=/path/to/YourFont-Bold.ttf
"""


def find_fonts():
    """回傳 (一般體路徑, 粗體路徑)。找不到就結束並印出安裝指示。"""
    reg = os.environ.get(ENV_FONT_REG)
    bold = os.environ.get(ENV_FONT_BOLD)
    if reg and os.path.exists(reg):
        return reg, (bold if bold and os.path.exists(bold) else reg)

    for r, b in FONT_CANDIDATES:
        if os.path.exists(r):
            return r, (b if b and os.path.exists(b) else r)

    # 最後手段：問系統的字型資料庫（Linux / macOS 有 fc-match）
    try:
        out = subprocess.run(["fc-match", "-f", "%{file}", ":lang=zh-tw"],
                             capture_output=True, timeout=5).stdout.decode().strip()
        if out and os.path.exists(out):
            return out, out
    except Exception:
        pass

    sys.exit(FONT_HELP)


def css_font_stack():
    """網頁版用的字型清單（瀏覽器會由左往右找，用第一個裝得到的）。"""
    return ('"Microsoft JhengHei","微軟正黑體","PingFang TC","Noto Sans TC",'
            '"Noto Sans CJK TC","Hiragino Sans GB","Microsoft YaHei",sans-serif')


# =============================================================================
# ffmpeg（用來解碼 mp3、以及把畫面編成 MP4）
# =============================================================================
FFMPEG_HELP = """
找不到 ffmpeg（處理影音用的工具）。最簡單的裝法是透過 Python 套件，
不需要系統管理員權限：

    pip install imageio-ffmpeg

或者用系統的套件管理員安裝：
    Windows   winget install ffmpeg      （或到 ffmpeg.org 下載後把資料夾加進 PATH）
    macOS     brew install ffmpeg
    Linux     sudo apt install ffmpeg

也可以直接指定執行檔位置：
    export MUSICDISK_FFMPEG=/path/to/ffmpeg
"""


def find_ffmpeg():
    """回傳 ffmpeg 執行檔的路徑。找不到就結束並印出安裝指示。"""
    p = os.environ.get(ENV_FFMPEG)
    if p and (os.path.exists(p) or shutil.which(p)):
        return p

    # 1) 系統有沒有裝
    p = shutil.which("ffmpeg")
    if p:
        return p

    # 2) Python 套件 imageio-ffmpeg 自帶一份（不用系統權限，最好裝）
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if p and os.path.exists(p):
            return p
    except Exception:
        pass

    sys.exit(FFMPEG_HELP)


def describe():
    """環境自我檢查：裝好之後先跑這支，確認該有的都有。

    執行：python3 scripts/env.py
    """
    ok = True
    print(f"作業系統    {platform.system()} {platform.release()}")
    print(f"Python      {platform.python_version()}")

    # --- 必要的 Python 套件 ---
    for mod, pipname, why in (("numpy", "numpy", "做數學運算"),
                              ("PIL", "pillow", "畫圖")):
        try:
            m = __import__(mod)
            v = getattr(m, "__version__", "?")
            print(f"{pipname:11s} {v}")
        except ImportError:
            ok = False
            print(f"{pipname:11s} ✗ 沒裝。請執行：pip install {pipname}   （{why}用的）")

    # --- 中文字型 ---
    try:
        reg, bold = find_fonts()
        print(f"中文字型    {reg}")
        print(f"  粗體      {bold}"
              f"{'  ← 找不到粗體，改用一般體（字會細一點但能用）' if bold == reg else ''}")
    except SystemExit as e:
        ok = False
        print("中文字型    ✗ 找不到" + str(e))

    # --- ffmpeg ---
    try:
        print(f"ffmpeg      {find_ffmpeg()}")
    except SystemExit as e:
        ok = False
        print("ffmpeg      ✗ 找不到" + str(e))

    # --- 瀏覽器（只有預覽／測試會用到，沒有也不影響出片）---
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import webshot
        print(f"瀏覽器      {webshot.find_chrome()}   （只有預覽和測試會用到）")
    except SystemExit:
        print("瀏覽器      － 沒有。做網頁和影片不受影響，只是不能自動截圖預覽。")

    print("\n" + ("環境沒問題，可以開始用了 ✅" if ok
                  else "上面有 ✗ 的項目要先處理 ❌"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(describe())
