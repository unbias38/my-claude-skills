"""
autotune.py —— 看一眼封面和歌詞，自動決定該用多大的字、背景要壓多暗、主色挑什麼。

這支的每一條規則，都是把「當初手工調這首歌時的判斷」寫成程式：

  字級   當初是「算出最長那句放大後 717px、超出 700px 的欄寬」才改成 36px。
         → 現在自動算：塞不下就往下降，永遠不會被切掉。

  遮罩   當初是「看截圖覺得背景太亮」才把濃度從 .52 一路調到 .72。
         → 現在自動算：量封面在歌詞區的亮度，反推要壓多暗才讀得清楚。

  主色   當初是「看到封面是冷藍色，決定配金色」。
         → 現在自動抽 3 個搭得上的候選色讓人挑（全自動挑色常常很難看）。
"""

import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env import find_fonts   # noqa: E402


# =============================================================================
# 一、字級：保證每一句都塞得進歌詞欄
# =============================================================================
def fit_lyric_size(lines, cfg, visible_lines=None, margin=10, min_size=18):
    """算出「既塞得下、又剛好看得到 N 句」的字級。

    有兩個限制，取比較嚴格的那個：
      · 高度：歌詞欄要能同時看到大約 N 句，所以一句不能太高
      · 寬度：最長的那句「放大之後」不能超出欄寬
              （放大很容易被忘記 —— 當初就是栽在這裡，字被切掉右半邊）
    """
    ly = cfg["lyrics"]
    # 一次看到幾句：每套版面自己在設定檔裡定（直式空間高可以多幾句，正方形要少一點）
    if visible_lines is None:
        visible_lines = ly.get("visible_lines", 7)
    _, bold = find_fonts()

    # 限制一：高度
    per_line = ly["h"] / visible_lines
    by_height = int((per_line - ly["gap"]) / ly["line_height"])

    # 限制二：寬度（從高度上限往下試，找出第一個塞得下的）
    usable = ly["w"] - margin
    size = by_height
    while size > min_size:
        f = ImageFont.truetype(bold, size)
        widest = max(f.getlength(L["text"]) for L in lines)
        if widest * ly["zoom"] <= usable:
            break
        size -= 1

    f = ImageFont.truetype(bold, size)
    widest = max(f.getlength(L["text"]) for L in lines)
    longest = max(lines, key=lambda L: f.getlength(L["text"]))["text"]
    return {
        "size": size,
        "by_height": by_height,
        "widest_px": round(widest * ly["zoom"]),
        "usable_px": usable,
        "longest": longest,
    }


# =============================================================================
# 一點五、封面必須是正方形
# =============================================================================
def ensure_square(art_path):
    """封面不是正方形就置中裁成正方形，另存一份。

    回傳 (要用的圖檔路徑, 說明文字)；本來就是正方形時說明文字是 None。

    為什麼要擋：碟片和方形封面都是 `art.resize((S, S))` ——
    非正方形的圖會被「壓扁」而不是裁切，人會變矮胖、字會變窄，
    而且整個過程不會有任何錯誤訊息。這種「輸出是錯的但程式不報錯」
    最難發現（很可能一路做到影片才被看出來），所以在最前面處理掉。

    為什麼是自動裁而不是直接中止：中止會讓流程卡住，還要使用者自己去開修圖軟體。
    置中裁切八成的封面都可用，不行的話再換一張就好 —— 但一定要印警告，
    因為主體偏一邊的封面會被切掉。
    """
    art = Image.open(art_path)
    w, h = art.size
    if w == h:
        return art_path, None

    s = min(w, h)
    left, top = (w - s) // 2, (h - s) // 2
    stem = os.path.splitext(art_path)[0]
    out = f"{stem}_square.png"
    art.convert("RGB").crop((left, top, left + s, top + s)).save(out)
    return out, (
        f"封面不是正方形（{w}×{h}），已置中裁成 {s}×{s} 另存為 "
        f"{os.path.basename(out)}\n"
        f"    非正方形的圖會被壓扁變形，所以一定要先裁。\n"
        f"    ⚠ 置中裁切會切掉兩側 —— 主體如果偏一邊就會被切到，"
        f"請打開看一眼再往下走。\n"
        f"    不滿意就自己裁一張正方形的，改 project.json 的 art 即可。")


