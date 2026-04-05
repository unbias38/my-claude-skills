---
name: hackmd-note
description: Write rich, well-formatted HackMD notes using the full range of HackMD-flavored Markdown syntax. Use this skill when the user asks to create, write, or draft a HackMD note, or when the output target is HackMD. Triggers on mentions of "HackMD", "hackmd note", "hackmd 筆記", or requests for notes with HackMD-specific features (admonition blocks, mermaid diagrams, spoilers, embedded content, slide decks, book mode, etc.).
---

# HackMD Note Writer

Write information-rich HackMD notes that make full use of HackMD's extended Markdown syntax.

## Before Writing

Read [references/hackmd-syntax-reference.md](references/hackmd-syntax-reference.md) to load the complete HackMD syntax reference. This is essential — HackMD supports many features beyond standard Markdown (admonition blocks, spoilers, embedded content, diagrams, slide/book modes, ruby annotations, etc.).

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

2. **Structure clearly.** Use headings (`##`–`####`), horizontal rules (`---`), and tags (`###### tags: \`tag\``). Lead with a brief summary or context block.

3. **Keep it scannable.** Combine prose paragraphs with bullet lists, tables, and diagrams. Avoid walls of text.

4. **Respect the output mode.** If the user asks for a slide deck, use `---` / `----` separators and `slideOptions` YAML. If they ask for a book, use `===` / `---` with list-of-links structure.

5. **Language.** Match the user's language. Default to Traditional Chinese (繁體中文) if the user writes in Chinese.

6. **Output format.** Produce the note content as a single Markdown code block so the user can copy-paste it directly into HackMD.
