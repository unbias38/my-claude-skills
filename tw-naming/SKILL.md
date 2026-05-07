---
name: tw-naming
license: MIT
description: 'Traditional Chinese name skill for Taiwan context. Three modes — (1) Generate: 新生兒命名, given 姓 + 生辰, produce shortlist using 三才五格 + 八字 + 喜用神. (2) Analyze: 反查既有名字, score its 五格三才 grade. (3) Suggest: 改名建議, fix one position to fix bad grades. Uses 康熙筆劃 (NOT simplified strokes). Filters for 台灣語境 (avoid 菜市場名, taboo homophones, mainland chars) and supports 父母避諱 (--avoid). Triggers — "幫我取名", "繁體取名", "改名建議", "這個名字好不好", "三才五格 + 喜用神", "新生兒命名".'
metadata:
  version: 0.3.0
  sources:
    - breezyreeds/kangxi-strokecount (MIT) — Kangxi stroke counts CSV (bundled)
    - johnwu1114/chinese-name (no LICENSE — see README) — 繁體 字庫 + 12 生肖宜忌 (bundled with caveat)
    - zh.wikiversity 生肖姓名學 (CC BY-SA 4.0) — radical-level rules paraphrased into zodiac_explain.py
    - 熊崎健翁《姓名 の 神秘》系統 — 81 數 + 125 三才 (folk / public domain)
---

# Traditional Chinese Name Generator (TW)

## Three Modes

| Mode | When | Entry script |
|---|---|---|
| **Generate** (新生兒命名) | 全新取名, 姓 + 生辰已知 | `find_combos.py` → `chars_by_stroke.py` → LLM |
| **Analyze** (反查) | 評估既有名字好不好 | `analyze_name.py` |
| **Suggest** (改名建議) | 既有名字想改一個字 | `suggest_changes.py` |

All three share the same data layer (康熙 CSV, 81/125 表) and respect the same 父母避諱 filter via `--avoid`.

## Two-tier signal model

| Signal | Role | Output |
|---|---|---|
| 三才五格 + 喜用神 | **Hard filter** (剪枝) | 通過/不通過, 縮減候選空間 |
| 生肖派 (`--year`) | **Soft signal** (排序加分) | 每字 +1/0/-1, 顯示但不否決 |
| 父母避諱 (`--avoid`) | **Hard filter** (剔除) | 完全不出現 |

不要把 soft signal 升級為 hard filter — 派別爭議大的算法當硬篩會崩塌候選空間。see `references/zodiac-school.md`.

## Goal (Generate mode)

Produce a shortlist of name candidates for a person, given 姓 (surname) and 生辰 (birth datetime),
that satisfy:

1. **三才五格大吉/吉** — using **康熙字典筆劃** (NOT simplified strokes; this is the most common error in mainland tools)
2. **喜用神五行配合** — derived from 八字
3. **台灣語境合宜** — common in TW, no taboo homophones (台語/國語), not 菜市場名, good 字義/聲調

This skill explicitly rejects the common mistake of treating 簡體筆劃 = 繁體筆劃. 「張」=11 劃 (康熙), not 7.

## Architecture (4 layers)

```
[Bazi layer]      birth time → 八字 + 喜用神 (五行)
       ↓
[Stroke layer]    surname + 康熙筆劃 → 三才五格大吉的名字筆劃組合
       ↓
[Char layer]      筆劃組合 × 喜用神五行 → 候選字 (繁體, 台灣常用)
       ↓
[LLM layer]       候選字 → 組合成名字, 過濾菜市場/諧音/字義 → shortlist
```

Each layer has different fragility. **Stroke layer must be deterministic (script);
LLM layer must be judgmental (prompt with TW context).** Don't blur this.

## Workflow

### Step 1 — Gather inputs

Ask the user for:
- **姓** (繁體, e.g., 張, 陳, 王)
- **出生時間** (公曆，到「時」的精度，e.g., `2026/03/15 14:20`)
- **性別** (optional but helps with character selection)
- **是否已有屬意字** (optional — if the user has 1-2 字 in mind, skill becomes "complete the name" mode)

### Step 2 — 八字 + 喜用神 (Bazi layer)

This skill **does not bundle a 八字 calculator**. Pick one:

