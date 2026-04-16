---
name: survey-design
description: Design publication-quality academic questionnaires with self-evaluation scoring. Use this skill when users want to design a survey, questionnaire, or measurement scale for academic research or journal submission. Also trigger when users mention scale development, questionnaire validation, Likert scale design, construct measurement, or psychometric instrument development — even if they don't explicitly say "survey design."
---

# Academic Survey/Questionnaire Design

Design questionnaires that meet academic publication standards, with built-in self-evaluation based on COSMIN, Dillman, and psychometric best practices.

## When to Use

- User wants to design a questionnaire or scale for research
- User needs to measure a psychological, behavioral, or social construct
- User is preparing a survey instrument for journal submission
- User asks about questionnaire methodology (construct definition, item writing, validation)

## Input

Collect the following from the user before starting. If any required field is missing, ask for it.

**Required:**
1. **Research purpose** — What research question does this questionnaire answer?
2. **Target construct** — What are you measuring? (one or more constructs)
3. **Target population** — Who will fill out this questionnaire?
4. **Language** — Questionnaire language (default: same as conversation language)

**Optional:**
- Existing theory or model
- Expected sub-dimensions
- Item count limit
- Special needs (cross-cultural, specific population, etc.)

## Process

The workflow has two phases: an alignment phase (interactive) and an execution phase (autonomous).

### Phase 1: Align — Construct Definition (interactive)

This is the only phase that requires user confirmation. Getting the construct definition and sub-dimensions right is critical because everything downstream depends on it. If this is wrong, the entire questionnaire is wasted effort.

#### Step 1: Load Reference Frameworks

Read all four reference files:
- [COSMIN content validity framework](./reference/cosmin.md) — evaluation criteria for measurement instruments
- [Dillman survey design principles](./reference/dillman.md) — item writing and questionnaire structure rules
- [Common pitfalls checklist](./reference/common-pitfalls.md) — defects to actively avoid
- [Self-evaluation rubric](./reference/rubric.md) — scoring rubric for the finished questionnaire

#### Step 2: Propose Construct Definition

Based on the user's research purpose, present the following to the user for confirmation:

1. **Operational definition** of the construct (cite supporting literature/theory)
2. **Distinction from related concepts** — how it differs from similar constructs
3. **Existing validated scales** — list them, compare, explain why a new instrument is needed (or recommend adopting an existing one if it fits)
4. **Sub-dimension decomposition** with definition and source for each
5. **Item blueprint** — sub-dimension × planned item count

Present it in this format:

```
## Construct Definition
[Operational definition]

## Distinction from Related Concepts
[How this construct differs from similar concepts]

## Existing Scale Review
| Scale | Author | Features | Reason for not adopting |
|-------|--------|----------|----------------------|

## Sub-dimension Decomposition
| Sub-dimension | Definition | Source | Planned items |
|---------------|-----------|--------|---------------|
```

Then ask the user: **"Does this decomposition look right? Any sub-dimensions to add, remove, or rename?"**

Wait for the user to confirm or adjust before proceeding. If the user changes the sub-dimensions, update the blueprint accordingly.

### Phase 2: Execute — Design & Output (autonomous)

Once the user confirms the construct definition, execute Steps 3–6 without stopping.

#### Step 3: Item Design

Design items for each sub-dimension following Dillman principles. Actively check against the common-pitfalls checklist.

Each item must include:
- Item ID (dimension code + number, e.g., A1, A2, B1...)
- Item text
- Response format (scale type and options)
- Sub-dimension assignment
- Forward/reverse scoring indicator

Design rules:
- One idea per item (no double-barreled questions)
- Neutral wording (no leading language)
- Clear time frame where applicable
- Simple language appropriate for the target population
- Reverse items should not exceed 20-30% of total items
- Each factor needs at least 3-5 items for factor analysis

#### Step 4: Questionnaire Structure

1. Write **questionnaire instructions** (opening statement for respondents)
2. Arrange **item order** following Dillman ordering principles:
   - Start with easy, engaging items
   - Place sensitive items later
   - Demographics at the end
3. Design **section structure** with section titles and section instructions
4. Add **filter questions** and **skip logic** if needed
5. Arrange **demographic items** at the end

#### Step 5: Self-Evaluation & Auto-Remediation Loop

**5a. Run self-evaluation**

Read `reference/rubric.md` and score each of the 24 items honestly. Be honest — the purpose is to find weaknesses, not inflate scores. Write the justification for each score specifically (why this score, not 4 or 2).

**5b. Auto-remediation loop** (only if any item scored below 3)

The rubric defines the 5/5 state for each criterion. If an item is below 3, apply the specific fix to move it toward the 5/5 definition. Do NOT modify items that are already ≥3 — don't let chasing a higher total score create new problems.

Loop structure:

```
iteration = 0
MAX_ITERATIONS = 3

while any item < 3 AND iteration < MAX_ITERATIONS:
    iteration += 1
    
    For each item scoring < 3:
      - Identify the specific fix based on the rubric's 5/5 definition
        and relevant entries in reference/common-pitfalls.md
      - Apply the fix (edit items, add reverse items, add a note, etc.)
      - Record what changed (item IDs affected, before/after text if applicable)
    
    Re-score ONLY the items that were below 3 (don't re-score the whole rubric)
    
    Announce to user:
      "Iteration [N]:
       - Fixed: F2 (2→4) — added 2 reverse items (A5R, C5R)
       - Fixed: C4 (3→4) — same reverse items serve as attention checks
       - Remaining below 3: [list] / none"
```