# =============================================================================
# 二、背景遮罩：從「讀得清楚」這個目標反推要壓多暗
# =============================================================================
def _cover_fit(art, w, h, pos_x=0.5, pos_y=0.46):
    """把圖放大鋪滿指定尺寸（跟 CSS 的 background-size:cover 一樣）。"""
    s = max(w / art.width, h / art.height)
    sw, sh = int(round(art.width * s)), int(round(art.height * s))
    big = art.resize((sw, sh), Image.LANCZOS)
    ox, oy = int(round(pos_x * (w - sw))), int(round(pos_y * (h - sh)))
    return big.crop((-ox, -oy, -ox + w, -oy + h))


def _luma(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def suggest_mask(art_path, cfg, title_text=None, target_lyrics=16, target_overall=44):
    """算出背景該壓多暗。

    做法不是憑感覺，而是設一個「可讀性目標」再反推：
      歌詞區裡最亮的那些地方（第 95 百分位），壓完之後要降到 target_lyrics 以下。
      這兩個目標值不是憑感覺訂的，是拿「使用者實際驗收通過」的那一版
      反推出來的 —— 照這組數字算，會重現當初手工調到滿意的濃淡。

    這張封面滿版都是手寫字和亮色紙張，所以會被壓得比較重；
    換一張素淨的深色封面，同一條規則就會自動壓得比較輕，保留更多原畫。
    """
    art = Image.open(art_path).convert("RGB")
    cv = cfg["canvas"]
    bgc = cfg["background"]
    bg = _cover_fit(art, cv["w"], cv["h"], bgc["position_x"], bgc["position_y"])
    a = np.asarray(bg).astype(np.float32)
    lum = _luma(a)

    # 先確定「畫面上到底有沒有字要讀」，再決定量哪一區。
    # 無歌詞版面沒有歌詞區，改看標題那一帶；標題也留空的話就完全沒有字，
    # 這時候再為了可讀性壓暗就是白壓 —— 封面會被壓黑一片卻沒換到任何好處。
    ly = cfg.get("lyrics")
    if ly:
        region = lum[ly["y"]:ly["y"] + ly["h"], ly["x"]:ly["x"] + ly["w"]]
        where = "歌詞區"
    elif str(title_text or "").strip():
        t = cfg["title"]
        y0 = max(0, t["y"] - 20)
        region = lum[y0:min(lum.shape[0], t["rule_y"] + 60), :]
        where = "標題那一帶"
    else:
        region, where = None, None

    p95_txt = None if region is None else float(np.percentile(region, 95))
    p90_all = float(np.percentile(lum, 90))

    def needed(bright, target):
        if bright <= target:
            return 0.0
        return float(np.clip(1 - target / bright, 0.0, 0.93))

    base = needed(p90_all, target_overall)
    total_txt = 0.0 if p95_txt is None else needed(p95_txt, target_lyrics)

    if ly:
        # 兩層遮罩是疊加的：總濃度 = 1-(1-base)(1-side)，反解出 side
        side = 0.0 if total_txt <= base else (total_txt - base) / (1 - base)
    else:
        # 側邊漸層是為了「右邊那一欄歌詞」而存在的。無歌詞版面沒有那一欄，
        # 再套上去只會平白把右半邊壓暗、吃掉封面右側的主體。
        # 標題的可讀性改用「整體壓暗」達成，這樣畫面才是對稱的。
        base, side = max(base, total_txt), 0.0

    return {
        "mask_base": round(float(np.clip(base, 0.30, 0.88)), 3),
        "mask_side": round(float(np.clip(side, 0.0, 0.88)), 3),
        "p90_all": round(p90_all, 1),
        "p95_text": None if p95_txt is None else round(p95_txt, 1),
        "text_where": where,
    }


# =============================================================================
# 三、主色：抽 3 個搭得上的候選色
# =============================================================================
def _rgb_to_hsv(a):
    """整批把 RGB 換算成 HSV（色相／飽和度／明度）。"""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-6
    idx = m & (mx == r)
    h[idx] = ((g - b)[idx] / d[idx]) % 6
    idx = m & (mx == g)
    h[idx] = ((b - r)[idx] / d[idx]) + 2
    idx = m & (mx == b)
    h[idx] = ((r - g)[idx] / d[idx]) + 4
    return h / 6.0, np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0), mx


