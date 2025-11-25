# Discipline Module Layering for Numerical Content

This blueprint defines the tiered structure for Math and Science discipline modules so that only courses needing numerical detail load it into LLM context.

## Overview
- Base modules remain concise, describing core pedagogy and question types without numerical internals.
- Higher tiers introduce numerical guidance progressively.
- Each tier adds a short metadata block the Packager can read if needed (e.g., `numeric_level: intermediate`).

## Math Module Stack
1. **QF_MOD_Math_Foundations.md**
   - Audience: Elementary & middle school general math.
   - Content: Core quiz strategies, MC/TF/FITB patterns.
   - Numerical guidance: Minimal; refer to optional numeric quick reference file if needed.
2. **QF_MOD_Math_Intermediate.md**
   - Audience: Algebra I/II, Geometry.
   - Adds: Simple numerical question authoring (exact, percent, absolute margins).
   - Includes pointer: `Include: ../question_types/numeric_quickref.md` only when teacher opts in.
3. **QF_MOD_Math_STEMLab.md**
   - Audience: Precalculus, AP courses.
   - Adds: Advanced modes (significant digits, decimal places, profession-specific examples).
   - Metadata block: `numeric_level: advanced` for Packager heuristics.

## Science Module Stack
1. **QF_MOD_Science_Foundations.md**
   - Audience: Middle school science.
   - Focus: Conceptual questions, small usage of numerical prompts.
2. **QF_MOD_Science_LabReady.md**
   - Audience: Chemistry, Biology lab courses.
   - Adds: Numerical tolerances for measurement questions (absolute/percent).
3. **QF_MOD_Science_AP.md**
   - Audience: AP Physics/Chemistry.
   - Adds: Significant digits, decimal places, engineering-style tolerance notes.

## Supporting Files
- `LLM_Modules/question_types/numeric_quickref.md`
  - On-demand cheat sheet for authoring numeric questions.
  - Teachers copy into prompts only when necessary.
- `Packager/docs/numeric_presets.md` (future): enumerates tolerance presets keyed by `numeric_level`.

## Next Steps
1. Scaffold tiered files with placeholders.
2. Update documentation templates to reference tiered modules.
3. Provide teacher-facing chooser guide mapping grade/course -> module tier.
4. (Optional) Add Packager option to warn if numeric question appears but module level is "Foundations".
