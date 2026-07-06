# tw-naming

> 繁體中文姓名 Claude Code skill — 取名、評估、改名建議。台灣語境，康熙筆劃為基準。

整合三才五格 + 八字喜用神 + 生肖派的傳統姓名學工具。三個模式：

- **取名（generate）**：給姓 + 生辰，產出候選名 shortlist
- **評估（analyze）**：給既有姓名，跑出三才五格分析
- **改名（suggest）**：固定 N-1 字，搜剩下一字怎麼改會變吉

特別處理了大陸取名工具的兩個常見錯誤：簡體筆劃當基準算三才五格、檔名標「繁體」實際是簡體字。

---

## 上游資料來源與致謝 Attribution

本 skill 是「整合多個獨立來源」的工具，不是衍生鏈。各來源依其授權狀態 bundle 或引用：

### 直接 bundle 的資料

| 檔案 | 來源 | 授權 |
|---|---|---|
| `assets/kangxi-strokecount.csv` | [breezyreeds/kangxi-strokecount](https://github.com/breezyreeds/kangxi-strokecount)（Kawai Lo） | **MIT** |
| `assets/ChineseCharacters.json` | [johnwu1114/chinese-name](https://github.com/johnwu1114/chinese-name) | ⚠️ **無 upstream LICENSE**（見下方警語） |
| `assets/zodiac/*.json` × 12 | 同上 | ⚠️ 同上 |
| `assets/EightyOne.json`、`Sancai.json` | 同上 | ⚠️ 同上（僅作交叉驗證用） |

### 整理自公開知識（沒 bundle 原始檔）

| 來源 | 用途 |
|---|---|
| 熊崎健翁《姓名 の 神秘》系統（民俗 / 公有領域） | `scripts/lucky_81.py` 81 靈動數、`scripts/sancai_table.py` 125 三才 |
| [zh.wikiversity 生肖姓名學](https://zh.wikiversity.org/wiki/生肖姓名學)（CC BY-SA 4.0） | `scripts/zodiac_explain.py` 186 條字根層級宜忌規則。規則本身是民俗公有，wiki 的具體遣詞造句受 CC BY-SA 保護，本 skill 已改寫並標註來源 |

### 引用但沒 bundle（推薦搭配）

| 專案 | 用途 |
|---|---|
| [tony801015/chinese-lunar](https://github.com/tony801015/chinese-lunar) | 繁體八字排盤 npm 套件，建議用於 Step 2 推算喜用神 |
| [cantian-ai/bazi-mcp](https://github.com/cantian-ai/bazi-mcp) | 八字 MCP server，可接到 Claude Code |
| [BYVoid/OpenCC](https://github.com/byvoid/opencc) | 簡繁轉換（曾用，現已不依賴） |

### 影響架構但沒用程式碼的反面教材

| 專案 | 為什麼不用 |
|---|---|
| [babyname/fate](https://github.com/babyname/fate) | 兩萬星的中文取名工具，但字典筆劃用簡體筆劃，整套三才五格從根上歪掉 |
| [JakLiao/GoodGoodName](https://github.com/JakLiao/GoodGoodName) | 簡體骨架 |
| [James88/qiming](https://github.com/James88/qiming) | fork GoodGoodName，宣稱有「繁體」字典，實際內容仍是簡體字 |

---

## ⚠️ License Caveat — 關於 johnwu1114 資料

`johnwu1114/chinese-name` upstream **沒有 LICENSE 檔案**（截至 2026-05-07）。作者描述為「免費的取名程式」，**意圖** permissive 但**法律上**不具拘束力。

### 風險分級

| 場景 | 風險 |
|---|---|
| 個人私下用這個 skill | 低（合理使用） |
| Fork 到自己 repo 個人用 | 低 |
| 公開散布 / 部落格介紹 | **中**（你需要把這份 caveat 一併傳遞） |
| 商業用途 | **高**（建議先聯絡原作者或自建資料） |

### Fork 這個 skill 的人請注意

如果你準備 fork 並 redistribute：
1. **聯絡 johnwu1114 取得明確授權**（最乾淨），或
2. **移除 `assets/ChineseCharacters.json` 與 `assets/zodiac/*` 後自建等價資料**（最徹底），或
3. **保留現狀並把這份 LICENSE Caveat 傳下去**（接受灰色地帶）

詳情見 [LICENSE](./LICENSE) 與 [`references/data-caveats.md`](./references/data-caveats.md)。

---

## 安裝 Installation

本 skill 是 [unbias38/my-claude-skills](https://github.com/unbias38/my-claude-skills) 集合中的其中一個。

**只安裝這一個 skill（sparse-checkout）**

```bash
git clone --filter=blob:none --sparse https://github.com/unbias38/my-claude-skills.git
cd my-claude-skills
git sparse-checkout set tw-naming
cp -r tw-naming ~/.claude/skills/
```

**或 clone 整包再複製**

```bash
git clone https://github.com/unbias38/my-claude-skills.git
cp -r my-claude-skills/tw-naming ~/.claude/skills/
```

**Windows (PowerShell)**

```powershell
git clone https://github.com/unbias38/my-claude-skills.git
Copy-Item -Recurse my-claude-skills\tw-naming "$env:USERPROFILE\.claude\skills\"
```

安裝完重啟 Claude Code 即可使用。

### 選用依賴

無強制依賴。Skill 純 Python 標準函式庫即可運作。

---

## 觸發 Trigger

本 skill 會在你提到下列關鍵字時自動觸發：

- 「幫我取名」「幫小孩取名」「新生兒命名」
- 「繁體取名」「三才五格」「喜用神」
- 「這個名字好不好」「評估名字」「姓名分析」
- 「改名建議」「想改名」

或當對話中出現「姓 + 出生年月日時」這類資訊時，Claude 會自動判斷該用哪個模式。

---

## 示範用法 Usage Examples

以下範例都假設你已經安裝 skill 並在 Claude Code 對話中。**直接用自然語言講就好**——Claude 會幫你串起整個流程。下面也附上對應的指令版本，以防你想自己跑。

### 範例 1：評估別人的名字

**自然語言**

> 用 tw-naming 評估「林志玲」，1974 年生

**Claude 會做的事**

1. 跑 `analyze_name.py 林志玲 --year 1974 --report`
2. 用 Write tool 把 markdown 報告存成 `林志玲_姓名評估.md`
3. 訊息裡呈現三段：
   - **A 段**：5 行內快速摘要（人格大吉、地格半吉、三才大吉、生肖 +2 偏吉）
   - **B 段**：完整 markdown 報告（含五格 + 81 名稱含義 + 三才 content + 生肖 per-char）
   - **C 段**：詢問要不要也產一份 Word 檔（.docx）給長輩

**手動指令版**

```bash
python scripts/analyze_name.py 林志玲 --year 1974 --explain-zodiac --report --output 林志玲_姓名評估.md
```

### 範例 2：幫朋友的小孩取名

**自然語言**

> 用 tw-naming 幫朋友的小孩取名：姓陳、2026/03/15 14:20、男嬰、避開「明芳華」

**Claude 會做的事**

1. 從生辰算八字 → 推算喜用神（例：火）
2. 跑 `kangxi_lookup.py 陳` → 查姓的康熙筆劃（16）
3. 跑 `find_combos.py --surname-strokes 16 --grade 中吉 --sancai-grade 大吉` → 列三才五格大吉的筆劃組合
4. 對每組筆劃，跑 `chars_by_stroke.py --strokes N --wuxing 火 --avoid 明芳華` → 列繁體候選字
5. 從候選字組成 5-10 個名字 shortlist
6. 跑 `score_candidates.py` 把候選名整成完整 markdown 報告
7. LLM 補上每個候選的字義 / 聲調 / 台語檢音 / 撞菜市場名 + 取捨建議

**手動指令版**

```bash
# Step 1: 查姓筆劃
python scripts/kangxi_lookup.py 陳
# → 16

# Step 2: 找筆劃組合
python scripts/find_combos.py --surname-strokes 16 --grade 中吉 --sancai-grade 大吉

# Step 3: 對每組筆劃列候選字（例如選到 5,12 組合）
python scripts/chars_by_stroke.py --strokes 5 --wuxing 火 --avoid 明芳華
python scripts/chars_by_stroke.py --strokes 12 --wuxing 火 --avoid 明芳華

# Step 4: 把候選名清單整成完整報告
python scripts/score_candidates.py 陳承翰 陳承宇 陳子煊 --year 2026 --birth "2026/03/15 14:20（男）" --xiyongshen "火、土" --avoid "明芳華" --title "陳姓男嬰命名候選" --output 陳姓男嬰_命名候選.md
```

### 範例 3：改名建議

**自然語言**

> 用 tw-naming 看「張小明」改第三字能改成什麼，喜用神火，避免跟父親「明」字相同

**Claude 會做的事**

1. 跑 `analyze_name.py 張小明 --report`，發現人格、外格、總格三大凶（被前兩字鎖死）
2. 跑 `suggest_changes.py 張小明 --change 3 --wuxing 火 --avoid 明`，回傳 0 組——表示這個位置救不回來
3. 試 `--change 2`（改中間字）看有沒有救
4. 若仍救不回，建議整個重取（轉 generate 模式）

**手動指令版**

```bash
python scripts/suggest_changes.py 張小明 --change 3 --wuxing 火 --avoid 明 --report --output 張小明_改名建議.md
```

### 範例 4：複姓 / 單字名

```bash
# 複姓 + 單字名（如歐陽修）
python scripts/analyze_name.py 歐陽修 --surname-len 2 --year 1007 --report

# 單姓 + 單字名（如林森）
python scripts/analyze_name.py 林森 --year 1868 --report
```

支援的姓名組合：
- 單姓 + 單名（林森、王偉）
- 單姓 + 雙名（張小明、林志玲）
- 複姓 + 單名（歐陽修、司馬遷）
- 複姓 + 雙名（司馬相如、諸葛孔明）

### 範例 5：純查單字筆劃

```bash
python scripts/kangxi_lookup.py 張陳王李華
# → 張 11 / 陳 16 / 王 4 / 李 7 / 華 14
```

注意「華」=14 不是手寫的 12——這是康熙字典「艸」部首作 6 劃 + 8 = 14 的算法。台灣命理師用康熙筆劃，大陸取名工具用簡體筆劃，差異就在這裡。

### 範例 6：純查生肖加分

```bash
python scripts/zodiac_score.py 林志玲 --year 1974
# → 志（宜 +1）、玲（宜 +1）、總分 +2 偏吉

# 1-2 月初出生（立春前）用 --zodiac 強制覆寫
python scripts/zodiac_score.py 王某某 --zodiac 蛇
```

---

## 三模式對照

| 模式 | 你會說 | Claude 跑的腳本 | 輸出 |
|---|---|---|---|
| **取名** | 「幫小孩取名」 | find_combos → chars_by_stroke → score_candidates | `XX姓_命名候選.md` |
| **評估** | 「這個名字好不好」 | analyze_name --report | `XXX_姓名評估.md` |
| **改名** | 「想改名」 | suggest_changes --report | `XXX_改名建議.md` |

三模式底層共用 `kangxi_lookup` + `wuge` + `lucky_81` + `sancai_table`，所以**換模式不換結果可信度**。

---

## 信號分層

skill 用兩種信號處理「該不該採納這個結果」：

| 信號 | 角色 | 用法 |
|---|---|---|
| 三才五格 + 喜用神 | **Hard filter（剪枝）** | 通過 / 不通過，縮減候選空間 |
| 生肖派（`--year`） | **Soft signal（排序加分）** | 每字 +1/0/-1，顯示但不否決 |
| 父母避諱（`--avoid`） | **Hard filter（剔除）** | 完全不出現 |

**生肖派故意不升級為 hard filter**——因為它的派別爭議比三才五格還大，硬篩會把候選空間崩掉（例如鼠年忌人/亻/日/火/午，14 劃火屬性的字砍下去剩不到 5 個能用）。

詳情見 [`references/zodiac-school.md`](./references/zodiac-school.md)。

---

## 限制與誠實聲明

- **三才五格僅是傳統姓名學六大派之一**，預測準確度約 56.6%。
- **喜用神判定**目前靠 LLM 推算，非命理師判斷。嚴肅命名建議找命理師確認。
- **生肖派字級對照來自 johnwu1114 的單一派別**，跟 `zodiac_explain.py` 的 wiki 字根規則偶爾會不一致——這是派別差異的真實反映。
- **天格代表祖蔭，由姓氏決定不可改**。本 skill 預設不把天格納入主判定（`--include-tiange` 才會納入）。
- **CJK 字元拆字根的精準匹配**目前未實作。Per-char 生肖解釋走 LLM 即時生成 + `zodiac_explain.py` 的字根層級規則表作 ground truth。

---

## 授權 License

本 skill 程式碼與文件採 [MIT License](./LICENSE)，Copyright (c) 2026 九月筍。

**Bundled 資料**保留各上游來源的授權狀態：
- `kangxi-strokecount.csv` — MIT (Kawai Lo)
- `ChineseCharacters.json` 與 `zodiac/*` — johnwu1114 upstream **無 LICENSE**，使用前請閱讀上方 ⚠️ License Caveat 段落

---

## 變更紀錄

見 [CHANGELOG.md](./CHANGELOG.md)。三大版本：

- **0.1.0**：基礎 skill（康熙 CSV + 81 + 125 + 三模式骨架 + 天格祖蔭發現）
- **0.2.0**：johnwu1114 資料整合 + 生肖派 soft signal + wikiversity 字根規則
- **0.3.0**：三入口報告規格一致化 + LLM placeholder + 完整 markdown 輸出
