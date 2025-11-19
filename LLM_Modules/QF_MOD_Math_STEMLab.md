# QF_MOD_Math_STEMLab

Audience: Precalculus, AP Calculus, STEM lab courses with complex quantitative tasks.

## Extends Intermediate Module
- Assumes familiarity with `QF_MOD_Math_Intermediate.md` content.
- Emphasizes precision, tolerances, and multi-part numeric reasoning.

## Advanced Numerical Authoring
Use rich prompts and numerical tolerances while keeping syntax lean per `LLM_Modules/question_types/QF_QTYPE_Numerical.md`:
```
Type: NUMERICAL
Points: 15
Prompt:
Given f(x) = e^x, estimate f(0.01) using a linear approximation.
Answer: 1.01005
Precision: 3 decimal places
```
Refer the LLM to `CANVAS_BEHAVIORS_REFERENCE.md` (Numerical section) for quick mode summaries and `QF_QTYPE_Numerical.md` when precision math is required.

## Additional Strategies
- Provide parameterized problems (e.g., varying coefficients) to foster conceptual understanding.
- Mix numerical questions with proof or explanation prompts for depth.

## Metadata
- `numeric_level: advanced`
