"""Look up 康熙筆劃 for a Traditional Chinese character.

Data source: assets/kangxi-strokecount.csv (breezyreeds/kangxi-strokecount, MIT).
The CSV starts with 4 preamble lines (3 license + 1 blank), then a column header row:
    CodePoint,Value,Character,Strokes
"""

import csv
import sys
from pathlib import Path

ASSETS = Path(__file__).parent.parent / "assets"
CSV_PATH = ASSETS / "kangxi-strokecount.csv"


def load_table():
    """Return dict: {character: stroke_count}."""
    table = {}
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        # skip the 4-line MIT header preamble (3 license + 1 blank)
        for _ in range(4):
            next(f)
        reader = csv.DictReader(f)
        for row in reader:
            ch = row.get("Character")
            strokes = row.get("Strokes")
            if ch and strokes:
                try:
                    table[ch] = int(strokes)
                except ValueError:
                    continue
    return table


def lookup(char: str, table=None) -> int | None:
    table = table if table is not None else load_table()
    return table.get(char)


def main():
    if len(sys.argv) < 2:
        print("Usage: python kangxi_lookup.py <字> [<字> ...]", file=sys.stderr)
        sys.exit(1)
    table = load_table()
    for arg in sys.argv[1:]:
        for ch in arg:
            n = lookup(ch, table)
            if n is None:
                print(f"{ch}\tNOT_FOUND")
            else:
                print(f"{ch}\t{n}")


if __name__ == "__main__":
    main()
