"""List characters by Kangxi stroke count, optionally filtered by 五行.

Data sources:
1. assets/kangxi-strokecount.csv — authoritative for stroke counts (Unicode 11.0).
2. assets/ChineseCharacters.json — clean 繁體 (stroke, wuxing) dictionary
   (johnwu1114/chinese-name).

Behavior:
- For --strokes only: read CSV, return all chars with that stroke count.
- For --strokes + --wuxing: read ChineseCharacters.json directly; verify each
  candidate against the Kangxi CSV (catches data drift).
"""

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from wuxing_lookup import chars_for as _wuxing_chars_for  # noqa: E402

ASSETS = Path(__file__).parent.parent / "assets"

WUXING_KEYS = ["金", "木", "水", "火", "土"]


def load_kangxi_table() -> dict[str, int]:
    table = {}
    with (ASSETS / "kangxi-strokecount.csv").open(encoding="utf-8-sig", newline="") as f:
        for _ in range(4):
            next(f)
        for row in csv.DictReader(f):
            try:
                table[row["Character"]] = int(row["Strokes"])
            except (ValueError, KeyError):
                continue
    return table


def chars_by_stroke(strokes: int, kangxi_table: dict[str, int]) -> list[str]:
    return [ch for ch, s in kangxi_table.items() if s == strokes]


def chars_by_stroke_and_wuxing(strokes: int, wuxing: str,
                               kangxi_table: dict[str, int]) -> tuple[list[str], list[str]]:
    """Return (verified繁體chars, warnings).

    Each candidate from ChineseCharacters.json is cross-checked against the
    Kangxi CSV; mismatches are dropped (typically 5-15% per bucket).
    """
    warnings = []
    bucket = _wuxing_chars_for(strokes, wuxing)
    if not bucket:
        warnings.append(f"No candidates at {strokes} 劃 五行={wuxing}")
        return [], warnings
    out, seen = [], set()
    for ch in bucket:
        actual = kangxi_table.get(ch)
        if actual is None:
            warnings.append(f"{ch}: not in Kangxi table, skipped")
            continue
        if actual != strokes:
            warnings.append(f"{ch}: stroke mismatch ({actual} vs {strokes}), skipped")
            continue
        if ch not in seen:
            seen.add(ch)
            out.append(ch)
    return out, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strokes", type=int, required=True)
    ap.add_argument("--wuxing", choices=WUXING_KEYS)
    ap.add_argument("--avoid", default="",
                    help="避諱字清單 (連寫即可, e.g., '明芳華')")
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args()
    avoid_set = set(args.avoid)

    kangxi = load_kangxi_table()

    if args.wuxing is None:
        chars = chars_by_stroke(args.strokes, kangxi)
        if avoid_set:
            chars = [ch for ch in chars if ch not in avoid_set]
        print(json.dumps(chars[:args.limit], ensure_ascii=False))
        print(f"# {len(chars)} chars with {args.strokes} strokes (Kangxi)"
              + (f", excluded {len(avoid_set)} 避諱字" if avoid_set else ""),
              file=sys.stderr)
        return

    chars, warnings = chars_by_stroke_and_wuxing(args.strokes, args.wuxing, kangxi)
    if avoid_set:
        chars = [ch for ch in chars if ch not in avoid_set]
    print(json.dumps(chars[:args.limit], ensure_ascii=False))
    print(f"# {len(chars)} chars at {args.strokes}劃 五行={args.wuxing}",
          file=sys.stderr)
    for w in warnings[:5]:
        print(f"# {w}", file=sys.stderr)
    if len(warnings) > 5:
        print(f"# ... +{len(warnings) - 5} more warnings", file=sys.stderr)


if __name__ == "__main__":
    main()
