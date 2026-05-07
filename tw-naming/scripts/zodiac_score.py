"""生肖派姓名學評分（soft signal，不過濾，僅加分排序）。

設計原則：
- 三才五格 = hard filter（剪枝）
- 生肖派 = soft signal（排序）

理由：生肖派在台灣命理界爭議比三才五格大，硬過濾會讓候選空間崩塌。
此腳本回傳每個字的 +1/0/-1 分數，由上層決定如何使用。

Data source: johnwu1114/chinese-name (zodiac/N_animal.json)
資料是字級對照表（不是字根級），給定一個字直接查 better/worse 列表。

Caveat:
- 生肖以「立春」為界 (約 2/4)，不是 1/1。
- 此模組以 西元年 % 12 推算，邊界月份 (1月、2月初) 的人需手動 --zodiac override。
"""

import argparse
import json
import sys
from pathlib import Path

ASSETS = Path(__file__).parent.parent / "assets" / "zodiac"

# 生肖檔名對照
ZODIAC_FILES = {
    "鼠": "1_rat", "牛": "2_ox", "虎": "3_tiger", "兔": "4_rabbit",
    "龍": "5_dragon", "蛇": "6_snake", "馬": "7_horse", "羊": "8_goat",
    "猴": "9_monkey", "雞": "10_rooster", "狗": "11_dog", "豬": "12_pig",
}

# 西元年 % 12 → 生肖
YEAR_MOD_TO_ZODIAC = {
    4: "鼠", 5: "牛", 6: "虎", 7: "兔", 8: "龍", 9: "蛇",
    10: "馬", 11: "羊", 0: "猴", 1: "雞", 2: "狗", 3: "豬",
}


def zodiac_from_year(year: int) -> str:
    return YEAR_MOD_TO_ZODIAC[year % 12]


def load_zodiac_data(zodiac: str) -> dict:
    """Return {'better': set[str], 'worse': set[str]}."""
    fname = ZODIAC_FILES.get(zodiac)
    if not fname:
        raise ValueError(f"Unknown zodiac: {zodiac}")
    raw = json.load(open(ASSETS / f"{fname}.json", encoding="utf-8-sig"))
    # better/worse 各自是 {_3: [字], _4: [字], ...} 按筆劃分組
    flatten = lambda d: {ch for chars in d.values() for ch in chars}
    return {
        "type": raw["type"],
        "better": flatten(raw.get("better", {})),
        "worse":  flatten(raw.get("worse",  {})),
    }


def score_name(name_chars: list[str], zodiac_data: dict) -> dict:
    """Return {chars: [{char, score, label}], total_score}."""
    better = zodiac_data["better"]
    worse = zodiac_data["worse"]
    breakdown = []
    total = 0
    for ch in name_chars:
        if ch in better:
            score, label = 1, "宜"
        elif ch in worse:
            score, label = -1, "忌"
        else:
            score, label = 0, "中性"
        breakdown.append({"char": ch, "score": score, "label": label})
        total += score
    return {"chars": breakdown, "total_score": total}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="姓名 (繁體, 含姓), e.g., 張小明")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--year", type=int,
                   help="西元出生年, e.g., 2026")
    g.add_argument("--zodiac", choices=list(ZODIAC_FILES.keys()),
                   help="直接指定生肖 (1-2月初出生者建議用此 override)")
    ap.add_argument("--include-surname", action="store_true",
                    help="姓也納入評分 (預設只評名)")
    ap.add_argument("--surname-len", type=int, default=1, choices=[1, 2])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    zodiac = args.zodiac or zodiac_from_year(args.year)
    data = load_zodiac_data(zodiac)

    if args.include_surname:
        chars_to_score = list(args.name)
    else:
        chars_to_score = list(args.name[args.surname_len:])

    result = score_name(chars_to_score, data)
    result["zodiac"] = zodiac
    result["name"] = args.name

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"姓名: {args.name}   生肖: {zodiac}")
        for item in result["chars"]:
            mark = {"宜": "✅", "忌": "❌", "中性": "・"}[item["label"]]
            print(f"  {mark} {item['char']}  {item['label']}  ({item['score']:+d})")
        print(f"\n生肖總分: {result['total_score']:+d}")
        if result["total_score"] >= 1:
            print("→ 生肖派偏吉")
        elif result["total_score"] <= -1:
            print("→ 生肖派偏忌")
        else:
            print("→ 中性 (無加分也無扣分)")


if __name__ == "__main__":
    main()
