# QF_MOD_Science_LabReady

Audience: Chemistry, Physics, and Biology lab courses requiring data analysis.

## Builds on Foundations
- Includes all guidance from `QF_MOD_Science_Foundations.md`.
- Adds emphasis on measurement, error analysis, and quantitative lab reporting.

## Numerical Authoring
When lab activities require tolerances, use concise directives aligned with `LLM_Modules/question_types/QF_QTYPE_Numerical.md`:
```
Type: NUMERICAL
Points: 12
Prompt:
A solution has a measured pH of 6.95. Report an acceptable value within 0.1 units.
Answer: 6.95
Tolerance: ±0.1
```
For alternate modes (percent, range), instruct the LLM to include `CANVAS_BEHAVIORS_REFERENCE.md` (Numerical section) or the full spec in `QF_QTYPE_Numerical.md` in the prompt session.

## Lab Tip Highlights
- Encourage units in every numeric response.
- Pair numerical questions with follow-up reflection (“What factors could affect accuracy?”).

## Metadata
- `numeric_level: intermediate`
