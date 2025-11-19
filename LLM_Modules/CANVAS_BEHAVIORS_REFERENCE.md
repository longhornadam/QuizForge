# Canvas Question Type Behaviors — Technical Reference
**Canvas-specific rendering, grading, and edge cases for all QuizForge question types**

Use this document when you need Canvas implementation details. For format specifications and examples, see `LLM_Modules/core/QF_BASE.md` Section 6.

---

## Multiple Choice (MC)

### Canvas Behavior
- Renders as radio buttons (single selection only)
- Exactly one correct answer required; 2-7 choices total
- No penalty for wrong answer (0 points, not negative)
- Randomizes choice order by default unless Canvas shuffle disabled

### Format Rules (non-obvious)
- `[x]` and `[X]` both normalized to correct; case-insensitive
- Two or more `[x]` markers fails validation (use MA instead)
- One `[x]` among 1 choice total is invalid (need 2+ choices for MC)

### Edge Cases
- Student skips question → 0 points (not penalized beyond losing the points)
- Choice text with leading/trailing whitespace preserved; Canvas doesn't trim
- Duplicate choice text allowed but confuses students

---

## Multiple Answer (MA)

### Canvas Behavior
- Renders as checkboxes (multiple selections allowed)
- At least one choice must be marked `[x]`; multiple `[x]` required for MA to make sense
- **Partial credit formula**: `(correct_selected / total_correct) × points`
- Selecting wrong answers (unmarked choices) does NOT reduce score below zero

### Format Rules (non-obvious)
- Zero `[x]` markers fails validation (all-wrong has no correct answer)
- All choices marked `[x]` is valid but trivial (student checks all → 100%)
- At least 2 choices required; single-choice MA makes no sense (use TF instead)

### Edge Cases
- Student selects 2 of 3 correct answers, 0 wrong → 66.67% credit
- Student selects all 3 correct + 1 wrong → still 100% (wrong selections ignored in calculation)
- Student selects nothing → 0 points (not treated as implicit "none of the above")

---

## True/False (TF)

### Canvas Behavior
- Renders as two radio buttons labeled "True" and "False"
- 50% probability of guessing correctly
- Case normalization: `Answer: true`, `Answer: True`, `Answer: TRUE` all valid

### Format Rules (non-obvious)
- `Answer:` line must be `true` or `false` (other values fail validation)
- No additional lines after `Answer:` (explanation text goes in Prompt:, not after)
- Exactly 0 points for wrong answer; no partial credit

### Edge Cases
- Student skips question → 0 points (treated same as wrong answer)
- Canvas doesn't support "Not enough information" third option; strict true/false binary

---

## Essay (ESSAY)

### Canvas Behavior
- Renders as multi-line text area (expandable)
- **No auto-grading**; instructor must manually assign points
- Canvas doesn't enforce length limits (word count or character count)

### Format Rules (non-obvious)
- Only `Prompt:` required; no answer key fields
- `Points:` determines maximum possible score; instructor assigns 0 to max during grading
- Canvas preserves student formatting (line breaks, spacing) but strips HTML tags

### Edge Cases
- Empty submission allowed; Canvas doesn't require text to submit quiz
- Student can paste images into text area, but Canvas may strip depending on settings
- Grading rubrics can be attached in Canvas UI but aren't specified in QTI file

---

## File Upload (FILEUPLOAD)

### Canvas Behavior
- Renders as "Choose File" button
- **No file type validation enforced** by Canvas (institution may set size limits)
- Instructor must manually review submissions and assign points

### Format Rules (non-obvious)
- Only `Prompt:` required; no additional fields
- Canvas doesn't check file extensions, MIME types, or virus scan at QTI level (handled by Canvas backend)
- Students can resubmit; latest upload overwrites previous

### Edge Cases
- Empty submission allowed (student submits quiz without attaching file)
- Institution-specific size limits (typically 500MB–5GB) cause silent upload failures
- Multiple files not supported; student must ZIP if multiple artifacts required

