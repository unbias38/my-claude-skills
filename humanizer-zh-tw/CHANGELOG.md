# Changelog

本檔案記錄 humanizer-zh-tw 的版本變更。

格式參考 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)，
版本號依循 [Semantic Versioning](https://semver.org/lang/zh-TW/)。

---

## [2.3.0-zh-tw] - 2026-04-15

### 首次釋出 (Initial Release)

這是 humanizer-zh-tw 的首次公開發佈，基於 [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh) 進行繁體中文轉換。

### 轉換內容 Converted from op7418/Humanizer-zh

- 簡體中文 → 繁體中文全文轉換
- 用語在地化（台灣慣用詞）：
  - `软件` → `軟體`
  - `文本` → `文字`
  - `质量` → `品質`
  - `默认` → `預設`
  - `信息` → `資訊`
  - `数据` → `數據`（金融／量化相關）、`資料`（一般用法）
  - `响应` → `回應`
  - `框架` → `架構`
  - 其他台灣慣用詞調整
- 保留 op7418 原版結構：
  - 24 種 AI 寫作模式
  - 5 大分類（內容 / 語法 / 風格 / 交流 / 填充）
  - 核心規則速查、個性與靈魂、快速檢查清單
  - **5 維度 50 分制品質評分表**（op7418 原創貢獻）

### 保留 blader/humanizer 原版特色

所有以下項目皆為 blader 原版設計，經 op7418 翻譯後再由本專案繁體化：

- 24 種 AI 寫作模式（Wikipedia 分類法）
- 雙重審查流程（改寫 → 自我批判 → 再改寫）
- 「個性與靈魂」章節（Personality and Soul）
- 完整範例（AI 味道 → 初稿 → 最終稿）

### 沒有新增的東西

本版本**沒有**：

- 新增任何 AI 寫作模式
- 修改核心處理流程
- 修改 50 分制評分表的設計
- 新增任何 skill 功能

如果只需要簡體中文版，請使用上游 [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh)。

### 授權 Licensing

本版本依 MIT 授權重新發佈，完整保留三方著作權：

- Copyright (c) 2026 Siqi Chen (blader/humanizer)
- Copyright (c) 2026 歸藏 / op7418 (Humanizer-zh)
- Copyright (c) 2026 九月筍 (humanizer-zh-tw)

---

## 上游版本對照 Upstream Version Mapping

| 本專案版本 | op7418/Humanizer-zh | blader/humanizer |
|---|---|---|
| 2.3.0-zh-tw | 1.0 (2026-01-19) | v2.1.x–v2.2.x 時代（24 patterns） |

**說明**：版本號 `2.3.0` 對應 blader 當時的版本標記，但在 blader v2.3.0 正式發佈時其實已加入 pattern #25「Hyphenated Word Pair Overuse」（25 patterns）。op7418 及本專案選擇保留 24 patterns 的版本，因為 pattern #25 是英文專屬（中文沒有連字號詞組概念），不適用。

---

## 未來計畫 Future Plans

- [ ] 追蹤 blader/humanizer 的更新（目前已到 v2.5.1，新增了被動語態、hyphenated、persuasive authority tropes 等模式）
- [ ] 評估是否將 blader 新增的非英文專屬模式移植到繁中版
- [ ] 收集繁中使用者回饋，補充台灣在地的 AI 寫作特徵範例
