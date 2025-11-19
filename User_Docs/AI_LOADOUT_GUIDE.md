# QuizForge - Files to Load into Your Pro AI Account

## 🎯 MINIMUM REQUIRED (Core Knowledge)

For baseline quiz generation, start with this **single essential file**. Token counts are approximate so you can plan LLM context usage (≈4 tokens per source line).

### 1. **QF_BASE.md** (≈3.2k tokens)
**Path:** `LLM_Modules/QF_BASE.md`

**What it contains:**
- Full QuizForge TXT specification for every question type (MC, TF, MA, MATCHING, FITB, ESSAY, FILEUPLOAD, ORDERING, CATEGORIZATION, NUMERICAL, STIMULUS/STIMULUS_END)
- Output contract and validation checklist the LLM must obey
- Point-weighting heuristics and workflow expectations
- Formatting tools (code fences, excerpts, inline code, math) with Canvas-safe rules
- Stimulus pattern reference and reminder to return downloadable files when possible

**Why essential:** This is the canonical system prompt for QuizForge; it tells the LLM exactly how to transform teacher requests into parser-ready TXT.

---

## 📚 RECOMMENDED ADD-ONS (Optional Modules)

Load these **only when needed** for specific use cases:

### Discipline Modules (Choose What You Need)

**Computer Science:**
- `LLM_Modules/QF_MOD_CompSci.md` (≈1.9k tokens)
- Load for: Code-heavy quizzes, syntax highlighting, debugging questions
- Features: Monokai theme specs, code output prediction patterns, trace tables

**Math (pick a tier):**
- `LLM_Modules/QF_MOD_Math_Foundations.md` — General math, minimal numeric detail
- `LLM_Modules/QF_MOD_Math_Intermediate.md` — Algebra/Geometry with simple tolerances
- `LLM_Modules/QF_MOD_Math_STEMLab.md` — Precalculus/AP with advanced precision

**English/Language Arts (pick a tier):**
- `LLM_Modules/QF_MOD_ELA_Foundations.md` — Grades 3-8, literal comprehension, basic inference (Lexile 420-1050L)
- `LLM_Modules/QF_MOD_ELA_Intermediate.md` — Grades 8-10, literary devices, theme analysis (Lexile 925-1185L)
- `LLM_Modules/QF_MOD_ELA_Advanced.md` — Grades 11-12/AP, rhetorical analysis, synthesis (Lexile 1185-1605L)

**Science (pick a tier):**
- `LLM_Modules/QF_MOD_Science_Foundations.md` — Intro science without tolerances
- `LLM_Modules/QF_MOD_Science_LabReady.md` — Lab courses needing tolerances
- `LLM_Modules/QF_MOD_Science_AP.md` — AP-level precision & advanced analysis

**Humanities:**
- `LLM_Modules/QF_MOD_Humanities.md`
- Load for: History, geography, social studies

---

### Pedagogy Modules (Optional)

**Rigor/Bloom's Taxonomy:**
- `LLM_Modules/QF_MOD_Rigor.md` (≈660 tokens)
- Load when: Teacher wants explicit higher-order thinking, DOK levels

**Differentiation:**
- `LLM_Modules/QF_MOD_Differentiation.md`
- Load when: Need multiple reading levels or scaffolded versions

**UDL (Universal Design for Learning):**
- `LLM_Modules/QF_MOD_UDL.md`
- Load when: Accessibility, multiple means of representation/engagement

---

### Advanced Question Types (Optional)

**Canvas-Specific Behaviors (All Question Types):**
- `LLM_Modules/CANVAS_BEHAVIORS_REFERENCE.md`
- Load when: Need Canvas grading mechanics, rendering details, edge cases for any question type

**Numerical Questions (Complex):**
- `LLM_Modules/QF_QTYPE_Numerical.md`
- Load when: Need tolerance modes (exact, percent, absolute, range, significant digits, decimal places) or numeric authoring reminders

**⚠️ Note:** Other question type docs have been consolidated into `CANVAS_BEHAVIORS_REFERENCE.md`. QF_BASE.md Section 6 contains all format requirements with examples.

**⚠️ Experimental Question Types (NOT PRODUCTION READY):**

---

## 🎯 RECOMMENDED LOADOUT BY USE CASE

### Use Case 1: Computer Science Teacher (You!)
**Load these files:**
1. `LLM_Modules/QF_BASE.md` ✅ (essential)
2. `LLM_Modules/QF_MOD_CompSci.md` ✅ (CS-specific)

**Total:** ≈5.1k tokens

**Optional add:**
- `LLM_Modules/CANVAS_BEHAVIORS_REFERENCE.md` for Canvas-specific quirks

