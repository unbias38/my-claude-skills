# Changelog

## 0.3.0 (2026-05-07) — 三入口報告規格一致化

### Added
- `scripts/score_candidates.py`：generate-mode 完整報告產生器，把所有資料層內容（康熙筆劃 / 五格 / 81 數名稱與含義 / 三才 + content / 生肖加分 + 字根參考 / 避諱狀態 / 完整免責）強制串入 markdown 輸出，避免 LLM 邊想邊寫漏資料。
- `scripts/suggest_changes.py --report`：改名模式新增 markdown 報告輸出，先前只有 terminal 列表。
- `scripts/analyze_name.py --report`：升級至跟 score_candidates.py 同等完整度（五格表加「含義」欄、三才下方拉 Sancai content、不利處附 81 名稱、`--explain-zodiac` 時把字根層級宜忌完整參考表塞進報告）。
- 三入口報告統一加 `> （待 LLM 補...）` placeholder 章節，避免 script 重跑時把 LLM 已寫的內容覆蓋掉。

### Removed
- `assets/wuxing_dict_fanti.json` 與相關 legacy code path（`chars_by_stroke.py --source qiming`、`_legacy_qiming` 函式、back-compat shim）。先前已 deprecated，僅留作交叉檢查。

### Insight
這一輪不在補單一功能，是補三個 user-facing 入口（generate / analyze / suggest）之間的規格落差。「user 抱怨偏少」常常不是少了哪個欄位，是這條入口落後另一條入口一個版本。

## 0.2.0 — johnwu1114 資料整合與生肖派加入

### Added
- `assets/ChineseCharacters.json`：取代有問題的 qiming wuxing dict（後者檔名標 fanti 但內容是簡體字）。14 劃火屬性的候選字從 32 個跳到 90 個。
- `scripts/wuxing_lookup.py`：(筆劃, 五行) → 繁體字查詢模組。
- `scripts/zodiac_score.py`：生肖派加分（soft signal）。每字 +1（宜）/ 0 / -1（忌），加總顯示但不過濾候選。
- `scripts/zodiac_explain.py`：12 生肖字根層級宜忌規則 186 條（含五行、方位、食物、居所、三合、三會、相沖、相害、相破），來源 zh.wikiversity 生肖姓名學。
- `assets/zodiac/*.json` × 12：johnwu1114 的 12 生肖字級宜忌對照。
- `references/zodiac-school.md`：生肖派的 hard-vs-soft 設計理由說明。
- `analyze_name.py --year YYYY` / `--zodiac 鼠`：自動觸發生肖加分。
- `analyze_name.py --explain-zodiac`：加印生肖字根層級宜忌參考表。

### Changed
- 兩層信號模型寫進 SKILL.md：三才五格 + 喜用神 = hard filter（剪枝），生肖派 = soft signal（排序加分），父母避諱 `--avoid` = hard filter（剔除）。
- `references/data-caveats.md` 加 johnwu1114 無 LICENSE 的警語段落。

### Decisions
- 生肖派**不**升級為 hard filter（爭議大、會崩塌候選空間）。
- 81 數與 125 三才表跟 johnwu1114 cross-validate 後保留現有版本（EightyOne 94% 一致；Sancai 33% 分歧多為粒度差異）。

## 0.1.0 — 基礎 skill

### Added
- `scripts/kangxi_lookup.py`：康熙筆劃查表，從 breezyreeds/kangxi-strokecount.csv 載入。
- `scripts/lucky_81.py`：81 靈動數完整表（含名稱與含義），含 mod-80 還原邏輯。
- `scripts/sancai_table.py`：125 三才完整表（5×5×5 五行組合）。
- `scripts/wuge.py`：五格 + 三才計算，支援單姓單名／單姓雙名／複姓單名／複姓雙名 4 種組合。
- `scripts/find_combos.py`：暴力搜尋三才五格大吉的筆劃組合。
- `scripts/chars_by_stroke.py`：按筆劃 + 五行查字。
- `scripts/analyze_name.py`：反查模式（評估既有名字）。
- `scripts/suggest_changes.py`：改名模式（固定 N-1 字、暴力搜剩下一字）。
- `references/`：81-lucky.md、sancai-table.md、xiyongshen.md、taiwan-naming.md、data-caveats.md。
- `assets/kangxi-strokecount.csv`：63,696 字的康熙筆劃資料。

### Discoveries
- **天格祖蔭不論**：對 11 劃姓（如張）來說，天格永遠是 12 大凶。傳統命名師慣例不把天格納入主判定。寫進 `find_combos.py` 預設行為（`--include-tiange` 才開）。
- **CSV preamble 有 4 行不是 3 行**：康熙 CSV 開頭是 3 行 license + 1 行空白 + header。
- **「fanti」檔名不一定是繁體**：qiming/wuxing_dict_fanti.json 內容是簡體字（後續 0.2.0 已棄用此來源）。
