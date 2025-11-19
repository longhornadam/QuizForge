# QuizForge Agent Navigation Map

**For LLM agents working on QuizForge codebase**

## Agent Status Summary

| Agent | File | Status | Notes |
|-------|------|--------|-------|
| Orchestrator | orchestrator.py | PRODUCTION | Calls validators now |
| Text Parser | text_parser.py | PRODUCTION | - |
| Point Calculator | validators/point_calculator.py | PRODUCTION | New in v2.3 |
| Answer Balancer | validators/answer_balancer.py | PRODUCTION | New in v2.3 |
| Packager Router | packagers/packager.py | PRODUCTION | Dual output |
| Canvas Handler | packagers/canvas_handler.py | PRODUCTION | - |
| Physical Handler | packagers/physical_handler.py | PRODUCTION | New in v2.3 |
| LLM Agent | External + QF_BASE.md | PRODUCTION | Slimmed v2.3 |

## Quick Reference

### I need to modify question types
- **ADD new question type**: 
  1. Add model to `engine/core/questions.py`
  2. Add parsing logic to `engine/parsing/text_parser.py`
  3. Add validation to `engine/validation/rules/question_rules.py`
  4. Add Canvas renderer to `engine/rendering/canvas/question_renderers/`
  
- **MODIFY existing question type**: Edit `engine/core/questions.py`

### I need to change QTI output
- **Assessment XML**: `engine/rendering/canvas/qti_builder.py`
- **Numerical questions**: `engine/rendering/canvas/question_renderers/numerical_renderer.py`
- **HTML formatting**: `engine/rendering/canvas/formatters/html_formatter.py`
- **Manifest**: `engine/rendering/canvas/manifest_builder.py`
- **Metadata**: `engine/rendering/canvas/metadata_builder.py`

### I need to modify validation
- **Add hard fail rule**: `engine/validation/rules/structure_rules.py`
- **Add fairness check**: `engine/validation/rules/fairness_rules.py`
- **Add auto-fixer**: `engine/validation/fixers/` (create new file or modify existing)
- **Change validation flow**: `engine/validation/validator.py`
 - **Point allocation / Answer balancing**: `engine/validation/point_calculator.py`, `engine/validation/answer_balancer.py`

### I need to modify parsing
- **TXT format parsing**: `engine/parsing/text_parser.py`
- **Add new input format**: Create new file in `engine/parsing/`, implement parser protocol
- **Parser utilities**: `engine/utils/text_utils.py`

### I need to modify the pipeline
- **Main workflow**: `engine/orchestrator.py`
- **Packaging router**: `engine/packagers/packager.py`
- **Canvas output**: `engine/packagers/canvas_handler.py`
- **Physical output**: `engine/packagers/physical_handler.py`

### I need to modify user feedback
- **Success logs**: `engine/feedback/log_generator.py`
- **Fail prompts**: `engine/feedback/fail_prompt_generator.py`

---

## Data Flow (Read This First!)

```
TXT file in DropZone/
    ↓
[Orchestrator Agent]
    ↓
[Parser Agent] → Quiz Data Structure
    ↓
[Point Calculator Agent] → Quiz Data + Points
    ↓
[Answer Balancer Agent] → Quiz Data + Shuffled Choices
    ↓
[Packager Router Agent]
    ├→ [Canvas Handler Agent] → QTI-ZIP in Finished_Exports/
    └→ [Physical Handler Agent] → 3x DOCX in Finished_Exports/
    ↓
Teacher receives all outputs
```

---

## Directory Structure