- **Preferred for TW**: `tony801015/chinese-lunar` (npm, 繁體, 台灣作者). Provides 年月日時柱.
- **Alternative**: `cantian-ai/bazi-mcp` (MCP server, plugs straight into Claude Code).
- **Fallback**: ask the user to provide the 八字 directly, OR have Claude compute it from 萬年曆 knowledge (less reliable — verify against an external source).

Output expected from this step: **喜用神 (1-2 個五行字: 金/木/水/火/土)** + the full 八字 for record.

> Determining 喜用神 from 八字 is a judgment call (扶抑/調候/通關/病藥). For new users,
> a simple heuristic is "補不足 + 平衡". See `references/xiyongshen.md`.

### Step 3 — 筆劃組合 (Stroke layer)

This is the deterministic part. Use the bundled scripts:

```bash
# Look up the surname's 康熙筆劃
python scripts/kangxi_lookup.py 張
# → 11

# Find auspicious (firstname1_strokes, firstname2_strokes) combos
python scripts/find_combos.py --surname-strokes 11 --grade 大吉
# → list of (s1, s2) tuples that yield 三才大吉 + 五格全吉
```

Output: a list of stroke pairs like `[(4, 12), (6, 10), ...]`.

### Step 4 — 候選字 (Char layer)

For each (s1, s2) combo from Step 3, find characters with:
- `kangxi_strokes == s1` (or `s2`)
- `wuxing in 喜用神`
- 繁體 + 台灣常用 + 適合人名

```bash
python scripts/chars_by_stroke.py --strokes 12 --wuxing 木
# → list of candidate 繁體 chars
```

**Data sources**:
- `assets/kangxi-strokecount.csv` — authoritative for 筆劃. Trust.
- `assets/ChineseCharacters.json` — preferred 繁體 五行 字典 (default in `chars_by_stroke.py`).
- See `references/data-caveats.md` for license + data drift notes.

### Step 5 — 組成名字 + LLM 篩選 (LLM layer)

Pass the candidate chars + context to the LLM with this kind of prompt:

> 姓「{surname}」，生辰「{datetime}」，喜用神「{wuxing}」。
> 候選筆劃組合：{combos}。
> 第一字候選（{s1} 劃，五行 {wuxing}）：{chars1}
> 第二字候選（{s2} 劃，五行 {wuxing}）：{chars2}
>
> 請組合 5-10 個名字，並對每個說明：
> - 字義（必須正面、適合人名，避免生僻字）
> - 聲調搭配（避免三聲連續、避免拗口）
> - 台語讀音是否有不雅諧音
> - 是否撞菜市場名（如目前台灣常見年度排行）
> - 字形美感

Refer to `references/taiwan-naming.md` for TW-specific taboos and aesthetic principles.

### Step 6 — Final report assembly

**MUST use `scripts/score_candidates.py`** to assemble the final markdown — DO NOT hand-write the report. The script forces all data-layer content into the report (81 數名稱、三才 content、生肖字根參考、天格祖蔭標註、避諱狀態、完整免責) so nothing gets dropped.

```bash
python scripts/score_candidates.py 蔡明芳 蔡沛芬 蔡沛君 \
    --year 1956 --birth "1956/08/31 09:23（女）" \
    --xiyongshen "水、木" --avoid "芳華" \
    --title "蔡姓女嬰命名候選" \
    --output 蔡姓女嬰_命名候選.md
```

The script produces a report with:
- 快速摘要表
- 每個候選的完整詳情（康熙筆劃、五格 + 81 數名稱與含義、三才 content、生肖 per-char 加分）
- 該生肖的字根層級宜忌參考
- 取捨建議 placeholder（待 LLM 補）
- 「字義 / 聲調 / 台語 / 在地風格」placeholder per candidate（待 LLM 補）
- 完整免責聲明

**LLM 接手只負責填三件事**（標 `（待 LLM ...）` 的位置）：
1. 每個候選的字義 / 國語聲調 / 台語檢音 / 在地風格評估
2. 取捨建議（依「優先 X 推 ___」「優先 Y 推 ___」格式）
3. 把空白 placeholder 改寫成具體段落

Internal cross-check (DEV ONLY, do **NOT** mention to the user): `chname.blogspot.tw/` is a TW naming web tool that can verify scoring manually.

