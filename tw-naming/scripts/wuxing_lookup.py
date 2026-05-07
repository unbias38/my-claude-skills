"""(筆劃, 五行) → 繁體候選字 字典查詢，從 ChineseCharacters.json 載入。

This replaces the buggy qiming wuxing_dict_fanti.json which mixed simplified
and traditional. The new source (johnwu1114/chinese-name) is properly 繁體 +
康熙筆劃.

Usage:
    from wuxing_lookup import chars_for, all_buckets

    chars_for(14, "火")   # → ["熬", "暢", "塵", "逞", ...]
    all_buckets()         # → list of (stroke, wuxing) tuples available
"""

import json
from pathlib import Path

ASSETS = Path(__file__).parent.parent / "assets"

_cache: dict[tuple[int, str], list[str]] | None = None


def _load() -> dict[tuple[int, str], list[str]]:
    global _cache
    if _cache is not None:
        return _cache
    raw = json.load(open(ASSETS / "ChineseCharacters.json", encoding="utf-8-sig"))
    out: dict[tuple[int, str], list[str]] = {}
    for entry in raw:
        key = (entry["draw"], entry["fiveEle"])
        # dedupe + preserve order
        seen, uniq = set(), []
        for ch in entry["chars"]:
            if ch not in seen:
                seen.add(ch)
                uniq.append(ch)
        out[key] = uniq
    _cache = out
    return out


def chars_for(stroke: int, wuxing: str) -> list[str]:
    """Return list of 繁體 chars with given Kangxi stroke + 五行."""
    return _load().get((stroke, wuxing), [])


def all_buckets() -> list[tuple[int, str]]:
    return list(_load().keys())


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        stroke = int(sys.argv[1])
        wuxing = sys.argv[2]
        chars = chars_for(stroke, wuxing)
        print(f"# {len(chars)} chars at {stroke} 劃 {wuxing}")
        print(" ".join(chars))
    else:
        buckets = all_buckets()
        print(f"# {len(buckets)} (stroke, wuxing) buckets")
        # show coverage matrix
        strokes = sorted({s for s, _ in buckets})
        wuxings = ["金", "木", "水", "火", "土"]
        print(f"  劃 |" + " ".join(f"{w:>4}" for w in wuxings))
        for s in strokes:
            row = [f"{len(chars_for(s, w)):>4}" for w in wuxings]
            print(f"  {s:>2} |" + " ".join(row))
