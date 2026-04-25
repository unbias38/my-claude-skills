---
name: paper-language-pass
description: Multi-agent staged language polish for academic manuscripts whose science is already settled (post peer-review). Runs seven parallel specialist subagents — consistency, tense, hedging, prose, coherence, abstract, and manuscript hygiene (reviewer-talk, journal sycophancy, and implementation-detail leakage including untaken fallback paths) — each scanning the whole paper for one dimension. Venue- and discipline-agnostic — user provides venue rules (citation policy, tense, spelling, word limit, etc.) and the skill calibrates severity accordingly; unspecified rules fall back to general academic defaults with downgraded flags. Produces a unified, severity-ranked, numbered issue list, then waits for user approval before applying any fix. Use when the user has a near-final draft (.docx, .md, or .tex) and wants a systematic language pass. Trigger phrases include "language pass", "polish my paper", "proofread my manuscript", "tense check", "hedging check", "整篇 polish", "潤稿", "投稿前最後檢查".
---

# Paper Language Pass

## When to use

The user has a complete academic manuscript whose **science is already validated** (peer review done, reviewers' substantive concerns addressed) and wants a **language-layer polish across the entire paper**. Seven specialist subagents run in parallel, each scanning the whole paper for a single dimension of writing quality:

| Pass | Subagent | Looks for |
|---|---|---|
| 1 | Consistency auditor | Term/acronym/capitalization/number/unit/hyphenation consistency |
| 2 | Tense auditor | Section-appropriate tense, within-section consistency, et al. agreement |
| 3 | Hedging auditor | Claim-strength calibration, overclaiming, under-hedging, abstract-body alignment |
| 4 | Prose polisher (review only) | Grammar, nominalization, fillers, awkward phrasing, AI tells |
| 5 | Coherence reviewer | Paragraph claim-first, transitions, argument chaining, repetition |
| 6 | Abstract auditor | WHY→PROBLEM→HOW→RESULTS structure, acronyms, no citations, single paragraph |
| 7 | Manuscript hygiene auditor | Three classes of phrasing that leak from adjacent genres into the manuscript body and never belong there: (A) reviewer / editor process meta-discourse, (B) journal self-reference / sycophancy, (C) implementation / engineering-detail leakage including untaken fallback paths |

This skill is **not** for: initial drafting, content review, scientific critique, figure/table data verification, statistics. Those are upstream concerns.

## Workflow

### Step 0 — Pre-flight

Confirm with the user:

1. **Manuscript path** — single file (`.docx`, `.md`, `.tex`) or root file plus included sections.
2. **Target venue** — affects voice, hedging tolerance, and length expectations. If unknown, proceed with general academic defaults.
3. **Venue rules** — a short free-form list of known conventions for the target venue. This is what stops the skill from hard-coding one discipline's habits onto another. Collect whichever of these the user knows (ask once; do not interrogate field by field):

   | Key | Example values | Used by |
   |---|---|---|
   | `abstract-citations` | `forbidden` / `allowed` / `unspecified` | Pass 6 |
   | `abstract-word-limit` | `250` / `150–250` / `unspecified` | Pass 6 |
   | `methods-tense` | `past-required` / `present-accepted` / `unspecified` | Pass 2 |
   | `results-tense` | `past-required` / `present-accepted` / `unspecified` | Pass 2 |
   | `spelling` | `UK` / `US` / `either` | Pass 1 |
   | `reporting-guidelines` | `CONSORT` / `STROBE` / `PRISMA` / `none` | context only |
   | `citation-style-in-body` | `author-year` / `numeric` / `footnote` | Pass 1 |
   | `hedging-default` | `conservative` / `standard` / `assertive` | Pass 3 |

   If the user does not know a value, mark it `unspecified` — the skill falls back to general academic defaults and downgrades the corresponding severity flags from CRITICAL to MAJOR, with a note recommending the user verify against 2–3 recent target-venue papers.

   The user can also pass free-form notes (e.g., `reviewers at this venue heavily flag causal language for observational designs`) — these get injected into Pass 3 and Pass 4 prompts.

4. **Which passes to run** — default is all six. The user may request a subset (e.g., "only Pass 2 and 3").
5. **Format-specific notes**:
   - `.docx`: read with the `docx` skill if available, otherwise convert to text for analysis. Phase 2 fixes use tracked changes.
   - `.tex`: read root file, follow every `\input{}` and `\include{}` recursively. Pass 1 may flag LaTeX-specific patterns (cite style, thin space).
   - `.md`: read as-is.
6. **Skip suggestions**: if the user explicitly says peer review covered structure/claims, you may de-emphasize Pass 5/6 — but never skip silently.

### Step 1 — Phase 1: parallel detection

Spawn the selected pass subagents **in parallel** using the `Agent` tool (one Agent call per pass, all in a single assistant message so they execute concurrently).

For each pass:

- **Subagent type**: `general-purpose`
- **Description** (3–5 words): e.g., `Pass 1 consistency audit`
- **Prompt template**:
  ```
  You are running Pass <N> of a multi-pass language audit on an academic manuscript.

  Your full instructions, persona, checklist, severity guide, and required output
  format are in this reference file:

      <ABSOLUTE_PATH>/references/pass<N>-<name>.md

  Read that file first, then read the manuscript at:

      <MANUSCRIPT_PATH>

  (For .tex: follow every \input{} and \include{} recursively before producing
  output. For .docx: use Read on the file directly; if Read returns binary,
  request a markdown extract first.)

  Target venue: <venue or "general academic">.

  Venue rules (apply when calibrating severity; treat any "unspecified" key as
  general academic default and downgrade the corresponding flag from CRITICAL
  to MAJOR with a note recommending the user verify against 2–3 recent
  target-venue papers):
      abstract-citations: <forbidden | allowed | unspecified>
      abstract-word-limit: <number | range | unspecified>
      methods-tense: <past-required | present-accepted | unspecified>
      results-tense: <past-required | present-accepted | unspecified>
      spelling: <UK | US | either>
      reporting-guidelines: <CONSORT | STROBE | PRISMA | none>
      citation-style-in-body: <author-year | numeric | footnote>
      hedging-default: <conservative | standard | assertive>
  Free-form venue notes from user: <verbatim or "none">

  Detect only — do NOT modify any file. Output the numbered issue list exactly
  in the format specified in the reference file. Use the prefix [<N>-K] for
  every issue.
  ```

Run all selected passes in one message so they execute concurrently. Do not run sequentially unless the user requests it.

### Step 2 — Synthesize

When all subagents return:

1. **Merge** all issues into a single list, preserving the `[N-K]` prefixes (so the user can trace which pass flagged what).
2. **Re-group by severity** (CRITICAL → MAJOR → MINOR → STYLE), not by pass.
3. **Produce an executive summary**:
   ```
   Paper language quality: GOOD / NEEDS REVISION / MAJOR REVISION

   By severity:
   | CRITICAL | N |
   | MAJOR    | N |
   | MINOR    | N |
   | STYLE    | N |

   By pass:
   | Pass 1 Consistency | N issues |
   | Pass 2 Tense       | N issues |
   | Pass 3 Hedging     | N issues |
   | Pass 4 Prose       | N issues |
   | Pass 5 Coherence   | N issues |
   | Pass 6 Abstract    | N issues |

   Most common patterns across passes:
   - …
   - …

   Top 5 issues to address first (by severity + likely reviewer impact):
   - [N-K] …
   - …
   ```
4. **Append the merged issue list**, severity-grouped, then **the per-pass detail reports** (so the user can dive deeper into any one pass).
5. **Stop. Do not modify any file yet.**

### Step 2.5 — Recommendation

Most users do not want to read 100+ issues and decide one by one. After the synthesis but before the menu, give a **tiered recommendation** that classifies issues by how safe and how high-leverage they are. Use this template:

```
## Recommendation

I do **not** suggest blindly applying every fix. Here is why and what I would prioritise:

**Why not `proceed with all`:**
- Hedging is judgement-dependent — over-softening every claim can make the paper read as under-confident, and reviewers will flag that too.
- Section-wide tense rewrites (Methods/Results) change the paper's voice, not just its grammar. **Tense convention is venue-dependent — verify against 2–3 recent papers in the target venue before bulk-applying.** Finance/econ journals frequently accept present tense; medical journals strongly prefer past.
- **Em-dash sweeps are usually counterproductive.** Em dashes are legitimate academic punctuation; aggressive removal can read worse than the original and may itself signal "LLM-washed text". Only act on em-dash flags where they cluster (multiple per paragraph) or stack with other AI tells.
- **AI-tell flags are pattern signals, not lint errors.** Symmetric pivots (`X rather than Y`), triadic enumerations, and vague intensifiers are normal academic English in moderation. They become tells only when used mechanically and densely. A few occurrences in a 10,000-word manuscript do not warrant removal.
- **Domain conventions matter.** Finance papers naturally use nominalization (`the estimation of`), introduction narrative naturally uses intensifiers (`rapidly`, `dramatically`), and humanities/CS/finance/medicine each have different baseline expectations. The skill flags general patterns; the author judges domain fit.
- Coherence-level structural suggestions (split a subsection, reorder paragraphs, consolidate limitations) are editorial decisions, not polish.
- Many STYLE items are taste calls; applied wholesale they can flatten the author's rhythm.

**Tiered priority for this paper:**

| Tier | What to fix | Why |
|---|---|---|
| **Must fix** | All N CRITICAL issues that are *factual errors, broken grammar, venue-rule violations, or claim-evidence mismatches* | These are unambiguous reviewer red flags |
| **Strongly recommend** | Pass 1 mechanical consistency (spelling, dashes, cross-ref style, undefined acronyms) + all of Pass 6 (abstract is the front door) | Zero risk, pure upside |
| **Recommend** | Pass 4 *clustered* AI-tells (em dashes appearing >2× per paragraph, mechanical triadic openers); single-instance grammar fixes; clear filler removal | Targeted improvements that read dramatically better |
| **Judgement call (verify before applying)** | Pass 3 hedging MAJOR/MINOR; Pass 2 tense flags marked CRITICAL or MAJOR for whole-section patterns | Hedging strength is voice-dependent; tense is venue-dependent (check 2–3 recent target-venue papers before bulk-applying tense changes) |
| **Author decision** | Pass 5 structural suggestions | Not polish — editorial judgement |
| **Mostly skip** | Pass 4 STYLE items: isolated em dashes, single `rather than` constructions, individual intensifiers in narrative sections, single triadic lists, single filler openers | Often taste or domain-conventional; applied wholesale they erase voice |

**Caveat to the audit itself:** the six subagents are pattern matchers. They cannot tell whether a `rather than` construction is mechanical or rhetorically structural; whether nominalization is awkward or genre-appropriate; whether present-tense Methods is wrong or venue-conventional. Treat the audit as a list of *candidates for review*, not a list of *required fixes*. When in doubt, leave the original.

**Two practical commands:**

- **Conservative path (low risk, fast):** `fix critical only` — clears the N must-fix items, ~half-hour turnaround, leaves nothing reviewer-embarrassing.
- **Recommended path (proper polish):** `proceed with all, discard <list>` — I can pre-build the discard list for the Style/Structural items so you only review what matters. Reply `build my discard list` and I will draft it.

Pick the conservative path if you are submitting this week. Pick the recommended path if you have at least a week of buffer.
```

Tailor the wording and the recommended discard list to what the audit actually found. If a pass returned almost no issues, drop it from the tier table. If the paper is clean overall (e.g., <5 CRITICAL, <20 total), say so and recommend `proceed with all`.

### Step 3 — Phase 1 complete: prompt the user

Conclude the synthesis output with this menu (verbatim):

```
Phase 1 complete — awaiting your decision.

Reply with one of:
- `fix safe`          fix only definite typos, duplicate words, and unambiguous grammar errors
- `fix critical only` fix only CRITICAL issues
- `proceed with all`  fix every detected issue
- `discard 1-3, 1-7, 4-12`  skip specific issue numbers (any others get fixed)
- `only pass N`       fix only issues from a specific pass
- `build my discard list`  draft a discard list following the recommendation above
- `show pass N`       re-display the full report for one pass
- `nothing — I'll fix manually` exit without edits

I will not modify any file until you confirm.
```

### Step 4 — Phase 2: apply approved fixes

Once the user confirms a scope:

1. **Build the fix set** based on the user's reply. If the user replied `build my discard list`, draft the discard list per the tiered recommendation (typically: most STYLE items beyond em dashes/fillers, Pass 5 structural suggestions, low-impact Pass 3 hedging where the paper is already calibrated), then present it for one round of approval before applying. Do not begin Phase 2 edits until the user confirms the proposed discard list.
2. **For each fix**, apply the smallest possible edit that resolves the issue. Do not rewrite surrounding sentences.
3. **Format-specific behavior**:
   - `.docx`: use the `docx` skill to apply edits as **tracked changes** so the user can accept/reject. Do not silently overwrite.
   - `.md` / `.tex`: use the `Edit` tool for each change. Group consecutive edits to the same file when possible.
4. **No em dashes** in any fix you write. Use comma, semicolon, colon, or restructure (em dashes are an AI tell flagged by Pass 4).
5. **Preserve formatting and citations.** Do not remove `\cite{}`, `\ref{}`, or markdown links unless the issue specifically required it and the user approved.
6. **Report back** with a summary:
   ```
   Phase 2 complete.
   Fixed: 23 issues (8 CRITICAL, 12 MAJOR, 3 MINOR)
   Skipped: 7 issues (per your discard list)
   Files modified: <list>
   ```

If a flagged issue requires authorial judgment (e.g., a hedging rewrite where the right strength depends on data the user has but the model cannot verify), surface it back to the user instead of guessing.

### Step 5 — Iterate

Offer to re-run any single pass after fixes are applied (especially Pass 1 consistency, which can shift after Pass 4 prose edits).

## Pass reference files

Detailed checklists, persona, and output formats for each pass live in `references/`:

- [Pass 1 — Consistency](references/pass1-consistency.md)
- [Pass 2 — Tense](references/pass2-tense.md)
- [Pass 3 — Hedging](references/pass3-hedging.md)
- [Pass 4 — Prose Polish](references/pass4-prose.md)
- [Pass 5 — Coherence](references/pass5-coherence.md)
- [Pass 6 — Abstract](references/pass6-abstract.md)
- [Pass 7 — Manuscript Hygiene](references/pass7-manuscript-hygiene.md)

Each subagent reads its corresponding reference file as its full instruction set. The orchestrator (this SKILL.md) does not duplicate that content — it routes work and synthesizes results.

## Design principles

- **Detect first, fix later.** Never modify files before the user confirms which issues to fix.
- **One dimension per agent.** Each subagent looks at the whole paper but focuses on a single dimension. This avoids the "checklist sprawl" that happens when one agent tries to check everything at once.
- **Parallel by default.** Seven concurrent agents finish faster than seven sequential ones, and their outputs do not depend on each other.
- **Prefix issues by pass.** Numbering as `[N-K]` lets the user discard or focus by pass without re-numbering.
- **Stay above science.** This skill assumes the science is settled. It does not check methods, statistics, claims, or experimental design. Direct the user to a `peer-review` skill or `scientific-critical-thinking` skill for that.
- **Preserve voice.** Phase 2 fixes target the smallest correct change, not a full rewrite. The author's voice belongs to the author.
- **Calibrate to domain and venue.** Tense norms, nominalization tolerance, hedging strength, and acceptable rhetorical structures vary across disciplines and even across journals within a discipline. A pattern that is "wrong" in CS may be conventional in finance. The skill flags general patterns; the user (and a venue check) decides domain fit. When the synthesizer recommends action, it must explicitly note venue-dependence for tense and domain-dependence for AI-tell items.
- **Pattern signals, not lint errors.** AI tells (em dashes, triadic enumerations, symmetric pivots, intensifiers) are signals only when they cluster mechanically. Single occurrences are normal academic English. Aggressive blanket removal often produces worse text than the original and may itself read as suspicious.
- **Audit ≠ required fixes.** The six subagents are pattern matchers, not editors. The output is a list of candidates for human review, never a list of required edits. The recommendation step exists precisely to push back against the temptation to "fix everything the audit found".
