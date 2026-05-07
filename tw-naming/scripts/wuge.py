"""Compute 五格 (天/人/地/外/總) and 三才 from surname + given-name strokes.

STUB — needs implementation. Reference formulas:

For a 1-character surname (s) + 2-character given name (n1, n2):
    天格 = s + 1            (single surname adds an imaginary 1)
    人格 = s + n1
    地格 = n1 + n2
    外格 = n2 + 1            (single surname adds an imaginary 1 here too)
    總格 = s + n1 + n2

For a 2-character surname (s1, s2) + 2-character given name (n1, n2):
    天格 = s1 + s2
    人格 = s2 + n1
    地格 = n1 + n2
    外格 = s1 + n2
    總格 = s1 + s2 + n1 + n2

三才 = (天格 五行, 人格 五行, 地格 五行)
    五行 derivation: take the last digit of the 格 number.
        1, 2 → 木
        3, 4 → 火
        5, 6 → 土
        7, 8 → 金
        9, 0 → 水
    (數字 > 10 時看尾數: e.g., 11 → 1 → 木; 24 → 4 → 火)

吉凶判定 needs two tables:
    - 81 靈動數 → 吉/凶 grade (each 格 individually graded)
    - 三才 (125 combos) → 大吉/吉/凶/大凶 (see references/sancai-table.md)

Final grade = combine all 五格 grades + 三才 grade. Common rule:
    五格全吉 + 三才大吉 = 大吉
    任一格凶 OR 三才凶 = 排除
"""

import argparse
import json
import sys
from pathlib import Path

# Allow running this script directly OR being imported as a module.
sys.path.insert(0, str(Path(__file__).parent))
from lucky_81 import grade_of as _lucky_grade  # noqa: E402
from sancai_table import grade_of_sancai as _sancai_grade  # noqa: E402


def stroke_to_wuxing(n: int) -> str:
    last = n % 10
    return {1: "木", 2: "木", 3: "火", 4: "火", 5: "土",
            6: "土", 7: "金", 8: "金", 9: "水", 0: "水"}[last]


def compute_wuge(surname: list[int], given: list[int]) -> dict:
    """surname and given are lists of stroke counts (1-2 entries each).

    Supported configs:
        單姓 + 單名 (1+1): e.g. 林森
        單姓 + 雙名 (1+2): e.g. 張小明 (most common)
        複姓 + 單名 (2+1): e.g. 歐陽修
        複姓 + 雙名 (2+2): e.g. 司馬相如
    """
    if len(surname) == 1 and len(given) == 1:
        s = surname[0]
        n1 = given[0]
        tian = s + 1
        ren = s + n1
        di = n1 + 1
        wai = 1 + 1   # both ends imaginary
        zong = s + n1
    elif len(surname) == 1 and len(given) == 2:
        s = surname[0]
        n1, n2 = given
        tian = s + 1
        ren = s + n1
        di = n1 + n2
        wai = n2 + 1
        zong = s + n1 + n2
    elif len(surname) == 2 and len(given) == 1:
        s1, s2 = surname
        n1 = given[0]
        tian = s1 + s2
        ren = s2 + n1
        di = n1 + 1
        wai = s1 + 1
        zong = s1 + s2 + n1
    elif len(surname) == 2 and len(given) == 2:
        s1, s2 = surname
        n1, n2 = given
        tian = s1 + s2
        ren = s2 + n1
        di = n1 + n2
        wai = s1 + n2
        zong = s1 + s2 + n1 + n2
    else:
        raise NotImplementedError(
            f"Unsupported: surname={len(surname)} chars + given={len(given)} chars"
        )

    sancai = (
        stroke_to_wuxing(tian),
        stroke_to_wuxing(ren),
        stroke_to_wuxing(di),
    )
    return {
        "天格": tian, "人格": ren, "地格": di,
        "外格": wai, "總格": zong,
        "三才": sancai,
        "天格吉凶": _lucky_grade(tian),
        "人格吉凶": _lucky_grade(ren),
        "地格吉凶": _lucky_grade(di),
        "外格吉凶": _lucky_grade(wai),
        "總格吉凶": _lucky_grade(zong),
        "三才吉凶": _sancai_grade(*sancai),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--surname-strokes", required=True,
                    help="Comma-separated, e.g., '11' or '7,4' for 司馬")
    ap.add_argument("--name-strokes", required=True,
                    help="Comma-separated, e.g., '4,12'")
    args = ap.parse_args()
    surname = [int(x) for x in args.surname_strokes.split(",")]
    given = [int(x) for x in args.name_strokes.split(",")]
    result = compute_wuge(surname, given)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
