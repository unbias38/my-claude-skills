"""反查既有名字的三才五格評估。

Usage:
    python analyze_name.py 張小明
    python analyze_name.py 歐陽修 --surname-len 2
    python analyze_name.py 王雪 --json    # machine-readable output
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from kangxi_lookup import load_table  # noqa: E402
from wuge import compute_wuge  # noqa: E402
from lucky_81 import info_of as lucky_info  # noqa: E402
from sancai_table import grade_of_sancai  # noqa: E402
from zodiac_score import (  # noqa: E402
    zodiac_from_year, load_zodiac_data, score_name as score_zodiac,
    ZODIAC_FILES,
)
from zodiac_explain import format_reference as zodiac_reference  # noqa: E402


def split_name(name: str, surname_len: int) -> tuple[list[str], list[str]]:
    if len(name) < surname_len + 1:
        raise ValueError(f"Name '{name}' too short for surname-len {surname_len}")
    return list(name[:surname_len]), list(name[surname_len:])


def lookup_strokes(chars: list[str], table: dict[str, int]) -> list[tuple[str, int | None]]:
    return [(ch, table.get(ch)) for ch in chars]


def overall_verdict(result: dict, ignore_tiange: bool = True) -> tuple[str, list[str]]:
    """Return (verdict, problems_list)."""
    keys = ["人格吉凶", "地格吉凶", "外格吉凶", "總格吉凶", "三才吉凶"]
    if not ignore_tiange:
        keys.insert(0, "天格吉凶")

    bad_keys = [k for k in keys if result.get(k) in ("凶", "大凶", "凶帶吉")]
    soso_keys = [k for k in keys if result.get(k) == "半吉"]
    good_keys = [k for k in keys if result.get(k) in ("大吉", "中吉")]

    if len(bad_keys) >= 3:
        verdict = "❌ 多格不利，建議改名"
    elif len(bad_keys) >= 1:
        problems = "、".join(k.replace("吉凶", "") for k in bad_keys)
        verdict = f"⚠️ {problems} 不利，建議檢視"
    elif len(soso_keys) >= 2:
        verdict = "🔸 中等，部分格半吉"
    elif len(good_keys) == len(keys):
        verdict = "✅ 全吉"
    else:
        verdict = "✅ 整體良好"

    return verdict, bad_keys


def format_human(name: str, surname_chars: list[str], given_chars: list[str],
                 surname_strokes: list[int], given_strokes: list[int],
                 result: dict, ignore_tiange: bool = True) -> str:
    lines = []
    lines.append(f"姓名：{name}")
    lines.append("")
    lines.append("筆劃 (康熙):")
    for ch, n in zip(surname_chars + given_chars, surname_strokes + given_strokes):
        role = "姓" if ch in surname_chars else "名"
        lines.append(f"  {ch} ({role})  {n} 劃")
    lines.append("")
    lines.append("五格:")
    for key in ["天格", "人格", "地格", "外格", "總格"]:
        n = result[key]
        grade, gname, gdesc = lucky_info(n)
        marker = "  (祖蔭, 不論吉凶)" if (key == "天格" and ignore_tiange) else ""
        lines.append(f"  {key}: {n:>2}  {grade:<6}  {gname}{marker}")
    lines.append("")
    sancai = result["三才"]
    sgrade = result["三才吉凶"]
    lines.append(f"三才: {sancai[0]}-{sancai[1]}-{sancai[2]}  {sgrade}")
    lines.append("")
    verdict, bad = overall_verdict(result, ignore_tiange)
    lines.append(f"整體評估: {verdict}")
    if bad:
        lines.append("")
        lines.append("不利的格:")
        for k in bad:
            lines.append(f"  - {k.replace('吉凶','')}: {result[k]}")
    return "\n".join(lines)


def _load_sancai_content() -> dict:
    """Load johnwu Sancai.json for richer 三才 explanations. Cached."""
    import json as _json
    from pathlib import Path as _Path
    path = _Path(__file__).parent.parent / "assets" / "Sancai.json"
    if not path.exists():
        return {}
    try:
        raw = _json.load(open(path, encoding="utf-8-sig"))
        return {k: v for k, v in raw.items() if v is not None}
    except Exception:
        return {}


def format_markdown_report(name: str, surname_chars: list[str], given_chars: list[str],
                           surname_strokes: list[int], given_strokes: list[int],
                           result: dict, zodiac_result: dict | None,
                           ignore_tiange: bool = True,
                           include_zodiac_reference: bool = False) -> str:
    """Markdown report — 適合貼 LINE/HackMD/Notion. 不含內部術語."""
    sancai_content_db = _load_sancai_content()
    lines = []
    lines.append(f"# 姓名評估：{name}")
    lines.append("")

    # Basic info
    info_parts = []
    if zodiac_result:
        info_parts.append(f"**生肖**：{zodiac_result['zodiac']}")
    info_parts.append(f"**康熙筆劃**：" + "　・　".join(
        f"{ch} {n} 劃" for ch, n in zip(surname_chars + given_chars,
                                        surname_strokes + given_strokes)
    ))
    lines.append("　・　".join(info_parts))
    lines.append("")

    # 五格 + 81 數理 (含含義)
    lines.append("## 三才五格")
    lines.append("")
    lines.append("| 格 | 數 | 吉凶 | 數名 | 含義 |")
    lines.append("|---|---|---|---|---|")
    for key in ["天格", "人格", "地格", "外格", "總格"]:
        n = result[key]
        grade, gname, gdesc = lucky_info(n)
        note = "（祖蔭，主判定不論）" if (key == "天格" and ignore_tiange) else ""
        lines.append(f"| {key}{note} | {n} | {grade} | {gname} | {gdesc} |")
    lines.append("")

    # 三才 + content
    sancai = result["三才"]
    sancai_key = "".join(sancai)
    sancai_full = sancai_content_db.get(sancai_key, {})
    lines.append(f"**三才**：{sancai[0]}-{sancai[1]}-{sancai[2]}　**{result['三才吉凶']}**")
    if sancai_full.get("content"):
        lines.append("")
        content = sancai_full["content"].strip()
        for para in content.split("\n"):
            if para.strip():
                lines.append(f"> {para.strip()}")
    lines.append("")

    # 整體評估
    verdict, bad = overall_verdict(result, ignore_tiange)
    lines.append("## 整體評估")
    lines.append("")
    lines.append(f"{verdict}")
    if bad:
        lines.append("")
        lines.append("**不利之處**：")
        for k in bad:
            grade = result[k]
            n_key = k.replace("吉凶", "")
            n_val = result.get(n_key)
            if n_val:
                _, gname, _ = lucky_info(n_val)
                lines.append(f"- {n_key}：{grade}（{n_val}「{gname}」）")
            else:
                lines.append(f"- {n_key}：{grade}")
        lines.append("")
        lines.append("> （待 LLM 對不利之處做延伸解讀：傳統姓名學如何詮釋這個數，性格與命理的具體影響，是否仍可用 / 建議改名 / 看綜合格局）")
    lines.append("")

    # 字義 / 聲調 / 台語 placeholder
    lines.append("## 字義 / 聲調 / 台語")
    lines.append("")
    lines.append("> （待 LLM 補上：每個名字字的字義、國語聲調搭配、台語讀音與諧音、整體字感、撞菜市場名與否）")
    lines.append("")

    # 生肖派
    if zodiac_result:
        lines.append("## 生肖派參考（附加，不影響上方主判定）")
        lines.append("")
        lines.append("| 字 | 宜/忌 | 加分 |")
        lines.append("|---|---|---|")
        for item in zodiac_result["chars"]:
            lines.append(f"| {item['char']} | {item['label']} | {item['score']:+d} |")
        total = zodiac_result["total_score"]
        tag = "偏吉" if total >= 1 else "偏忌" if total <= -1 else "中性"
        lines.append("")
        lines.append(f"**生肖總分**：{total:+d}（{tag}）")
        lines.append("")

        if include_zodiac_reference:
            from zodiac_explain import format_reference as _zref
            lines.append("### 生肖字根層級宜忌參考")
            lines.append("")
            lines.append("```")
            lines.append(_zref(zodiac_result["zodiac"]))
            lines.append("```")
            lines.append("")

    # 結語 / 適用建議 placeholder
    lines.append("## 評語與建議")
    lines.append("")
    lines.append("> （待 LLM 補綜合評語：")
    lines.append("> - 是否建議使用此名（可用 / 慎用 / 建議改）")
    lines.append("> - 主要優勢（哪幾格吉、字義、聲韻）")
    lines.append("> - 主要疑慮（如有不利處，可否被其他格抵消）")
    lines.append("> - 若考慮改名，建議改哪個位置）")
    lines.append("")

    # 免責聲明 (per references/taiwan-naming.md § 8 — no internal jargon)
    lines.append("---")
    lines.append("")
    lines.append("## 說明")
    lines.append("")
    lines.append("本評估以康熙筆劃為基準，依傳統姓名學的三才五格計算。")
    lines.append("")
    lines.append("- 三才五格僅是傳統姓名學六大派之一，預測準確度約 56.6%")
    if zodiac_result:
        lines.append("- 生肖派宜忌僅為附加參考，因派別爭議較大未列入主判定")
    lines.append("- 天格代表祖蔭，由姓氏決定不可改，主判定不納入")
    lines.append("- 重大命名（新生兒、改名）建議由專業命理師最後確認")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="完整姓名 (繁體), e.g., 張小明 or 歐陽修")
    ap.add_argument("--surname-len", type=int, default=1, choices=[1, 2],
                    help="姓氏字數 (1=單姓, 2=複姓如歐陽)")
    ap.add_argument("--include-tiange", action="store_true",
                    help="納入天格吉凶判定 (預設排除, 因祖蔭不可改)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--year", type=int,
                   help="西元出生年, 加上後會額外輸出生肖派加分 (soft signal)")
    g.add_argument("--zodiac", choices=list(ZODIAC_FILES.keys()),
                   help="直接指定生肖 (1-2月初出生用此 override)")
    ap.add_argument("--explain-zodiac", action="store_true",
                    help="加印該生肖的部首層級宜忌參考 (需配 --year 或 --zodiac)")
    ap.add_argument("--json", action="store_true",
                    help="輸出 JSON 格式")
    ap.add_argument("--report", action="store_true",
                    help="輸出可分享的 Markdown 報告 (適合貼 LINE/HackMD/Notion)")
    args = ap.parse_args()

    surname_chars, given_chars = split_name(args.name, args.surname_len)
    table = load_table()

    surname_lookups = lookup_strokes(surname_chars, table)
    given_lookups = lookup_strokes(given_chars, table)

    not_found = [ch for ch, n in surname_lookups + given_lookups if n is None]
    if not_found:
        print(f"⚠️ 找不到康熙筆劃: {' '.join(not_found)}", file=sys.stderr)
        print("(該字不在 Unicode 11.0 康熙字典範圍, 可能是異體字或新字)", file=sys.stderr)
        sys.exit(1)

    surname_strokes = [n for _, n in surname_lookups]
    given_strokes = [n for _, n in given_lookups]

    if len(given_strokes) not in (1, 2):
        print(f"⚠️ 目前僅支援單字或雙字名 (你的名為 {len(given_strokes)} 字)",
              file=sys.stderr)
        sys.exit(1)

    result = compute_wuge(surname_strokes, given_strokes)
    verdict, bad = overall_verdict(result, ignore_tiange=not args.include_tiange)

    # Optional zodiac soft signal
    zodiac_result = None
    if args.year or args.zodiac:
        zodiac = args.zodiac or zodiac_from_year(args.year)
        zdata = load_zodiac_data(zodiac)
        zodiac_result = score_zodiac(given_chars, zdata)
        zodiac_result["zodiac"] = zodiac

    if args.json:
        out = {
            "name": args.name,
            "surname": {"chars": surname_chars, "strokes": surname_strokes},
            "given": {"chars": given_chars, "strokes": given_strokes},
            **result,
            "verdict": verdict,
            "bad_keys": bad,
        }
        if zodiac_result:
            out["zodiac"] = zodiac_result
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.report:
        print(format_markdown_report(
            args.name, surname_chars, given_chars,
            surname_strokes, given_strokes,
            result, zodiac_result,
            ignore_tiange=not args.include_tiange,
            include_zodiac_reference=args.explain_zodiac,
        ))
    else:
        print(format_human(args.name, surname_chars, given_chars,
                           surname_strokes, given_strokes,
                           result, ignore_tiange=not args.include_tiange))
        if zodiac_result:
            print()
            print(f"生肖派 ({zodiac_result['zodiac']}) — 軟性參考, 不影響上方主判定:")
            for item in zodiac_result["chars"]:
                mark = {"宜": "✅", "忌": "❌", "中性": "・"}[item["label"]]
                print(f"  {mark} {item['char']}  {item['label']}  ({item['score']:+d})")
            total = zodiac_result["total_score"]
            tag = "偏吉" if total >= 1 else "偏忌" if total <= -1 else "中性"
            print(f"  生肖總分: {total:+d}  ({tag})")
            if args.explain_zodiac:
                print()
                print(zodiac_reference(zodiac_result["zodiac"]))


if __name__ == "__main__":
    main()
