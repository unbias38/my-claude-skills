---
name: hackmd-note
description: 'Write rich, well-formatted HackMD notes using the full range of HackMD-flavored Markdown syntax. Use this skill when the user asks to create, write, or draft a HackMD note, or when the output target is HackMD. Triggers on mentions of "HackMD", "hackmd note", "hackmd 筆記", or requests for notes with HackMD-specific features (:::info admonition blocks, :::spoiler, {%youtube%}/{%pdf%} embeds, slide decks, book mode). Scope: drafts note *content* only — it does not publish to hackmd.io, call any HackMD API/MCP tool, or manage existing notes.'
---

# HackMD Note Writer

Write information-rich HackMD notes that make full use of HackMD's extended Markdown syntax.

## Before Writing

Read [references/syntax-core.md](references/syntax-core.md) for the core HackMD syntax.
Read [references/syntax-advanced.md](references/syntax-advanced.md) ONLY when the note needs
diagrams (mermaid/graphviz/sequence/flow/markmap/vega), music notation, a slide deck, or book mode.

## Writing Guidelines

1. **Use the right feature for the job.** Pick syntax that enhances readability:
   - `:::info` / `:::warning` / `:::danger` / `:::success` for callouts
   - `:::spoiler` for supplementary details the reader can expand
   - `> [!TIP]` / `> [!NOTE]` / `> [!IMPORTANT]` for inline alerts
   - `==highlight==` for key terms, `++underline++` for emphasis
   - Tables for structured comparisons
   - `[TOC]` when the note has 4+ sections
   - Mermaid / flow / sequence / graphviz diagrams when visualizing processes or relationships
   - MathJax when formulas appear
   - `{%youtube ID %}` / `{%pdf URL %}` / `{%figma URL %}` for embeds

2. **Structure clearly.** Use headings (`##`–`####`), horizontal rules (`---`), and tags (`` ###### tags: `tag` ``). Lead with a brief summary or context block.

3. **Keep it scannable.** Combine prose paragraphs with bullet lists, tables, and diagrams. Avoid walls of text.

4. **Respect the output mode.** If the user asks for a slide deck, use `---` / `----` separators and `slideOptions` YAML. If they ask for a book, use `===` / `---` with list-of-links structure.

5. **Language.** Match the user's language. Default to Traditional Chinese (繁體中文) if the user writes in Chinese.

6. **Output format.** Produce the note as one copy-pasteable block. Because the note itself
   usually contains ``` fences (mermaid, code samples), wrap it in a **four-backtick** fence
   (````markdown ... ````), never a three-backtick one.

## 範圍邊界

本 skill 只負責產出筆記內容（Markdown 文字），保持無副作用。以下不在範圍：

- **發表／上傳**：不呼叫 HackMD API 或 `mcp__hackmd__*` 工具。若使用者要求「發表」且環境有發表用 skill 或 MCP 工具，先用本 skill 完成草稿，再交給該工具/工作流。
- **既有筆記管理**：不列出、更新、刪除使用者的 HackMD 筆記。

未來維護者：不要把 API 發表流程加進本 skill——發表涉及帳號、team 路徑、權限等狀態，屬另一條工作流。
