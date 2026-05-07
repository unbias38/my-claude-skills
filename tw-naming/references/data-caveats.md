# Bundled Data Caveats

## `assets/kangxi-strokecount.csv`

- **Source**: [breezyreeds/kangxi-strokecount](https://github.com/breezyreeds/kangxi-strokecount) (MIT License, © 2018 Kawai Lo)
- **Coverage**: 63,696 漢字 from Unicode 11.0.0
- **Format**: 4 preamble lines (3 license + 1 blank) → header `CodePoint,Value,Character,Strokes` → data rows
- **Encoding**: UTF-8 with BOM, Windows CRLF
- **Trust level**: ✅ **Authoritative**. Use this for all 筆劃 lookups.
- **Verified examples** (from upstream README):
  - 華 = 14 劃 (艸部 6 + 8) ✅
  - 張 = 11、陳 = 16、王 = 4、李 = 7 — all verified

## `assets/ChineseCharacters.json` (preferred 五行 字典)

- **Source**: [johnwu1114/chinese-name](https://github.com/johnwu1114/chinese-name) (no LICENSE — see notes below)
- **Format**: list of `{draw: int, fiveEle: 五行, chars: "字串"}`
- **Coverage**: 139 buckets, 1-30 劃 × 5 五行
- **Trust level**: ✅ **High** — 繁體 + 康熙筆劃，已 cross-validate against `kangxi-strokecount.csv`.
- **Verified examples**:
  - 14 劃 火: 104 chars — 約 90 個通過 Kangxi 校驗保留
  - About 14 chars per bucket fail Kangxi cross-check (johnwu's stroke count differs from breezyreeds Kangxi by ±1-3); these are auto-rejected.
- This is the **default source** for `chars_by_stroke.py`.

## `assets/zodiac/*.json` (12 zodiac taboo tables)

- **Source**: [johnwu1114/chinese-name](https://github.com/johnwu1114/chinese-name) (same license caveat)
- **Format**: `{type: "鼠", better: {_3: [chars], _4: [chars], ...}, worse: {...}}`
- **Coverage**: 12 zodiac files, ~250-400 chars each in better+worse combined
- **Trust level**: ✅ for what it claims (one school's interpretation). **Soft signal only** — use as add-on score, not hard filter. See `references/zodiac-school.md`.

## `assets/EightyOne.json` & `assets/Sancai.json` (cross-reference, NOT primary)

- **Source**: same johnwu1114 repo
- **Use**: cross-validation of our `lucky_81.py` and `sancai_table.py`. **Not loaded by any script** by default.
- **Cross-validation results**:
  - **EightyOne**: 5/81 (6%) coarse-level disagreements, all in 「凶帶吉/吉帶凶」 edge cases (49, 50, 57, 61, 80). Both versions can be considered valid; we kept ours.
  - **Sancai**: 41/125 (33%) coarse-level disagreements. Most are granularity differences (johnwu has 「凶多於吉」「吉凶爭衡」which we collapse to 「凶」). A few are real disagreements (e.g., 水木土: johnwu=大吉, ours=凶) — these reflect school differences. We retain our version for self-consistency.
- These files contain richer `content` text (long descriptive prose for each entry) which could be loaded for narrative output in future iterations.

## License caveat (johnwu1114 data)

The upstream `johnwu1114/chinese-name` repo has **no LICENSE file** as of fetch date.
Implications:
- For personal/private use within this skill: low risk
- For redistribution / commercial use: **must contact author** or replace with own data
- Author description: "免費的取名程式" (free naming program), suggests permissive intent but not legally binding
- See `assets/`'s individual data files; if you republish this skill publicly, consider:
  1. Reaching out to johnwu1114 for explicit permission
  2. Replacing the data with self-curated equivalents
  3. Using only `kangxi-strokecount.csv` (MIT licensed) as the data spine

## What's NOT bundled (and why)

| Missing | Why | How to add later |
|---|---|---|
| 81 靈動數吉凶表 | Different schools disagree, picking one needs an editorial decision | Hand-curate from one TW source into `references/81-lucky.md` |
| 125 三才吉凶表 | Same — partisan choices | Same as above, into `references/sancai-table.md` |
| 八字計算引擎 | Heavy dependency, better delegated to `tony801015/chinese-lunar` or `bazi-mcp` | See SKILL.md Step 2 |
| 部首 → 五行 對照 | Kangxi CSV doesn't include 部首; would need separate dataset | Source from Unihan database or a 部首字典 |
| 教育部常用字表 | Not bundled to keep skill lightweight | Pull from [教育部辭典](https://dict.revised.moe.edu.tw/) when filtering 生僻字 |
| 年度新生兒命名統計 | Updates yearly | Have user paste the latest list, or LLM web-search at Step 5 |

## Adding new data

If extending the asset bundle, document the source + license + verification example here, following the same structure as the two existing entries above.