**For the user-facing output, see `references/taiwan-naming.md` § 8** —
no internal jargon (no "soft signal", no script/repo names, no school codenames).

## Analyze Mode (反查既有名字)

```bash
python scripts/analyze_name.py 張小明
python scripts/analyze_name.py 歐陽修 --surname-len 2
python scripts/analyze_name.py 林志玲 --json
```

Output covers: 康熙筆劃 / 五格 / 三才 / overall verdict.
天格 by default 不論吉凶 (祖蔭不可改). Pass `--include-tiange` to enforce.

Supports: 單姓+單名, 單姓+雙名, 複姓+單名, 複姓+雙名.

### Output formats

| Flag | Use case | Format |
|---|---|---|
| (none) | quick terminal lookup | pretty text |
| `--json` | feed to other tools | JSON |
| `--report` | **share with user / pa**rents | clean Markdown (LINE / HackMD / Notion / PDF 友善) |

The `--report` mode follows `references/taiwan-naming.md` § 8 — no internal jargon.

```bash
# Save report to file for sharing
python scripts/analyze_name.py 林志玲 --year 1974 --report > 林志玲_姓名評估.md
```

### Standard output flow (when responding to user)

When finishing an `analyze` (or `suggest` / `generate`) run, **present the result to the user in this 3-step pattern**:

**Step A — Quick summary** (3-5 行, 給快速判讀)
```
林志玲（虎）
五格：人格大吉、地格半吉、外格大吉、總格中吉
三才：水土金 大吉
整體：✅ 整體良好；生肖派 +2 偏吉
```

**Step B — Full markdown report (產出 .md 檔)**

不只是貼出來，**要實際存成檔案**：

1. 跑 `python scripts/analyze_name.py {name} --year {year} --report` 取得 markdown 內容
2. 用 `Write` tool 存成 `{name}_姓名評估.md`（放在使用者當前工作目錄；多人時加日期 `{name}_姓名評估_{YYYYMMDD}.md` 避免覆蓋）
3. 告訴使用者：
   > 完整報告已存到 `林志玲_姓名評估.md`，可直接貼 LINE / HackMD / Notion。
4. 回應內也貼一份 markdown 內容（讓使用者不開檔就能讀）

**Step C — 詢問是否要 docx 版**
> 要不要也幫你產一份 Word 檔（.docx）？方便列印或寄信給長輩。

如果使用者回 yes：
1. 把 Step B 的 markdown 內容傳給 `docx` skill
2. 存成 `{name}_姓名評估.docx`（同樣路徑，加日期避免覆蓋）
3. 告訴使用者檔案位置

如果使用者回 no 或直接挑名字討論，就跳過 docx，繼續對話。

> 為什麼是這個順序：A 給秒判（多數人看完就走）、B 給可分享版（多數人會想存檔）、C 給長輩版（少數要列印）。一層一層加深度，使用者隨時可停。

## Suggest Mode (改名建議)

```bash
# 鎖住其他字, 改第 N 字, 暴力搜尋吉筆劃
python scripts/suggest_changes.py 張小明 --change 3
python scripts/suggest_changes.py 林志玲 --change 3 --grade 中吉 --sancai-grade 中吉

# 加上喜用神過濾
python scripts/suggest_changes.py 林志玲 --change 3 --wuxing 金

# 加上父母避諱
python scripts/suggest_changes.py 林志玲 --change 3 --wuxing 金 --avoid 玲珍珊

# 完整 Markdown 報告（含原名分析 + 候選 + 生肖參考 + LLM 待補處）
python scripts/suggest_changes.py 林志玲 --change 3 --wuxing 金 --year 1974 --report \
    > 林志玲_改名建議.md
```

`--report` 模式同 analyze/generate 規格：自動串入 81 數含義、三才 content、生肖加分 + 字根參考、避諱狀態、完整免責。LLM 只需補「字義 / 聲調 / 取捨建議」這個 placeholder 段。

**Reality check**: 有些原名是「不可救」的 (例如「張小明」中固定姓+某一字後, 人格/外格已被鎖死成大凶, 再怎麼換另一字都救不回). 此時 `suggest_changes.py` 會回 `Found 0`. 要嘛換改第 2 字試試, 要嘛建議使用者整個重取 (回到 Generate mode).

