"""
lyrics.py —— 讀入歌詞，統一轉成程式好用的格式。

輸出永遠長這樣（時間一律換算成「總秒數」的小數）：
    [{"start": 17.5, "end": 22.0, "text": "過往早已變的平淡。"}, ...]

為什麼統一換算成秒？
    因為程式裡要一直做「現在唱到哪一句」的比較，
    用「時:分:秒,毫秒」比大小很麻煩，換成單一個數字最直接。

支援四種來源，會自己判斷是哪一種：

  1. 單行式（本專案原本的格式）
         1 00:00:17,500 --> 00:00:22,000 過往早已變的平淡。

  2. 標準 SRT（字幕檔最常見的格式，一句佔三行）
         1
         00:00:17,500 --> 00:00:22,000
         過往早已變的平淡。

  3. LRC（音樂播放器的歌詞格式，網路上大部分歌詞是這種）
         [00:17.50]過往早已變的平淡。

  4. 純文字（沒有時間軸）—— 這種沒辦法直接用，
     會請你用「敲拍對時」工具跑一遍歌，把時間點標出來。
"""

import re
import statistics

# ---- 格式 1：一行寫完 ----
_ONE_LINE = re.compile(
    r"^\s*(\d+)\s+"
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*"
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})\s+(.*\S)\s*$"
)
# ---- 格式 2：標準 SRT 的時間行 ----
_SRT_TIME = re.compile(
    r"^\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*"
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})"
)
# ---- 格式 3：LRC 的時間標籤 [mm:ss.xx] ----
_LRC_TAG  = re.compile(r"\[(\d{1,3}):(\d{2})(?:[.:](\d{1,3}))?\]")
_LRC_META = re.compile(r"^\s*\[(ti|ar|al|by|offset|re|ve|length):(.*?)\]\s*$", re.I)

# 最後一句沒有結束時間時，預設讓它唱這麼久（秒）
_DEFAULT_TAIL = 4.0


class NoTimestamps(Exception):
    """歌詞檔裡完全沒有時間軸 —— 需要先用敲拍對時工具標時間。"""

    def __init__(self, texts):
        self.texts = texts          # 純文字的每一句，可以直接餵給對時工具
        super().__init__(f"這份歌詞沒有時間軸（共 {len(texts)} 句）")


def no_timestamps_help(project_dir, n_lines):
    """歌詞沒有時間軸時，該告訴使用者的完整說法。

    寫成一份共用的，是因為 prepare.py 和 build_html.py 都會遇到這個情況。
    以前兩邊各寫各的，結果 SKILL.md 改推「請 Gemini 轉字幕」之後，
    腳本還停在只叫人手動敲拍 —— 照著終端機做的人就白白多花好幾倍時間。
    同一件事只留一份，才不會再發生。
    """
    return "\n".join([
        f"這份歌詞沒有時間軸（共 {n_lines} 句），沒辦法直接用。有兩條路：",
        "",
        "  方法 A：請 Gemini 聽出時間軸（快，建議先試這個）",
        "    到 https://aistudio.google.com/ 上傳這首歌的音檔，",
        "    要它輸出 SRT 字幕，並要求「每句話獨立一條」、",
        "    「逐句對應，不要用時間區間概括一整段」。",
        "    輸出存成 .srt 或 .txt 放進資料夾（內容是標準 SRT 就讀得進來），",
        "    再把 project.json 的 lyrics 指到它就好。",
        "    完整的 prompt 寫在 SKILL.md 步驟 2。",
        "",
        "  方法 B：自己敲拍對時（方法 A 不能用時的備案）",
        f"    python3 scripts/timetap.py {project_dir}",
        "    會產生一個網頁，播歌時每唱到一句就敲一下空白鍵，標完匯出即可。",
        "    4 分鐘的歌大約花 5 分鐘，但時間點是自己敲的、最準。",
    ])


def _hms(h, m, s, frac):
    """時:分:秒,毫秒 → 總秒數。毫秒欄位可能是 1~3 位，要補齊。"""
    ms = int((frac or "0").ljust(3, "0")[:3])
    return int(h) * 3600 + int(m) * 60 + int(s) + ms / 1000.0


def _ms(m, s, frac):
    """LRC 的 分:秒.百分秒 → 總秒數。"""
    f = (frac or "0")
    val = int(f) / (10 ** len(f))
    return int(m) * 60 + int(s) + val


# =============================================================================
def _parse_one_line(raw):
    out = []
    for line in raw.splitlines():
        m = _ONE_LINE.match(line)
        if m:
            g = m.groups()
            out.append({"start": round(_hms(*g[1:5]), 3),
                        "end":   round(_hms(*g[5:9]), 3),
                        "text":  g[9].strip()})
    return out


