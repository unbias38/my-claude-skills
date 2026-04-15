# My Claude Skills

自製的 Claude Skills 收藏。想到有用的就加進來。

## Skills

| Skill | 說明 |
|---|---|
| [hackmd-note](./hackmd-note) | 寫充分運用 HackMD 語法的筆記（色塊、收合、mermaid、簡報模式等 36 類語法） |
| [humanizer-zh-tw](./humanizer-zh-tw) | 去除 AI 寫作痕跡，基於 24 種模式 + 50 分制評分。繁中版，衍生自 blader/humanizer → op7418/Humanizer-zh |

## 安裝

把想用的 skill 資料夾複製到 Claude 的 skills 目錄：

**macOS / Linux：**

```bash
git clone https://github.com/unbias38/my-claude-skills.git
cp -r my-claude-skills/hackmd-note ~/.claude/skills/
```

**Windows (Git Bash)：**

```bash
git clone https://github.com/unbias38/my-claude-skills.git
cp -r my-claude-skills/hackmd-note "$HOME/.claude/skills/"
```

**Windows (PowerShell)：**

```powershell
git clone https://github.com/unbias38/my-claude-skills.git
Copy-Item -Recurse my-claude-skills/hackmd-note "$env:USERPROFILE/.claude/skills/"
```

安裝完重啟 Claude Code 即可使用。

## 只想安裝單一 skill？

用 git sparse-checkout 只抓你要的：

```bash
git clone --filter=blob:none --sparse https://github.com/unbias38/my-claude-skills.git
cd my-claude-skills
git sparse-checkout set hackmd-note
```

## 觸發方式

各 skill 的觸發條件寫在各自的 `SKILL.md` 裡，Claude 會自動判斷何時啟用。

例如 `hackmd-note` 會在你提到 HackMD、hackmd 筆記，或要求產生 HackMD 格式輸出時自動觸發。
