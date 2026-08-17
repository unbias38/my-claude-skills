---
name: learn-notes
description: >
  Manage a structured learning notes system (LEARN.md + learns/ folder) that helps non-technical users
  accumulate knowledge over time. Use this skill whenever the user says anything related to learning notes,
  updating LEARN, writing a summary of what was done, recording what was learned, or reviewing past notes.
  Also trigger when a task or project is completed and the user asks to document it. Trigger phrases include:
  "更新 LEARN", "寫學習筆記", "update learn", "記錄一下", "幫我整理筆記", "我學到了什麼",
  "做一下筆記", "做筆記", "做個筆記", "筆記一下", "幫我筆記", "note this down", "take notes",
  "review my notes", "複習", "查 LEARN". Even if the user just says "筆記" or "learn" in the context
  of wrapping up a task, use this skill. IMPORTANT: when the user mentions 筆記/notes in ANY form,
  it ALWAYS means this LEARN.md + learns/ file system in the project — NEVER Claude's internal
  persistent memory. Do not write to Claude's memory directory in response to note-taking requests.
---

# Learn Notes — 學習筆記系統

You are managing a learning notes system for a user who is NOT technical. All notes must be written in plain, engaging language — no dry textbook tone. Use metaphors, analogies, and fun anecdotes to make concepts stick.

## System Structure

```
project-root/
├── LEARN.md              ← Index page (table of contents)
├── learns/
│   ├── YYYYMMDD_topic-A.md
│   ├── YYYYMMDD_topic-B.md
│   └── ...
```

- **`LEARN.md`** (in project root) = **Index page**. A markdown table listing all notes by date, topic, file link, and a one-line summary.
- **`learns/` folder** = **Detailed notes**. One file per topic. Filename format: `YYYYMMDD_topic.md` (e.g., `20260311_claude設定.md`).

## When to Create / Update Notes

Trigger note creation when:
1. The user explicitly asks (e.g., "更新 LEARN", "幫我寫筆記")
2. A task or project has been completed and the user wants to document it

## How to Write the Index (LEARN.md)

If `LEARN.md` doesn't exist yet, create it with this template:

```markdown
# LEARN.md — 我的學習筆記目錄

> 這是目錄頁，詳細內容請看 `learns/` 資料夾裡的各篇筆記。
> 想複習時，跟 Claude 說「幫我查 LEARN」就好！

---

| 日期 | 主題 | 筆記檔案 | 一句話摘要 |
|------|------|----------|-----------|
```

When adding a new entry, append a row to the table. Do not overwrite existing rows.

## How to Write a Detailed Note (learns/*.md)

Each note file should include:

1. **Title** — Date and topic as the heading
2. **我們做了什麼？** — What was accomplished, in plain language
3. **為什麼這樣做？** — The reasoning behind key decisions
4. **學到的小知識** — Bite-sized takeaways the user can remember
5. **遇到的問題與解決方式** (if applicable) — Mistakes, bugs, and how they were fixed. Explain the "why" so the user can recognize similar issues in the future
6. **未來小提醒** (if applicable) — Pitfalls to watch out for, best practices

### Writing Style Rules

- Write in the user's language (default: 繁體中文, unless the user prefers otherwise)
- Explain technical terms like you're talking to a smart friend who has never coded
- Use metaphors liberally (e.g., "API 就像餐廳的菜單，你看菜單點菜，廚房幫你做好送出來")
- Include fun analogies or real-world comparisons to make concepts memorable
- Keep paragraphs short — walls of text are intimidating
- Use tables, bullet points, and headers to break up content
- The tone should feel like a knowledgeable friend explaining things over coffee, not a professor lecturing
- **Obsidian links**: Use `[[雙括號連結]]` for tools, technologies, and concepts mentioned in notes (e.g., `[[Claude Code]]`, `[[Google Sheets]]`, `[[Gemini]]`, `[[Python]]`). This enables knowledge graph visualization when imported into Obsidian. Do NOT add links inside headings, code blocks, or URLs.

## How to Handle "Review" / "複習" Requests

When the user asks to review their notes:
1. Read `LEARN.md` to get the full index
2. Present the list of topics with summaries
3. Ask which topic they'd like to dive into, or offer a quick recap of recent notes
4. Read the relevant file(s) from `learns/` and summarize the key points

## First-Time Setup

If neither `LEARN.md` nor `learns/` exist:
1. Create the `learns/` directory
2. Create `LEARN.md` with the template above
3. Inform the user that the system has been set up and explain briefly how it works
