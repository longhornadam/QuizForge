# QF_MOD_Math_Intermediate

Audience: Algebra I/II, Geometry courses where computation rigor increases.

## Building on Foundations
- Inherits guidance from `QF_MOD_Math_Foundations.md`.
- Adds support for multi-step problem solving and applied scenarios.

## Question Type Highlights
- Multiple Choice with distractors derived from common algebraic errors.
- Short Answer / Fill-in for expressions and numeric solutions.
- Matching for function–graph or formula–description pairs.

## Numerical Question Support
When authoring numerical items, keep prompts concise and rely on Packager-side tolerance logic defined in `LLM_Modules/core/QF_BASE.md`:
```
Type: NUMERICAL
Points: 12
Prompt:
Solve for x: 2x + 5 = 17.
Answer: 6
Tolerance: ±0.5
```
If you need additional tolerance modes, instruct the LLM to include content from `CANVAS_BEHAVIORS_REFERENCE.md` (Numerical section) or `QF_QTYPE_Numerical.md` on demand.

## Instructional Tips
- Encourage rationale prompts (“Explain your reasoning”) for open-ended items.
- Use contextual problems (geometry, rate of change) to motivate numerical answers.

## Metadata
- `numeric_level: intermediate`
