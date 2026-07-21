"""
render_video.py —— 把網頁版的畫面「一格一格畫出來」，串成 MP4 影片。

執行方式：
    python3 scripts/render_video.py <歌曲資料夾>                    # 整首
    python3 scripts/render_video.py <歌曲資料夾> --start 88 --end 118  # 試片
    python3 scripts/render_video.py <歌曲資料夾> --dump 20,85         # 只要幾張參考圖

核心觀念（跟網頁版同一條鐵律）：
    畫面上每一樣會動的東西 —— 碟片角度、歌詞捲動位置、哪句金色、頻譜柱高 ——
    都是「時間 t 的函數」。所以只要對每一格算出它的 t，套同一組公式，
    畫出來的結果就會跟網頁版一模一樣。
    也因此可以直接跳到第 3 分 12 秒單獨渲染那一格而不會出錯。

版面數字全部來自 layouts/*.json，跟網頁版讀同一份 —— 這是「兩邊不會不一致」的保證。

速度的關鍵：分辨「會動的」和「不會動的」
    背景、遮罩、方形封面、標題、碟片陰影從頭到尾長一樣，開始前畫「一次」就好。
    真正每格要重畫的只有：旋轉的碟片、歌詞、頻譜。
"""

import argparse
import math
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lyrics as lyrics_mod
from env import find_fonts
from layout import Layout, load_project, check_materials, resolve_out
from spectrum import compute_spectrum, DATA_FPS, FFMPEG

# 中文字型交給 env.py 自動尋找（Windows / Mac / Linux 都能跑）
FONT_REG, FONT_BOLD = find_fonts()


def round_half_up(x):
    """四捨五入 —— 但碰到剛好 .5 一律進位。

    為什麼不用 Python 內建的 round()？因為它用的是「銀行家捨入法」：
    碰到 .5 會往最接近的偶數靠，所以 round(190.5)=190、round(189.5)=190，兩個一樣！

    這在我們這裡會出事：一句歌詞剛唱到開頭時會「正好」落在歌詞欄正中央，
    算出來剛好是 .5。這時內部緩衝區大小差 1，文字就會上下跳 1 像素。
    改用「.5 一律進位」之後，位置只跟真正的座標有關，跟內部參數無關。
    """
    return math.floor(x + 0.5)


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# =============================================================================
# 小工具：把 CSS 的漸層翻譯成 numpy 運算
# =============================================================================
def grad_eval(t, stops):
    """給一堆位置 t（0~1 或像素值），依照 CSS 漸層的色標算出每點的 RGBA。

    stops 格式：[(位置, (r,g,b,a)), ...]，位置必須由小到大。
    CSS 漸層就是「兩個色標之間直線內插」，這裡就是在做這件事。
    """
    pos  = np.array([s[0] for s in stops], dtype=np.float32)
    cols = np.array([s[1] for s in stops], dtype=np.float32)
    tc   = np.clip(t, pos[0], pos[-1])
    idx  = np.clip(np.searchsorted(pos, tc, side="right") - 1, 0, len(pos) - 2)
    p0, p1 = pos[idx], pos[idx + 1]
    f = np.where(p1 > p0, (tc - p0) / np.maximum(p1 - p0, 1e-9), 0.0)[..., None]
    return cols[idx] * (1 - f) + cols[idx + 1] * f


def over(dst_rgb, src_rgba):
    """把一層半透明的東西疊到「不透明的底圖」上。"""
    a = src_rgba[..., 3:4] / 255.0
    return dst_rgb * (1 - a) + src_rgba[..., :3] * a


def stack(base, layer):
    """把 layer 疊在 base 上面（兩張都是半透明的 RGBA）。

    這裡有個很容易寫錯的陷阱：當「上下兩層都半透明」時，
    不能直接寫成 顏色 = 上層色×上層透明度 + 下層色×(1-上層透明度)。
    那樣算出來的是「已經乘過透明度」的顏色，可是後面又會再乘一次，
    等於乘了兩遍 —— 白色反光會變成灰色、金色光暈會變成暗斑。

    正確做法要再除以「合成後的總透明度」把它還原回來。
    """
    a_s = layer[..., 3:4] / 255.0
    a_b = base[..., 3:4] / 255.0
    a_o = a_s + a_b * (1 - a_s)
    rgb = (layer[..., :3] * a_s + base[..., :3] * a_b * (1 - a_s)) / np.maximum(a_o, 1e-6)
    out = np.empty_like(base)
    out[..., :3] = np.where(a_o > 1e-6, rgb, 0.0)
    out[..., 3:4] = a_o * 255.0
    return out


