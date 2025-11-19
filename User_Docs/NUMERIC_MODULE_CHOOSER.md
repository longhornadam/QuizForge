# Selecting Numerical Module Layers

Use this chooser to decide which Math/Science module tier to load when authoring quizzes.

| Course Type | Recommended Module | Numeric Level |
|-------------|--------------------|---------------|
| Elementary Math | QF_MOD_Math_Foundations | foundations |
| Algebra I/Geometry | QF_MOD_Math_Intermediate | intermediate |
| Precalculus / AP Calculus | QF_MOD_Math_STEMLab | advanced |
| Middle School Science | QF_MOD_Science_Foundations | foundations |
| Chemistry/Biology Labs | QF_MOD_Science_LabReady | intermediate |
| AP Physics/Chemistry | QF_MOD_Science_AP | advanced |

### How to Use
1. Load only the foundation module by default.
2. If you need numerical tolerances, add the intermediate or advanced module for your discipline.
3. Include `question_types/numeric_quickref.md` in your prompt only when crafting numerical questions.

### Packager Metadata
- Foundation modules include `numeric_level: foundations` to signal minimal numeric expectations.
- Intermediate/Advanced modules tag higher levels, enabling future Packager automation (e.g., warning if advanced numeric questions appear in a foundation context).
