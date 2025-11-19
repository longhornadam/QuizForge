# QuizForge Question Type: Numerical
**Status:** Production-ready as of 2025-11-08

---

## Overview
Numerical questions accept decimal or integer responses that are auto-graded using tolerance or precision rules. The Packager supports six Canvas-compatible evaluation strategies: exact match, percent margin, absolute margin, range, significant digits, and decimal places.

Use this document as the canonical specification for `Type: NUMERICAL`. Pair it with `LLM_Modules/QF_BASE.md` for system-level requirements and `LLM_Modules/CANVAS_BEHAVIORS_REFERENCE.md` when a compact mode summary is sufficient.

---

## Plain-Text Authoring Format
```
Type: NUMERICAL
Points: <integer or decimal>
Prompt:
<question stem>
Answer: <decimal-formatted value>
<Tolerance|Precision|Range>: <mode-specific data>
```

Exactly one modifier is required out of `Tolerance:`, `Precision:`, or `Range:`. Omit all modifiers only for strict exact-match grading.

### Example: Exact Match
```
Type: NUMERICAL
Points: 8
Prompt:
Solve for x: 3x + 7 = 22.
Answer: 5.0
```

### Example: Percent Margin
```
Type: NUMERICAL
Points: 10
Prompt:
A machine produces rods that should be 5.0 cm long. Accept responses within 1%.
Answer: 5.0
Tolerance: 1%
```

### Example: Absolute Margin
```
Type: NUMERICAL
Points: 10
Prompt:
Report the measured mass to the nearest tenth of a gram.
Answer: 12.4
Tolerance: ±0.1
```

### Example: Range
```
Type: NUMERICAL
Points: 12
Prompt:
Estimate the kinetic energy (in J) of a 2.0 kg object moving at 10 m/s.
Answer: 100.0
Range: 98.0 to 102.0
```

### Example: Significant Digits
```
Type: NUMERICAL
Points: 15
Prompt:
Using significant figures, report the density with 2 significant digits.
Answer: 1.80
Precision: 2 significant digits
```

### Example: Decimal Places
```
Type: NUMERICAL
Points: 15
Prompt:
Report the time of flight in seconds to three decimal places.
Answer: 1.247
Precision: 3 decimal places
```

---

## Supported Modes
| Mode | Modifier Syntax | Canvas Behaviour |
|------|-----------------|------------------|
| Exact | (no modifier) | Requires exact match after normalization |
| Percent Margin | `Tolerance: <value>%` | Canvas sets `margintype="percent"` with symmetric inclusive bounds |
| Absolute Margin | `Tolerance: ±<value>` or signed literal | Canvas sets `margintype="absolute"` with symmetric inclusive bounds |
| Range | `Range: <min> to <max>` | Inclusive `<vargte>` and `<varlte>` bounds, Packager still emits `<varequal>` for Canvas parity |
| Significant Digits | `Precision: <n> significant digit(s)` | Strict lower bound `<vargt>`, inclusive upper `<varlte>`; precision stored as integer |
| Decimal Places | `Precision: <n> decimal place(s)` | Strict lower bound `<vargt>`, inclusive upper `<varlte>` centred on midpoint |

All numeric literals are normalized with `Decimal` to guarantee Canvas-compatible formatting (e.g., `4` → `4.0`, `5E+1` → `5.0E+1`).

---

## Canvas QTI Structure
- Items render with `<presentation>` containing `render_fib fibtype="Decimal"` and one `response_label`.
- Scoring conditions live under `<resprocessing>` with:
  - `<varequal>` carrying margin or precision metadata.
  - `<vargte>/<varlte>` for inclusive bounds.
  - `<vargt>` paired with `<varlte>` when precision modes require a strict lower bound.
- Range mode still includes a `<varequal>` element to satisfy Canvas' parser while the bounds govern evaluation.
- Canvas expects all numeric strings to contain a decimal point; `_format_decimal` enforces this across the renderer.
- `setvar` assigns `SCORE` to `100`; QuizForge scales the score back to the specified `Points:` value when exporting metadata.

Refer to `dev/numerical_decimal_fix_test.zip` and `dev/pipeline_test_quiz.zip` for sample imports captured during validation.

---

## Implementation Notes
- Bounds are precomputed in the domain layer using `Decimal` arithmetic to avoid floating-point drift.
- Validation enforces mutually exclusive modifiers and ensures ranges obey `min < max`.
- Percent margins use `abs(answer) * (margin / 100)`; zero answers fall back to absolute tolerance logic.
- Precision modes compute offsets via:
  - **Significant digits:** `0.5 * 10^(floor(log10(|answer|)) - precision + 1)`.
  - **Decimal places:** `0.5 * 10^(-precision)`.
- Renderer mirrors Canvas' strict-vs-inclusive boundary pairing so that imported questions grade identically to native Canvas items.

---

## Authoring Guidance
- State required units in the prompt; never rely on the answer field to hold units.
- Default to decimal notation; use scientific notation only when the magnitude requires it.
- For percent margins, ensure the prompt clarifies that grading is percentage-based.
- Use range mode when real-world variance is expected or multiple solution paths converge on a band of values.
- Precision modes are ideal for significant-figure labs or instrumentation readings with asymmetric rounding rules.

### Common Pitfalls
- Omitting the decimal point in `Answer:` (Packager will normalize, but author clarity matters).
- Supplying both `Tolerance:` and `Precision:`; validation rejects these cases.
- Providing negative upper bounds in `Range:`; always order as `min to max`.
- Forgetting to mention rounding instructions in the prompt.

---

## Related Resources
- `CANVAS_BEHAVIORS_REFERENCE.md` – Quick mode reference and Canvas rendering behaviors.
- `LLM_Modules/QF_BASE.md` – Global output contract and validation checklist.
- `dev/DECIMAL_FORMATTING_FIX.md` – Engineering change log for Canvas compatibility.
- `Packager/tests/test_numerical_integration.py` – Unit tests covering all tolerance modes.

---

**Maintainer:** QuizForge Core Team

**Next Review:** Sync with the next Canvas QTI export verification or when a new tolerance mode is introduced.