def tracked_text(draw, x, y, text, font, fill, spacing):
    """PIL 沒有 CSS 的 letter-spacing（字距），只好一個字一個字自己排。"""
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill, anchor="lm")
        x += font.getlength(ch) + spacing


# =============================================================================
# 畫面組裝器：吃一份版面設定 + 素材，吐出「給我 t 就還你一格」的函式
# =============================================================================
class Renderer:
    def __init__(self, lay, art_path, lines, spec, duration, title, subtitle):
        self.lay, self.cfg, self.px = lay, lay.cfg, lay.px
        self.lines, self.spec, self.duration = lines, spec, duration
        self.title, self.subtitle = title, subtitle
        self.W = self.cfg["canvas"]["w"]
        self.H = self.cfg["canvas"]["h"]
        self.accent = hex_rgb(self.cfg["colors"]["accent"])
        self.text_c = hex_rgb(self.cfg["colors"]["text"])
        self.art = Image.open(art_path).convert("RGB")
        self.has_lyrics = bool(self.cfg.get("has_lyrics", True)) and bool(lines)
        self._build_static()
        if self.has_lyrics:
            self._prerender_lines()
        self._prepare_spectrum()

    # ------------------------------------------------------------------
    def blend(self, frame, x, y, rgba):
        """把一張小的 RGBA 圖貼到大畫布的 (x,y)，超出邊界的自動裁掉。"""
        h, w = rgba.shape[:2]
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.W, x + w), min(self.H, y + h)
        if x0 >= x1 or y0 >= y1:
            return
        sub = rgba[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)
        a   = sub[..., 3:4] / 255.0
        reg = frame[y0:y1, x0:x1].astype(np.float32)
        frame[y0:y1, x0:x1] = (reg * (1 - a) + sub[..., :3] * a).astype(np.uint8)

    def _place(self, rgba, x, y):
        out = np.zeros((self.H, self.W, 4), dtype=np.float32)
        out[y:y + rgba.shape[0], x:x + rgba.shape[1]] = rgba
        return out

    # ------------------------------------------------------------------
    def _build_static(self):
        """把「從頭到尾都不會變」的東西先畫好。"""
        c, px, W, H = self.cfg, self.px, self.W, self.H
        bgc, cover, d, t = c["background"], c["cover"], c["disc"], c["title"]
        veil, veil_d = c["colors"]["veil"], c["colors"]["veil_deep"]

        # ---- 背景：封面圖放大鋪滿整個畫面（等同 CSS 的 background-size:cover）----
        s = max(W / self.art.width, H / self.art.height)
        sw, sh = int(round(self.art.width * s)), int(round(self.art.height * s))
        big = self.art.resize((sw, sh), Image.LANCZOS)
        ox = int(round(bgc["position_x"] * (W - sw)))
        oy = int(round(bgc["position_y"] * (H - sh)))
        bg = np.asarray(big.crop((-ox, -oy, -ox + W, -oy + H))).astype(np.float32)

        # ---- 遮罩：橢圓形整體壓暗 + 由左至右加深 ----
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        cx, cy = bgc["mask_radial_center"]
        rx, ry = bgc["mask_radial_size"]
        r = np.sqrt(((xx - cx * W) / (rx * W)) ** 2 + ((yy - cy * H) / (ry * H)) ** 2)
        base = bgc["mask_base"]
        bg = over(bg, grad_eval(r, [
            (0.0, (*veil, 255 * (base - bgc["mask_base_center_lift"]))),
            (bgc["mask_radial_mid_stop"], (*veil, 255 * base)),
            (1.0, (*veil_d, 255 * (base + bgc["mask_base_edge_add"]))),
        ]))
        s0, s1, s2 = bgc["mask_side_stops"]
        side = bgc["mask_side"]
        bg = over(bg, grad_eval(xx / W, [
            (0.0, (*veil, 0)), (s0, (*veil, 0)),
            (s1, (*veil, 255 * side * bgc["mask_side_mid_ratio"])),
            (s2, (*veil, 255 * side)), (1.0, (*veil, 255 * side)),
        ]))

        # ---- 碟片：封面裁成圓形，中央用遮罩挖出真正的透明孔 ----
        S = d["size"]
        disc_img = self.art.resize((S, S), Image.LANCZOS)
        dy, dx = np.mgrid[0:S, 0:S].astype(np.float32)
        rad = px["disc_radius"]
        rr = np.sqrt((dx - rad + 0.5) ** 2 + (dy - rad + 0.5) ** 2)
        pa = d["hub"]["plastic_alpha"]
        disc_a = grad_eval(rr, [
            (0.0, (0, 0, 0, 0)), (px["disc_hole"], (0, 0, 0, 0)),
            (px["disc_plastic_start"], (0, 0, 0, pa * 255)),
            (px["disc_plastic_end"],   (0, 0, 0, pa * 255)),
            (px["disc_data_start"],    (0, 0, 0, 255)), (rad, (0, 0, 0, 255)),
        ])[..., 3] * np.clip(rad - rr, 0, 1)          # 最外圈做 1px 抗鋸齒
        self.disc = Image.fromarray(
            np.dstack([np.asarray(disc_img).astype(np.float32), disc_a]).astype(np.uint8), "RGBA")

        # ---- 碟片陰影：碟片是圓的，轉起來輪廓不變，所以陰影只算一次 ----
        ds = d["shadow"]
        blurred = Image.fromarray(disc_a.astype(np.uint8), "L").filter(
            ImageFilter.GaussianBlur(ds["blur"] / 2))   # CSS 的模糊半徑 ≈ 高斯 sigma×2
        shadow = np.zeros((H, W, 4), dtype=np.float32)
        shadow[d["y"] + ds["dy"]:d["y"] + ds["dy"] + S, d["x"]:d["x"] + S, 3] = \
            np.asarray(blurred) * ds["alpha"]
        bg = over(bg, shadow)

        # ---- CD 反光層（固定不動，不隨碟片旋轉）----
        sh = d["sheen"]
        sheen = np.zeros((S, S, 4), dtype=np.float32)
        for key, radkey in (("hole_ring", "sheen_hole_ring"),
                            ("hub_ring", "sheen_hub_ring"),
                            ("edge_ring", "sheen_edge_ring")):
            stops = [(rv, (255, 255, 255, av * 255))
                     for rv, av in zip(px[radkey], sh[key]["a"])]
            sheen = stack(sheen, grad_eval(rr, stops))
        for st in sh["streaks"]:
            a = np.radians(st["angle"])
            L = abs(S * np.sin(a)) + abs(S * np.cos(a))
            tt = 0.5 + ((dx - rad) * np.sin(a) - (dy - rad) * np.cos(a)) / L
            stops = [(p, (*col, al * 255))
                     for p, col, al in zip(st["stops"], st["colors"], st["alpha"])]
            sheen = stack(sheen, grad_eval(tt, stops))
        hr = px["sheen_hole_ring"]
        sheen[..., 3] *= np.clip((rr - hr[0]) / max(hr[1] - hr[0], 1e-6), 0, 1) \
            * np.clip(rad - rr, 0, 1)
        self.sheen = Image.fromarray(np.clip(sheen, 0, 255).astype(np.uint8), "RGBA")

        # ---- 方形封面（含投影與 1px 內框）----
        # 圖層順序很重要：網頁版靠 HTML 先後順序決定「碟片在後、封面在前」，
        # 這裡得自己排 —— 封面不能烤進背景，否則每格畫碟片時會蓋到封面上面。
        CS, cs = cover["size"], cover["shadow"]
        box = Image.new("L", (CS, CS), 0)
        ImageDraw.Draw(box).rounded_rectangle([0, 0, CS - 1, CS - 1], cover["radius"], fill=255)
        cov = np.zeros((H, W, 4), dtype=np.float32)
        csh = Image.new("L", (W, H), 0)
        csh.paste(box, (cover["x"], cover["y"] + cs["dy"]))
        cov[..., 3] = np.asarray(csh.filter(
            ImageFilter.GaussianBlur(cs["blur"] / 2))).astype(np.float32) * cs["alpha"]

        cimg = self.art.resize((CS, CS), Image.LANCZOS).convert("RGBA")
        cimg.putalpha(box)
        ring = Image.new("RGBA", (CS, CS), (0, 0, 0, 0))
        ImageDraw.Draw(ring).rounded_rectangle(
            [0, 0, CS - 1, CS - 1], cover["radius"],
            outline=(255, 255, 255, int(cover["inner_ring_alpha"] * 255)), width=1)
        cimg.alpha_composite(ring)
        cov = stack(cov, self._place(np.asarray(cimg).astype(np.float32), cover["x"], cover["y"]))
        # 只留封面＋投影會用到的那一小塊，每格就不必疊整張畫布
        pad = int(round(cs["blur"] * 1.75))
        self.cover_box = (max(0, cover["x"] - pad), max(0, cover["y"] - pad),
                          min(W, cover["x"] + CS + pad),
                          min(H, cover["y"] + CS + cs["dy"] + pad))
        b = self.cover_box
        self.cover_layer = np.clip(cov[b[1]:b[3], b[0]:b[2]], 0, 255).astype(np.uint8)

        # ---- 標題、英文副標、小橫線 ----
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dr = ImageDraw.Draw(ov)
        # 標題可以靠左或置中。置中時要先量出整串（含字距）的寬度再回推起點，
        # 因為我們是一個字一個字排的，沒辦法交給排版引擎自動置中。
        def draw_title(text, font, y, tracking, fill):
            if not text:
                return
            w = sum(font.getlength(ch) + tracking for ch in text) - tracking
            x = t["x"] if t.get("align", "left") == "left" else (W - w) / 2
            tracked_text(dr, x, y, text, font, fill, tracking)

        draw_title(self.title, ImageFont.truetype(FONT_BOLD, t["size"]),
                   t["y"] + round(t["size"] * t["center_ratio"]),
                   t["size"] * t["tracking"], (255, 255, 255, 255))
        draw_title(self.subtitle, ImageFont.truetype(FONT_REG, t["sub_size"]),
                   t["sub_y"] + round(t["sub_size"] * t["sub_center_ratio"]),
                   t["sub_size"] * t["sub_tracking"],
                   (*self.text_c, int(t["sub_alpha"] * 255)))
        ova = np.asarray(ov).astype(np.float32)
        rule = grad_eval(np.linspace(0, 1, t["rule_w"], dtype=np.float32),
                         [(0, (*self.accent, 255)), (1, (*self.accent, 0))])
        rx = t["x"] if t.get("align", "left") == "left" else (W - t["rule_w"]) // 2
        ova[t["rule_y"]:t["rule_y"] + t["rule_h"], rx:rx + t["rule_w"]] = rule[None, :, :]
        bg = over(bg, ova)

        self.base = np.clip(bg, 0, 255).astype(np.uint8)

    # ------------------------------------------------------------------
    def _prerender_lines(self):
        """把每一句歌詞的三種樣子先畫好（金色／白色／間奏）。

        之後每一格只是「貼上去 + 調透明度」，比每格重新排字快非常多。
        """
        ly = self.cfg["lyrics"]
        self.pad = int(round(ly["size"] * 1.3))       # 四周留白，給光暈擴散用
        variants = {
            "normal": (ImageFont.truetype(FONT_REG, ly["size"]), self.text_c, 1.0, []),
            "gold":   (ImageFont.truetype(FONT_BOLD, self.px["size_gold"]), self.accent, 1.0,
                       [(0, ly["glow_blur"] / 2, self.accent, ly["glow_alpha"]),
                        (ly["shadow_dy"], ly["shadow_blur"] / 2, (0, 0, 0), ly["shadow_alpha"])]),
            "idle":   (ImageFont.truetype(FONT_REG, self.px["size_idle"]), self.text_c,
                       ly["idle_alpha"],
                       [(ly["shadow_dy"], ly["idle_shadow_blur"] / 2, (0, 0, 0),
                         ly["shadow_alpha"])]),
        }
        # CSS 的 transform:scale() 是以「整個區塊的中心」為支點放大的，
        # 而那個區塊底下含了 gap 的行距空白，支點因此比文字中心低 gap/2。
        # 放大時支點以上的東西會被往上推，推的距離 = (gap/2) × (放大倍率 - 1)。
        # Python 這邊是「換大一號的字、原地置中」，沒有這個效應，
        # 所以要手動補上，兩邊才會對齊。（不補的話影片會比網頁低約 2~3 像素）
        self.nudge = {
            "normal": 0.0,
            "gold":   -(ly["gap"] / 2) * (ly["zoom"] - 1),
            "idle":   -(ly["gap"] / 2) * (ly["idle_zoom"] - 1),
        }
        self.LINES = {}
        for key, (font, col, amul, shadows) in variants.items():
            imgs = []
            for L in self.lines:
                tw = int(font.getlength(L["text"])) + 1
                th = int(font.size * 1.6)
                im = Image.new("L", (tw + 2 * self.pad, th + 2 * self.pad), 0)
                ImageDraw.Draw(im).text((self.pad, self.pad + th / 2), L["text"],
                                        font=font, fill=255, anchor="lm")
                base = np.asarray(im).astype(np.float32)
                canvas = np.zeros(base.shape + (4,), dtype=np.float32)
                for dy, sig, scol, sa in shadows:                 # 先畫陰影／光暈
                    b = np.asarray(Image.fromarray(base.astype(np.uint8), "L")
                                   .filter(ImageFilter.GaussianBlur(sig))).astype(np.float32)
                    canvas = stack(canvas, np.dstack([
                        np.full(base.shape + (3,), scol, dtype=np.float32),
                        np.roll(b, dy, axis=0) * sa]))
                canvas = stack(canvas, np.dstack([                # 再畫文字本體
                    np.full(base.shape + (3,), col, dtype=np.float32), base * amul]))
                imgs.append(np.clip(canvas, 0, 255).astype(np.uint8))
            self.LINES[key] = imgs

        # 歌詞視窗上下邊緣淡出（CSS 的 mask-image: linear-gradient）
        h, f = ly["h"], ly["fade"]
        self.fade = np.clip(np.minimum(np.arange(h) / (f * h),
                                       (h - np.arange(h)) / (f * h)), 0, 1)[:, None]

    def _prepare_spectrum(self):
        sp = self.cfg["spectrum"]
        gy = np.linspace(1, 0, sp["h"], dtype=np.float32)     # 0 = 底部
        stops = [(g["at"], (g["rgba"][0], g["rgba"][1], g["rgba"][2], g["rgba"][3] * 255))
                 for g in sp["gradient"]]
        self.sgrad = np.repeat(grad_eval(gy, stops)[:, None, :], sp["w"], axis=1)

    # ------------------------------------------------------------------
    # 以下三個都是「時間 t 的函數」，跟網頁版 JS 的邏輯一字不差
    # ------------------------------------------------------------------
    def active_index(self, t):
        lo, hi, ans = 0, len(self.lines) - 1, -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if self.lines[mid]["start"] <= t:
                ans, lo = mid, mid + 1
            else:
                hi = mid - 1
        return ans

    def lyric_offset(self, t):
        """歌詞整列要往上位移多少像素。"""
        mid = self.cfg["lyrics"]["h"] / 2
        i = self.active_index(t)
        ctr = self.lay.lyric_centre
        if i < 0:
            return mid - ctr(0)
        if i >= len(self.lines) - 1:
            return mid - ctr(len(self.lines) - 1)
        a, b = self.lines[i]["start"], self.lines[i + 1]["start"]
        u = min(1.0, max(0.0, (t - a) / max(0.001, b - a)))
        u = u * u * (3 - 2 * u)                    # smoothstep：慢起步、慢收尾
        return (mid - ctr(i)) * (1 - u) + (mid - ctr(i + 1)) * u

    # ------------------------------------------------------------------
    def draw_frame(self, t):
        """整支程式的核心：給我一個時間 t，還你那一格完整的畫面。

        因為所有會動的東西都只依賴 t（不依賴「上一格畫了什麼」），
        這個函式可以單獨叫出任何一格，順序完全無所謂。
        """
        c, px, sp = self.cfg, self.px, self.cfg["spectrum"]
        ly = self.cfg.get("lyrics") or {}
        d = c["disc"]
        frame = self.base.copy()

        # ---- 旋轉的碟片 ----（負角度＝順時針，跟 CSS 的 rotate 一致）
        rot = self.disc.rotate(-(t / d["period"]) * 360.0, resample=Image.BICUBIC)
        rot.alpha_composite(self.sheen)
        self.blend(frame, d["x"], d["y"], np.asarray(rot))

        # ---- 方形封面：一定要在碟片「之後」畫，才會壓在碟片前面 ----
        self.blend(frame, self.cover_box[0], self.cover_box[1], self.cover_layer)

        # ---- 歌詞（無歌詞版面直接跳過）----
        if self.has_lyrics:
          box = np.zeros((ly["h"], ly["w"], 4), dtype=np.float32)
          i = self.active_index(t)
          idle = (i < 0) or (t > self.lines[i]["end"] + ly["idle_grace"])
          off = self.lyric_offset(t)
          for k in range(len(self.lines)):
              cy = self.lay.lyric_centre(k) + off      # 這句在視窗裡的垂直中心
              if cy < -80 or cy > ly["h"] + 80:
                  continue                             # 看不到的就別畫，省時間
              if k == i:
                  key, alpha = ("idle" if idle else "gold"), 1.0
              else:
                  dist = abs(k - i)
                  key = "normal"
                  alpha = max(ly["dim_floor"], ly["dim_start"] - (dist - 1) * ly["dim_step"])
              img = self.LINES[key][k].astype(np.float32)
              y0 = round_half_up(cy + self.nudge[key] - img.shape[0] / 2)
              x0 = -self.pad
              ys, ye = max(0, y0), min(ly["h"], y0 + img.shape[0])
              xs, xe = max(0, x0), min(ly["w"], x0 + img.shape[1])
              if ys >= ye or xs >= xe:
                  continue
              sub = img[ys - y0:ye - y0, xs - x0:xe - x0].copy()
              sub[..., 3] *= alpha
              box[ys:ye, xs:xe] = stack(box[ys:ye, xs:xe], sub)
          box[..., 3] *= self.fade
          self.blend(frame, ly["x"], ly["y"], box.astype(np.uint8))

        # ---- 頻譜 ----
        nf = self.spec.shape[0]
        fi = min(max(0.0, t * DATA_FPS), nf - 1.001)
        f0 = int(fi); w = fi - f0
        vals = self.spec[f0] * (1 - w) + self.spec[f0 + 1] * w
        m = Image.new("L", (sp["w"], sp["h"]), 0)
        md = ImageDraw.Draw(m)
        for k in range(sp["bars"]):
            bh = max(float(sp["min_height"]), vals[k] / 255.0 * sp["h"])
            x = k * px["bar_slot"] + (px["bar_slot"] - px["bar_width"]) / 2
            md.rounded_rectangle([x, sp["h"] - bh, x + px["bar_width"], sp["h"]],
                                 px["bar_width"] / 2, fill=255)
        srgba = self.sgrad.copy()
        srgba[..., 3] *= np.asarray(m).astype(np.float32) / 255.0
        self.blend(frame, sp["x"], sp["y"], srgba.astype(np.uint8))

        # ---- 底部細進度線（影片沒有互動控件，用一條線表示播放進度）----
        pr = c.get("video_progress")
        if pr:
            y0, y1 = pr["y"], pr["y"] + pr["h"]
            x0, x1 = pr["x"], pr["x"] + pr["w"]
            frame[y0:y1, x0:x1] = (frame[y0:y1, x0:x1] * (1 - pr["track_alpha"])
                                   + np.array(pr["track_rgb"]) * pr["track_alpha"]).astype(np.uint8)
            done = int(pr["w"] * min(1.0, max(0.0, t / self.duration)))
            if done > 0:
                frame[y0:y1, x0:x0 + done] = self.accent
        return frame


