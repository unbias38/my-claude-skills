"""對一組候選名產出完整 generate-mode 評估報告。

把 skill 內所有資料層內容強制串進報告：
- 康熙筆劃 (kangxi_lookup)
- 五格 + 三才 + 吉凶 + **81 數名稱與含義** (lucky_81)
- 三才完整解釋 content (Sancai.json)
- 生肖派加分 (zodiac_score)
- 生肖字根層級宜忌參考 (zodiac_explain)
- 父母避諱檢查狀態
- 天格祖蔭明確標註
- 完整 user-facing 免責聲明 (依 taiwan-naming.md § 8)

LLM 只需要再補：字義 / 聲調 / 台語檢音 / 在地風格 / 取捨建議。

Usage:
    python score_candidates.py 蔡明芳 蔡沛芬 蔡沛君 --year 1956
    python score_candidates.py 蔡明芳 蔡沛芬 --year 1956 --xiyongshen 水,木 --avoid 芳華
    python score_candidates.py --names-file candidates.txt --year 1956 --output report.md
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from kangxi_lookup import load_table  # noqa: E402
from wuge import compute_wuge  # noqa: E402
from lucky_81 import info_of as lucky_info  # noqa: E402
from zodiac_score import (  # noqa: E402
    zodiac_from_year, load_zodiac_data, score_name as score_zodiac, ZODIAC_FILES,
)
from report_common import (  # noqa: E402
    load_sancai_content, kangxi_line, wuge_table_md, sancai_block_md,
    zodiac_tag, zodiac_reference_md, disclaimer_md,
)


def analyze_one(name: str, surname_len: int, kangxi: dict,
                sancai_content: dict, year: int | None = None,
                zodiac_override: str | None = None) -> dict | None:
    """Return all data points for a single candidate name."""
    surname_chars = list(name[:surname_len])
    given_chars = list(name[surname_len:])
    surname_strokes = [kangxi.get(c) for c in surname_chars]
    given_strokes = [kangxi.get(c) for c in given_chars]
    if any(s is None for s in surname_strokes + given_strokes):
        missing = [c for c, s in zip(surname_chars + given_chars,
                                      surname_strokes + given_strokes) if s is None]
        return {"name": name, "error": f"找不到康熙筆劃: {' '.join(missing)}"}

    result = compute_wuge(surname_strokes, given_strokes)

    格_info = {}
    for key in ["天格", "人格", "地格", "外格", "總格"]:
        n = result[key]
        grade, gname, gdesc = lucky_info(n)
        格_info[key] = {"n": n, "grade": grade, "name": gname, "desc": gdesc}

    sancai_key = "".join(result["三才"])
    sancai_full = sancai_content.get(sancai_key, {})

    zodiac_data = None
    if year or zodiac_override:
        z = zodiac_override or zodiac_from_year(year)
        zdata = load_zodiac_data(z)
        zodiac_data = score_zodiac(given_chars, zdata)
        zodiac_data["zodiac"] = z

    return {
        "name": name,
        "surname_chars": surname_chars,
        "given_chars": given_chars,
        "surname_strokes": surname_strokes,
        "given_strokes": given_strokes,
        "格": 格_info,
        "三才": result["三才"],
        "三才吉凶": result["三才吉凶"],
        "三才content": sancai_full.get("content", ""),
        "zodiac": zodiac_data,
    }


def format_report(data_list: list[dict], header: dict) -> str:
    """Build complete markdown report."""
    lines: list[str] = []

    # === Header ===
    lines.append(f"# {header['title']}")
    lines.append("")
    info_lines = []
    if header.get("birth"):
        info_lines.append(f"**生辰**：{header['birth']}")
    if header.get("zodiac"):
        info_lines.append(f"**生肖**：{header['zodiac']}")
    if header.get("xiyongshen"):
        info_lines.append(f"**喜用神**：{header['xiyongshen']}（粗估，非命理師判斷）")
    avoid = header.get("avoid")
    info_lines.append(f"**避諱字**：{avoid if avoid else '未提供，候選未過濾父母 / 祖輩用字'}")
    lines.append("　・　".join(info_lines))
    lines.append("")

    # === A 段：快速摘要 ===
    lines.append("## 快速摘要")
    lines.append("")
    lines.append("| 候選名 | 三才 | 主判（人/地/外/總） | 生肖加分 |")
    lines.append("|---|---|---|---|")
    for d in data_list:
        if d.get("error"):
            lines.append(f"| {d['name']} | — | — | ⚠️ {d['error']} |")
            continue
        sancai = "-".join(d["三才"]) + f" {d['三才吉凶']}"
        mains = [d["格"][k]["grade"] for k in ["人格", "地格", "外格", "總格"]]
        z = d.get("zodiac")
        z_str = f"{z['total_score']:+d}（{z['zodiac']}）" if z else "—"
        lines.append(f"| {d['name']} | {sancai} | {' / '.join(mains)} | {z_str} |")
    lines.append("")

    # === 各候選詳情 ===
    lines.append("## 各候選名詳情")
    lines.append("")
    for i, d in enumerate(data_list, 1):
        if d.get("error"):
            lines.append(f"### {i}. {d['name']}　⚠️ {d['error']}")
            lines.append("")
            continue
        lines.append(f"### {i}. {d['name']}")
        lines.append("")

        all_chars = d["surname_chars"] + d["given_chars"]
        all_strokes = d["surname_strokes"] + d["given_strokes"]
        lines.append(kangxi_line(all_chars, all_strokes))
        lines.append("")

        lines.append("**五格 + 81 數理**")
        lines.append("")
        lines.extend(wuge_table_md({k: v["n"] for k, v in d["格"].items()}))
        lines.append("")

        lines.extend(sancai_block_md(d["三才"], d["三才吉凶"],
                                     d.get("三才content", "")))
        lines.append("")

        if d.get("zodiac"):
            z = d["zodiac"]
            lines.append(f"**生肖派加分（{z['zodiac']}）**")
            lines.append("")
            for item in z["chars"]:
                mark = {"宜": "✅", "忌": "❌", "中性": "・"}[item["label"]]
                lines.append(f"- {mark} {item['char']}　{item['label']}　({item['score']:+d})")
            total = z["total_score"]
            lines.append(f"- **總分 {total:+d}（{zodiac_tag(total)}）**")
            lines.append("")

        lines.append("**字義 / 聲調 / 台語檢音 / 在地風格**")
        lines.append("")
        lines.append("> （待 LLM 依在地語感補上：字義解釋、國語聲調搭配、台語讀音與諧音、撞菜市場名檢查、所屬年代風格評估）")
        lines.append("")
        lines.append("---")
        lines.append("")

    # === 生肖字根參考 ===
    if header.get("zodiac"):
        lines.extend(zodiac_reference_md(header["zodiac"]))

    # === 取捨建議 placeholder ===
    lines.append("## 取捨建議")
    lines.append("")
    lines.append("> （待 LLM 依字義 / 聲調 / 台語諧音 / 在地語感歸類，至少給三條：")
    lines.append("> - 若優先 X，建議 ___")
    lines.append("> - 若優先 Y，建議 ___")
    lines.append("> - 若優先 Z，建議 ___）")
    lines.append("")

    # === 免責（依 taiwan-naming.md § 8）===
    has_zodiac = bool(header.get("zodiac"))
    intro = ("本評估以康熙筆劃為基準，依傳統姓名學的三才五格計算，並參考生肖派宜忌作為附加資訊。"
             if has_zodiac else
             "本評估以康熙筆劃為基準，依傳統姓名學的三才五格計算。")
    lines.extend(disclaimer_md(
        intro,
        include_zodiac=has_zodiac,
        include_xiyongshen=bool(header.get("xiyongshen")),
        include_avoid_note=True,
    ))

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*", help="候選姓名 (繁體, 含姓), e.g., 蔡明芳 蔡沛芬")
    ap.add_argument("--names-file", help="從檔案讀候選名 (一行一個)")
    ap.add_argument("--surname-len", type=int, default=1, choices=[1, 2])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--year", type=int, help="西元出生年, 推算生肖")
    g.add_argument("--zodiac", choices=list(ZODIAC_FILES.keys()))
    ap.add_argument("--birth", help="顯示用生辰字串, e.g., '1956/08/31 09:23'")
    ap.add_argument("--xiyongshen", help="喜用神, e.g., '水,木'")
    ap.add_argument("--avoid", help="父母 / 祖輩避諱字串, e.g., '芳華'")
    ap.add_argument("--title", default=None, help="報告標題")
    ap.add_argument("--output", help="輸出檔路徑 (省略則印到 stdout)")
    args = ap.parse_args()

    names = list(args.names)
    if args.names_file:
        names.extend(line.strip() for line in open(args.names_file, encoding="utf-8")
                     if line.strip())
    if not names:
        ap.error("至少需要一個候選名 (positional 或 --names-file)")

    kangxi = load_table()
    sancai_content = load_sancai_content()

    data_list = [
        analyze_one(n, args.surname_len, kangxi, sancai_content,
                    year=args.year, zodiac_override=args.zodiac)
        for n in names
    ]

    zodiac = args.zodiac or (zodiac_from_year(args.year) if args.year else None)
    title = args.title or f"{names[0][:args.surname_len]}姓命名候選"
    header = {
        "title": title,
        "birth": args.birth,
        "zodiac": zodiac,
        "xiyongshen": args.xiyongshen,
        "avoid": args.avoid,
    }

    report = format_report(data_list, header)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"# 報告已存到 {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
