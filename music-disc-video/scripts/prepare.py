"""
prepare.py —— 開工前先分析這首歌，把該調的都調好。

執行方式：
    python3 scripts/prepare.py <歌曲資料夾>              # 分析並套用
    python3 scripts/prepare.py <歌曲資料夾> --accent 2   # 改用第 2 個候選主色

它會做四件事：
  1. 讀歌詞（各種格式都吃；沒時間軸的話會叫你先去對時）
  2. 算出不會被切掉的字級
  3. 算出背景該壓多暗才讀得清楚
  4. 抽 3 個候選主色，畫成對照圖讓你挑

算完的結果會寫進 project.json 的 overrides 裡，
之後 build_html.py 和 render_video.py 都會自動吃到。

為什麼要獨立成一步、而不是每次建置都算？
    因為「主色」需要你用眼睛挑，不能自動決定。
    分成「準備 → 挑色 → 建置」三步，每一步都清楚。
"""

import argparse
import colorsys
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import autotune
import lyrics as lyrics_mod
from layout import Layout, load_project, check_materials, hex_to_rgb_str


def lighten(hex_color, amount=0.45):
    """把顏色調淡一點，用在進度條的漸層等地方。"""
    r, g, b = (int(hex_color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    f = lambda c: int(round(c + (255 - c) * amount))
    return "#%02X%02X%02X" % (f(r), f(g), f(b))


def accent_gradient(accent_hex, base_gradient):
    """從主色推出整條頻譜漸層（由下往上：主色 → 過渡 → 淡的互補色）。

    只換最底下那一段是不夠的 —— 中間那段的顏色佔了柱子大部分的面積，
    不換的話會出現「歌詞是藍的、柱子還是金的」這種前後不一致。

    為什麼頂端用互補色？因為單一顏色由深到淺會有點單調，
    兩個對比色之間漸層看起來有層次，也是原本手工配色的做法。
    """
    r, g, b = (int(accent_hex.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, sat, val = colorsys.rgb_to_hsv(r, g, b)
    top = colorsys.hsv_to_rgb((h + 0.5) % 1.0, sat * 0.55, 1.0)      # 淡的互補色
    mid = tuple(a + (c - a) * 0.35 for a, c in zip((r, g, b), top))  # 兩者之間
    to255 = lambda c: [int(round(x * 255)) for x in c]
    alphas = [g_["rgba"][3] for g_ in base_gradient]
    return [
        {"at": 0.00, "rgba": to255((r, g, b)) + [alphas[0]]},
        {"at": 0.45, "rgba": to255(mid) + [alphas[1] if len(alphas) > 1 else 0.88]},
        {"at": 1.00, "rgba": to255(top) + [alphas[-1]]},
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--accent", type=int, default=None,
                    help="直接指定要用第幾個候選主色（1/2/3）")
    ap.add_argument("--visible-lines", type=int, default=None,
                    help="歌詞欄同時大約看到幾句（不填就用版面設定檔裡的值）")
    args = ap.parse_args()

    proj = load_project(args.project)
    lay = Layout.load(proj["layout"], proj.get("overrides"))
    cfg = lay.cfg
    print(f"=== 準備：{proj['title']}（版面 {proj['layout']}）===\n")

    has_lyrics = cfg.get("has_lyrics", True)
    check_materials(proj, ["art", "audio"] + (["lyrics"] if has_lyrics else []))

    # ---- 0. 封面必須是正方形（非正方形會被壓扁，而且不會報錯）----
    square_art, square_note = autotune.ensure_square(proj["art"])
    if square_note:
        print(f"⚠ {square_note}\n")
        proj["art"] = square_art

    # ---- 1. 歌詞 ----
    lines, fit = [], None
    if not has_lyrics:
        print("這是無歌詞版面，跳過歌詞與字級")
    else:
      try:
          lines = lyrics_mod.parse(proj["lyrics"])
      except lyrics_mod.NoTimestamps as e:
        print(lyrics_mod.no_timestamps_help(args.project, len(e.texts)))
        return 1
      print(f"歌詞：{len(lines)} 句，"
            f"{lines[0]['start']:.1f}s 開始唱，{lines[-1]['end']:.1f}s 結束")

      # ---- 2. 字級 ----
      fit = autotune.fit_lyric_size(lines, cfg, visible_lines=args.visible_lines)
      print(f"\n字級：{fit['size']}px（一次看到約 {cfg['lyrics'].get('visible_lines',7)} 句）")
      print(f"  最長的一句「{fit['longest']}」")
      print(f"  放大後 {fit['widest_px']}px，欄寬可用 {fit['usable_px']}px"
            f"（{'塞得下 ✓' if fit['widest_px'] <= fit['usable_px'] else '塞不下 ✗'}）")
      if fit["size"] < fit["by_height"]:
        print(f"  註：本來高度可以放到 {fit['by_height']}px，"
              f"但為了讓最長那句不被切掉而縮到 {fit['size']}px")
        # 縮太多的話字會小到看不清楚。與其默默接受，不如告訴使用者可以怎麼改
        if fit["size"] < fit["by_height"] * 0.7:
            print(f"  ⚠ 為了那一句，其他所有句子都被連累縮小了不少。")
            print(f"    建議把它拆成兩句（在歌詞檔裡拆成兩行、各給一段時間），")
            print(f"    這樣其他句子就能維持 {fit['by_height']}px 左右。")

    # ---- 3. 遮罩 ----
    mask = autotune.suggest_mask(proj["art"], cfg, proj.get("title"))
    total = 1 - (1 - mask["mask_base"]) * (1 - mask["mask_side"])
    side_txt = (f"、歌詞區再加深 {mask['mask_side']:.2f}" if mask["mask_side"] else "")
    print(f"\n背景遮罩：整體 {mask['mask_base']:.2f}{side_txt}"
          f"（合計壓暗 {total*100:.0f}%）")
    if mask["p95_text"] is None:
        print("  依據：這個版面畫面上沒有字要讀（無歌詞、標題也留空），"
              "只做一般性壓暗，盡量保留封面本身")
    else:
        print(f"  依據：{mask['text_where']}最亮的地方是 {mask['p95_text']:.0f}/255，"
              f"壓完會降到 {mask['p95_text']*(1-total):.0f}/255，白字才讀得清楚")

    # ---- 4. 主色 ----
    cands = autotune.accent_candidates(proj["art"])
    preview = os.path.join(args.project, "_主色候選.png")
    if fit:
        tuned = dict(cfg["lyrics"]); tuned["size"] = fit["size"]
        cfg_preview = dict(cfg); cfg_preview["lyrics"] = tuned
        autotune.accent_preview(proj["art"], cfg_preview, cands,
                                fit["longest"], preview, mask)
    print("\n主色候選：")
    for i, c in enumerate(cands, 1):
        print(f"  {i}. {c['hex']}  {c['why']}")
    if fit:
        print(f"  對照圖：{preview}")

    pick = args.accent if args.accent in (1, 2, 3) else 2      # 預設用最保險的金色
    accent = cands[pick - 1]["hex"]
    print(f"\n這次採用第 {pick} 個：{accent}"
          f"{'（預設值，可用 --accent 1/2/3 換）' if args.accent is None else ''}")

    # ---- 寫回 project.json ----
    ov = proj.get("overrides", {})
    ov.setdefault("colors", {})
    ov["colors"]["accent"] = accent
    ov["colors"]["accent_soft"] = lighten(accent)
    if fit:
        ov.setdefault("lyrics", {})["size"] = fit["size"]
    ov.setdefault("background", {})
    ov["background"]["mask_base"] = mask["mask_base"]
    ov["background"]["mask_side"] = mask["mask_side"]
    # 頻譜整條漸層都跟著主色走，整體才協調
    ov.setdefault("spectrum", {})["gradient"] = accent_gradient(
        accent, cfg["spectrum"]["gradient"])

    path = os.path.join(args.project, "project.json")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    raw["overrides"] = ov
    raw["accent_candidates"] = [c["hex"] for c in cands]
    if square_note:
        # 裁好的正方形圖要寫回去，否則 build_html / render_video 還是會讀到原圖
        raw["art"] = os.path.basename(square_art)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)
    print(f"\n已寫回 {path}，接下來可以直接建置：")
    print(f"    python3 scripts/build_html.py {args.project}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