```
engine/
├── orchestrator.py              # Main pipeline controller
├── core/                        # Domain models (data structures)
│   ├── quiz.py                  # Quiz aggregate
│   ├── questions.py             # All question types
│   └── answers.py               # Answer specifications (NumericalAnswer)
├── parsing/                     # Input → Domain models
│   ├── text_parser.py           # TXT → Quiz
│   └── parser_protocol.py       # Parser interface
├── validation/                  # Quality control
│   ├── validator.py             # Main validator
│   ├── rules/                   # What to check
│   │   ├── structure_rules.py   # Hard fails (missing fields)
│   │   └── fairness_rules.py    # Soft fails (patterns, bias)
│   └── fixers/                  # How to fix
│       ├── auto_fixer.py        # Orchestrates all fixes
│       ├── point_normalizer.py  # Distribute 100 points
│       ├── choice_randomizer.py # Shuffle + pattern breaking
│       ├── text_cleaner.py      # Sanitize text
│       └── bounds_calculator.py # Numerical bounds
├── rendering/                   # Domain models → Output
│   ├── canvas/                  # Canvas QTI output
│   │   ├── canvas_packager.py   # Main Canvas builder
│   │   ├── qti_builder.py       # Core QTI XML
│   │   ├── manifest_builder.py  # imsmanifest.xml
│   │   ├── metadata_builder.py  # assessment_meta.xml
│   │   ├── question_renderers/  # One file per question type
│   │   │   ├── numerical_renderer.py
│   │   │   └── ...
│   │   └── formatters/
│   │       └── html_formatter.py
│   └── physical/                # Physical quiz (PRODUCTION)
│       └── physical_packager.py
├── packagers/                   # Bundle outputs
│   ├── packager.py              # Router
│   ├── canvas_handler.py        # Canvas QTI
│   └── physical_handler.py      # Physical DOCX
├── packaging/                   # Legacy packaging
│   ├── zip_packager.py
│   └── folder_creator.py
├── feedback/                    # User-facing messages
│   ├── log_generator.py
│   └── fail_prompt_generator.py
├── utils/                       # Shared utilities
│   └── text_utils.py
├── web/                         # Web interface (optional)
├── dev/                         # EXPERIMENTS ONLY
│   ├── experiments/
│   ├── prototypes/
│   └── test_cases/
├── tests/                       # Automated tests
│   ├── unit/
│   └── integration/
└── docs/
    ├── AGENT_MAP.md             # This file
    ├── ARCHITECTURE.md          # System design
    └── MIGRATION_GUIDE.md       # Migration history
```

---

## Validator Agents

### Point Calculator Agent
**File:** `engine/validation/point_calculator.py`
**Responsibilities:**
- Assign point values to all questions
- Apply 2.5x weight to ESSAY and FILEUPLOAD types
- Ensure total equals 100 (or specified target)
- Correct rounding errors
- Log point allocation decisions

**Inputs:** Parsed question list
**Outputs:** Questions with `points` field assigned
**Configuration:** `default_styles.py`

**Key Principle:** Remove ALL point calculation from LLM. Teacher edits in Canvas if needed.

### Answer Balancer Agent
**File:** `engine/validation/answer_balancer.py`
**Responsibilities:**
- Balance MC correct answer distribution (A/B/C/D)
- Balance TF correct answer ratio (~50/50)
- Shuffle MA choices randomly
- Update `correct_index` after shuffling
- Log distribution statistics

**Inputs:** Questions with points assigned
**Outputs:** Questions with shuffled choices
**Critical:** Maintains correctness while improving distribution

**Key Principle:** Remove answer balancing from LLM. Script handles mechanical shuffling.

## Orchestrator Agent
**File:** `orchestrator.py`
**Responsibilities:**
- Coordinate entire quiz generation pipeline
- Route teacher input to parser
- **NEW:** Call validators in sequence (points, then balancing)
- Route validated data to packager
- **NEW:** Always generate BOTH Canvas and Physical outputs
- Report all output paths to teacher
- Handle errors gracefully

**Pipeline Order:**
1. Parse teacher input → quiz data
2. Calculate points → quiz data with points
3. Balance answers → quiz data with shuffled choices  
4. Package → Canvas ZIP + Physical DOCXs
5. Report success

**Key Principle:** Pure coordination. No quiz logic in orchestrator.

## Packager Agents

### Router Agent
**File:** `packagers/packager.py`
**Responsibilities:**
- Main packaging entry point
- Route to canvas_handler AND physical_handler (always both)
- Aggregate results
- Return combined output dictionary

