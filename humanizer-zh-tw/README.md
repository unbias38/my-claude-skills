# humanizer-zh-tw

> 繁體中文版 Claude Code humanizer skill — 去除 AI 寫作痕跡，讓文字聽起來更像真人寫的。

基於維基百科 [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) 歸納的 24 種 AI 寫作特徵，辨識並修正包含：誇大象徵意義、宣傳性語言、膚淺的 -ing 分析、模糊歸因、破折號過度使用、三段式法則、AI 詞彙、否定式排比、過度填充短語等。

---

## 上游鏈條與致謝 Attribution

本專案有完整的上游依賴鏈，依照 MIT 授權保留所有上游著作權：

```
blader/humanizer (英文原版)
        ↓ 翻譯 + 加上 50 分制評分表
op7418/Humanizer-zh (簡體中文版)
        ↓ 繁簡轉換
本專案 humanizer-zh-tw (繁體中文版)
```

| 層級 | 專案 | 作者 | 貢獻 |
|---|---|---|---|
| 1 | [blader/humanizer](https://github.com/blader/humanizer) | Siqi Chen ([@blader](https://github.com/blader)) | 英文原版：24 模式架構、Wikipedia 分類法、雙重審查流程、「Personality and Soul」章節 |
| 2 | [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh) | 歸藏 ([@op7418](https://github.com/op7418)) | 簡體中文翻譯、**新增 5 維度 50 分制品質評分表** |
| 3 | 本專案 | 九月筍 | 簡體 → 繁體中文轉換與在地化調整 |

> op7418 自述亦參考了 [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop)（MIT），一併致謝。

### 本專案的實際貢獻

**誠實說明**：本專案主要貢獻是**將 op7418 的簡體中文版轉換為繁體中文**，並做了台灣用語的在地化調整（例如「軟體」而非「软件」、「文字」而非「文本」、「品質」而非「质量」等）。

本專案**沒有**新增任何新的 AI 寫作模式，也**沒有**修改核心的處理流程與評分表。所有技術骨幹來自 blader，所有評分表設計來自 op7418。

如果你只需要簡體中文版，請直接使用 [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh)。

---

## 安裝 Installation

本 skill 是 [unbias38/my-claude-skills](https://github.com/unbias38/my-claude-skills) 集合中的其中一個。

**只安裝這一個 skill（sparse-checkout）：**

```bash
git clone --filter=blob:none --sparse https://github.com/unbias38/my-claude-skills.git
cd my-claude-skills
git sparse-checkout set humanizer-zh-tw
cp -r humanizer-zh-tw ~/.claude/skills/
```

**或 clone 整包再複製：**

```bash
git clone https://github.com/unbias38/my-claude-skills.git
cp -r my-claude-skills/humanizer-zh-tw ~/.claude/skills/
```

---

## 使用 Usage

在 Claude Code 中直接呼叫：

```
/humanizer-zh-tw
```

或將 skill 作為 Task 工具傳入待處理的文字。

### 範例

**輸入（AI 味道）：**
> 新的軟體更新作為公司致力於創新的證明。此外，它提供了無縫、直觀和強大的使用者體驗——確保使用者能夠高效地達成目標。這不僅僅是一次更新，而是我們思考生產力方式的革命。

**輸出（人性化）：**
> 這次更新加了批次處理、快捷鍵和離線模式。測試的人反應不錯，主要是覺得做事比以前快了。

---

## 核心原則

1. **刪除填充短語** — 去除開場白和強調性支撐詞
2. **打破公式結構** — 避免二元對比、戲劇性分段、修辭性設置
3. **變化節奏** — 混合句子長度，兩項優於三項
4. **信任讀者** — 直接陳述事實，跳過軟化與過度引導
5. **刪除金句** — 如果聽起來像可引用的語句，重寫它

## 處理流程

1. 辨識 24 種 AI 寫作模式
2. 改寫有問題的片段
3. 進行自我批判：「下面這段文字哪裡還是一看就像 AI 寫的？」
4. 根據批判再次改寫
5. 用 5 維度 50 分制評估品質（直接性 / 節奏 / 信任度 / 真實性 / 精煉度）

## 24 種 AI 寫作模式

**內容模式 (1–6)**：誇大意義、宣傳性媒體報導、膚淺 -ing 分析、宣傳廣告式語言、模糊歸因、提綱式「挑戰與未來」段落

**語法模式 (7–12)**：AI 詞彙、繫詞迴避、否定式排比、三段式法則、刻意換詞、虛假範圍

**風格模式 (13–18)**：破折號過度、粗體過度、內嵌標題列表、標題首字母大寫、表情符號、彎引號

**交流模式 (19–21)**：共用交流痕跡、知識截止免責、諂媚語氣

**填充詞 (22–24)**：填充短語、過度限定、通用積極結論

---

## 授權 License

**MIT License**

本專案依照 MIT 授權重新發佈，保留了所有上游著作權聲明。詳見 [LICENSE](./LICENSE)。

- Copyright (c) 2026 Siqi Chen (blader/humanizer)
- Copyright (c) 2026 歸藏 / op7418 (Humanizer-zh)
- Copyright (c) 2026 九月筍 (繁體中文版)

---

## 相關資源

- [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) — 本 skill 的理論基礎
- [blader/humanizer](https://github.com/blader/humanizer) — 英文原版（13,000+ ⭐）
- [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh) — 簡體中文版（6,000+ ⭐）
- [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop) — 另一個相關的 AI 寫作清理工具