def _hsv_to_hex(h, s, v):
    i = int(h * 6) % 6
    f = h * 6 - int(h * 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    rgb = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i]
    return "#%02X%02X%02X" % tuple(int(round(c * 255)) for c in rgb)


def accent_candidates(art_path):
    """回傳 3 個候選主色（附一句說明為什麼推薦它）。"""
    art = Image.open(art_path).convert("RGB").resize((180, 180), Image.LANCZOS)
    a = np.asarray(art).astype(np.float32) / 255.0
    h, s, v = _rgb_to_hsv(a)

    # 只讓「顏色明確」的像素參與投票 —— 灰灰暗暗的區域不代表這張圖的調性
    w = (s * v).ravel()
    hist, edges = np.histogram(h.ravel(), bins=36, range=(0, 1), weights=w)
    dom = (edges[int(np.argmax(hist))] + edges[int(np.argmax(hist)) + 1]) / 2

    gold = 45 / 360.0                            # 溫暖的金色，幾乎百搭
    comp = (dom + 0.5) % 1.0                     # 互補色 = 對比最強

    def apart(a, b):
        return min(abs(a - b), 1 - abs(a - b))

    # 互補色如果剛好落在金色附近，兩個候選就沒有選的意義了 —— 改用三分色拉開
    if apart(comp, gold) < 0.06:
        c1 = ((dom + 1 / 3.0) % 1.0, 0.74, 1.00,
              "三分色 — 跟封面拉開但不刺眼（互補色剛好跟金色太像，改用這個）")
    else:
        c1 = (comp, 0.74, 1.00, "互補色 — 跟封面主色調對比最強，最跳出來")

    cands = [
        c1,
        (gold, 0.71, 1.00, "經典金 — 暖色調，幾乎搭什麼封面都好看"),
        # 第三個刻意用「淡色」而不是同色系的濃色：
        # 濃色跟封面同調的話會糊在一起看不清楚，淡色又亮又和諧，最保險。
        (dom, 0.26, 1.00, "同調淡色 — 取自封面本身的色調、調亮調淡，和諧又清楚"),
    ]
    return [{"hex": _hsv_to_hex(hh, ss, vv), "why": why} for hh, ss, vv, why in cands]


def accent_preview(art_path, cfg, candidates, sample_text, out_path, mask=None):
    """把每個候選色實際畫在「壓暗後的背景」上，存成一張對照圖讓人挑。

    只給色塊很難判斷 —— 一定要放在真實背景上、用真實的字，才看得出好不好看。
    """
    mask = mask or {"mask_base": cfg["background"]["mask_base"],
                    "mask_side": cfg["background"]["mask_side"]}
    art = Image.open(art_path).convert("RGB")
    cv, ly = cfg["canvas"], cfg["lyrics"]
    bg = _cover_fit(art, cv["w"], cv["h"],
                    cfg["background"]["position_x"], cfg["background"]["position_y"])
    strip_h = int(ly["size"] * 2.6)
    total = 1 - (1 - mask["mask_base"]) * (1 - mask["mask_side"])

    _, bold = find_fonts()
    font = ImageFont.truetype(bold, int(round(ly["size"] * ly["zoom"])))
    rows = []
    for i, c in enumerate(candidates):
        y = ly["y"] + i * strip_h
        crop = np.asarray(bg.crop((ly["x"], y, ly["x"] + ly["w"], y + strip_h))).astype(np.float32)
        crop = crop * (1 - total) + np.array([5, 9, 14]) * total
        im = Image.fromarray(np.clip(crop, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        d.text((14, strip_h / 2), sample_text, font=font, anchor="lm", fill=c["hex"])
        d.text((ly["w"] - 12, strip_h / 2), f"{i+1}", font=font, anchor="rm",
               fill=(255, 255, 255, 90))
        rows.append(np.asarray(im))
    Image.fromarray(np.vstack(rows)).save(out_path)
    return out_path
