"""
webshot.py —— 把做好的網頁「在指定的第幾秒」拍成圖片。

用途：
    1. 驗收：改了版面之後，拍幾張圖看看有沒有跑掉
    2. 回歸測試：拿改版前後的圖逐點比對像素，確認沒改壞
    3. 預覽：不想等整支影片渲染，先看幾格長什麼樣

執行方式：
    python3 scripts/webshot.py 做好的.html 5,20,85 輸出資料夾

原理：
    用瀏覽器的「無視窗模式」開網頁再截圖。但網頁一打開是停在第 0 秒的，
    所以我們會先做一份「除錯用的複本」，把時間軸改成由網址參數指定
    （?t=85 就代表跳到第 85 秒），順便拿掉音樂（省 5MB、開得快）
    以及淡入動畫（截圖會拍到動畫跑一半，看不準）。
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

CHROME_CANDIDATES = [
    # Windows（含從 WSL 借用）
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    "/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    # macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]

CHROME_HELP = """
找不到 Chrome 或 Edge，無法拍網頁截圖。
（只有「驗收 / 預覽」會用到，做網頁和影片本身不需要它。）

    Windows / macOS   安裝 Google Chrome 即可
    Linux             sudo apt install chromium-browser
或指定路徑：
    export MUSICDISK_CHROME=/path/to/chrome
"""


def find_chrome():
    p = os.environ.get("MUSICDISK_CHROME")
    if p and (os.path.exists(p) or shutil.which(p)):
        return p
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    sys.exit(CHROME_HELP)


def _is_windows_exe(chrome):
    """判斷我們是不是「在 WSL 裡呼叫 Windows 的瀏覽器」。

    這種情況下路徑要換算：Linux 的 /home/... 對 Windows 來說是另一種寫法，
    直接餵過去它會看不懂。
    """
    return chrome.lower().endswith(".exe") and chrome.startswith("/mnt/")


def _win_path(p):
    """把 Linux 路徑換算成 Windows 看得懂的寫法。"""
    return subprocess.run(["wslpath", "-w", os.path.abspath(p)],
                          capture_output=True, text=True).stdout.strip()


def make_debug_copy(html_path, out_path):
    """做一份除錯用複本：時間可指定、沒有音樂、沒有動畫。"""
    with open(html_path, encoding="utf-8") as f:
        s = f.read()
    s = re.sub(r'const MP3_B64   = "[^"]*";', 'const MP3_B64   = "";', s)
    s = s.replace("const t = audio.currentTime || 0;",
                  "const t = (parseFloat(new URLSearchParams(location.search).get('t'))||0);")
    s = s.replace("</style>",
                  "#loading{display:none!important}\n.line{transition:none!important}\n</style>")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(s)
    return out_path


def shoot(html_path, times, outdir, prefix="shot", size=None):
    """在每個指定秒數拍一張圖，回傳檔案路徑清單。"""
    chrome = find_chrome()
    os.makedirs(outdir, exist_ok=True)

    # 除錯複本要放在原網頁旁邊（Windows 瀏覽器才讀得到 WSL 的路徑）
    dbg = os.path.join(os.path.dirname(os.path.abspath(html_path)), "_webshot_tmp.html")
    make_debug_copy(html_path, dbg)

    # 沒指定尺寸就從網頁最前面的 CSS 變數抓畫布大小。
    # （注意：不能只讀檔案前面一小段去找 JS 裡的設定 —— 那一段全被
    #   3MB 的圖片編碼佔滿了，設定其實在很後面。CSS 變數在最前面，穩。）
    if size is None:
        with open(html_path, encoding="utf-8") as f:
            head = f.read(4000)
        mw = re.search(r"--canvas-w:\s*(\d+)px", head)
        mh = re.search(r"--canvas-h:\s*(\d+)px", head)
        if not (mw and mh):
            sys.exit("讀不到畫布尺寸，請用 size 參數指定")
        size = (int(mw.group(1)), int(mh.group(1)))

    win = _is_windows_exe(chrome)
    url_base = ("file:///" + _win_path(dbg).replace("\\", "/")) if win \
        else ("file://" + os.path.abspath(dbg))
    tmpdir = tempfile.mkdtemp(prefix="webshot_")

    out_files = []
    try:
        for t in times:
            name = f"{prefix}_{t:g}s.png"
            local = os.path.join(tmpdir, name)
            target = _win_path(local) if win else local
            subprocess.run(
                [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                 "--virtual-time-budget=12000",
                 f"--window-size={size[0]},{size[1]}",
                 f"--screenshot={target}", f"{url_base}?t={t}"],
                capture_output=True, timeout=120)
            if not os.path.exists(local):
                sys.exit(f"截圖失敗（t={t}）。瀏覽器：{chrome}")
            dest = os.path.join(outdir, name)
            shutil.copy(local, dest)
            out_files.append(dest)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        if os.path.exists(dbg):
            os.remove(dbg)
    return out_files


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit("用法：python3 webshot.py <做好的.html> <秒數,逗號分隔> <輸出資料夾>")
    ts = [float(x) for x in sys.argv[2].split(",")]
    for p in shoot(sys.argv[1], ts, sys.argv[3]):
        print("  已存", p)
