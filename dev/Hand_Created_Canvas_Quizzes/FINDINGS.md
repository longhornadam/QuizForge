# Hand-Created Canvas Quiz Findings

Tracking quirks from hand-authored Canvas New Quizzes exports. Append new quizzes as we unpack them.

## Quiz: Categorization, 2 stimulus (below, right), matching, and 3 styles of FITB (export `gd1dee4774c1818bab03ad9bc018470d4`, 2025-12-02)
- **Stimuli/layout**: Stimuli are `text_only_question` items with `points_possible` 0 and an `instructions` attribute; `passage=false`. `<material orientation="top">` renders "questions below"; `orientation="left"` renders "questions to the right." Children reference the parent via qtimetadata `parent_stimulus_item_ident`.
- **Categorization** (matches `User_docs/Canvas_QTI_Patterns.md`): HTML allowed in the stem; category labels and choices are `texttype="text/plain"`. Each category repeats the full pool; scoring is one `<respcondition>` per category adding 50 points (maps to 100%).
- **Ordering**: HTML allowed inside choices (links, underline, table). Top/bottom labels use `<material position="top|bottom">` with plaintext. `ims_render_object shuffle="No"` encloses a `<flow_label>` list. Correct order is enumerated via `<varequal>` entries; `setvar SCORE 100` if exact. Canvas also emits `decvar varname="ORDERSCORE"` default 1.
- **Matching** (Stimulus 1, "questions below"): Choices are plaintext; an optional `distractor_0` is appended to each `render_choice`. Partial credit uses `scoring_algorithm="PartialDeep"`; each subquestion has its own `<respcondition>` adding 25 toward SCORE 100.
- **Fill in the Blank variants** (Stimulus 2, "questions to the right"; all use `question_type` = `fill_in_multiple_blanks_question` with `[blank_id]` tokens in the stem):
  - Open-entry: `answer_type="openEntry"` and `scoring_algorithm="TextContainsAnswer"`; only the keyed `response_label` appears in `render_choice`.
  - Dropdown: `answer_type="dropdown"` and `scoring_algorithm="Equivalence"`; options carry a `position` attribute; scoring is a single `varequal` to the correct option.
  - Word bank: `answer_type="wordbank"` and `scoring_algorithm="TextEquivalence"`; full bank listed under the blank; scoring checks the correct `response_label` id.
- **Plaintext vs HTML**: Stems and stimuli accept HTML. Category descriptions, matching subquestions/answers, and FITB answer options export as plaintext; ordering answers can carry HTML.

## Quiz: Categorization, 2 stimulus (below, right), matching, 3 styles of FITB + FITB answer opts (export `gd1dee4774c1818bab03ad9bc018470d4`, 2025-12-02)
- Same stimulus/layout patterns as above (`orientation="top"` → below; `orientation="left"` → right; children point to `parent_stimulus_item_ident`).
- FITB dropdown and word bank match prior export (single blank each; dropdown uses `answer_type="dropdown"` + `Equivalence`; word bank uses `answer_type="wordbank"` + `TextEquivalence`).
- New multi-blank FITB (`fitb_multiblank`) shows per-blank scoring split equally (`setvar Add SCORE 33.33` each) and three different text match modes on separate blanks:
  - Blank 1: `answer_type="openEntry"`, `scoring_algorithm="TextCloseEnough"`, `levenshtein_distance="1"`, `ignore_case="false"`.
  - Blank 2: `answer_type="openEntry"`, `scoring_algorithm="TextEquivalence"` (exact text match, case-sensitive by default).
  - Blank 3: `answer_type="openEntry"`, `scoring_algorithm="TextRegex"` (regex-based acceptance).

### Pedagogy note (for future integration into QF_BASE)
- Tier 1 interventions: prefer constrained FITB modes (word bank or dropdown) to reduce case/spelling sensitivity and cognitive load.
- Tier 2/3: use open-entry FITB (default `TextEquivalence` with case-insensitive matching where possible) unless a teacher explicitly requests dropdown/word bank.
- Open-entry FITB: Canvas is case-sensitive by default; we should explicitly set `case_sensitive: false` (or include variants) when using `TextEquivalence` to avoid penalizing capitalization differences.

### Possible next pedagogical tweaks to consider (for later)
- Default typo tolerance? Keep off unless requested; `TextCloseEnough` with small distance (1) could be a teacher opt-in for ELL/younger learners.
- Regex acceptance? Leave as advanced/opt-in; not a default.
- Dropdown vs word bank selection: For Tier 1, pick dropdown when options are short and clear; pick word bank when spatial drag/drop helps (but watch for mobile accessibility).