---

## Fill in the Blank (FITB)

### Canvas Behavior
- Renders as text input box(es) matching number of `[blank]` tokens in prompt
- **Exact string match** grading; case-sensitive unless Canvas settings override
- No partial credit; all blanks must match exactly for full points

### Format Rules (non-obvious)
- `Accept:` must list acceptable answers using `- value` syntax
- **Order matters**: first `- value` corresponds to first `[blank]`, second to second, etc.
- If prompt has 2 `[blank]` tokens, `Accept:` must have exactly 2 items (or validation fails)

### Edge Cases
- Whitespace differences cause false negatives: "H2O" ≠ "H2O " (trailing space)
- Punctuation causes false negatives: "9.8" ≠ "9.8." (period)
- Canvas case-sensitivity setting in quiz options can override; default is case-sensitive
- Multiple acceptable answers per blank not supported in current packager (Canvas can do it, but QuizForge doesn't expose yet)

---

## Matching (MATCHING)

### Canvas Behavior
- Terms displayed on left; dropdowns on right
- **All matches appear in every dropdown** (pool shared across all terms)
- Partial credit: `(correct_matches / total_matches) × points`

### Format Rules (non-obvious)
- Use `- term => match` syntax with ASCII arrow `=>` (not Unicode →)
- Each term must map to exactly one match; one-to-one pairing
- 2+ pairs required; single-pair matching is trivial (use MC instead)

### Edge Cases
- Duplicate matches confuse students but Canvas allows (e.g., "Apple => Fruit", "Orange => Fruit")
- Canvas randomizes dropdown order to prevent pattern guessing
- Student leaves dropdowns blank → 0 points for those terms (not treated as wrong, just unanswered)
- ~7-10 pairs maximum recommended (UI usability degrades with 15+)

---

## Ordering (ORDERING)

### Canvas Behavior
- Items displayed in shuffled order; students drag to rearrange
- **All-or-nothing grading**: must match exact sequence for full credit; no partial credit
- `Header:` field (optional) labels the column above draggable items
- Canvas randomizes initial display order to prevent pattern guessing

### Format Rules (non-obvious)
- `Items:` must list the correct sequence using numbered lines (`1.`, `2.`, ...)
- First item in list = top of correct order; last item = bottom
- **2+ items required**; single-item ordering is invalid
- Recommended maximum: 7–10 items (Canvas UI usability limit)

### Edge Cases
- Partially correct sequences receive zero credit (e.g., items 1-2-4-3 when correct is 1-2-3-4)
- Ties or ambiguous orderings not supported; author must define single canonical order
- Students can leave items unordered (drag zone empty); treated as incorrect

---

## Categorization (CATEGORIZATION)

### Canvas Behavior
- Items displayed in shared pool; students drag to category drop zones
- **Per-category partial credit**: points split equally among categories; must get ALL items in a category correct (all included, none extra) to earn that category's fraction
- Example: 10 points, 2 categories → 5 points per category; student gets NFL perfect but MLB incomplete → 5 points total
- Distractors can remain unplaced or be incorrectly placed without penalty

### Format Rules (non-obvious)
- `Categories:` must list 2+ category names
- Each category must have at least 1 correct item in `Items:` mapping
- `Items:` use `- item => Category` syntax (same `=>` arrow as MATCHING)
- `Distractors:` (optional) items that don't belong to any category

### Edge Cases
- Adding one wrong item to a category OR missing one required item = 0% for that category
- Unequal items-per-category is allowed; grading still splits points equally (not by item count)
- Canvas doesn't enforce item uniqueness; duplicate item text in different categories will confuse students
- 5+ categories degrades UI usability; 2-4 recommended

---

## Stimulus (STIMULUS / STIMULUS_END)

### Canvas Behavior
- Displays in shaded box that stays visible while students answer linked questions
- **Always 0 points**; doesn't count toward quiz total
- Subsequent questions automatically link to it until next STIMULUS block or `Type: STIMULUS_END`
- Canvas shows stimulus above each linked question (not as separate item in question list)

### Format Rules (critical)
- `Type: STIMULUS` opens stimulus block; content in `Prompt:`
- **Must close with `Type: STIMULUS_END`** (0-point terminator; no other fields required)
- Questions between STIMULUS and STIMULUS_END are children of that stimulus
- Missing STIMULUS_END causes all remaining questions to link to stimulus (common error caught by packager)
- Multiple stimuli in one quiz: each STIMULUS...STIMULUS_END pair groups its own questions

### Edge Cases
- Single question after STIMULUS is valid but inefficient; just include content in question prompt instead
- Empty stimulus (no Prompt: or empty `>>>` block) is invalid
- STIMULUS_END with Prompt: or Points: fields is ignored; only Type: matters
- Questions before first STIMULUS are standalone (not linked to any passage)

---

## Numerical (NUMERICAL)

### Canvas Behavior
- Renders as single text input accepting decimal or integer
- Auto-graded using tolerance, precision, or range rules
- Six modes available:
  - **Exact match:** Student response must equal answer exactly (no modifier)
  - **Percent margin:** `Tolerance: 5%` → Answer ±5% (symmetric margin using `abs(answer) × 0.05`)
  - **Absolute margin:** `Tolerance: ±0.1` → Answer ±0.1 units (symmetric)
  - **Range:** `Range: 6.8 to 7.2` → Inclusive min/max bounds
  - **Significant digits:** `Precision: 2 significant digits` → Strict lower bound `<vargt>`, inclusive upper `<varlte>`
  - **Decimal places:** `Precision: 3 decimal places` → Strict lower bound `<vargt>`, inclusive upper `<varlte>` centered on midpoint

### Format Rules (non-obvious)
- `Answer:` must be decimal-formatted (`5.0`, not `5`) — Canvas requires decimal point in all numeric XML values
- Exactly one modifier required: `Tolerance:`, `Precision:`, or `Range:` (omit all for exact match)
- Percent syntax: `Tolerance: 1%` (with percent sign)
- Absolute syntax: `Tolerance: ±0.1` (with ± symbol or `+0.1` / `-0.1`)
- Range syntax: `Range: 98.0 to 102.0` (with `to` keyword)
- Significant digits syntax: `Precision: 2 significant digit(s)` (with "significant")
- Decimal places syntax: `Precision: 3 decimal place(s)` (with "decimal")

### Authoring Template
```
Type: NUMERICAL
Points: 10
Prompt:
Calculate the acceleration (in m/s²) of an object with F=20N and m=4kg.
Answer: 5.0
Tolerance: ±0.1
```

### Edge Cases
- **Units must be stated in prompt**; answer field is numeric only (no "5 kg")
- Canvas expects all numeric strings to contain decimal point (`4.0`, not `4`) — packager auto-formats
- Scientific notation supported but must use decimal: `5.0E+1`, not `5E1`
- Zero answers with percent margin fall back to absolute tolerance logic (can't calculate percentage of zero)
- Omitting decimal in `Answer:` works (packager normalizes) but author clarity matters
- Supplying both `Tolerance:` and `Precision:` fails validation (mutually exclusive)
- Negative upper bounds in `Range:` fail validation; always order as `min to max`

### Tips for Authoring
- Default to decimal notation; use scientific notation only when magnitude requires it
- For percent margins, clarify in prompt that grading is percentage-based
- Use range mode when real-world variance expected or multiple solution paths converge on a band
- Precision modes ideal for significant-figure labs or instrumentation readings with asymmetric rounding

**For full technical details** (Canvas QTI XML structure, bounds computation, precision formulas), see `QF_QTYPE_Numerical.md`.

---

**Version:** 1.0  
**Last Updated:** 2025-11-08  
**Maintainer:** QuizForge Core Team
