"""
layout.py —— 讀取版面設定檔，並算出所有「衍生數值」。

這支是整個 skill 的樞紐。它做三件事：

  1. 讀 layouts/xxx.json（共用版面設定）
  2. 套上這首歌自己的微調（project.json 裡的 overrides）
  3. 把「比例」換算成「實際像素」

第 3 點很重要。設定檔裡碟片中心孔寫的是 0.125（半徑的 12.5%），
不是寫死的 40px。這樣以後碟片放大縮小，孔跟光環會自動跟著等比例縮放。
但 CSS 和 Python 畫圖都要用實際像素，所以在這裡統一換算一次，
兩邊拿到的數字保證一模一樣 —— 這就是「不會再對不上」的關鍵。
"""

import copy
import json
import os

HERE     = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
LAYOUT_DIR = os.path.join(SKILL_DIR, "layouts")


def deep_merge(base, patch):
    """把 patch 疊到 base 上面，只覆蓋有寫到的欄位，其餘保留。

    比方說 overrides 只寫 {"colors": {"accent": "#7FD4FF"}}，
    colors 裡其他顏色不會被清掉，只有 accent 換掉。
    """
    out = copy.deepcopy(base)
    for k, v in (patch or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def strip_notes(obj):
    """把設定檔裡以 _ 開頭的說明欄位濾掉（那些是寫給人看的，不是資料）。"""
    if isinstance(obj, dict):
        return {k: strip_notes(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [strip_notes(v) for v in obj]
    return obj


def hex_to_rgb_str(h):
    """#FFD54A → "255,213,74"。CSS 裡寫 rgba(var(--accent-rgb),.5) 就能調透明度。"""
    h = h.lstrip("#")
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


class Layout:
    """一份算好的版面。cfg 是設定值，px 是換算後的實際像素。"""

    def __init__(self, cfg):
        self.cfg = cfg
        self.px = self._derive()

    # ------------------------------------------------------------------
    @classmethod
    def load(cls, name, overrides=None):
        path = os.path.join(LAYOUT_DIR, f"{name}.json")
        if not os.path.exists(path):
            avail = sorted(f[:-5] for f in os.listdir(LAYOUT_DIR) if f.endswith(".json"))
            raise SystemExit(f"找不到版面設定 {name}.json；目前有：{', '.join(avail)}")
        with open(path, encoding="utf-8") as f:
            cfg = strip_notes(json.load(f))
        return cls(deep_merge(cfg, strip_notes(overrides or {})))

    # ------------------------------------------------------------------
    def _derive(self):
        """把比例換算成像素，並算出一些兩邊都會用到的中間值。"""
        c = self.cfg
        d = c["disc"]
        ly = c.get("lyrics") or {"size": 10, "line_height": 1.4, "gap": 0,
                                 "zoom": 1, "idle_zoom": 1}
        r = d["size"] / 2.0                       # 碟片半徑

        hub = d["hub"]
        sh  = d["sheen"]

        px = {
            # ---- 碟片：把半徑比例換成像素 ----
            "disc_radius":        r,
            "disc_hole":          hub["hole"] * r,
            "disc_plastic_start": hub["plastic_start"] * r,
            "disc_plastic_end":   hub["plastic_end"] * r,
            "disc_data_start":    hub["data_start"] * r,
            "sheen_hole_ring":    [v * r for v in sh["hole_ring"]["r"]],
            "sheen_hub_ring":     [v * r for v in sh["hub_ring"]["r"]],
            "sheen_edge_ring":    [v * r for v in sh["edge_ring"]["r"]],

            # ---- 歌詞：一行有多高、一句佔多少空間 ----
            # line_h = 文字行高；box_h = 行高 + 句與句之間的空隙
            # centre_off = 從「這句的頂端」到「這句視覺中心」的距離
            "line_h":     ly["size"] * ly["line_height"],
            "box_h":      ly["size"] * ly["line_height"] + ly["gap"],
            "centre_off": ly["size"] * ly["line_height"] / 2.0,

            # ---- 放大後的字級（CSS 用 transform 縮放，Python 直接用大一號的字）----
            "size_gold": int(round(ly["size"] * ly["zoom"])),
            "size_idle": int(round(ly["size"] * ly["idle_zoom"])),

            # ---- 頻譜：每根柱子分到多寬、柱子本身多寬 ----
            "bar_slot":  c["spectrum"]["w"] / c["spectrum"]["bars"],
        }
        px["bar_width"] = px["bar_slot"] * c["spectrum"]["bar_ratio"]
        return px

    # ------------------------------------------------------------------
    def lyric_centre(self, k):
        """第 k 句歌詞的視覺中心，離歌詞列頂端多少像素。"""
        return k * self.px["box_h"] + self.px["centre_off"]

    def css_vars(self):
        """產生要注入網頁 :root 的 CSS 變數。

        全部都是算好的最終像素值 —— 這樣 CSS 裡不必寫任何 calc()，
        而且保證跟 Python 畫圖用的是同一組數字。
        """
        c, px = self.cfg, self.px
        cv, cover, d, t, sp, ct = (c["canvas"], c["cover"], c["disc"],
                                   c["title"], c["spectrum"], c["controls"])
        # 無歌詞版面沒有 lyrics 這一區，給一組不會被用到的空值就好
        ly = c.get("lyrics") or {
            "x": 0, "y": 0, "w": 10, "h": 10, "size": 10, "line_height": 1.4,
            "gap": 0, "zoom": 1, "idle_zoom": 1, "idle_alpha": 1, "fade": .15,
            "glow_blur": 0, "glow_alpha": 0, "shadow_dy": 0, "shadow_blur": 0,
            "shadow_alpha": 0}
        v = {
            "canvas-w": f"{cv['w']}px", "canvas-h": f"{cv['h']}px",
            "accent": c["colors"]["accent"], "accent-soft": c["colors"]["accent_soft"],
            "text": c["colors"]["text"], "ink": c["colors"]["ink"],

            "cover-x": f"{cover['x']}px", "cover-y": f"{cover['y']}px",
            "cover-size": f"{cover['size']}px", "cover-radius": f"{cover['radius']}px",
            "cover-shadow": (f"0 {cover['shadow']['dy']}px {cover['shadow']['blur']}px "
                             f"rgba(0,0,0,{cover['shadow']['alpha']})"),
            "cover-ring": f"rgba(255,255,255,{cover['inner_ring_alpha']})",

            "disc-x": f"{d['x']}px", "disc-y": f"{d['y']}px", "disc-size": f"{d['size']}px",
            "disc-period": f"{d['period']}s",
            "disc-shadow": (f"0 {d['shadow']['dy']}px {d['shadow']['blur']}px "
                            f"rgba(0,0,0,{d['shadow']['alpha']})"),
            "hole": f"{px['disc_hole']:g}px",
            "plastic-a": f"{px['disc_plastic_start']:g}px",
            "plastic-b": f"{px['disc_plastic_end']:g}px",
            "data-start": f"{px['disc_data_start']:g}px",
            "plastic-alpha": f"{d['hub']['plastic_alpha']}",

            "title-x": f"{t['x'] if t.get('align','left')=='left' else 0}px",
            "title-w": ("auto" if t.get("align", "left") == "left"
                        else f"{cv['w']}px"),
            "title-align": t.get("align", "left"),
            "rule-x": (f"{t['x']}px" if t.get("align", "left") == "left"
                       else f"{(cv['w'] - t['rule_w']) // 2}px"),
            "title-y": f"{t['y']}px",
            "title-size": f"{t['size']}px", "title-track": f"{t['tracking']}em",
            "sub-y": f"{t['sub_y']}px", "sub-size": f"{t['sub_size']}px",
            "sub-track": f"{t['sub_tracking']}em", "sub-alpha": f"{t['sub_alpha']}",
            "rule-y": f"{t['rule_y']}px", "rule-w": f"{t['rule_w']}px",
            "rule-h": f"{t['rule_h']}px",

            "lyr-x": f"{ly['x']}px", "lyr-y": f"{ly['y']}px",
            "lyr-w": f"{ly['w']}px", "lyr-h": f"{ly['h']}px",
            "lyric-size": f"{ly['size']}px", "lyric-lh": f"{ly['line_height']}",
            "lyric-gap": f"{ly['gap']}px", "lyric-zoom": f"{ly['zoom']}",
            "lyric-idle-zoom": f"{ly['idle_zoom']}",
            "lyric-idle-color": (f"rgba({hex_to_rgb_str(c['colors']['text'])},"
                                 f"{ly['idle_alpha']})"),
            "fade": f"{ly['fade'] * 100:g}%", "fade-end": f"{(1 - ly['fade']) * 100:g}%",
            "accent-rgb": hex_to_rgb_str(c["colors"]["accent"]),
            "text-rgb":   hex_to_rgb_str(c["colors"]["text"]),
            "glow": (f"0 0 {ly['glow_blur']}px "
                     f"rgba({hex_to_rgb_str(c['colors']['accent'])},{ly['glow_alpha']}), "
                     f"0 {ly['shadow_dy']}px {ly['shadow_blur']}px "
                     f"rgba(0,0,0,{ly['shadow_alpha']})"),

            "spec-x": f"{sp['x']}px", "spec-y": f"{sp['y']}px",
            "spec-w": f"{sp['w']}px", "spec-h": f"{sp['h']}px",

            "ctl-y": f"{ct['y']}px", "ctl-h": f"{ct['h']}px",
            "ctl-btn": f"{ct['button']}px", "ctl-gap": f"{ct['gap']}px",
            "ctl-bar": f"{ct['bar_h']}px", "ctl-dot": f"{ct['dot']}px",
            "hint-y": f"{ct['hint_y']}px", "hint-size": f"{ct['hint_size']}px",
        }
        # 背景遮罩的濃度
        bg = c["background"]
        v["mask-base"] = f"{bg['mask_base']}"
        v["mask-side"] = f"{bg['mask_side']}"
        v["bg-pos"] = f"{bg['position_x'] * 100:g}% {bg['position_y'] * 100:g}%"
        return v

    # ------------------------------------------------------------------
    # 下面三個是「多層漸層」，寫成一整串 CSS。
    # 它們用的每一個數字都來自同一份設定檔，所以影片版照著同樣的數字畫，
    # 結果一定一致。
    # ------------------------------------------------------------------
    def disc_mask_css(self):
        """碟片的挖洞遮罩：中心真的透明，外面一圈只留一點點。"""
        p = self.px
        a = self.cfg["disc"]["hub"]["plastic_alpha"]
        return (f"radial-gradient(circle at 50% 50%,"
                f"rgba(0,0,0,0) 0,rgba(0,0,0,0) {p['disc_hole']:g}px,"
                f"rgba(0,0,0,{a}) {p['disc_plastic_start']:g}px,"
                f"rgba(0,0,0,{a}) {p['disc_plastic_end']:g}px,"
                f"rgba(0,0,0,1) {p['disc_data_start']:g}px,rgba(0,0,0,1) 100%)")

    def sheen_mask_css(self):
        """反光層也要挖同一個洞，否則會把中心孔糊起來。"""
        r = self.px["sheen_hole_ring"]
        return (f"radial-gradient(circle at 50% 50%,"
                f"transparent 0 {r[0]:g}px,#000 {r[1]:g}px,#000 100%)")

    def sheen_css(self):
        """CD 反光：三圈光環 + 兩道斜向高光。先寫的在上面。"""
        sh = self.cfg["disc"]["sheen"]
        parts = []
        for key, rad in (("hole_ring", "sheen_hole_ring"),
                         ("hub_ring", "sheen_hub_ring"),
                         ("edge_ring", "sheen_edge_ring")):
            rs, alphas = self.px[rad], sh[key]["a"]
            stops = ",".join(f"rgba(255,255,255,{a}) {r:g}px" for r, a in zip(rs, alphas))
            parts.append(f"radial-gradient(circle at 50% 50%,{stops})")
        for s in sh["streaks"]:
            stops = ",".join(
                f"rgba({c[0]},{c[1]},{c[2]},{a}) {pos * 100:g}%"
                for pos, c, a in zip(s["stops"], s["colors"], s["alpha"]))
            parts.append(f"linear-gradient({s['angle']}deg,{stops})")
        return ",".join(parts)

    def tint_css(self):
        """背景遮罩：由左至右加深的那層在上，整體壓暗的橢圓在下。"""
        b = self.cfg["background"]
        v = ",".join(str(x) for x in self.cfg["colors"]["veil"])
        vd = ",".join(str(x) for x in self.cfg["colors"]["veil_deep"])
        s0, s1, s2 = b["mask_side_stops"]
        side = b["mask_side"]
        lin = (f"linear-gradient(90deg,"
               f"rgba({v},0) 0%,rgba({v},0) {s0 * 100:g}%,"
               f"rgba({v},{side * b['mask_side_mid_ratio']:g}) {s1 * 100:g}%,"
               f"rgba({v},{side}) {s2 * 100:g}%,rgba({v},{side}) 100%)")
        cx, cy = b["mask_radial_center"]
        rx, ry = b["mask_radial_size"]
        base = b["mask_base"]
        rad = (f"radial-gradient({rx * 100:g}% {ry * 100:g}% "
               f"at {cx * 100:g}% {cy * 100:g}%,"
               f"rgba({v},{base - b['mask_base_center_lift']:g}) 0%,"
               f"rgba({v},{base:g}) {b['mask_radial_mid_stop'] * 100:g}%,"
               f"rgba({vd},{base + b['mask_base_edge_add']:g}) 100%)")
        return lin + "," + rad

    def lyric_fade_css(self):
        """歌詞視窗上下邊緣淡出。（無歌詞版面用不到，回一個無害的值）"""
        if not self.cfg.get("lyrics"):
            return "none"
        f = self.cfg["lyrics"]["fade"] * 100
        return (f"linear-gradient(to bottom,transparent 0,#000 {f:g}%,"
                f"#000 {100 - f:g}%,transparent 100%)")

    def js_config(self):
        """要交給網頁 JS 的那一小撮設定（它只需要這些）。"""
        c = self.cfg
        return {
            "canvas":   c["canvas"],
            "disc":     {"period": c["disc"]["period"]},
            "lyrics":   ({k: c["lyrics"][k] for k in
                          ("size", "line_height", "gap",
                           "dim_start", "dim_step", "dim_floor", "idle_grace")}
                         if c.get("lyrics") else None),
            "spectrum": c["spectrum"],
        }

    def css_root_block(self):
        """組成可以直接貼進 <style> 的 :root { ... } 文字。"""
        v = self.css_vars()
        v["disc-mask"]  = self.disc_mask_css()
        v["sheen-mask"] = self.sheen_mask_css()
        v["lyr-fade"]   = self.lyric_fade_css()
        lines = ["  --%s: %s;" % (k, val) for k, val in v.items()]
        return ":root{\n" + "\n".join(lines) + "\n}"


def load_project(project_dir):
    """讀某一首歌的 project.json，並補上預設值與絕對路徑。"""
    path = os.path.join(project_dir, "project.json")
    if not os.path.exists(path):
        raise SystemExit(f"找不到 {path}\n（每一首歌要有一個 project.json 說明素材在哪、標題是什麼）")
    with open(path, encoding="utf-8") as f:
        p = strip_notes(json.load(f))

    p.setdefault("layout", "16x9")
    p.setdefault("subtitle", "")
    p.setdefault("out_prefix", "musicdisk")
    p.setdefault("overrides", {})
    for key in ("art", "audio", "lyrics"):
        if p.get(key):
            p[key] = os.path.join(project_dir, p[key])
    p["dir"] = project_dir
    return p


_MATERIAL_LABELS = {"art": "封面圖", "audio": "音樂　", "lyrics": "歌詞　"}


def check_materials(proj, need):
    """確認 project.json 指到的素材檔真的在。缺的話一次列出全部。

    為什麼要「一次列出」而不是缺一個報一個：三個都沒放好的時候，
    一次報一個會變成「補一個→再跑→又被擋」來回三趟。

    為什麼要順便列出資料夾裡現有的檔案：實務上最常見的並不是忘了放檔案，
    而是檔名跟 project.json 對不上（.jpg 寫成 .png、中文檔名複製時被改掉）。
    把現有檔案攤開來，多數人自己就看出哪裡對不上了。
    """
    missing = [k for k in need if not proj.get(k) or not os.path.exists(proj[k])]
    if not missing:
        return

    out = [f"這個資料夾少了 {len(missing)} 個素材："]
    for k in missing:
        name = os.path.basename(proj[k]) if proj.get(k) else "（project.json 裡沒寫）"
        out.append(f"    {_MATERIAL_LABELS[k]}　{name}　　← project.json 的 {k}")
    try:
        have = sorted(f for f in os.listdir(proj["dir"]) if f != "project.json")
    except OSError:
        have = []
    out.append("")
    out.append("  資料夾裡現有的檔案：" + ("、".join(have) if have else "（沒有其他檔案）"))
    out.append("  檔名不必改成一樣 —— 改 project.json 裡的欄位指到現有檔案也可以。")
    raise SystemExit("\n".join(out))


def resolve_out(out, project_dir, default_name):
    """決定產出檔要寫到哪裡。

        沒給 --out            → 歌曲資料夾/default_name
        --out musicdisk_v2.html → 歌曲資料夾/musicdisk_v2.html
        --out D:/somewhere/x.html → 就寫那裡

    只給檔名時之所以要補上歌曲資料夾、而不是寫進當下的工作目錄：
    產出永遠屬於使用者的歌曲資料夾（這是本 skill 的基本原則），
    而執行時的工作目錄常常是 skill 資料夾，寫進去就髒了。
    """
    if not out:
        return os.path.join(project_dir, default_name)
    return out if os.path.dirname(out) else os.path.join(project_dir, out)
