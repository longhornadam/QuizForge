# QF_MOD_Science_AP

Audience: Advanced Placement and upper-level science courses requiring high precision and complex quantitative analysis.

## Extends LabReady Module
- Assumes `QF_MOD_Science_LabReady.md` guidance.
- Adds advanced tolerance handling and calculus-based reasoning.

## Advanced Numerical Patterns
```
Type: NUMERICAL
Points: 18
Prompt:
A radioactive isotope decays following N(t) = N_0 e^{-0.04t}. Determine N(25) within 1%.
Answer: 0.3679
Tolerance: 1%
```
Include significant digits or decimal place constraints as needed by referencing `CANVAS_BEHAVIORS_REFERENCE.md` (Numerical section) or the production spec in `QF_QTYPE_Numerical.md`.

## Instructional Notes
- Integrate multi-step problem chains (e.g., derive formula, compute numeric result, analyze error).
- Encourage justification prompts alongside numeric responses.

## Metadata
- `numeric_level: advanced`
