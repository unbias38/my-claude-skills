"""Brute-force search for auspicious (n1_strokes, n2_strokes) given-name combos.

Iterate stroke ranges, compute 五格 + 三才 via wuge.compute_wuge,
filter by minimum grade across all 6 outputs (5格 + 三才).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from wuge import compute_wuge  # noqa: E402
from lucky_81 import GRADE_RANK  # noqa: E402

MIN_STROKE = 1
MAX_STROKE = 30   # 30+ 大多為冷僻字, 不適人名


def search(surname_strokes: list[int],
           min_grade: str = "大吉",
           sancai_min: str | None = None,
           include_tiange: bool = False) -> list[dict]:
    """Return all (n1, n2) combos meeting the grade thresholds.

    By default 天格 is excluded from the cutoff (代表祖蔭, 不可改 — 命名師慣例).
    Pass include_tiange=True to include it.

    人格 / 地格 / 總格 are the 主三格 and must meet `min_grade`.
    外格 is also checked at `min_grade`.
    三才 must meet `sancai_min` (defaults to `min_grade`).
    """
    sancai_min = sancai_min or min_grade
    threshold = GRADE_RANK[min_grade]
    sancai_threshold = GRADE_RANK[sancai_min]

    checked_keys = ["人格吉凶", "地格吉凶", "外格吉凶", "總格吉凶"]
    if include_tiange:
        checked_keys.insert(0, "天格吉凶")

    results = []
    for n1 in range(MIN_STROKE, MAX_STROKE + 1):
        for n2 in range(MIN_STROKE, MAX_STROKE + 1):
            r = compute_wuge(surname_strokes, [n1, n2])
            grades = [r[k] for k in checked_keys]
            if not all(GRADE_RANK.get(g, -1) >= threshold for g in grades):
                continue
            if GRADE_RANK.get(r["三才吉凶"], -1) < sancai_threshold:
                continue
            results.append({
                "n1": n1, "n2": n2,
                "三才": r["三才"],
                "三才吉凶": r["三才吉凶"],
                "五格": [r["天格"], r["人格"], r["地格"], r["外格"], r["總格"]],
                "天格吉凶": r["天格吉凶"],
                "人格吉凶": r["人格吉凶"],
                "地格吉凶": r["地格吉凶"],
                "外格吉凶": r["外格吉凶"],
                "總格吉凶": r["總格吉凶"],
            })
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--surname-strokes", required=True,
                    help="Comma-separated, e.g., '11' or '7,4'")
    ap.add_argument("--grade", default="大吉",
                    choices=["大吉", "中吉", "半吉"],
                    help="Minimum grade for all 5 五格 (default 大吉)")
    ap.add_argument("--sancai-grade", default=None,
                    choices=["大吉", "中吉", "半吉"],
                    help="Minimum 三才 grade (default same as --grade)")
    ap.add_argument("--include-tiange", action="store_true",
                    help="Also enforce 天格 grade (default: 排除天格, 因為祖蔭不可改)")
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()

    surname = [int(x) for x in args.surname_strokes.split(",")]
    results = search(surname, args.grade, args.sancai_grade,
                     include_tiange=args.include_tiange)
    print(json.dumps(results[:args.limit], ensure_ascii=False, indent=2))
    print(f"\n# Found {len(results)} combos (showing first {min(args.limit, len(results))})",
          file=sys.stderr)


if __name__ == "__main__":
    main()
