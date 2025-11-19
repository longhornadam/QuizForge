# Canvas QTI Patterns (Numeric, Ordering, Categorization)

Source: Canvas export "Numeric, Ordering, and Categorization Question Types" (College Algebra shell). All items share `points_possible` = `1.0`, `calculator_type` = `none`, and score scaling that maps 100 to full credit.

## Numerical questions
- Metadata: `question_type` = `numerical_question` with a single `response_str` block. Answers render via `<render_fib fibtype="Decimal">` and use one `respcondition continue="No">` that sets `SCORE` to `100` when satisfied.
- Canvas always supplies both an inline constraint (e.g., `<varequal>` with attributes) and explicit bounds (`<vargte>`/`<varlte>` or `<vargt>`/`<varlte>`). The bounds already reflect the intended tolerance and can be trusted as-is.
- Observed variations:

| Variation | XML cues | Acceptance details |
| --- | --- | --- |
| Exact value | `<varequal>4.0</varequal>` plus `<vargte>` = `<varlte>` = `4.0` | Any response numerically equal to the key; duplicate equality checks are present but redundant. |
| Percent margin | `<varequal margintype="percent" margin="1">5.0</varequal>` | Canvas pre-computes numeric limits (here 4.95-5.05) in the `<vargte>`/`<varlte>` nodes; respect those instead of recomputing. |
| Absolute margin | `<varequal margintype="absolute" margin="1">6.0</varequal>` | Bounds reflect the absolute window (5.0-7.0 in the sample). |
| Within a range | Only `<vargte>`/`<varlte>` (6.0-8.0) without `<varequal>` | One-way range check; Canvas skips `<or>` and goes straight to the bound pair. |
| Significant digits | `<varequal precisiontype="significantDigits" precision="1">8.0</varequal>` | Uses `<vargt>` (strict lower bound) and `<varlte>`; strictness enforces the requested significant-digit count. |
| Decimal places | `<varequal precisiontype="decimals" precision="1">9.0</varequal>` | Same pattern as significant digits but represents required decimal places. |

## Ordering question
- Metadata: `question_type` = `ordering_question` with `rcardinality="Ordered"`.
- Presentation: `<ims_render_object shuffle="No">` wraps the ordered choices. The stem appears in `<material position="top">`, with optional footer in `<material position="bottom">`.
- Scoring: `<respcondition>` lists `<varequal respident="response1">` entries in target order (first entry = top of the correct order). Full credit sets `SCORE` to `100`; there is no per-position partial credit in this export.

## Categorization question
- Metadata: `question_type` = `categorization_question`. Each category is represented by its own `response_lid` element with `rcardinality="Multiple"` and a `<material>` label (e.g., `NFL`, `MLB`).
- Choices: Every `response_lid` repeats the full pool of `<response_label>` options; Canvas distinguishes categories by the `respident` on each `<varequal>`.
- Scoring: Canvas emits one `<respcondition>` per category. Each condition lists the expected option IDs for that category and adds half of the available score (`<setvar action="Add" varname="SCORE">50.00</setvar>` in the sample). All required matches must be present for the category’s points to be awarded.
