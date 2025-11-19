# QuizForge Architecture Guide

**Purpose:** This document explains the QuizForge codebase structure, data flow, module responsibilities, and safe modification patterns. It is written for LLM agents and developers working on this project.

**Last Updated:** 2025-11-16

---

## Table of Contents

1. [High-Level Data Flow](#high-level-data-flow)
2. [Module Responsibilities](#module-responsibilities)
3. [Directory Structure](#directory-structure)
4. [Import Patterns](#import-patterns)
5. [Safe vs. Risky Changes](#safe-vs-risky-changes)
6. [Adding a New Question Type](#adding-a-new-question-type)
7. [Key Integration Points](#key-integration-points)
8. [Common Pitfalls](#common-pitfalls)

---

## High-Level Data Flow

All QuizForge workflows follow this pipeline:

```
Text Quiz File
  ↓
[TextOutlineParser] ← parses into
  ↓
[Quiz Aggregate] (title + list of Questions)
  ↓
Validators (post-parse enhancement):
  ├→ [Point Calculator] (assigns points per question)
  └→ [Answer Balancer] (shuffles choices, balances distribution)
  ↓
[Packager Service] ← orchestrates
  ├→ [QTI Assessment XML Builder] (Canvas ZIP)
  ├→ [Manifest XML Builder]
  ├→ [Canvas Meta XML Builder]
  └→ [ZIP Writer]
  └→ [DOCX Writer] (Physical outputs: student quiz, key, rationale)
  ↓
quiz outputs (Canvas ZIP + 3x DOCX + logs)
```

**Key Principle:** Each step is independent. You can test parsing without rendering, or rendering without ZIP packaging.

---

## System Data Flow

```
Teacher Input
    ↓
Orchestrator
    ↓
Parser (text → quiz data structure)
    ↓
Validators:
  - Point Calculator (assign points)
  - Answer Balancer (shuffle choices)
    ↓
Packagers:
  - Canvas Handler (QTI-ZIP)
  - Physical Handler (student & key & rationale DOCX)
    ↓
Output Folder:
  - quiz_name.zip (Canvas import)
  - quiz_name_student.docx (printable quiz)
  - quiz_name_key.docx (answer key)
  - quiz_name_rationale.docx (corrections sheet)
  - validation.log
```

  ---

  ## Token Optimization Strategy

  QuizForge offloads mechanical tasks from LLMs to local deterministic scripts to reduce token usage and improve reliability.

  **LLM Responsibilities (Creative):**
  - Generate educationally sound questions and plausible distractors
  - Compose clear, scaffolded prompts and rationales

  **Script Responsibilities (Mechanical):**
  - Assign point values (point calculator)
  - Shuffle and balance answer choices (answer balancer)
  - Validate format and fix minor issues (validation rules and fixers)
  - Generate Canvas QTI XML and DOCX layout for physical output

  **Benefits:**
  - Reduced token usage in LLM prompts (shorter and focused prompts)
  - Deterministic behavior for mechanical aspects (consistent exports)
  - Easier test coverage for non-creative workflows



---

## Module Responsibilities

### Domain Layer (`quizforge/domain/`)

These modules define **what** the data looks like. They contain no business logic.

#### `questions.py`
- **Purpose:** Define all question type classes (dataclasses)
- **What it contains:** `Question`, `MCQuestion`, `TFQuestion`, `NumericalQuestion`, etc.
- **Safe to modify:** YES, but only to:
  - Add new fields to existing question types
  - Add new question type classes
  - Modify validation logic in `NumericalQuestion.validate()`
- **Unsafe to modify:** Never rename existing fields—doing so breaks `text_parser.py` and all renderers
- **Depends on:** Nothing (pure data classes)
- **Depended on by:** `text_parser.py`, `assessment.py`, `numerical.py`, `validation.py`

#### `quiz.py`
- **Purpose:** Define the `Quiz` aggregate (title + questions list)
- **What it contains:** Simple `@dataclass Quiz` with a `total_points()` method
- **Safe to modify:** YES, only to add new aggregate-level methods
- **Depends on:** `questions.py`
- **Depended on by:** `text_parser.py`, `packager.py`, `validation.py`

---

### Input/Output Layer (`quizforge/io/parsers/`)

These modules convert external formats into domain objects.

#### `base.py`
- **Purpose:** Define the `QuizParser` protocol (interface)
- **What it contains:** `Protocol` that all parsers must implement
- **Safe to modify:** RARELY. Only if you want to change the parsing interface
- **Key method:** `parse(source: str, *, title_override: Optional[str] = None) -> Quiz`

---

### Validators Module (`quizforge/validation/`)

Post-parsing validation and correction layer. Runs after parsing and before packaging.

#### `point_calculator.py`
- **Purpose:** Automatic point allocation
- **Input:** Parsed question list (`Quiz.questions`)
- **Output:** Questions with `points` assigned consistently
- **Logic:**
  - Default: `DEFAULT_QUIZ_POINTS` (100)
  - ESSAY and FILEUPLOAD = `HEAVY_QUESTION_WEIGHT` (defaults to 2.5x)
  - All other types = 1x weight
  - Rounding errors corrected on the first scorable question
- **Configuration:** `engine/rendering/physical/styles/default_styles.py` (contains `DEFAULT_QUIZ_POINTS`, `HEAVY_QUESTION_WEIGHT`)

#### `answer_balancer.py`
- **Purpose:** Balance correct answer distribution and shuffle choices where appropriate
- **Input:** Parsed question list
- **Output:** Questions with shuffled `choices` and updated `choice.correct` flags (packagers read these)
- **Operations:**
  - **MC:** Distribute correct answers evenly across A/B/C/D positions (per choice-count grouping)
  - **MA:** Shuffle choices randomly while preserving `correct` flags
  - **TF:** Balance True/False ratio to approximately 50/50 by flipping when necessary
  - Update `correct_index` and `correct_indices` in any serialized output if needed

**Critical:** Packagers render according to the mutated domain models (the shuffled choices are authoritative). Answer keys, rationales, and QTI XML will reference the shuffled ordering.


#### `text_parser.py` (COMPLEX)
- **Purpose:** Parse the plain-text quiz outline format into a `Quiz` object
- **What it contains:**
  - `TextOutlineParser.parse()` — reads from file path
  - `TextOutlineParser.parse_text()` — reads from string (web-compatible)
  - `_parse_block()` — converts a single `---` delimited block into a Question
  - Helpers for numerical questions: `_parse_decimal_value()`, `_parse_numerical_tolerance()`, etc.
- **Safe to modify:** YES, but carefully
  - Add new question type parsing in `_parse_block()`
  - Modify prompt/choice sanitization
  - Adjust point normalization logic
- **Unsafe to modify:**
  - Never change the signature of `parse()` or `parse_text()`
  - Never rename field parsing (e.g., `Type:`, `Prompt:`, `Points:`)
  - Be careful with numerical bounds computation (`_resolve_numerical_bounds()`)—it feeds into rendering
- **Depends on:** `questions.py`, `quiz.py`, `utils.py` (for `sanitize_text`, `rand8`)
- **Depended on by:** `packager.py` (via `Packager` service)

---

### Rendering Layer (`quizforge/renderers/qti/`)

These modules convert domain objects into QTI XML strings.

#### `assessment.py` (COMPLEX)
- **Purpose:** Build the main QTI 1.2 assessment XML (`<questestinterop>`)
- **What it contains:**
  - `build_assessment_xml(quiz)` — entry point
  - `_build_item()` — converts a Question into a QTI `<item>`
  - `_build_response()` — builds the response structure (MC choices, TF radio buttons, etc.)
  - `_build_scoring()` — builds resprocessing with scoring rules
- **Safe to modify:** YES, but only:
  - Adjust XML attributes for Canvas compatibility
  - Modify scoring logic per question type
  - Add new question type rendering in `_build_response()` or `_build_scoring()`
- **Unsafe to modify:**
  - Never change the XML namespace prefixes
  - Never remove metadata fields—Canvas expects them
  - Be careful with `_build_response()` return value shape—`_build_scoring()` depends on it
- **Depends on:** `questions.py`, `html.py`, `numerical.py`, `utils.py`
- **Depended on by:** `packager.py`

#### `physical/` (Physical DOCX renderer)
- **Purpose:** Generate printable DOCX outputs (student quiz, teacher key, rationale)
- **What it contains:** `physical_packager.py`, helper `key_formatter.py`, layout/format utilities
- **Key behavior:**
  - Smart MC layout (2-column if short choices, 1-column otherwise)
  - Generates answer key with letters corresponding to shuffled choices
  - Rationale sheet embeds correct answer text in explanation
  - Reports layout and distribution statistics in log
- **Depends on:** `questions.py`, `default_styles.py`, `docx` (python-docx)
- **Depended on by:** `packager.py`

#### `html.py` (VERY COMPLEX)
- **Purpose:** Convert quiz prompts and choices into Canvas-safe HTML
- **What it contains:**
  - `htmlize_prompt()` — processes multi-line text, code blocks, excerpts, blockquotes
  - `htmlize_choice()` — wraps choice text in safe HTML
  - `add_passage_numbering()` — auto-detects passage type (poetry, prose_short, prose_long)
  - `syntax_highlight_python()` — colorizes Python code
  - Helper functions for serialization and escaping
- **Safe to modify:** YES, but only:
  - Adjust CSS styling in HTML output
  - Add new code language highlighting
  - Modify passage numbering behavior
- **Unsafe to modify:**
  - Never change XML escaping logic—it breaks Canvas imports
  - Be careful with regex patterns—they're fragile
  - Don't remove `html_mattext()` or change its signature
- **Depends on:** Standard library (re, xml.etree, xml.sax.saxutils)
- **Depended on by:** `assessment.py`, `numerical.py`

#### `manifest.py`
- **Purpose:** Build the IMS Content Common Cartridge manifest XML
- **What it contains:** Single function `build_manifest_xml(quiz_title, guid)` that returns XML string
- **Safe to modify:** RARELY—Canvas has strict requirements here
- **Unsafe to modify:** Almost anything. Only change if Canvas updates the CC spec.
- **Depends on:** Nothing (pure string generation)
- **Depended on by:** `packager.py`

#### `meta.py`
- **Purpose:** Build Canvas quiz metadata XML (`assessment_meta.xml`)
- **What it contains:** Single function `build_assessment_meta_xml(title, total_points, guid)`
- **Safe to modify:** YES, only to add Canvas-specific metadata fields (shuffle, time limits, etc.)
- **Unsafe to modify:** Never remove existing fields—Canvas expects them
- **Depends on:** Nothing
- **Depended on by:** `packager.py`

#### `numerical.py` (CRITICAL)
- **Purpose:** Special rendering for numerical questions (Canvas has unique requirements)
- **What it contains:**
  - `build_numerical_item()` — creates a numerical question item
  - `_build_scoring()` — handles tolerance/precision/range scoring
  - `_format_decimal()` — formats Decimal values for Canvas (must include `.0` for integers)
- **Safe to modify:** YES, but very carefully
  - Adjust margin/tolerance logic
  - Modify precision computation
  - Adjust decimal formatting
- **Unsafe to modify:**
  - Never change bounds computation—it must match `text_parser.py` logic
  - Never remove the `vargte`/`vargt`/`varlte` bounds elements
  - Don't change the decimal format without testing on live Canvas
- **Depends on:** `questions.py`, `html.py`, `utils.py`
- **Depended on by:** `assessment.py`

---

### Service Layer (`quizforge/services/`)

These modules orchestrate workflows.

#### `packager.py`
- **Purpose:** Coordinate the entire parse → render → package workflow
- **What it contains:**
  - `Packager` class — main orchestrator
  - `package()` — file-based packaging
  - `package_text()` — text-based packaging (web-compatible)
  - `summarize()` — validation-only mode
- **Safe to modify:** YES
  - Add new workflow methods (e.g., `package_with_key()`)
  - Modify inspection/validation steps
  - Add error handling
- **Unsafe to modify:** Never change the public API (`parse()`, `package()`, `package_text()`)
- **Depends on:** `TextOutlineParser`, all renderers (Canvas + Physical), `validation.py`, `zip_writer.py`, `folder_creator.py`
- **Depended on by:** CLI (`main.py`), web app (`web/app.py`)

### Packagers Module (`quizforge/packagers/`)

These modules handle the final packaging step: converting domain objects into packaged files for distribution.

#### `packager.py` (Router)
- **Purpose:** Main entry point for all packaging; returns a result dict with both Canvas and Physical outputs
- **Behavior:** After receiving validated quiz data, call both Canvas and Physical handlers and write result paths to disk

#### `canvas_handler.py`
- **Purpose:** Generate Canvas QTI ZIP files for Canvas import
- **Outputs:** QTI ZIP, manifest, assessment XML, assessment_meta.xml
- **Notes:** Applies Canvas-specific validation and logs Canvas-only warnings

#### `physical_handler.py`
- **Purpose:** Generate printable DOCX files (student quiz, answer key, rationale)
- **Outputs:** Student docx, key docx, rationale docx, physical validation log
- **Notes:** Physical handler uses `default_styles.py` for layout and documents; it expects the quiz to have points assigned and choices balanced by validators.


**Behavior:** Always generates BOTH Canvas QTI-ZIP and Physical DOCX files (student quiz, answer key, rationale) and returns their paths in the result dictionary.

#### `validation.py`
- **Purpose:** Inspect generated QTI packages for integrity and completeness
- **What it contains:**
  - `summarize_quiz()` — human-readable quiz summary
  - `inspect_qti_package()` — parses ZIP, checks XML structure, counts question types
  - `PackageInspection` — dataclass for inspection results
- **Safe to modify:** YES, safely
  - Add new inspection checks
  - Modify summary format
  - Add validation rules
- **Depends on:** `questions.py`, `quiz.py`, XML parsing (stdlib)
- **Depended on by:** `packager.py`, CLI

#### `orchestrator.py`
- **Purpose:** Coordinate the file-driven pipeline (DropZone → Output)
- **What it contains:** `QuizForgeOrchestrator` class with `process_all()`, `process_file()` methods
- **Pipeline responsibilities:**
  1. Read quiz text files from DropZone
  2. Parse with `TextOutlineParser`
  3. Run validators (point calculator, answer balancer)
  4. Validate quiz with `validation.py` (inspection rules)
  5. Route to `packager.py` to produce both Canvas and Physical outputs
  6. Archive originals and write logs
- **Key Principle:** Orchestrator performs coordination and file I/O only — quiz logic resides in parsers/validators/renderers.

---

### CLI Layer (`quizforge/cli/`)

#### `main.py`
- **Purpose:** Command-line interface for QuizForge
- **What it contains:**
  - `build_arg_parser()` — sets up argparse
  - `run_cli()` — main entry point
- **Safe to modify:** YES
  - Add new CLI flags
  - Modify help text
  - Add new subcommands
- **Depends on:** `packager.py`, `argparse`
- **Depended on by:** `quizforge_packager.py`, `run_packager.py`

---

### Infrastructure Layer (`quizforge/infrastructure/`)

#### `zip_writer.py`
- **Purpose:** Create QTI ZIP package as bytes
- **What it contains:** Single function `create_zip_bytes(manifest_xml, assessment_xml, assessment_meta_xml, guid)`
- **Safe to modify:** RARELY—only if you want to add compression options or change ZIP structure
- **Depends on:** `zipfile` (stdlib)
- **Depended on by:** `packager.py`

---

### Utilities (`quizforge/utils.py`)

- **Purpose:** Shared helper functions
- **Key functions:**
  - `rand8()` — generate 8-character random identifier
  - `sanitize_text()` — convert smart quotes, fancy dashes to ASCII
- **Safe to modify:** YES, add new utilities as needed
- **Depended on by:** Almost everything

---

## Directory Structure

```
Packager/
├── quizforge_packager.py          # Backward-compat wrapper (DO NOT EDIT)
├── run_packager.py                # Preferred CLI entry point (safe to modify)
├── requirements.txt               # Python dependencies
├── README_QTI_PACKAGER.md         # User documentation
│
└── quizforge/
    ├── __init__.py                # Package marker
    ├── utils.py                   # Shared utilities (safe to modify)
    │
    ├── cli/                       # Command-line interface
    │   ├── __init__.py
    │   └── main.py                # (safe to modify)
    │
    ├── domain/                    # Data models (CORE—handle carefully)
    │   ├── __init__.py
    │   ├── questions.py           # (safe to modify, but impacts many files)
    │   └── quiz.py                # (safe to modify)
    │
    ├── io/                        # Input/output
    │   ├── parsers/
    │   │   ├── __init__.py
    │   │   ├── base.py            # Parser protocol (rarely modify)
    │   │   └── text_parser.py     # (COMPLEX—modify carefully)
    │   └── __init__.py
    │
    ├── renderers/                 # Output rendering
    │   ├── qti/
    │   │   ├── __init__.py
    │   │   ├── assessment.py      # (COMPLEX—modify carefully)
    │   │   ├── html.py            # (VERY COMPLEX—modify very carefully)
    │   │   ├── manifest.py        # (rarely modify)
    │   │   ├── meta.py            # (safe to modify)
    │   │   └── numerical.py       # (CRITICAL—modify very carefully)
    │   └── __init__.py
    │
    ├── services/                  # Orchestration layer (SAFE)
    │   ├── __init__.py
    │   ├── packager.py            # (safe to modify)
    │   └── validation.py          # (safe to modify)
    │
    └── infrastructure/            # Low-level utilities
        ├── __init__.py
        └── zip_writer.py          # (rarely modify)

tests/
├── test_numerical_decimal_formatting.py
└── test_numerical_integration.py

dev/                              # EXPERIMENTAL WORK ONLY
├── generate_numerical_zip.py
├── numerical_experimental.py
└── ... (various test files and notes)
```

---

## Module Dependencies

```
default_styles.py (configuration constants)
  ↑
  ├── validators/point_calculator.py
  ├── validators/answer_balancer.py
  ├── renderers/qti/qti_builder.py
  └── renderers/physical/physical_packager.py
    
orchestrator.py
  ├── parsers/text_parser.py
  ├── validators/point_calculator.py
  ├── validators/answer_balancer.py
  └── services/packager.py
      ├── renderers/qti/qti_builder.py
      └── renderers/physical/physical_packager.py
```


---

## Import Patterns

### Safe Import Patterns

✅ **Within the same layer (horizontal imports):**
```python
# In assessment.py (same layer)
from .html import htmlize_prompt
from .numerical import build_numerical_item
```

✅ **From domain to anything (downward imports):**
```python
# In text_parser.py (io layer)
from ...domain.questions import MCQuestion, TFQuestion
from ...domain.quiz import Quiz
```

✅ **From lower layers to higher:**
```python
# In packager.py (services layer)
from ..io.parsers.text_parser import TextOutlineParser
from ..renderers.qti.assessment import build_assessment_xml
```

✅ **Shared utilities are always safe:**
```python
from ...utils import rand8, sanitize_text
```

### Unsafe Import Patterns

❌ **Never go upward (from services to renderers, etc.):**
```python
# BAD: assessment.py importing from packager.py
from ...services.packager import Packager  # WRONG
```

❌ **Never create circular imports:**
```python
# BAD: text_parser.py importing from assessment.py
from ...renderers.qti.assessment import build_assessment_xml  # WRONG
```

---

## Safe vs. Risky Changes

### Safe Changes (Low Risk)

✅ **Add new utility functions** in `utils.py`
```python
def new_helper_function():
    # This won't break anything
    pass
```

✅ **Add new question type** (requires changes in 4 files, but follows a pattern):
1. Add `class NewQuestion(Question)` in `questions.py`
2. Add parsing logic in `text_parser.py` `_parse_block()`
3. Add rendering in `assessment.py` `_build_response()` and `_build_scoring()`
4. Test in CLI: `python run_packager.py test.txt -o test.zip`

✅ **Modify CLI flags** in `main.py` without changing public Packager API

✅ **Adjust HTML styling** in `html.py` (CSS changes only, no XML structure changes)

✅ **Add validation checks** in `validation.py`

### Risky Changes (Requires Testing)

⚠️ **Rename question fields** in `questions.py`
- Breaks: `text_parser.py`, `assessment.py`, `numerical.py`, `validation.py`
- Mitigation: Search all 4 files for old name before committing

⚠️ **Change numerical bounds computation**
- Breaks: Canvas scoring if bounds don't match tolerance logic
- Mitigation: Test on live Canvas, verify score computation matches expected results

⚠️ **Modify XML namespace or structure** in manifest/assessment
- Breaks: Canvas import entirely
- Mitigation: Test import on live Canvas, don't commit without verification

⚠️ **Change `Packager` public API** (`parse()`, `package()`, `package_text()`)
- Breaks: CLI, web app, any external code
- Mitigation: Update all call sites, test end-to-end

### Forbidden Changes (High Risk)

🚫 **Never edit `quizforge_packager.py`** — it's a backward-compatibility wrapper
🚫 **Never remove XML elements** from renderers — Canvas expects them
🚫 **Never change import structure** without coordinating across the codebase

---

## Adding a New Question Type

Follow this checklist for adding a new question type (e.g., `MULTISELECT`):

### Step 1: Define the Domain Model
**File:** `quizforge/domain/questions.py`

```python
@dataclass
class MultiSelectQuestion(Question):
    choices: List[MCChoice] = field(default_factory=list)
    min_selections: int = 1
    max_selections: int = 5
```

✅ Inherit from `Question`
✅ Use `@dataclass` decorator
✅ Document fields clearly

### Step 2: Add Parser Logic
**File:** `quizforge/io/parsers/text_parser.py`

In `_parse_block()`, add a new branch:

```python
if qtype == "MULTISELECT":
    if len(choices) < 2:
        raise ValueError("MULTISELECT requires at least 2 choices.")
    if sum(1 for c in choices if c.correct) < 1:
        raise ValueError("MULTISELECT requires at least 1 correct choice.")
    return MultiSelectQuestion(
        qtype="MULTISELECT",
        prompt=prompt,
        points=points_value,
        points_set=points_explicit,
        choices=choices
    )
```

✅ Validate inputs (raise ValueError with clear message)
✅ Return the new Question subclass

### Step 3: Add Rendering Logic
**File:** `quizforge/renderers/qti/assessment.py`

In `_build_response()`, add:

```python
if isinstance(question, MultiSelectQuestion):
    response_lid = ET.SubElement(presentation, "response_lid", 
                                 {"ident": "response1", "rcardinality": "Multiple"})
    render_choice = ET.SubElement(response_lid, "render_choice")
    identifiers = [chr(ord("a") + i) for i in range(len(question.choices))]
    correct: List[str] = []
    for ident, choice in zip(identifiers, question.choices):
        label = ET.SubElement(render_choice, "response_label", {"ident": ident})
        material = ET.SubElement(label, "material")
        material.append(html_mattext(htmlize_choice(choice.text)))
        if choice.correct:
            correct.append(ident)
    return {"type": "multiselect", "choices": question.choices, "correct": correct}
```

In `_build_scoring()`, add:

```python
if response_info["type"] == "multiselect":
    choices: List[MCChoice] = response_info["choices"]
    correct: List[str] = response_info["correct"]
    per = round(100.0 / len(correct), 2)
    # ... implement scoring logic
```

✅ Use same naming conventions as existing types
✅ Return dict with clear structure for scoring
✅ Update metadata in `_build_item()` to recognize the new type

### Step 4: Update Metadata Recognition
**File:** `quizforge/renderers/qti/assessment.py`

In `_build_item()`:

```python
elif isinstance(question, MultiSelectQuestion):
    meta_field("question_type", "multiselect_question")
    meta_field("calculator_type", "none")
```

### Step 5: Test
```bash
cd Packager
echo "---
Type: MULTISELECT
Points: 5
Prompt: Pick all that apply
Choices:
- [x] Right A
- [x] Right B
- [ ] Wrong
" > test_ms.txt

python run_packager.py test_ms.txt -o test_ms.zip --validate
```

✅ See parsed summary
✅ Verify ZIP structure: `unzip -l test_ms.zip`
✅ Import on live Canvas and test

---

## Key Integration Points

### Workflow 1: File-Based Packaging (Traditional CLI)
```
run_packager.py → Packager.package(input_path, output_path) 
  → TextOutlineParser.parse(file_path)
  → build_assessment_xml()
  → build_manifest_xml()
  → build_assessment_meta_xml()
  → create_zip_bytes()
  → write to disk
```

### Workflow 2: Text-Based Packaging (Web App)
```
web/app.py → Packager.package_text(content, title_override)
  → TextOutlineParser.parse_text(content)
  → [same as above, but returns bytes instead of writing]
```

### Workflow 3: Validation-Only
```
CLI --validate flag → Packager.summarize()
  → TextOutlineParser.parse()
  → Print human-readable summary (no ZIP)
```

### Extension Point: New Packager Format (Future)
To support a different file format (e.g., JSON, YAML, Markdown):

1. Create `JsonOutlineParser` in `quizforge/io/parsers/json_parser.py`
2. Implement `QuizParser` protocol
3. Register in `Packager.__init__()` as optional parameter
4. Add CLI flag to `main.py` to select parser

This requires **NO changes** to renderers or services—clean separation of concerns.

---

## Common Pitfalls

### Pitfall 1: Forgetting Numerical Bounds Are Computed Twice
**Problem:** You change tolerance logic in `text_parser.py` but not in `numerical.py`
**Solution:** Both files independently compute the same bounds. They must stay in sync.
**Mitigation:** Add a comment linking them, or extract to shared function if logic is complex.

### Pitfall 2: Regex in `html.py` Breaks on Edge Cases
**Problem:** You modify a regex pattern and it breaks on nested code blocks or special characters
**Solution:** These regexes are fragile and need extensive testing
**Mitigation:** Always run `test_numerical_integration.py` and test on live Canvas after changes.

### Pitfall 3: XML Escaping Is Subtle
**Problem:** You add HTML output without escaping and Canvas import fails silently
**Solution:** Use `xml_escape()` from `xml.sax.saxutils` for all user text
**Mitigation:** Search for `xml_escape` to see patterns; follow them exactly.

### Pitfall 4: Canvas Expects Specific Metadata Fields
**Problem:** You remove what looks like an unused metadata field and Canvas breaks
**Solution:** Canvas is rigid about expected fields in assessment_meta.xml and qtimetadata
**Mitigation:** Never delete fields without Canvas documentation and testing.

### Pitfall 5: Point Normalization Changes Affect All Quizzes
**Problem:** You tweak point normalization (e.g., `point_calculator.py` or legacy `_normalize_points()`), and all existing quiz point distributions change
**Solution:** This is global logic that touches every quiz and now lives in the validators module (`engine/validation/point_calculator.py`).
**Mitigation:** Only modify if you have a strong reason; test on diverse quiz structures and update unit tests to cover the new behavior.

### Pitfall 6: Stimulus Items Are Special
**Problem:** Stimulus items have 0 points but still appear in the assessment
**Solution:** They're rendered but don't count toward total points
**Mitigation:** When looping questions, filter with `isinstance(q, StimulusItem)` if needed.

---

## Decision Tree for "Is This Change Safe?"

```
START: I want to modify File X

Q1: Is File X in quizforge/domain/?
   ├─ YES → Q2
   └─ NO → Q3

Q2: Am I only adding new fields or classes?
   ├─ YES → SAFE (low impact)
   ├─ NO: Am I renaming existing fields?
   │   ├─ YES → RISKY (search all files)
   │   └─ NO → RISKY (other breaking change)
   └─ STOP: Get code review before proceeding

Q3: Is File X in quizforge/renderers/qti/ OR quizforge/io/parsers/?
   ├─ YES (renderer) → Q4
   ├─ YES (parser) → Q5
   └─ NO → Q6

Q4: Am I changing XML structure or namespace?
   ├─ YES → FORBIDDEN (breaks Canvas)
   ├─ NO: Am I changing CSS or HTML only?
   │   ├─ YES → SAFE (style changes only)
   │   └─ NO: Am I adding question type handling?
   │       ├─ YES → RISKY (needs 4-file coordination)
   │       └─ NO: Am I fixing a bug?
   │           ├─ YES → RISKY (test on Canvas)
   │           └─ → RISKY (likely edge case)
   └─ STOP: Test changes on live Canvas

Q5: Am I parsing a new field or question type?
   ├─ YES → SAFE (add new branch in _parse_block)
   ├─ NO: Am I changing how existing fields are parsed?
   │   ├─ YES → RISKY (may break existing quizzes)
   │   └─ NO: Am I modifying point normalization or numerical bounds?
   │       ├─ YES → RISKY (verify output on Canvas)
   │       └─ → RISKY (likely hidden impact)
   └─ STOP: Test thoroughly

Q6: Is File X in quizforge/services/?
   ├─ YES → SAFE (safe orchestration layer)
   ├─ NO: Is File X quizforge/cli/main.py?
   │   ├─ YES → SAFE (CLI is flexible)
   │   └─ NO: Is File X in quizforge/infrastructure/?
   │       ├─ YES → RISKY (rarely touches, easy to break)
   │       └─ → Check: Is File X quizforge/utils.py?
   │           ├─ YES → SAFE (add utilities)
   │           └─ → NOT FOUND (unknown file?)
   └─ STOP: Proceed with confidence or get review

SAFE → Proceed, test locally, commit
RISKY → Test on live Canvas, get review, test thoroughly
FORBIDDEN → Stop, escalate
```

---

## Quick Reference: File Edit Impact Matrix

| File | Editing Difficulty | Cascading Changes | Testing Effort | Notes |
|------|-------------------|-------------------|----------------|-------|
| `questions.py` | ⭐ (easy) | ⭐⭐⭐⭐⭐ (very high) | ⭐⭐⭐ (medium) | Central to system |
| `text_parser.py` | ⭐⭐⭐ (hard) | ⭐⭐⭐ (high) | ⭐⭐⭐ (medium) | Many branches, regex |
| `assessment.py` | ⭐⭐⭐ (hard) | ⭐⭐ (medium) | ⭐⭐⭐⭐ (high) | Complex XML logic |
| `html.py` | ⭐⭐⭐⭐ (very hard) | ⭐ (low) | ⭐⭐⭐⭐ (high) | Fragile regex, many edge cases |
| `numerical.py` | ⭐⭐ (medium) | ⭐⭐ (medium) | ⭐⭐⭐⭐⭐ (very high) | Must sync with text_parser |
| `packager.py` | ⭐ (easy) | ⭐ (low) | ⭐ (low) | Orchestration is stable |
| `validation.py` | ⭐ (easy) | ⭐ (low) | ⭐ (low) | Safe inspection layer |
| `main.py` | ⭐ (easy) | ⭐ (low) | ⭐ (low) | CLI is flexible |
| `utils.py` | ⭐ (easy) | ⭐⭐ (medium) | ⭐ (low) | Shared, but safe |

---

## Contact & Escalation

- **For architectural questions:** Review this document first
- **For parser changes:** Verify impact on `text_parser.py` and all 3 renderers
- **For numerical changes:** Test on live Canvas with diverse quiz structures
- **For rendering changes:** Always test ZIP import on live Canvas instance
- **For new question types:** Follow the "Adding a New Question Type" section exactly

---

**End of ARCHITECTURE.md**

Good luck! The system is solid; use this guide to navigate it safely.
