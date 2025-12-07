# QuizForge Full Stack (LLM → QTI ZIP) — Dev Module
**Purpose:** Drive an LLM to emit a Canvas-ready QTI 1.2 ZIP directly (base64 in-chat) without calling the QuizForge pipeline, while preserving QuizForge Base pedagogy and schema.

## Outputs (non-negotiable)
- Primary: Base64-encoded QTI ZIP wrapped in `<QTI_ZIP_BASE64>` … `</QTI_ZIP_BASE64>`.
- Optional helper: the same quiz in QuizForge JSON 3.0 tags (`<QUIZFORGE_JSON>` … `</QUIZFORGE_JSON>`) for traceability.
- Keep chatter outside tags; keep payloads ASCII-safe.

## QTI ZIP Layout
```
imsmanifest.xml
<GUID>/<GUID>.xml           # assessment
<GUID>/assessment_meta.xml  # Canvas quiz meta
```
- Use a single GUID (uuid4) folder name; reuse it for the assessment filename and manifest resource identifier.
- File encodings: UTF-8, LF.

### imsmanifest.xml (Canvas/IMS CC 1.1)
- Root `<manifest>` with namespaces per IMS CC v1.1 (match QuizForge manifest_builder).
- Two resources:
  - `identifier="<GUID>" type="imsqti_xmlv1p2"` with file `<GUID>/<GUID>.xml` and dependency on meta.
  - Meta resource `identifier="<uuid>" type="associatedcontent/imscc_xmlv1p1/learning-application-resource" href="<GUID>/assessment_meta.xml"`.
- Include `<metadata>` with `<imsmd:title>` = quiz title and `<schemaversion>1.1.3</schemaversion>`.

### assessment_meta.xml (Canvas quiz meta)
Namespace `http://canvas.instructure.com/xsd/cccv1p0`.
```
<quiz identifier="<GUID>">
  <title>...</title>
  <description></description>
  <shuffle_questions>false</shuffle_questions>
  <shuffle_answers>false</shuffle_answers>
  <calculator_type>none</calculator_type>
  <scoring_policy>keep_highest</scoring_policy>
  <allowed_attempts>1</allowed_attempts>
  <points_possible>{total_points:.1f}</points_possible>
</quiz>
```

### Assessment XML (`<GUID>.xml`, QTI 1.2)
- Root `<questestinterop>` with QTI 1.2 namespace.
- One `<assessment>` containing a single `<section>`; items in order.
- Every scorable item gets `points_possible` metadata (Canvas uses it). Use the points you assign; if no scheme given, distribute 2 points per question (or normalize to 100 if specified).
- `question_type` metadata values (Canvas-compatible, known-good):
  - MC: `multiple_choice_question`
  - MA: `multiple_answers_question`
  - TF: `true_false_question`
  - FITB: `fill_in_multiple_blanks_question`
  - MATCHING: `matching_question`
  - ORDERING: `ordering_question`
  - CATEGORIZATION: `categorization_question`
  - ESSAY: `essay_question`
  - FILEUPLOAD: `file_upload_question`
  - STIMULUS: `text_only_question` (points_possible 0)
  - STIMULUS_END: omit (structural marker only)

#### Item rendering rules (match QuizForge QTI builder)
- Prompts: HTML `<p>…</p>` wrapping; escape inner quotes.
- MC: `response_lid rcardinality="Single"`, choices A…; scoring sets SCORE=100 on correct ident.
- TF: same as MC, idents `true`/`false`.
- MA: `rcardinality="Multiple"`, partial credit: split 100 across correct choices; each correct adds its share; no penalty for incorrect.
- FITB (single blank, open-entry):
  - Use one `response_lid ident="response_<token>"`.
  - For each accepted variant (trim, dedupe case-insensitively), add a `response_label` with `scoring_algorithm="TextContainsAnswer" answer_type="openEntry" ident="<token>-<n>"` and `mattext` holding the variant.
  - Scoring: one `<respcondition>` per variant, `varequal respident="response_<token>">token-<n>` adds 100.
- FITB (multi-blank, open-entry only):
  - One `response_lid` per blank, ident `response_<token_i>`.
  - Variants per blank -> response_labels as above.
  - Scoring: split 100 across blanks equally; each blank’s variants Add its share (last blank gets remainder to sum 100).
- Dropdown/wordbank FITB: Not supported in this minimal template; prefer open_entry.
- Matching: Each left prompt gets its own `response_lid`; right answers become shared response_labels; partial credit per pair (even split to 100).
- Ordering: `response_lid rcardinality="Ordered"` with `ims_render_object` items; scoring all-or-nothing (must match order).
- Categorization: One `response_lid` per category (ident = category uuid); response_labels list all items+distractors; partial credit per category (even split of 100 across categories).
- Scoring boilerplate: `<outcomes><decvar maxvalue="100" minvalue="0" varname="SCORE" vartype="Decimal"/></outcomes>` then respconditions per logic above.

### Points & Totals
- Set per-item points in metadata; ensure meta points_possible matches sum of item points you assign. If no guidance, use 2 points per scorable item and compute total accordingly.

## Authoring Flow for the LLM
1) Clarify teacher intent (topic, count, types, tier) using QuizForge Base defaults.
2) Draft QuizForge JSON 3.0 (optional helper) with clean prompts, accepts, and IDs.
3) Choose points (default 2 each) and compute total.
4) Build QTI XML honoring the rules above; sanitize HTML; dedupe FITB variants.
5) Build manifest + assessment_meta with the same GUID.
6) Zip the three files; base64-encode; return inside `<QTI_ZIP_BASE64>` tags.

## FITB Accept Guidance (critical)
- Single blank: `accept` list of strings; dedupe lowercased; trim; keep all synonyms.
- Multi blank: `accept` is array-of-arrays; align one group per `[blankN]`; max 3 blanks; open_entry only.
- Case-insensitive by default; avoid case-sensitive unless teacher insists.

## Safety/Formatting
- ASCII only; escape inner quotes.
- Keep output concise: no extra explanations inside payload tags.
- If unable to zip, explain briefly and fall back to JSON 3.0 helper.

## Stimuli, Prose/Poetry, and Code
- Stimuli render as `text_only_question` items with 0 points. Preserve prose/poetry as text; wrap poetry in `<pre>` with line breaks intact.
- Code: carry fences in the JSON helper (e.g., ```python) and render to HTML in QTI using `<pre><code class="language-...">...</code></pre>` with escaped content.
- Do not strip newlines inside stimuli or code; keep indentation.