# =============================================================================
# 主流程
# =============================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", help="歌曲資料夾（裡面要有 project.json）")
    ap.add_argument("--start", type=float, default=0.0, help="從第幾秒開始")
    ap.add_argument("--end",   type=float, default=None, help="到第幾秒結束（不填=整首）")
    ap.add_argument("--fps",   type=int,   default=30)
    ap.add_argument("--out",   default=None)
    ap.add_argument("--dump",    default=None,
                    help="只輸出指定秒數的參考圖，用逗號分隔，例如 5,20,85")
    ap.add_argument("--dumpdir", default=".", help="參考圖存放資料夾")
    args = ap.parse_args()

    proj = load_project(args.project)
    lay  = Layout.load(proj["layout"], proj.get("overrides"))
    print(f"=== 影片渲染：{proj['title']}（版面 {proj['layout']}）===")

    # 純音樂版面可能根本沒有歌詞檔，不能硬讀
    has_lyrics = lay.cfg.get("has_lyrics", True)
    check_materials(proj, ["art", "audio"] + (["lyrics"] if has_lyrics else []))

    lines = []
    if has_lyrics:
        try:
            lines = lyrics_mod.parse(proj["lyrics"])
        except lyrics_mod.NoTimestamps as e:
            sys.exit(lyrics_mod.no_timestamps_help(proj["dir"], len(e.texts)))
    spec, duration = compute_spectrum(proj["audio"],
                                      n_bars=lay.cfg["spectrum"]["bars"], data_fps=DATA_FPS)

    print("[1/3] 預先畫好不會動的部分（背景、封面、標題、碟片陰影）…")
    print("[2/3] 預先畫好每一句歌詞的三種樣子（金色／白色／間奏）…")
    R = Renderer(lay, proj["art"], lines, spec, duration, proj["title"], proj.get("subtitle", ""))

    # ---- 只要幾張參考圖（不編影片）：用來比對改版前後畫面有沒有跑掉 ----
    if args.dump:
        os.makedirs(args.dumpdir, exist_ok=True)
        for ts in args.dump.split(","):
            tt = float(ts)
            p = os.path.join(args.dumpdir, f"ref_{tt:g}s.png")
            Image.fromarray(R.draw_frame(tt)).save(p)
            print("  已存參考圖", p)
        return

    t0, t1 = args.start, (args.end if args.end is not None else duration)
    n_frames = int(round((t1 - t0) * args.fps))
    out_path = resolve_out(
        args.out, proj["dir"],
        f"{proj['out_prefix']}{'' if args.end is None else '_test'}.mp4")
    print(f"範圍 {t0:.1f}s → {t1:.1f}s，{args.fps}fps，共 {n_frames} 格 → {os.path.basename(out_path)}")

    cmd = [FFMPEG, "-y", "-nostats", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{R.W}x{R.H}", "-r", str(args.fps), "-i", "-",
           "-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", proj["audio"],
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", "-shortest", out_path]

    # ⚠️ 踩過的坑，別改回管線（stderr=subprocess.PIPE）：
    #    作業系統的管線緩衝區只有 64KB。ffmpeg 一路把訊息寫進去，塞滿之後
    #    它就「寫不動、停在原地等人來讀」；而我們這邊正好在等 ffmpeg 結束
    #    → 兩邊互等，整個程式永遠凍結（術語叫 deadlock，死結）。
    #    導到「檔案」沒有容量上限，出錯時一樣讀得到內容。
    log_path = os.path.join(proj["dir"], "_ffmpeg_log.txt")
    log_f = open(log_path, "wb")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=log_f)

    def ffmpeg_log():
        log_f.flush()
        with open(log_path, encoding="utf-8", errors="ignore") as fh:
            return fh.read()[-2000:]

    print("[3/3] 開始逐格繪製並餵給 ffmpeg 編碼…")
    t_start = time.time()
    for f in range(n_frames):
        try:
            proc.stdin.write(R.draw_frame(t0 + f / args.fps).tobytes())
        except BrokenPipeError:
            print("\nffmpeg 中途結束了：", ffmpeg_log())
            sys.exit(1)
        if n_frames >= 20 and (f + 1) % max(1, n_frames // 10) == 0:
            el, pct = time.time() - t_start, (f + 1) / n_frames
            print(f"   {pct*100:5.1f}%  已跑 {el/60:.1f} 分，"
                  f"預估還要 {el/pct*(1-pct)/60:.1f} 分", flush=True)

    proc.stdin.close()
    proc.wait()
    log_f.close()
    if proc.returncode != 0:
        print("ffmpeg 錯誤：", ffmpeg_log())
        sys.exit(1)
    os.remove(log_path)
    print(f"完成！{out_path}（{os.path.getsize(out_path)/1e6:.1f} MB，"
          f"耗時 {(time.time()-t_start)/60:.1f} 分鐘）")
    return out_path


if __name__ == "__main__":
    main()
