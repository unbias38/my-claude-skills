---
name: paper-language-pass
description: Multi-agent staged language polish for English-language academic manuscripts whose science is already settled (post peer-review). Runs eight parallel specialist subagents — consistency, tense, hedging, prose, coherence, abstract, manuscript hygiene (reviewer-talk, sycophancy, implementation leakage), and AI-authorship tells (hype adjectives, self-coined jargon, evaluative adverb openers, procedural section roadmaps, recycled arguments, em-dash density) — each scanning the whole paper for one dimension. Venue- and discipline-agnostic — user provides venue rules (citation policy, tense, spelling, word limit, etc.) and the skill calibrates severity accordingly; unspecified rules fall back to general academic defaults with downgraded flags. Produces a unified, severity-ranked, numbered issue list, then waits for user approval before applying any fix. Use when the user has a near-final draft (.docx, .md, or .tex) and wants a systematic language pass. Trigger phrases include "language pass", "polish my paper", "proofread my manuscript", "tense check", "hedging check", "does my paper read as AI-written", "整篇 polish", "潤稿", "投稿前最後檢查", "這篇有沒有 AI 味", "看起來像不像 AI 寫的".
---

# Paper Language Pass

## When to use

The user has a complete academic manuscript whose **science is already validated** (peer review done, reviewers' substantive concerns addressed) and wants a **language-layer polish across the entire paper**. Eight specialist subagents run in parallel, each scanning the whole paper for a single dimension of writing quality:

| Pass | Subagent | Looks for |
|---|---|---|
| 1 | Consistency auditor | Term/acronym/capitalization/number/unit/hyphenation consistency |
| 2 | Tense auditor | Section-appropriate tense, within-section consistency, et al. agreement |
| 3 | Hedging auditor | Claim-strength calibration, overclaiming, under-hedging, abstract-body alignment |
| 4 | Prose polisher (review only) | Grammar, nominalization, fillers, wordiness, awkward phrasing — **sentence level only** |
| 5 | Coherence reviewer | Paragraph claim-first, transitions, argument chaining, organizational redundancy |
| 6 | Abstract auditor | WHY→PROBLEM→HOW→RESULTS structure, acronyms, no citations, single paragraph |
| 7 | Manuscript hygiene auditor | Three classes of phrasing that leak from adjacent genres into the manuscript body and never belong there: (A) reviewer / editor process meta-discourse, (B) journal self-reference / sycophancy, (C) implementation / engineering-detail leakage including untaken fallback paths |
| 8 | AI-authorship tell auditor | Eight tell families measured as whole-manuscript density: hype register (self-praise + literature disparagement), self-coined theoretical jargon, evaluative adverb-comma openers, procedural section roadmaps, near-verbatim argument recycling, em-dash density, signature vocabulary, mechanical rhetorical templates. Reports a **signature score** (families fired out of 8) |

**Why AI tells get their own pass.** These patterns are only meaningful as *density and co-occurrence* measurements across the whole manuscript. One `Notably,` is a word; eleven is a habit. One em dash is punctuation; 4.6 per thousand words is a fingerprint. A sentence-level reviewer cannot tell which one it is looking at, so Passes 1–7 have been explicitly instructed to leave every AI tell to Pass 8, and Pass 8 has been given per-family firing thresholds so it does not blanket-flag normal English. If the user's concern is specifically *"does this read as machine-written"*, Pass 8 is the pass that answers it.

This skill is **not** for: initial drafting, content review, scientific critique, figure/table data verification, statistics. Those are upstream concerns. It is also not for Chinese-language manuscripts or de-AI-flavoring Chinese text — use `humanizer-zh-tw` for that; this skill's passes (spelling, tense, articles, hedging verbs) are English-specific.

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
   | `ai-tell-sensitivity` | `standard` / `strict` / `relaxed` | Pass 8 |

   `ai-tell-sensitivity` is worth asking about explicitly. Set `strict` when the venue or editor is known to screen submissions for machine-generated text, when the author used an LLM anywhere in drafting, or when the author simply wants the tells hunted hard — it lowers every Pass 8 firing threshold by roughly one third and promotes MINOR to MAJOR. Set `relaxed` for venues with a florid house style. Default `standard`.

   If the user does not know a value, mark it `unspecified` — the skill falls back to general academic defaults and downgrades the corresponding severity flags from CRITICAL to MAJOR, with a note recommending the user verify against 2–3 recent target-venue papers.

   The user can also pass free-form notes (e.g., `reviewers at this venue heavily flag causal language for observational designs`) — these get injected into Pass 3, Pass 4, and Pass 8 prompts.

4. **Which passes to run** — default is all eight. The user may request a subset (e.g., "only Pass 2 and 3"). If the user's stated concern is "does this read as AI-written", run Pass 8 plus Passes 3, 4, and 5, not Pass 8 alone — the tells are easier to interpret alongside the claim-strength and coherence findings.
5. **Format-specific notes**:
   - `.docx`: the orchestrator first converts the manuscript to a markdown extract (using the `docx` skill's extraction tooling, or pandoc) saved to the scratchpad, and passes the extract path to every subagent — subagents never read the .docx directly. Phase 2 fixes still target the original .docx, applied as tracked changes.
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
  output. For .docx: the orchestrator has provided a pre-converted markdown
  extract at <EXTRACT_PATH>; read that, but reference locations by section
  heading + quoted text since line numbers will not match the .docx.)

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
      ai-tell-sensitivity: <standard | strict | relaxed>
  Free-form venue notes from user: <verbatim or "none">

  Detect only — do NOT modify any file. Output the numbered issue list exactly
  in the format specified in the reference file. Use the prefix [<N>-K] for
  every issue. Cap your report at the 60 highest-severity issues; if more
  exist, summarize the overflow as pattern counts (e.g. "in order to" ×14
  further instances) instead of listing each.

  Your reference file states which checks belong to you and which belong to
  other passes. Respect those boundaries exactly — every pass runs
  concurrently, so anything you flag outside your remit arrives at the
  synthesizer as a duplicate of another pass's finding.
  ```

For **Pass 8** append this to the prompt:

```
  ai-tell-sensitivity is <standard | strict | relaxed>. On `strict`, lower every
  firing threshold in your reference file by roughly one third and promote MINOR
  to MAJOR. On `relaxed`, raise thresholds by roughly one half. On `standard`,
  use the thresholds as written.

  Report the measurement table for ALL eight families even when a family does
  not fire — the author needs to see the margin, not only the failures. Never
  assert that the manuscript was written by an LLM; report density and
  reviewer-perception risk.
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
   | Pass 7 Hygiene     | N issues |
   | Pass 8 AI tells    | N issues |

   AI-authorship signature: N of 8 families fired
   (driven mainly by: <two or three family names>)

   Most common patterns across passes:
   - …
   - …

   Top 5 issues to address first (by severity + likely reviewer impact):
   - [N-K] …
   - …
   ```
4. **Reproduce Pass 8's signature table verbatim** (the eight-family measurement table with counts, thresholds, and fired/not-fired), immediately after the executive summary. This is the one per-pass artefact worth repeating in full: it is a small table, it is the only quantitative read in the whole audit, and the counts are what let the author judge the flags instead of trusting them. Reproduce the em-dash distribution and vocabulary tally too if Pass 8 flagged those families.
5. **Append the merged issue list**, severity-grouped. Do not re-print the other per-pass reports in full — they remain available via `show pass N`.
6. **Stop. Do not modify any file yet.**

### Step 2.5 — Recommendation

Most users do not want to read 100+ issues and decide one by one. After the synthesis but before the menu, give a **tiered recommendation** that classifies issues by how safe and how high-leverage they are. Use this template:

```
## Recommendation

I do **not** suggest blindly applying every fix. Here is why and what I would prioritise:

**Why not `proceed with all`:**
- Hedging is judgement-dependent — over-softening every claim can make the paper read as under-confident, and reviewers will flag that too.
- Section-wide tense rewrites (Methods/Results) change the paper's voice, not just its grammar. **Tense convention is venue-dependent — verify against 2–3 recent papers in the target venue before bulk-applying.** Finance/econ journals frequently accept present tense; medical journals strongly prefer past.
- **Em dashes need reduction, not elimination.** Pass 8 measured the rate; act on the number, not on the instinct. Below 1.0 per 1,000 words there is nothing to do. Above 2.0 there genuinely is, but the target is roughly 0.5 per 1,000 — not zero. A manuscript scrubbed to zero em dashes reads as scrubbed, and that is now its own signal. Fix the weakest dashes first (parenthetical asides, tacked-on afterthoughts); keep the ones marking a real interruption.
- **AI-tell flags are pattern signals, not lint errors.** Symmetric pivots (`X rather than Y`), triadic enumerations, and vague intensifiers are normal academic English in moderation. Pass 8's firing thresholds already encode this: a family that did not fire produced no MAJOR flags. Where a family *did* fire, though, the measurement is the argument — `Notably ×7, Importantly ×5, Crucially ×3` is not a taste call.
- **Domain conventions matter.** Finance papers naturally use nominalization (`the estimation of`), introduction narrative naturally uses intensifiers (`rapidly`, `dramatically`), and humanities/CS/finance/medicine each have different baseline expectations. The skill flags general patterns; the author judges domain fit.
- Coherence-level structural suggestions (split a subsection, reorder paragraphs, consolidate limitations) are editorial decisions, not polish.
- Many STYLE items are taste calls; applied wholesale they can flatten the author's rhythm.

**Tiered priority for this paper:**

| Tier | What to fix | Why |
|---|---|---|
| **Must fix** | All N CRITICAL issues that are *factual errors, broken grammar, venue-rule violations, or claim-evidence mismatches* + all Pass 7 CRITICAL (reviewer-talk, journal sycophancy, untaken fallback paths — unambiguous genre violations, zero-risk deletions) | These are unambiguous reviewer red flags |
| **Strongly recommend** | Pass 1 mechanical consistency (spelling, dashes, cross-ref style, undefined acronyms) + all of Pass 6 (abstract is the front door) + Pass 8 **T2 coined terminology** and **T1b literature disparagement** | Zero risk, pure upside. Deleting an unearned coined term and specifying a vague gap claim both make the paper strictly better — nobody has ever been rejected for naming fewer things |
| **Recommend** | Every Pass 8 family that **fired**, worked family by family: T3 adverb openers (mostly straight deletions), T6 em dashes down to ~0.5/1,000, T5 recycling clusters, T1a hype adjectives replaced by numbers, T7 hard signatures | Each family is one mechanical sweep with a measured stopping point. These are the highest ratio of reader-perception gain to effort in the whole audit |
| **Judgement call (verify before applying)** | Pass 3 hedging MAJOR/MINOR; Pass 2 tense flags marked CRITICAL or MAJOR for whole-section patterns; Pass 8 **T4 section roadmaps** | Hedging strength is voice-dependent; tense is venue-dependent (check 2–3 recent target-venue papers). T4 requires writing a substantive replacement opener, not deleting — that is authorial work, not a sweep |
| **Author decision** | Pass 5 structural suggestions | Not polish — editorial judgement |
| **Mostly skip** | Pass 4 STYLE items; Pass 8 STYLE items from families that did **not** fire (isolated em dashes below the rate threshold, a single `rather than`, one soft-signature word) | Below-threshold items are noise by construction; applied wholesale they erase voice |

**How to read the signature score.** If Pass 8 reports 5+ of 8 families fired, the tells are the highest-leverage thing in this audit and should be worked before the hedging and tense questions — a screener reacts to them within the first page. If 2 or fewer fired, treat Pass 8's output as minor polish and spend the effort on Passes 1, 3, and 6 instead. The score measures *reviewer-perception risk*, not authorship — say so plainly to the user, and do not repeat any claim that the paper was machine-written.

**Caveat to the audit itself:** the eight subagents are pattern matchers. They cannot tell whether a `rather than` construction is mechanical or rhetorically structural; whether nominalization is awkward or genre-appropriate; whether present-tense Methods is wrong or venue-conventional; whether a coined term is unearned jargon or the paper's actual theoretical contribution. Treat the audit as a list of *candidates for review*, not a list of *required fixes*. When in doubt, leave the original.

**Three practical commands:**

- **Conservative path (low risk, fast):** `fix critical only` — clears the N must-fix items, ~half-hour turnaround, leaves nothing reviewer-embarrassing. Note that Pass 8 almost never emits CRITICAL by design, so this path leaves the AI tells untouched; pair it with `fix ai tells` if the signature score is high.
- **AI-tell path (targeted, measurable):** `fix ai tells` — works only the Pass 8 families that fired, family by family, with a re-measured before/after table at the end. Worth running on its own when the signature score is 5+ even if you skip everything else.
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
- `fix ai tells`      fix only the Pass 8 families that fired
- `only family T3, T6`  fix specific AI-tell families
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
4. **Do not introduce new em dashes** in text you write. Use comma, semicolon, colon, or restructure. This is about not adding to a count Pass 8 may already have flagged; it is *not* a mandate to strip the author's existing em dashes beyond what the approved T6 fixes cover.
   **When applying Pass 8 fixes specifically**, work family by family rather than issue by issue, and respect each family's stopping point:
   - **T6 em dashes**: fix weakest-first and stop at roughly 0.5 per 1,000 words. Never global-replace. Re-count before you stop.
   - **T3 adverb openers**: delete the opener and its comma; do not rewrite the sentence that follows.
   - **T5 recycling**: keep the instance sitting closest to its supporting evidence at full strength; compress the others to a clause or cross-reference. Never delete all instances of a claim.
   - **T1a hype**: replace the adjective with the actual number wherever the number exists in the paper. Where it does not, surface the issue to the user rather than substituting a weaker adjective.
   - **T2 coined terms**: deleting the label usually requires rewording the sentence around it. If the term is load-bearing in more than three places, hand it back to the user as an authorial decision instead of unwinding it yourself.
   - **T4 roadmaps**: these need a written substantive replacement, not deletion. If you cannot write one from the section's actual content, surface it to the user.
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

**Re-run Pass 8 whenever any of its families were fixed**, and show the before/after measurement table side by side. This is the only pass whose output is quantitative, so it is the only one where the author can see that the work landed:

```
| Family | Before | After |
|---|---|---|
| T3 adverb openers | 11 (2.4/1,000) | 2 (0.4/1,000) |
| T6 em dashes      | 21 (4.6/1,000) | 4 (0.9/1,000) |
Signature: 6 of 8 fired → 1 of 8 fired
```

Watch for over-correction on the re-run: if T6 came back at 0.0 per 1,000, or if the prose now reads flattened, say so and suggest restoring one or two of the removed dashes. Landing at zero is a worse outcome than landing at 0.5.

## Pass reference files

Detailed checklists, persona, and output formats for each pass live in `references/`:

- [Pass 1 — Consistency](references/pass1-consistency.md)
- [Pass 2 — Tense](references/pass2-tense.md)
- [Pass 3 — Hedging](references/pass3-hedging.md)
- [Pass 4 — Prose Polish](references/pass4-prose.md)
- [Pass 5 — Coherence](references/pass5-coherence.md)
- [Pass 6 — Abstract](references/pass6-abstract.md)
- [Pass 7 — Manuscript Hygiene](references/pass7-manuscript-hygiene.md)
- [Pass 8 — AI-Authorship Tells](references/pass8-ai-authorship-tells.md)

Each subagent reads its corresponding reference file as its full instruction set. The orchestrator (this SKILL.md) does not duplicate that content — it routes work and synthesizes results.

**Pass boundaries are load-bearing.** Because all eight agents read the whole manuscript at once, any overlap in remit produces duplicate flags that the author has to reconcile by hand. The boundaries are written into the reference files themselves, and the main ones are:

| Question | Owner |
|---|---|
| Does the evidence support this claim's strength? | Pass 3 |
| Is the register inflated regardless of the evidence? | Pass 8 (T1) |
| Is this sentence awkward, wordy, or ungrammatical? | Pass 4 |
| Is this sentence merely carrying an AI-associated pattern? | Pass 8 |
| Is this content filed in the wrong place, or in two places? | Pass 5 |
| Is this sentence reworded and pasted four times? | Pass 8 (T5) |
| Should this section have an orienting opener? | Pass 5 |
| Is every section opening with a procedural to-do list? | Pass 8 (T4) |
| Does this phrasing belong to a different genre (response letter, cover letter, README)? | Pass 7 |

If two passes report the same sentence anyway, keep the flag from the owner in this table and note the other pass's angle in the issue text rather than listing it twice.

## Design principles

- **Detect first, fix later.** Never modify files before the user confirms which issues to fix.
- **One dimension per agent.** Each subagent looks at the whole paper but focuses on a single dimension. This avoids the "checklist sprawl" that happens when one agent tries to check everything at once. It also means each agent must be told what is *not* its job — see the boundary table above.
- **Parallel by default.** Eight concurrent agents finish faster than eight sequential ones, and their outputs do not depend on each other.
- **Prefix issues by pass.** Numbering as `[N-K]` lets the user discard or focus by pass without re-numbering.
- **Stay above science.** This skill assumes the science is settled. It does not check methods, statistics, claims, or experimental design. Direct the user to a `peer-review` skill or `scientific-critical-thinking` skill for that.
- **Preserve voice.** Phase 2 fixes target the smallest correct change, not a full rewrite. The author's voice belongs to the author.
- **Calibrate to domain and venue.** Tense norms, nominalization tolerance, hedging strength, and acceptable rhetorical structures vary across disciplines and even across journals within a discipline. A pattern that is "wrong" in CS may be conventional in finance. The skill flags general patterns; the user (and a venue check) decides domain fit. When the synthesizer recommends action, it must explicitly note venue-dependence for tense and domain-dependence for AI-tell items.
- **Pattern signals, not lint errors.** AI tells (em dashes, triadic enumerations, symmetric pivots, intensifiers) are signals only when they cluster mechanically. Single occurrences are normal academic English. Aggressive blanket removal often produces worse text than the original and may itself read as suspicious.
- **Measure, then judge.** The corollary to the previous principle: "don't over-flag" is not an excuse to under-flag. Pass 8 exists because the difference between a quirk and a habit is a number, and a number settles the argument in either direction. Report the counts even for families that come out clean, so the author sees the margin rather than a verdict.
- **Report perception risk, never authorship.** Pass 8 measures patterns that reviewers screen for. It does not, and cannot, establish that a manuscript was machine-written, and neither the pass nor the synthesizer may say that it does. The finding is always "this fires at N× the normal rate", never "this was written by an LLM".
- **Reduction targets, not zero targets.** Several tells are ordinary English used too often. The fix is to bring the rate down to normal, not to eliminate the pattern. A manuscript with zero em dashes, zero triads, and zero evaluative adverbs reads as laundered, which is the problem the author was trying to avoid.
- **Audit ≠ required fixes.** The eight subagents are pattern matchers, not editors. The output is a list of candidates for human review, never a list of required edits. The recommendation step exists precisely to push back against the temptation to "fix everything the audit found".