## 父母避諱 (Cultural taboo on reusing 父母 / 祖輩 names)

This is **strongly observed in TW culture** — children should NOT reuse characters from parents' / grandparents' names. The skill supports this via `--avoid`:

```bash
# Generate mode: filter at char-listing step
python scripts/chars_by_stroke.py --strokes 14 --wuxing 火 --avoid 明芳華

# Suggest mode: built-in
python scripts/suggest_changes.py 林志玲 --change 3 --avoid 玲珊珍
```

Note: This is `避諱` (taboo on same-character reuse), which has high cultural consensus.
**It's NOT 父母八字配合** (avoiding 五行 conflict with parents' 八字), which is **partisan and contested** — different schools disagree. The skill does not implement parent-bazi compatibility by default.

## Bundled Resources

### scripts/

| Script | Purpose |
|---|---|
| `kangxi_lookup.py` | Look up 康熙筆劃 of a single character |
| `lucky_81.py` | 81 靈動數 lookup table |
| `sancai_table.py` | 125 三才 lookup table |
| `wuge.py` | Compute 五格 + 三才 + grades; supports 單姓單名/單姓雙名/複姓單名/複姓雙名 |
| `wuxing_lookup.py` | (筆劃, 五行) → 繁體字 (from `ChineseCharacters.json`) |
| `find_combos.py` | Brute-force search auspicious (n1, n2) given-name combos |
| `chars_by_stroke.py` | List candidate chars by 筆劃 + 五行, supports `--avoid` |
| `analyze_name.py` | **反查模式**: score an existing name |
| `suggest_changes.py` | **改名模式**: fix one position, search for replacement |
| `zodiac_score.py` | 生肖派 +1/0/-1 加分 (soft signal) |
| `zodiac_explain.py` | 生肖字根層級宜忌參考 (來源: zh.wikiversity 生肖姓名學) |
| `score_candidates.py` | **generate mode 報告器**: 把所有資料層內容串進完整 markdown 報告 |

### references/

| File | When to read |
|---|---|
| `sancai-table.md` | When computing 三才 grade (125 combinations of 天人地 五行) |
| `81-lucky.md` | When evaluating 五格 — 81 靈動數吉凶表 |
| `xiyongshen.md` | When deriving 喜用神 from 八字 (heuristics only — for serious cases consult a 命理師) |
| `taiwan-naming.md` | At the LLM layer — TW-specific 避諱 / 字義 / 聲調 / 菜市場名 considerations |
| `zodiac-school.md` | When using --year / --zodiac flags — 生肖派 soft signal 的限制與用法 |
| `data-caveats.md` | Before trusting any bundled data file — known simplified/traditional issues |

### assets/