def _join_text(parts):
    """SRT 一句可能拆成好幾行顯示，要合併成一句。

    中文之間不加空白，中英交界處才加 —— 直接用空白接會變成「你好 world」那種怪樣子。
    """
    out = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if out and not (_is_cjk(out[-1]) and _is_cjk(p[0])):
            out += " "
        out += p
    return out


def _is_cjk(ch):
    return "　" <= ch <= "鿿" or "＀" <= ch <= "￯"


def _parse_srt(raw):
    out, i = [], 0
    lines = raw.splitlines()
    while i < len(lines):
        m = _SRT_TIME.match(lines[i])
        if not m:
            i += 1
            continue
        g = m.groups()
        text, i = [], i + 1
        while i < len(lines) and lines[i].strip() and not _SRT_TIME.match(lines[i]):
            if not re.fullmatch(r"\s*\d+\s*", lines[i]):     # 跳過純數字的序號行
                text.append(lines[i])
            i += 1
        t = _join_text(text)
        if t:
            out.append({"start": round(_hms(*g[0:4]), 3),
                        "end":   round(_hms(*g[4:8]), 3), "text": t})
    return out


def _parse_lrc(raw):
    offset = 0.0
    marks = []            # (時間, 文字)；文字是空的代表「唱到這裡停」
    for line in raw.splitlines():
        meta = _LRC_META.match(line)
        if meta:
            if meta.group(1).lower() == "offset":
                try:
                    offset = int(meta.group(2).strip()) / 1000.0
                except ValueError:
                    pass
            continue
        tags = _LRC_TAG.findall(line)
        if not tags:
            continue
        text = _LRC_TAG.sub("", line)
        text = re.sub(r"<\d{1,3}:\d{2}[.:]\d{1,3}>", "", text).strip()   # 逐字版的標籤
        for t in tags:
            marks.append((_ms(*t) + offset, text))

    marks.sort(key=lambda x: x[0])
    out = []
    for i, (t, text) in enumerate(marks):
        if not text:                                   # 空白標記 = 前一句唱完了
            if out and out[-1]["end"] is None:
                out[-1]["end"] = round(t, 3)
            continue
        out.append({"start": round(t, 3), "end": None, "text": text})

    # LRC 沒有結束時間，用「下一句的開始」補上
    durs = []
    for i, L in enumerate(out):
        if L["end"] is None:
            nxt = next((m[0] for m in marks if m[0] > L["start"]), None)
            L["end"] = round(nxt, 3) if nxt else None
        if L["end"]:
            durs.append(L["end"] - L["start"])
    tail = statistics.median(durs) if durs else _DEFAULT_TAIL
    for L in out:
        if L["end"] is None:
            L["end"] = round(L["start"] + tail, 3)
    return out


# =============================================================================
def parse(path):
    """讀歌詞檔，自動判斷格式，回傳依時間排序的句子清單。"""
    with open(path, encoding="utf-8-sig") as f:
        raw = f.read()

    for fn in (_parse_one_line, _parse_srt, _parse_lrc):
        out = fn(raw)
        if out:
            out.sort(key=lambda x: x["start"])
            return out

    # 完全沒有時間軸 → 當成純文字，交給敲拍對時工具處理
    texts = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    if texts:
        raise NoTimestamps(texts)
    raise SystemExit(f"{path} 是空的。")


def sanity_check(lines, duration=None):
    """檢查歌詞有沒有明顯的問題，回傳警告訊息清單（空的代表沒問題）。"""
    warn = []
    for i, L in enumerate(lines):
        if L["end"] <= L["start"]:
            warn.append(f"第 {i+1} 句的結束時間不晚於開始時間：{L['text']}")
        if i + 1 < len(lines) and lines[i + 1]["start"] < L["start"]:
            warn.append(f"第 {i+2} 句的時間比前一句還早：{lines[i+1]['text']}")
    if duration and lines and lines[-1]["end"] > duration + 1:
        warn.append(f"最後一句結束在 {lines[-1]['end']:.1f}s，但歌只有 {duration:.1f}s")
    return warn


def to_one_line(lines):
    """把解析好的歌詞寫回「單行式」格式（敲拍對時工具會輸出這種）。"""
    def fmt(s):
        h, r = divmod(s, 3600)
        m, sec = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(sec):02d},{int(round((sec % 1) * 1000)):03d}"
    return "\n\n".join(
        f"{i+1} {fmt(L['start'])} --> {fmt(L['end'])} {L['text']}"
        for i, L in enumerate(lines))