---

### Use Case 2: General Teacher (Any Subject)
**Load this core file:**
1. `LLM_Modules/QF_BASE.md` ✅ (essential)

**Total:** ≈3.2k tokens

**Add discipline module as needed:**
- Science, Math, ELA, or Humanities

---

### Use Case 3: Instructional Coach (Multiple Subjects)
**Load these files:**
1. `LLM_Modules/QF_BASE.md` ✅ (essential)
2. `LLM_Modules/QF_MOD_Rigor.md`
3. `LLM_Modules/QF_MOD_Differentiation.md`

**Total:** ≈4.5k tokens

---

## 💡 HOW TO USE WITH PRO AI

### Option 1: Project Knowledge Base
1. Upload `LLM_Modules/QF_BASE.md` as permanent project knowledge
2. Upload your chosen discipline module (e.g., CompSci)
3. Use the chat to request quizzes

**Prompt example:**
```
Create a quiz on Python loops: 10 MC questions, 2 FITB, 1 short essay.
8th grade level. Include code examples in at least half the questions.
```

### Option 2: Custom Instructions
1. Copy the "Output Contract" and "Validation Checklist" sections from `LLM_Modules/QF_BASE.md` into your custom instructions (or summarize them concisely in your own words).
2. Remind the AI in custom instructions that the full spec lives in `LLM_Modules/QF_BASE.md` and should be consulted for question-type rules.
3. Request quiz output in chat as usual.

**Prompt example:**
```
Using QuizForge format, create 15 MC questions on variables and data types.
Make sure code blocks use proper syntax highlighting.
```

### Option 3: Per-Request Upload
1. Start a new chat
2. Upload `LLM_Modules/QF_BASE.md` and any discipline module as files
3. Request the quiz immediately

**Prompt example:**
```
Based on the uploaded QuizForge guide, generate a quiz:
- Topic: Functions and parameters
- 12 MC questions @ 5 pts each (60 pts)
- 2 Short essay @ 20 pts each (40 pts)
- High school level
```

---

## 🚫 FILES YOU DON'T NEED

**Skip these:**
- `_ARCHIVE/*` - Old versions, superseded by QF_BASE.md
- `Packager/quizforge/*` - Python code (you don't need to teach the AI this)
- `User_Docs/samples/*` - Example outputs (useful for reference, but not for AI training)
- `DEPLOY_*.md` - Deployment docs for web app
- `WEB_APP_GUIDE.md` - Not needed for TXT generation

---

## 📊 FILE SIZE SUMMARY

Approximate tokens use 4 tokens per source line; actual usage will vary slightly.

| File | ≈Tokens | Purpose | Priority |
|------|---------|---------|----------|
| LLM_Modules/core/QF_BASE.md | 3.2k | Core system spec & validation | **ESSENTIAL** |
| LLM_Modules/disciplines/QF_MOD_CompSci.md | 1.9k | CS-specific patterns | Recommended |
| LLM_Modules/pedagogy/QF_MOD_Rigor.md | 660 | Bloom's / DOK scaffolds | Optional |
| LLM_Modules/pedagogy/QF_MOD_Differentiation.md | 780 | Multi-level supports | Optional |
| LLM_Modules/presets/QF_PRESET_QuickCheck.md | 380 | Quick check template | Optional |

**Total for CS teacher:** ≈5.1k tokens (QF_BASE + CompSci)
**Total for minimal use:** ≈3.2k tokens (QF_BASE only)

---

## ✅ WORKFLOW SUMMARY

1. **Load files into Pro AI** (QF_BASE.md + discipline module)
2. **Request quiz** in natural language
3. **AI outputs plain TXT** in QuizForge format
4. **Save TXT file** to your computer
5. **Run local CLI:**
   ```powershell
   python .\Packager\quizforge_packager.py your_quiz.txt -o output.zip
   ```
6. **Import ZIP** into Canvas

**No Python knowledge needed!** The AI generates the TXT, the CLI converts to QTI.

---

## 🎓 BONUS: What Makes This System Work

**The modules are ADDITIVE:**
- Start with QF_BASE.md (format rules)
- Add discipline knowledge (e.g., CompSci code patterns)
- Add pedagogy if needed (Bloom's, differentiation)
- Add presets for quick templates

**The AI doesn't need to know:**
- How the Python parser works
- QTI XML structure
- Canvas import mechanics
- ZIP file creation

**The AI only needs to know:**
- The TXT format syntax (QF_BASE.md)
- Domain-specific patterns (discipline modules)
- Quality standards (built into QF_BASE)

This separation keeps the AI's job simple: **just generate valid TXT format.**
