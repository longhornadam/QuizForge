# LLM Modules — QuizForge Authoring Documentation

**Flat structure containing all LLM-facing documentation for quiz authoring.**  
**22 files total** (3 core, 13 discipline/tier modules, 3 pedagogy, 3 other)

---

## Core Files

### **QF_BASE.md** 📘
**Primary specification for all LLM quiz authoring.**

The canonical system prompt for QuizForge. Contains:
- Output contract and validation checklist
- Format specifications with examples for all question types
- Point-weighting heuristics
- Canvas-safe formatting rules (code fences, math, excerpts)
- Stimulus patterns

**Load this first—it's the minimum required for quiz generation.**

---

### **CANVAS_BEHAVIORS_REFERENCE.md** 🎯
**Canvas-specific rendering, grading mechanics, and edge cases.**

Covers platform behaviors for:
- Multiple Choice, Multiple Answer, True/False
- Essay, File Upload
- Fill in the Blank, Matching
- Ordering, Categorization
- Stimulus blocks
- **Numerical** (mode quick reference with authoring template)

**Use when:** You need to understand how Canvas renders or grades a question type, or need quick numerical mode syntax.

---

### **QF_QTYPE_Numerical.md** 🔢
**Full technical specification for numerical questions.**

Numerical questions are complex (6 evaluation modes, Canvas QTI XML requirements). Covers:
- Exact match, percent margin, absolute margin, range, significant digits, decimal places
- Canvas QTI structure and Decimal normalization (all values require decimal point: `4.0`, not `4`)
- Bounds computation formulas and common pitfalls

**Use when:** You need deep technical details (XML structure, precision formulas, bounds computation).

---

## Discipline Modules

Subject-specific guidance for quiz authoring:

**Computer Science:**
- **QF_MOD_CompSci.md** — Code formatting (Monokai theme), debugging questions, trace tables

**Math (tiered by content complexity):**
- **QF_MOD_Math.md** — General math guidance
- **QF_MOD_Math_Foundations.md** — Basic math, minimal numeric detail
- **QF_MOD_Math_Intermediate.md** — Algebra/Geometry with tolerances
- **QF_MOD_Math_STEMLab.md** — Precalculus/AP with advanced precision

**English/Language Arts (tiered by content complexity):**
- **QF_MOD_ELA_Foundations.md** — Grades 3-8, literal comprehension, basic inference (Lexile 420-1050L)
- **QF_MOD_ELA_Intermediate.md** — Grades 8-10, literary devices, theme analysis (Lexile 925-1185L)
- **QF_MOD_ELA_Advanced.md** — Grades 11-12/AP, rhetorical analysis, synthesis (Lexile 1185-1605L)

**Science (tiered by content complexity):**
- **QF_MOD_Science.md** — General science guidance
- **QF_MOD_Science_Foundations.md** — Intro science without tolerances
- **QF_MOD_Science_LabReady.md** — Lab courses needing tolerances
- **QF_MOD_Science_AP.md** — AP-level precision

**Humanities:**
- **QF_MOD_Humanities.md** — History, geography, social studies (includes inline rigor calibration for Foundations/Intermediate/Advanced)

---

## Pedagogy Modules

Optional pedagogical frameworks:

- **QF_MOD_Rigor.md** — Bloom's Taxonomy, DOK levels, higher-order thinking
- **QF_MOD_Differentiation.md** — Multiple reading levels, scaffolded versions
- **QF_MOD_UDL.md** — Universal Design for Learning, accessibility

---

## Other Files

- **quizforge_outline.schema.json** — JSON schema for quiz structure validation
- **STRUCTURE_NUMERICAL_LAYERS.md** — Design notes on numerical question architecture

---

## Usage Guide

**Minimum loadout:**
1. Load `QF_BASE.md` (essential)
2. Add discipline module if needed (e.g., `QF_MOD_CompSci.md`)
3. Optionally add `CANVAS_BEHAVIORS_REFERENCE.md` for Canvas quirks

**For detailed loadout recommendations**, see `User_Docs/guides/AI_LOADOUT_GUIDE.md`.

---

## Future Platform Support

Canvas-specific behaviors are isolated in `CANVAS_BEHAVIORS_REFERENCE.md`. When extending to other platforms:
- Add `BLACKBOARD_BEHAVIORS_REFERENCE.md`, `MOODLE_BEHAVIORS_REFERENCE.md`, etc.
- Keep format specs in `QF_BASE.md` platform-agnostic

---

**Last Updated:** 2025-11-08  
**Maintainer:** QuizForge Core Team