**Key Change:** Now generates dual outputs by default (no teacher selection needed)

### Canvas Handler Agent
**File:** `packagers/canvas_handler.py`
**Status:** PRODUCTION (moved from dev)
**Responsibilities:**
- Generate QTI 1.2 XML
- Build manifest and metadata
- Create ZIP package
- Validate Canvas requirements
- Log Canvas-specific stats

### Physical Handler Agent
**File:** `packagers/physical_handler.py`
**Status:** PRODUCTION (newly completed)
**Responsibilities:**
- Generate student quiz DOCX (formatted for printing)
- Generate answer key DOCX (teacher grading reference)
- Generate rationale sheet DOCX (student corrections)
- Apply layout logic (2-column vs 1-column MC)
- Handle stimulus passages
- Log layout and distribution stats

**Sub-functions:**
- `_create_student_quiz()` - Main quiz with smart formatting
- `_create_answer_key()` - Simple table for grading
- `_create_rationale_sheet()` - Explanations for corrections
- `_log_validation_stats()` - Developer statistics

**Formatting Control:**
- Layout decisions: In physical_handler.py functions
- Style constants: In default_styles.py

## Agent Interaction Flow

```
Teacher Input
    ↓
[Orchestrator Agent]
    ↓
[Parser Agent] → Quiz Data Structure
    ↓
[Point Calculator Agent] → Quiz Data + Points
    ↓
[Answer Balancer Agent] → Quiz Data + Shuffled Choices
    ↓
[Packager Router Agent]
    ├→ [Canvas Handler Agent] → QTI-ZIP
    └→ [Physical Handler Agent] → 3x DOCX
    ↓
Teacher receives all outputs
```

## LLM Agent
**File:** External (Claude/GPT via API)
**System Prompt:** `QF_BASE.md`

**Responsibilities (REDUCED):**
- Generate educationally appropriate questions
- Create plausible distractors
- Write clear prompts
- Format text with Canvas-safe HTML/LaTeX
- Provide rationales

**NO LONGER RESPONSIBLE FOR:**
- ~~Point allocation~~
- ~~Answer distribution balancing~~
- ~~Format validation~~ (script validates)

**Recent Changes:**
- QF_BASE.md slimmed by ~500-800 words
- Token usage reduced
- Focus shifted to content quality over mechanical details

## Common Tasks

### Add a tolerance mode to numerical questions

1. **Update model**: `engine/core/answers.py`
   - Add new tolerance_mode value
   - Add any required fields (e.g., new_margin_value)

2. **Update parser**: `engine/parsing/text_parser.py`
   - Add parsing logic for new tolerance syntax in `_parse_numerical_tolerance()`
   - Update `_resolve_numerical_bounds()` to compute bounds for new mode

3. **Update renderer**: `engine/rendering/canvas/question_renderers/numerical_renderer.py`
   - Add QTI generation logic for new mode in `_build_scoring()`

4. **Add test**: `engine/tests/unit/test_numerical_questions.py`

### Fix a rendering bug

1. **Identify question type**: Which type has the bug?

2. **Find renderer**:
   - MC/TF/MA/Essay/etc: `engine/rendering/canvas/qti_builder.py` → `_build_item()`
   - Numerical: `engine/rendering/canvas/question_renderers/numerical_renderer.py`

3. **Fix + test**: Update logic, add regression test

### Add a validation rule

1. **Hard fail or soft fail?**
   - Hard fail (missing field, malformed): `engine/validation/rules/structure_rules.py`
   - Soft fail (pattern, bias): `engine/validation/rules/fairness_rules.py`

2. **Add rule function**: Return list of error/warning messages

3. **Update validator**: `engine/validation/validator.py` → call your new rule

4. **Add test**: `engine/tests/unit/test_validator.py`

### Add an auto-fixer

1. **Create fixer**: `engine/validation/fixers/my_fixer.py`
   - Implement `fix(quiz) -> (quiz, log_messages)` method

2. **Register fixer**: `engine/validation/fixers/auto_fixer.py`
   - Add to `fix_all()` method

