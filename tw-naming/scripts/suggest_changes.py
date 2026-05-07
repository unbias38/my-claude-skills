"""對既有姓名建議改字方案：固定其他字，搜尋某一位置改成什麼筆劃會吉。

Usage:
    # 張小明，固定姓+小，改最後一字
    python suggest_changes.py 張小明 --change 3

    # 林森，改名（單字名→單字名）
    python suggest_changes.py 林森 --change 2

    # 加 --wuxing 過濾候選字 (需 OpenCC for clean 繁體)
    python suggest_changes.py 張小明 --change 3 --wuxing 火

    # 加 --avoid 父母用過的字
    python suggest_changes.py 張小明 --change 3 --wuxing 火 --avoid 明芳華
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from kangxi_lookup import load_table  # noqa: E402
from wuge import compute_wuge  # noqa: E402
from lucky_81 import GRADE_RANK, info_of as lucky_info  # noqa: E402
from chars_by_stroke import (  # noqa: E402
    load_kangxi_table,
    chars_by_stroke as _chars_by_stroke,
    chars_by_stroke_and_wuxing,
)
from zodiac_score import (  # noqa: E402
    zodiac_from_year, load_zodiac_data, score_name as score_zodiac, ZODIAC_FILES,
)

MIN_STROKE = 1
MAX_STROKE = 30


def search_replacement(surname_strokes: list[int],
                       given_strokes: list[int],
                       change_idx: int,
                       min_grade: str = "中吉",
                       sancai_min: str = "大吉",
                       include_tiange: bool = False) -> list[dict]:
    """change_idx is 1-based: position within the FULL name.
    e.g. for 張小明 with change_idx=3, we replace 明 (the 1st char of given when surname_len=1).
    """
    surname_len = len(surname_strokes)
    given_len = len(given_strokes)
    name_len = surname_len + given_len

    if not (1 <= change_idx <= name_len):
        raise ValueError(f"change_idx {change_idx} out of range [1, {name_len}]")
    if change_idx <= surname_len:
        raise ValueError("Cannot change surname (姓不可改). Pick a given-name position.")

    given_idx = change_idx - surname_len - 1   # 0-based within given_strokes

    threshold = GRADE_RANK[min_grade]
    sancai_threshold = GRADE_RANK[sancai_min]
    checked_keys = ["人格吉凶", "地格吉凶", "外格吉凶", "總格吉凶"]
    if include_tiange:
        checked_keys.insert(0, "天格吉凶")

    results = []
    for s in range(MIN_STROKE, MAX_STROKE + 1):
        trial = list(given_strokes)
        trial[given_idx] = s
        r = compute_wuge(surname_strokes, trial)
        grades = [r[k] for k in checked_keys]
        if not all(GRADE_RANK.get(g, -1) >= threshold for g in grades):
            continue
        if GRADE_RANK.get(r["三才吉凶"], -1) < sancai_threshold:
            continue
        results.append({
            "new_stroke": s,
            "三才": r["三才"],
            "三才吉凶": r["三才吉凶"],
            "五格吉凶": grades,
        })
    return results


def _load_sancai_content() -> dict:
    import json as _json
    path = Path(__file__).parent.parent / "assets" / "Sancai.json"
    if not path.exists():
        return {}
    try:
        raw = _json.load(open(path, encoding="utf-8-sig"))
        return {k: v for k, v in raw.items() if v is not None}
    except Exception:
        return {}


def format_markdown_report(name: str,
                            surname_chars: list[str], given_chars: list[str],
                            surname_strokes: list[int], given_strokes: list[int],
                            change_idx: int, fixed_chars: list[str],
                            current_result: dict, enriched_combos: list[dict],
                            min_grade: str, sancai_min: str,
                            wuxing_filter: str | None, avoid_set: set,
                            zodiac: str | None,
                            current_zodiac_score: dict | None) -> str:
    """改名建議 Markdown 報告 — 可貼 LINE/HackMD/Notion."""
    sancai_content_db = _load_sancai_content()
    lines = []
    lines.append(f"# 改名建議：{name}")
    lines.append("")

    info_parts = []
    info_parts.append(f"**改第 {change_idx} 字**")
    info_parts.append(f"**保留**：{' '.join(fixed_chars)}")
    if zodiac:
        info_parts.append(f"**生肖**：{zodiac}")
    if wuxing_filter:
        info_parts.append(f"**喜用神過濾**：{wuxing_filter}")
    if avoid_set:
        info_parts.append(f"**避諱字**：{''.join(sorted(avoid_set))}")
    lines.append("　・　".join(info_parts))
    lines.append("")

    # 現名分析
    lines.append("## 原名現況")
    lines.append("")
    stroke_str = "　・　".join(f"{c} {n} 劃" for c, n in zip(
        surname_chars + given_chars, surname_strokes + given_strokes))
    lines.append(f"**康熙筆劃**：{stroke_str}")
    lines.append("")
    lines.append("**現有五格 + 81 數理**")
    lines.append("")
    lines.append("| 格 | 數 | 吉凶 | 數名 | 含義 |")
    lines.append("|---|---|---|---|---|")
    for key in ["天格", "人格", "地格", "外格", "總格"]:
        n = current_result[key]
        grade, gname, gdesc = lucky_info(n)
        tag = "（祖蔭，不參與主判）" if key == "天格" else ""
        lines.append(f"| {key}{tag} | {n} | {grade} | {gname} | {gdesc} |")
    lines.append("")
    sancai = current_result["三才"]
    sancai_key = "".join(sancai)
    lines.append(f"**三才**：{sancai[0]}-{sancai[1]}-{sancai[2]}　**{current_result['三才吉凶']}**")
    sancai_full = sancai_content_db.get(sancai_key, {})
    if sancai_full.get("content"):
        lines.append("")
        for para in sancai_full["content"].strip().split("\n"):
            if para.strip():
                lines.append(f"> {para.strip()}")
    lines.append("")

    if current_zodiac_score:
        z = current_zodiac_score
        total = z["total_score"]
        tag = "偏吉" if total >= 1 else "偏忌" if total <= -1 else "中性"
        lines.append(f"**生肖派加分（{z['zodiac']}）**：總分 {total:+d}（{tag}）")
        for item in z["chars"]:
            mark = {"宜": "✅", "忌": "❌", "中性": "・"}[item["label"]]
            lines.append(f"- {mark} {item['char']}　{item['label']}　({item['score']:+d})")
        lines.append("")

    # 改字搜尋結果
    lines.append("## 改字搜尋結果")
    lines.append("")
    lines.append(f"篩選條件：五格 ≥ {min_grade}、三才 ≥ {sancai_min}（不含天格祖蔭）")
    if wuxing_filter:
        lines.append(f"五行限定：{wuxing_filter}")
    if avoid_set:
        lines.append(f"避開：{''.join(sorted(avoid_set))}")
    lines.append("")

    if not enriched_combos:
        lines.append("⚠️ **沒找到任何改字組合**")
        lines.append("")
        lines.append("可能原因：")
        lines.append("- 保留的字（姓 + 其他名字）已把人格/外格鎖死成大凶，怎麼換另一字都救不回")
        lines.append("- 過濾條件太嚴")
        lines.append("")
        lines.append("**建議**：")
        lines.append("- 試改別的位置（`--change` 改成不同數字）")
        lines.append("- 放寬篩選（`--grade 中吉 --sancai-grade 中吉`）")
        lines.append("- 整個重取名（用 generate 模式而非改字）")
        lines.append("")
    else:
        lines.append(f"找到 **{len(enriched_combos)} 個吉筆劃組合**")
        lines.append("")
        for c in enriched_combos:
            stroke = c["new_stroke"]
            sancai_str = "-".join(c["三才"])
            grade, gname, gdesc = lucky_info(stroke)  # 81 數 of the new char's stroke (informational only — not the same as 五格)
            lines.append(f"### {stroke} 劃　三才：{sancai_str} {c['三才吉凶']}")
            lines.append("")
            chars_list = c.get("chars", [])
            if not chars_list:
                lines.append("*（無候選字 — 可能被五行或避諱條件過濾掉）*")
            else:
                lines.append("**候選字**：" + "、".join(chars_list))
            lines.append("")

    # 生肖字根參考
    if zodiac:
        try:
            from zodiac_explain import format_reference as _zref
            lines.append("## 生肖字根層級宜忌參考")
            lines.append("")
            lines.append("```")
            lines.append(_zref(zodiac))
            lines.append("```")
            lines.append("")
        except ImportError:
            pass

    # LLM placeholder
    lines.append("## 字義 / 聲調 / 取捨建議")
    lines.append("")
    lines.append("> （待 LLM 從上方候選字裡挑出 3-5 組合適的「保留字 + 新字」組合，")
    lines.append("> 每組標明：字義、國語聲調、台語檢音、是否撞菜市場名，最後給推薦排序）")
    lines.append("")

    # 免責
    lines.append("---")
    lines.append("")
    lines.append("## 說明")
    lines.append("")
    lines.append("本建議以康熙筆劃為基準，固定原名其他字，搜尋指定位置的吉字組合。")
    lines.append("")
    lines.append("- 三才五格僅是傳統姓名學六大派之一，預測準確度約 56.6%")
    if zodiac:
        lines.append("- 生肖派宜忌僅為附加參考，因派別爭議較大未列入主判定")
    lines.append("- 天格代表祖蔭，由姓氏決定不可改，主判定不納入")
    lines.append("- 父母 / 祖輩名字避諱請自行確認後告知")
    lines.append("- 重大改名建議由專業命理師最後確認後執行")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="現有完整姓名 (繁體)")
    ap.add_argument("--surname-len", type=int, default=1, choices=[1, 2])
    ap.add_argument("--change", type=int, required=True,
                    help="要改的字位置 (1-based, 全名中第幾個字; 不可指向姓)")
    ap.add_argument("--grade", default="中吉",
                    choices=["大吉", "中吉", "半吉"])
    ap.add_argument("--sancai-grade", default="大吉",
                    choices=["大吉", "中吉", "半吉"])
    ap.add_argument("--wuxing", choices=["金", "木", "水", "火", "土"],
                    help="只列出此五行的候選字 (需 OpenCC 才會輸出乾淨繁體)")
    ap.add_argument("--avoid", default="",
                    help="避諱字清單 (連寫即可, e.g., '明芳華' 表示避開三個字)")
    ap.add_argument("--include-tiange", action="store_true")
    ap.add_argument("--limit-strokes", type=int, default=10,
                    help="最多列出幾個吉筆劃")
    ap.add_argument("--limit-chars", type=int, default=20,
                    help="每個吉筆劃下最多列幾個候選字")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--year", type=int, help="西元出生年, 加生肖派字根參考")
    g.add_argument("--zodiac", choices=list(ZODIAC_FILES.keys()))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--report", action="store_true",
                    help="輸出可分享的 Markdown 報告 (適合貼 LINE/HackMD/Notion)")
    args = ap.parse_args()

    if len(args.name) < args.surname_len + 1:
        print(f"⚠️ 姓名 '{args.name}' 太短", file=sys.stderr)
        sys.exit(1)
    surname_chars = list(args.name[:args.surname_len])
    given_chars = list(args.name[args.surname_len:])

    table = load_table()
    surname_strokes = [table.get(ch) for ch in surname_chars]
    given_strokes = [table.get(ch) for ch in given_chars]
    if any(n is None for n in surname_strokes + given_strokes):
        missing = [ch for ch, n in zip(surname_chars + given_chars,
                                       surname_strokes + given_strokes) if n is None]
        print(f"⚠️ 找不到康熙筆劃: {' '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    avoid_set = set(args.avoid)
    fixed_chars = [ch for i, ch in enumerate(surname_chars + given_chars,
                                              start=1) if i != args.change]

    combos = search_replacement(
        surname_strokes, given_strokes, args.change,
        args.grade, args.sancai_grade,
        include_tiange=args.include_tiange,
    )

    print(f"# 改名建議: {args.name} (改第 {args.change} 字)", file=sys.stderr)
    print(f"# 保留: {' '.join(fixed_chars)}", file=sys.stderr)
    print(f"# 找到 {len(combos)} 個吉筆劃 (篩選: 五格>={args.grade}, 三才>={args.sancai_grade})",
          file=sys.stderr)

    output_combos = combos[:args.limit_strokes]

    kangxi = load_kangxi_table()
    enriched = []
    if args.wuxing:
        for c in output_combos:
            chars, _ = chars_by_stroke_and_wuxing(
                c["new_stroke"], args.wuxing, kangxi
            )
            chars = [ch for ch in chars if ch not in avoid_set]
            chars = [ch for ch in chars if ch not in surname_chars + given_chars]
            enriched.append({**c, "chars": chars[:args.limit_chars]})
    else:
        for c in output_combos:
            chars = _chars_by_stroke(c["new_stroke"], kangxi)
            chars = [ch for ch in chars if ch not in avoid_set]
            chars = [ch for ch in chars if ch not in surname_chars + given_chars]
            enriched.append({**c, "chars": chars[:args.limit_chars]})

    if args.json:
        print(json.dumps(enriched, ensure_ascii=False, indent=2))
    elif args.report:
        # Compute current name's wuge for context
        current_result = compute_wuge(surname_strokes, given_strokes)
        zodiac = args.zodiac or (zodiac_from_year(args.year) if args.year else None)
        current_zodiac_score = None
        if zodiac:
            zdata = load_zodiac_data(zodiac)
            current_zodiac_score = score_zodiac(given_chars, zdata)
            current_zodiac_score["zodiac"] = zodiac
        print(format_markdown_report(
            args.name, surname_chars, given_chars,
            surname_strokes, given_strokes,
            args.change, fixed_chars,
            current_result, enriched,
            args.grade, args.sancai_grade,
            args.wuxing, avoid_set, zodiac,
            current_zodiac_score,
        ))
    else:
        for c in enriched:
            print(f"\n  {c['new_stroke']:>2} 劃  三才:{'-'.join(c['三才'])} {c['三才吉凶']}")
            chars_preview = " ".join(c["chars"][:args.limit_chars])
            if not chars_preview:
                print("    (無候選字, 可能因 --wuxing 或 --avoid 過濾掉)")
            else:
                print(f"    {chars_preview}")


if __name__ == "__main__":
    main()
