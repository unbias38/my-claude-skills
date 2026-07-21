"""
_generate.py —— 從 16x9.json 衍生出其他版面。

為什麼用程式產、不手寫五份 JSON？
    因為五份裡有九成的內容是一樣的（顏色、碟片中心孔的比例、CD 反光的環、
    遮罩的漸層形狀…）。手寫五份的話，以後改一個共用設定就要改五個地方，
    而且一定會漏掉一個。這裡只寫「每套版面不一樣的那些座標」，其餘自動繼承。

    陰影的大小會依照元件尺寸等比例縮放 —— 直式版面的碟片比較小，
    陰影就該跟著變小，不然會顯得很笨重。

執行：python3 layouts/_generate.py
"""

import copy
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = json.load(open(os.path.join(HERE, "16x9.json"), encoding="utf-8"))

# 基準值：16:9 的碟片 640、封面 580，其他版面按比例縮放陰影
REF_DISC, REF_COVER = 640, 580


def make(name, aspect, canvas, cover, disc, title, spectrum, controls,
         progress, lyrics=None, bars=56):
    L = copy.deepcopy(BASE)
    L["_說明"] = [f"由 layouts/_generate.py 從 16x9.json 衍生，請不要手動改這份。",
                  f"要調整請改 _generate.py 裡 {name} 那一段，再重新執行它。"]
    L["name"], L["aspect"] = name, aspect
    L["canvas"] = {"w": canvas[0], "h": canvas[1]}
    L["has_lyrics"] = lyrics is not None

    ds, cs = disc["size"] / REF_DISC, cover["size"] / REF_COVER
    L["cover"] = {
        "x": cover["x"], "y": cover["y"], "size": cover["size"],
        "radius": max(6, round(14 * cs)),
        "shadow": {"dy": round(26 * cs), "blur": round(60 * cs), "alpha": 0.66},
        "inner_ring_alpha": 0.10,
    }
    L["disc"].update({
        "x": disc["x"], "y": disc["y"], "size": disc["size"],
        "period": disc.get("period", 12.0),
        "shadow": {"dy": round(20 * ds), "blur": round(46 * ds), "alpha": 0.62},
    })
    L["title"] = {
        "x": title["x"], "y": title["y"], "size": title["size"],
        "align": title.get("align", "left"),
        "tracking": 0.06, "center_ratio": 0.652,
        "sub_y": title["sub_y"], "sub_size": title["sub_size"],
        "sub_tracking": 0.42, "sub_alpha": 0.5, "sub_center_ratio": 0.667,
        "rule_y": title["rule_y"], "rule_w": title["rule_w"], "rule_h": 3,
    }
    if lyrics:
        L["lyrics"] = dict(BASE["lyrics"], **lyrics)
    else:
        L.pop("lyrics", None)
    L["spectrum"] = dict(BASE["spectrum"], **spectrum, bars=bars)
    L["controls"] = dict(BASE["controls"], **controls)
    L["video_progress"] = dict(BASE["video_progress"], **progress)

    path = os.path.join(HERE, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(L, f, ensure_ascii=False, indent=2)
    print(f"  {name:12s} {canvas[0]}×{canvas[1]}  "
          f"{'有歌詞' if lyrics else '無歌詞'}")


print("產生版面設定：")

# =========================================================================
# 橫式 16:9 純音樂版 —— 封面碟片整組置中當主角，標題置中放下方
# =========================================================================
make("16x9-solo", "橫式 16:9 純音樂版（無歌詞），適合 Podcast 片頭、背景音樂",
     canvas=(1920, 1080),
     cover={"x": 558, "y": 150, "size": 500},
     disc={"x": 803, "y": 120, "size": 560},
     title={"x": 0, "y": 700, "size": 54, "align": "center",
            "sub_y": 772, "sub_size": 17, "rule_y": 812, "rule_w": 110},
     spectrum={"x": 260, "y": 845, "w": 1400, "h": 110},
     controls={"y": 970, "h": 56, "button": 58, "hint_y": 1038, "hint_size": 13},
     progress={"x": 260, "y": 990, "w": 1400, "h": 6},
     bars=52)

# =========================================================================
# 直式 9:16 —— 手機短影音。封面碟片在上、歌詞在下
# =========================================================================
make("9x16", "直式 9:16，適合 IG Reels、抖音、YouTube Shorts",
     canvas=(1080, 1920),
     cover={"x": 157, "y": 220, "size": 480},
     disc={"x": 399, "y": 200, "size": 520},
     title={"x": 110, "y": 800, "size": 50,
            "sub_y": 866, "sub_size": 16, "rule_y": 906, "rule_w": 100},
     spectrum={"x": 110, "y": 1640, "w": 860, "h": 130},
     controls={"y": 1800, "h": 60, "button": 56, "hint_y": 1874, "hint_size": 13},
     progress={"x": 110, "y": 1830, "w": 860, "h": 6},
     lyrics={"x": 110, "y": 960, "w": 860, "h": 620, "visible_lines": 7},
     bars=44)

make("9x16-solo", "直式 9:16 純音樂版（無歌詞）",
     canvas=(1080, 1920),
     cover={"x": 93, "y": 330, "size": 560},
     disc={"x": 365, "y": 300, "size": 620},
     title={"x": 0, "y": 1010, "size": 62, "align": "center",
            "sub_y": 1096, "sub_size": 19, "rule_y": 1146, "rule_w": 130},
     spectrum={"x": 110, "y": 1270, "w": 860, "h": 180},
     controls={"y": 1560, "h": 60, "button": 58, "hint_y": 1642, "hint_size": 13},
     progress={"x": 110, "y": 1520, "w": 860, "h": 7},
     bars=44)

# =========================================================================
# 正方形 1:1 —— IG 貼文。空間最緊，字要小、看到的句數要少
# =========================================================================
make("1x1", "正方形 1:1，適合 IG 貼文",
     canvas=(1080, 1080),
     cover={"x": 250, "y": 70, "size": 360},
     disc={"x": 428, "y": 50, "size": 400},
     title={"x": 90, "y": 500, "size": 34,
            "sub_y": 546, "sub_size": 13, "rule_y": 576, "rule_w": 76},
     spectrum={"x": 90, "y": 934, "w": 900, "h": 62},
     controls={"y": 1004, "h": 50, "button": 46, "gap": 18,
               "hint_y": 1058, "hint_size": 11},
     progress={"x": 90, "y": 1018, "w": 900, "h": 5},
     lyrics={"x": 90, "y": 616, "w": 900, "h": 300, "gap": 20, "visible_lines": 5},
     bars=40)

make("1x1-solo", "正方形 1:1 純音樂版（無歌詞）",
     canvas=(1080, 1080),
     cover={"x": 157, "y": 170, "size": 480},
     disc={"x": 392, "y": 145, "size": 530},
     title={"x": 0, "y": 730, "size": 46, "align": "center",
            "sub_y": 792, "sub_size": 16, "rule_y": 832, "rule_w": 110},
     spectrum={"x": 120, "y": 872, "w": 840, "h": 90},
     controls={"y": 986, "h": 54, "button": 50, "hint_y": 1050, "hint_size": 12},
     progress={"x": 120, "y": 1000, "w": 840, "h": 6},
     bars=40)

print("\n完成。16x9.json 是手寫的原始版面，其餘由這支程式產生。")