**5c. Termination**

- **All items ≥3 within 3 iterations** → proceed to Step 6 with a changelog
- **Still below 3 after 3 iterations** → stop the loop. Proceed to Step 6 but flag the unresolved items in the delivery summary with an explanation (possible reasons: the criterion conflicts with user requirements, the construct is fundamentally hard to test on this dimension, etc.). Ask the user how to proceed.

**5d. Guardrails**

- Don't over-optimize. If a fix for one criterion would genuinely hurt another (e.g., adding reverse items to satisfy F2 but pushing C4 out of its optimal range), note the trade-off rather than chasing both scores.
- Don't invent new items or sub-dimensions in the loop. Only refine what's already there. Structural changes (new sub-dimensions, different theoretical framework) require going back to Phase 1.
- Keep the changelog factual. "Added 2 reverse items" not "Improved the questionnaire."

### Step 6: Output

Produce **3 files** in an `output/` folder — one per audience.

#### File 1: `questionnaire.md` — For respondents

Clean questionnaire only. No metadata, no variable names, no scoring information.

```
# [Questionnaire Title]

[Opening instructions — purpose, anonymity, time estimate, response format]

## Part 1: [Section Title] ([N] items)

> [Section instructions]

| # | Item | 1 [anchor] | 2 [anchor] | 3 [anchor] | 4 [anchor] | 5 [anchor] |
|---|------|---|---|---|---|---|
| 1 | [item text] | ○ | ○ | ○ | ○ | ○ |

## Part N: Demographics

1. [demographic item with options]
```

#### File 2: `documentation.md` — For the researcher

Combines codebook and methods into a single researcher reference. Use this structure:

```
# [Questionnaire Title] — Documentation

## 1. Construct Definition
[Operational definition, distinction from related concepts]

## 2. Existing Scale Review
| Scale | Author | Features | Reason for not adopting |
|-------|--------|----------|----------------------|

## 3. Sub-dimension Decomposition & Item Blueprint
| Sub-dimension | Definition | Source | Items |
|---------------|-----------|--------|-------|

## 4. Design Decisions
[Item writing principles applied, response format rationale, ordering logic, bias control measures. Cite reference/ frameworks.]

## 5. Codebook

### Variable Table
| Variable | Survey# | ItemID | Sub-dimension | Direction | Scoring |
|----------|---------|--------|---------------|-----------|---------|

### Scoring Instructions
[Sub-dimension scores, composite scores, reverse scoring, missing data handling]

## 6. References
```

#### File 3: `expert-review-form.md` — For domain experts

Read the template at `assets/expert-review-template.md`. Fill in all `{{placeholder}}` fields with the actual questionnaire content:
- Replace `{{QUESTIONNAIRE_NAME}}`, `{{CONSTRUCT}}`, `{{POPULATION}}` with questionnaire info
- For each sub-dimension, create a section with its name, definition, and item table
- Fill `{{ID}}` and `{{ITEM_TEXT}}` for every item
- Keep the CVI calculation tables at the bottom intact — those are for the researcher to fill after collecting expert ratings

#### Step 7: Delivery

Present results **directly in the conversation** — do not save self-evaluation as a file.

**7a. Final self-evaluation**

```
## Self-Evaluation: [XX]/120 (Grade [X])

| Dimension | Max | Score |
|-----------|-----|-------|
| A. Construct Definition | 15 | [X] |
| ... | | |
| **Total** | **120** | **[X]** |
```

**7b. Revision changelog** (only if the auto-remediation loop ran)

```
## Revisions Made

| Iteration | Item | Before | After | Change |
|-----------|------|--------|-------|--------|
| 1 | F2 | 2/5 | 4/5 | Added 2 reverse items (A5R, C5R) for attention checking |
| 1 | C4 | 3/5 | 4/5 | Same reverse items serve C4's purpose |
| 1 | F3 | 2/5 | 4/5 | Added within-section randomization note to instructions |
```

**7c. Unresolved items** (only if loop terminated with items still below 3)

```
## Unresolved Items After 3 Iterations

| Item | Final Score | Why Still Below 3 | Options for You |
|------|------|------|------|
| [ID] | [X]/5 | [explanation] | [A: accept as trade-off / B: restart with different approach / C: other] |
```

**7d. Output summary & next steps**

```
## Output Summary

| File | Audience | Next Action |
|------|----------|-------------|
| `questionnaire.md` | Respondents | Review wording, upload to survey platform |
| `documentation.md` | You (researcher) | Reference during analysis and paper writing |
| `expert-review-form.md` | Domain experts | Send to 5-7 experts for CVI assessment |

## Recommended Next Steps
1. [If unresolved items exist: address them first]
2. Send `expert-review-form.md` to 5-7 domain experts
3. After collecting expert ratings, calculate CVI using the form's built-in tables
4. Pilot test with 30-50 members of your target population
5. Run item analysis and exploratory factor analysis on pilot data
```

Adjust the next steps based on the final state — if there are unresolved items, that's the top priority, not expert review.

## Important Notes

- All design decisions must be traceable to principles in `reference/`
- If the user's research purpose is unclear, clarify before proceeding
- Do not add unnecessary items just to increase count
- If an existing validated scale fits the user's needs well, recommend adopting it instead of designing from scratch — explain how to properly cite and adapt it
- Use the conversation language for the questionnaire; keep technical terms in their original language