3. **Add test**: Verify fix is applied and logged

### Modify the text format

1. **Update parser**: `engine/parsing/text_parser.py`
   - Modify `_parse_block()` to handle new syntax

2. **Update sample**: Add example to `engine/dev/test_cases/`

3. **Add test**: Verify new syntax parses correctly

---

## File Naming Conventions

- **Models**: `engine/core/questions.py` (plural - contains many question types)
- **Parsers**: `engine/parsing/text_parser.py` (describes format, not function)
- **Renderers**: `engine/rendering/canvas/qti_builder.py` (describes output)
- **Services**: `engine/validation/validator.py` (describes function)
- **Utilities**: `engine/utils/text_utils.py` (plural - contains many functions)

---

## Trust Boundaries

**Critical concept**: Only the Validator is skeptical.

```
Parser output          → May have semantic errors
Validator output       → Guaranteed valid
Renderer input         → Can assume valid structure
```

This means:
- **Parsers** do minimal validation (just enough to parse)
- **Validators** do comprehensive validation
- **Renderers** trust their input (no defensive checks)

If you're tempted to add validation to a renderer, **add it to the validator instead**.

---

## Import Patterns

### Correct
```python
from engine.core.questions import MCQuestion
from engine.validation.validator import QuizValidator
from ..core.quiz import Quiz  # Relative import within engine/
```

### Incorrect
```python
from Packager.quizforge.domain.questions import MCQuestion  # OLD
from engine import *  # Too broad
```

---

## Testing Strategy

### When to write unit tests
- New question type
- New validation rule
- New auto-fixer
- Bug fix

### When to write integration tests
- New output format
- Pipeline modification
- Multi-component changes

### Where to put tests
- `engine/tests/unit/` - Component tests
- `engine/tests/integration/` - Full pipeline tests
- `engine/dev/test_cases/` - Manual test scripts (not automated)

---

## Debugging Tips

### Quiz not parsing
1. Check `engine/parsing/text_parser.py` → `_parse_block()`
2. Add print statements or breakpoints
3. Test with minimal example in `engine/dev/test_cases/`

### Validation failing unexpectedly
1. Check `engine/validation/rules/structure_rules.py`
2. Look for error message in returned list
3. Add test case to `engine/tests/unit/test_validator.py`

### Canvas ZIP not importing
1. Verify ZIP structure with `zipfile` module
2. Check QTI XML with Canvas import error message
3. Compare with known-good ZIP from `User_Docs/samples/`

### Tests failing after change
1. Check if you updated all import paths
2. Verify core models haven't changed unexpectedly
3. Look for circular imports

---

## DO NOT

- ❌ Import from `Packager/` or `Packager_OLD/` (deprecated)
- ❌ Put experiments in production directories
- ❌ Add validation to renderers (belongs in validator)
- ❌ Modify files in `engine/dev/` for production features
- ❌ Skip tests for bug fixes
- ❌ Use `from engine import *`

## DO

- ✅ Read relevant docstrings before modifying
- ✅ Add tests for new features
- ✅ Update AGENT_MAP.md if structure changes
- ✅ Keep experiments in `engine/dev/`
- ✅ Use relative imports within `engine/`
- ✅ Follow existing naming conventions

---

## Getting Help

### For architecture questions
→ Read `engine/docs/ARCHITECTURE.md`

### For migration history
→ Read `engine/docs/MIGRATION_GUIDE.md`

### For user features
→ Read `User_Docs/`

### For LLM prompt modules
→ Read `LLM_Modules/README.txt`

---

## Quick Command Reference

```bash
# Run all tests
python -m pytest engine/tests/ -v

# Run specific test file
python -m pytest engine/tests/unit/test_validator.py -v

# Run orchestrator
python engine/orchestrator.py

# Or use batch/shell scripts
run_quizforge.bat      # Windows
./run_quizforge.sh     # Mac/Linux

# Manual test a component
python engine/dev/test_cases/test_parser_manual.py
```

---

**Last Updated**: November 16, 2025  
**Version**: 2.3 (validators + physical packaging)