| File | Source | License |
|---|---|---|
| `kangxi-strokecount.csv` | [breezyreeds/kangxi-strokecount](https://github.com/breezyreeds/kangxi-strokecount) | MIT |
| `ChineseCharacters.json` | [johnwu1114/chinese-name](https://github.com/johnwu1114/chinese-name) | **NO LICENSE** ⚠️ (see data-caveats) |
| `zodiac/N_*.json` × 12 | [johnwu1114/chinese-name](https://github.com/johnwu1114/chinese-name) | **NO LICENSE** ⚠️ |
| `EightyOne.json`, `Sancai.json` | johnwu1114 (cross-reference only, not loaded) | **NO LICENSE** ⚠️ |

## Anti-patterns to avoid

- **Don't use 簡體筆劃**. The whole point of this skill is correct 康熙筆劃. Tools that use simplified strokes are wrong by definition.
- **Don't let the LLM compute 五格 / 三才 grades**. LLMs hallucinate auspiciousness tables. Use `wuge.py`.
- **Don't let the script pick the final name**. Stroke + 五行 only 剪枝 the search space. 字義 / 聲調 / 文化語感 is LLM territory.
- **Don't promise 100% accuracy of 喜用神 derivation**. Real 八字 命理 has decades of disagreement on extraction methods. Mark this layer as best-effort and recommend human verification.
- **Don't leak internal jargon to the user**. When constructing the user-facing reply (the final message in chat), follow `references/taiwan-naming.md` § 8: no script names, no GitHub repo names (johnwu, breezyreeds, qiming), no codenames (熊崎, school A/B), no engineering terms (hard filter / soft signal / pipeline / drift). Use plain Chinese the user can understand.
- **Don't promote `生肖派` to a hard filter**. It's a soft signal. The school is contested and hard-filtering with it collapses the candidate space.
- **Don't hand-write the final generate-mode report**. Use `score_candidates.py` to assemble. Hand-writing reliably drops 81 數名稱 / 三才 content / 字根參考 / 完整免責 — there are too many data points to remember manually. Script enforces completeness.

## Status

**Stroke / 三才五格 layer is fully implemented and tested end-to-end.**

- ✅ `scripts/kangxi_lookup.py` — 康熙筆劃查表 (verified: 張=11, 陳=16, 王=4, 李=7, 華=14)
- ✅ `scripts/lucky_81.py` — 81 靈動數完整表 + mod-80 reduction
- ✅ `scripts/sancai_table.py` — 125 三才完整表 (42 大吉 / 13 中吉 / 52 凶 / 18 大凶)
- ✅ `scripts/wuge.py` — 計算五格 + 三才, 接通 81 + 三才表
- ✅ `scripts/find_combos.py` — 暴力搜尋吉組合 (預設排除天格祖蔭)
- ✅ `scripts/chars_by_stroke.py` — 按筆劃 + 五行查字, 用 `ChineseCharacters.json` (繁體, 含 Kangxi cross-check), 支援 `--avoid` 避諱
- ✅ `scripts/wuxing_lookup.py` — 五行字典查詢模組
- ✅ `scripts/analyze_name.py` — **反查模式**: 既有名字評估 + 可選 `--year` 加生肖派分數
- ✅ `scripts/suggest_changes.py` — **改名模式**: 固定 N-1 字, 改一字, 含 `--report` 完整 markdown 輸出
- ✅ `scripts/zodiac_score.py` — **生肖派 soft signal**: +1/0/-1 加分, 不過濾
- ✅ `scripts/zodiac_explain.py` — 12 生肖部首層級宜忌參考表 (可由 `analyze_name.py --explain-zodiac` 觸發)
- ✅ `scripts/score_candidates.py` — **generate mode 完整報告產生器**: 強制把所有資料層內容串進報告 (81 名稱 / 三才 content / 生肖 per-char / 字根參考 / 避諱狀態 / 完整免責)
- ✅ `references/81-lucky.md` — 人類可讀對照 + 9×9 速查表
- ✅ `references/sancai-table.md` — 人類可讀對照 + 五大黃金組合
- ✅ `references/xiyongshen.md` — 喜用神三大判定法 + 啟發式 + 免責
- ✅ `references/taiwan-naming.md` — 8 大 TW 在地考量
- ✅ `references/data-caveats.md` — 已說明 wuxing dict 的簡繁混雜問題

**Optional dependency**:
```bash
pip install opencc-python-reimplemented
```
無此套件時 `chars_by_stroke.py` 仍可運作，但輸出可能含簡體字（會印警告）。

## Verified end-to-end demo

姓 張 (康熙 11 劃) + 喜用神 火 → 找到 9 組吉組合：

```
$ python scripts/find_combos.py --surname-strokes 11 --grade 中吉 --sancai-grade 大吉
[(2,22), (10,14), (12,12), (20,4), (21,20), ...]

$ python scripts/chars_by_stroke.py --strokes 10 --wuxing 火
["庭","納","倫","唐","朔","珍","玲","凌","烈","夏","烏",...]

$ python scripts/chars_by_stroke.py --strokes 14 --wuxing 火
["臺","盡","連","熔","嘆","圖","領","趙","團","暢","禎","寧","夥",...]
```

接下來把候選字組合餵給 LLM (Step 5) 即完成名字 shortlist。

## Future work

- [ ] Bundle a 部首 → 五行 對照表 (more principled than the johnwu char-level dict)
- [ ] 整合 `tony801015/chinese-lunar` 或 `bazi-mcp` 自動化 Step 2 (目前需人工或 LLM 算八字)
- [ ] 加入年度新生兒命名統計 (`taiwan-naming.md` 中提到的菜市場名清單) 自動更新機制
- [ ] Verify johnwu1114 data license before public redistribution (currently no LICENSE upstream)
