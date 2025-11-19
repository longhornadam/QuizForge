# DEVELOPMENT.md – Internal Reference for Coordinating VSCode Agents

**Audience:** Claude (coordinator), not the VSCode agents themselves.

**Purpose:** Quick reference for:
- How to decompose high-level goals into simple agent tasks
- Common workflows and their atomic steps
- Testing procedures and validation
- Common failure modes and fixes
- Debugging strategies

**Last Updated:** 2025-11-16

---

## Table of Contents

1. [Project Setup & Running](#project-setup--running)
2. [Decomposing Tasks for Agents](#decomposing-tasks-for-agents)
3. [Common Workflows](#common-workflows)
4. [Testing Procedures](#testing-procedures)
5. [Debugging Strategies](#debugging-strategies)
6. [File Change Checklist](#file-change-checklist)
7. [Quick Task Templates](#quick-task-templates)
8. [Validation Pipeline (v2.3+)](#validation-pipeline-v23)
9. [Physical Packaging (v2.3+)](#physical-packaging-v23)
10. [Token Optimization Strategy](#token-optimization-strategy)
11. [Production Modules (v2.3)](#production-modules-v23)
12. [Known Issues & Future Enhancements](#known-issues--future-enhancements)
13. [Performance Notes](#performance-notes)
14. [Version Control Workflow](#version-control-workflow)

---

## Project Setup & Running

### Minimal Environment Setup

```bash
cd Packager
pip install -r requirements.txt
```

Dependencies (from `requirements.txt`):
- Flask 3.0.0 (for web app, not core CLI)
- Werkzeug 3.0.1 (for web app)

Core packager needs **no external dependencies** beyond Python stdlib (xml, zipfile, argparse, uuid, decimal, re).

### Running the Packager

**CLI mode (traditional):**
```bash
python run_packager.py <input_file> -o <output_file>
```

Example:
```bash
python run_packager.py User_Docs/samples/simple_quiz.txt -o test.zip
```

**Validation mode (parse without ZIP):**
```bash
python run_packager.py <input_file> --validate
```

**Override title:**
```bash
python run_packager.py <input_file> -o <output_file> --title "My Custom Title"
```

### Backward Compatibility

`quizforge_packager.py` is a wrapper that calls `run_packager.py`. Both work identically. Never edit `quizforge_packager.py`—it's a compatibility shim.

### Testing the ZIP Output

After generating a ZIP:

```bash
# Inspect structure
unzip -l quiz_package.zip

# Extract to verify contents
mkdir -p test_extract
unzip quiz_package.zip -d test_extract
cat test_extract/imsmanifest.xml
cat test_extract/<guid>/<guid>.xml
```

---

## Decomposing Tasks for Agents

### The Three-Step Agent Instruction Pattern

**Step 1: File Reference** – Point agent to exact location
```
"Open Packager/quizforge/io/parsers/text_parser.py, lines 150-200"
```

**Step 2: Atomic Change** – Give one specific change, not multiple
```
"In the _parse_block() method, find the line:
    if qtype == "MC":
Replace it with:
    if qtype in {"MC", "MCQ"}:"
```

**Step 3: Validation** – Tell them exactly what success looks like
```
"After the change, run:
    python run_packager.py User_Docs/samples/simple_quiz.txt --validate
Verify the output shows 'MC:' in the type list (not 'MCQ')."
```

### Do NOT Do This

❌ "Refactor the parser to handle 5 new question types"
❌ "Fix the numerical scoring to work with Canvas"
❌ "Add support for Markdown input format"

### DO Do This

✅ "In `text_parser.py` line 456, change `if qtype == "MC":` to `if qtype in {"MC", "MCQ"}:`"
✅ "In `numerical.py` line 210, change the tolerance mode from 'absolute' to 'percent' in the test case"
✅ "Add a new function `parse_markdown_file()` to `text_parser.py` that takes a file path and returns a Quiz object"

---

## Common Workflows

### Workflow A: Add a Simple Question Type

**Goal:** Add support for a new question type (e.g., `SHORT_ANSWER`)

**My High-Level Plan:**
1. Add domain model in `questions.py`
2. Add parser logic in `text_parser.py`
3. Add renderer in `assessment.py`
4. Update metadata recognition in `assessment.py`
5. Test with sample quiz
6. Test on live Canvas if it's scoring-related

**Agent Instructions (Atomic Tasks):**

**Task A1 – Define domain model:**
```
In Packager/quizforge/domain/questions.py:
- Import at line 6: from typing import Optional
- At the end of the file (after FileUploadQuestion class), add:

    @dataclass
    class ShortAnswerQuestion(Question):
        pass

Run: python run_packager.py --validate (just to verify imports work)
```

**Task A2 – Add parser logic:**
```
In Packager/quizforge/io/parsers/text_parser.py:
- Find the line: if qtype == "ESSAY":
- After this block (after the return EssayQuestion(...) line), add:
    
    if qtype == "SHORT_ANSWER":
        return ShortAnswerQuestion(qtype="SHORT_ANSWER", prompt=prompt, points=points_value, points_set=points_explicit)

Then import at the top (line 10, in the long import):
Add ShortAnswerQuestion to the import list from ...domain.questions

Run: Create a test file:
    ---
    Type: SHORT_ANSWER
    Prompt: What is 2+2?
    
Save as test_sa.txt, run:
    python run_packager.py test_sa.txt --validate
Output should show "SHORT_ANSWER: 1"
```

**Task A3 – Add renderer logic:**
```
In Packager/quizforge/renderers/qti/assessment.py:
- Find the line: if isinstance(question, EssayQuestion):
- After that entire if-block, add:
    
    if isinstance(question, ShortAnswerQuestion):
        meta_field("question_type", "short_answer_question")
        meta_field("calculator_type", "none")

- Also at the top of the file, import ShortAnswerQuestion:
    Find line: from ...domain.questions import (
    Add ShortAnswerQuestion to the import list

- Find the _build_response() function, locate the line:
    if isinstance(question, EssayQuestion):
    
- After that entire if-block (the one that returns None), add:
    
    if isinstance(question, ShortAnswerQuestion):
        response_str = ET.SubElement(presentation, "response_str", {"ident": "response1", "rcardinality": "Single"})
        render_fib = ET.SubElement(response_str, "render_fib")
        ET.SubElement(render_fib, "response_label", {"ident": "answer1"})
        return None

Run:
    python run_packager.py test_sa.txt -o test_sa.zip
    unzip -l test_sa.zip
Verify the ZIP contains imsmanifest.xml and a guid folder.
```

**Task A4 – Test on Canvas:**
```
Upload test_sa.zip to your Canvas instance.
- Verify the question imports as "Short Answer"
- Verify students can type a response
- Verify it requires manual grading
Report any issues.
```

---

### Workflow B: Fix a Bug in Numerical Question Rendering

**Goal:** Numerical questions are rendering with wrong bounds

**My High-Level Plan:**
1. Identify which layer is wrong (parser or renderer)
2. Review the bounds computation logic
3. Make minimal fix to one layer
4. Test on diverse quiz types
5. Verify on live Canvas

**Agent Instructions (Atomic Tasks):**

**Task B1 – Verify current behavior:**
```
Create a test quiz file:
    ---
    Type: NUMERICAL
    Points: 10
    Prompt: What is 5+5?
    Answer: 10.0
    Tolerance: 10%

Save as test_num.txt, run:
    python run_packager.py test_num.txt -o test_num.zip
    unzip -l test_num.zip
    unzip -p test_num.zip */????.xml | grep -A5 "lower\|upper"
    
Report the exact bounds that appear in the XML.
```

**Task B2 – Review parser logic (if bounds are wrong):**
```
In Packager/quizforge/io/parsers/text_parser.py:
- Find the method _resolve_numerical_bounds()
- Run this test:

    from quizforge.io.parsers.text_parser import TextOutlineParser
    parser = TextOutlineParser()
    quiz = parser.parse_text("""
Type: NUMERICAL
Answer: 10.0
Tolerance: 10%
Prompt: Test
""")
    q = quiz.questions[0]
    print(f"Lower: {q.answer.lower_bound}, Upper: {q.answer.upper_bound}")

Expected for 10.0 ± 10%: Lower: 9.0, Upper: 11.0
If bounds are wrong, report the actual output to Claude.
```

**Task B3 – Review renderer logic (if bounds are right in parser):**
```
In Packager/quizforge/renderers/qti/numerical.py:
- Find the function _append_bounds()
- This adds <vargte> and <varlte> elements
- Make sure it's being called in _build_scoring()
- Run the same test_num.zip and verify XML has both bounds elements.
```

---

### Workflow C: Add a New CLI Flag

**Goal:** Add `--debug` flag that prints verbose output

**My High-Level Plan:**
1. Add arg to parser in `main.py`
2. Pass through to `Packager` or `run_cli()`
3. Modify behavior based on flag

**Agent Instructions:**

**Task C1 – Add CLI argument:**
```
In Packager/quizforge/cli/main.py:
- Find the function build_arg_parser()
- Before the "return parser" line (around line 18), add:

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print verbose debug output"
    )

Test:
    python run_packager.py --help
Verify "--debug" appears in the help output.
```

**Task C2 – Use the flag:**
```
In the same file (main.py), in the run_cli() function:
- After "args = parser.parse_args(argv)", add:

    if args.debug:
        print(f"[DEBUG] Input file: {args.input}")
        print(f"[DEBUG] Output path: {args.output}")

Test:
    python run_packager.py test_sa.txt -o test.zip --debug
Verify you see [DEBUG] lines in the output.
```

---

## Testing Procedures

### Level 1: Parser Validation (Fastest)

**Purpose:** Verify quiz parses without errors

**Command:**
```bash
python run_packager.py <quiz_file> --validate
```

**What to check:**
- No exceptions thrown
- Output shows item count
- Output shows question types

**Example:**
```
Validated 10 items (MC: 5, TF: 3, ESSAY: 2)
```

### Level 2: ZIP Generation (Moderate)

**Purpose:** Verify ZIP is structurally valid

**Commands:**
```bash
python run_packager.py <quiz_file> -o <output.zip>
unzip -l <output.zip>
```

**What to check:**
- ZIP is created without errors
- Contains `imsmanifest.xml`
- Contains `<guid>/<guid>.xml`
- Contains `<guid>/assessment_meta.xml`

### Level 3: XML Validation (Moderate)

**Purpose:** Verify XML is well-formed and contains expected elements

**Commands:**
```bash
unzip -p <output.zip> */????.xml | python -m xml.dom.minidom
```

**What to check:**
- No XML parse errors
- Output is indented (well-formed)

**For numerical questions specifically:**
```bash
unzip -p <output.zip> */????.xml | grep -A2 "vargte\|varlt"
```

Should show bounds elements for each numerical question.

### Level 4: Canvas Import Test (Slowest, Most Authoritative)

**Purpose:** Verify quiz actually imports and works in Canvas

**Steps:**
1. Generate ZIP
2. Log into Canvas (test instance if available)
3. Create a new quiz, choose "Import" → select ZIP
4. Verify:
   - All questions import
   - Question types are correct
   - Prompts and choices display correctly
   - Scoring works (submit test responses)

**For numerical questions:**
- Submit a response within tolerance (should score)
- Submit a response outside tolerance (should not score)

---

## Debugging Strategies

### Problem: Quiz Parses but ZIP Is Invalid

**Diagnosis:**
```bash
python run_packager.py quiz.txt -o quiz.zip
unzip -l quiz.zip  # Should show file structure
unzip -p quiz.zip */????.xml | python -m xml.dom.minidom
```

**Common Causes:**
1. **Missing XML namespace** — `assessment.py` didn't add namespace to root
2. **Unclosed tags** — renderer created malformed XML
3. **Bad character encoding** — non-UTF8 characters in prompts

**Fix Workflow:**
- Check: Is XML namespace present? (Should start with `<questestinterop xmlns=...`)
- Check: Are all tags closed? (Run through XML validator)
- Check: Are non-ASCII chars escaped? (Look for `&` sequences)

### Problem: Quiz Imports to Canvas but Questions Don't Score

**Diagnosis:**
```bash
unzip -p quiz.zip */????.xml | grep -A10 "resprocessing"
```

**Common Causes:**
1. **Missing SCORE decvar** — resprocessing doesn't define SCORE variable
2. **Wrong response ident** — varequal respident doesn't match response ident
3. **Missing setvar action** — respcondition doesn't have "Set" or "Add"

**Fix Workflow:**
```bash
# For each question, verify:
# 1. Has <decvar varname="SCORE">
# 2. Has <varequal respident="response1"> (or matching ident)
# 3. Has <setvar action="Set" varname="SCORE">
```

### Problem: Numerical Question Bounds Are Wrong

**Diagnosis:**
```bash
# Parse the quiz, check bounds before rendering
python -c "
from quizforge.io.parsers.text_parser import TextOutlineParser
p = TextOutlineParser()
q = p.parse_text(open('quiz.txt').read())
for qn in q.questions:
    if hasattr(qn, 'answer'):
        print(f'{qn.prompt[:50]}: {qn.answer.lower_bound} to {qn.answer.upper_bound}')
"
```

**Common Causes:**
1. **Tolerance mode mismatch** — `text_parser.py` computed percent but `numerical.py` expects absolute
2. **Precision bounds wrong** — significant digits or decimal places not computed correctly
3. **Range not respected** — min/max order reversed

**Fix Workflow:**
1. Check `_resolve_numerical_bounds()` in `text_parser.py` — bounds correct?
2. Check `_build_scoring()` in `numerical.py` — bounds used correctly?
3. Test on Canvas: submit response at lower_bound, lower_bound+0.1, upper_bound-0.1, upper_bound

### Problem: Agent Instruction Was Ambiguous

**Symptom:** Agent asks clarifying questions or makes wrong change

**Recovery:**
1. Ask agent to undo change
2. Re-read ARCHITECTURE.md with them to clarify concepts
3. Give new, more specific instruction (cite line numbers, show exact strings)
4. Have them verify success before moving on

---

## File Change Checklist

### When Modifying `questions.py`

- [ ] No existing field names changed (breaks parsers/renderers)
- [ ] New Question subclass inherits from `Question`
- [ ] Uses `@dataclass` decorator
- [ ] Added to imports in `text_parser.py` if new type
- [ ] Added to imports in `assessment.py` if new type
- [ ] Validation logic updated if complex type
- [ ] Test: `python run_packager.py --validate` succeeds

### When Modifying `text_parser.py`

- [ ] New parsing logic is in `_parse_block()`
- [ ] New question type has validation (raises ValueError with clear message)
- [ ] New question type returns correct Question subclass
- [ ] New imports added at top of file
- [ ] Test: `python run_packager.py quiz.txt --validate` shows new type
- [ ] Test: `unzip -l quiz.zip` shows valid structure
- [ ] Check: Does numerical bounds logic need updating?

### When Modifying `assessment.py`

- [ ] New question type added to `isinstance` checks
- [ ] Metadata fields added in `_build_item()`
- [ ] Response structure added in `_build_response()`
- [ ] Scoring logic added in `_build_scoring()`
- [ ] Imports updated at top
- [ ] Test: `python run_packager.py quiz.txt -o quiz.zip` succeeds
- [ ] Test: `unzip -p quiz.zip */????.xml | python -m xml.dom.minidom` validates
- [ ] Test: Import ZIP to Canvas and verify question renders

### When Modifying `numerical.py`

- [ ] Bounds logic matches `text_parser.py` exactly
- [ ] Decimal formatting applied consistently
- [ ] Test: Generate numerical quiz and verify bounds in XML
- [ ] Test: Submit responses at lower_bound, within bounds, upper_bound on Canvas
- [ ] Verify scoring is correct for each case

### When Modifying `html.py`

- [ ] Only CSS/styling changed (no XML structure)
- [ ] Regex changes tested extensively (easy to break edge cases)
- [ ] XML escaping used for all user content
- [ ] Test: `python run_packager.py quiz.txt --validate` succeeds
- [ ] Test: Export to Canvas and verify HTML renders correctly
- [ ] Test edge cases: code blocks, excerpts, special characters

---

## Quick Task Templates

### Template: "Add a new CLI flag"

```
TASK: Add --<flag_name> flag to packager

1. In Packager/quizforge/cli/main.py:
   - Find build_arg_parser() function
   - Before "return parser", add:
     parser.add_argument(
         "--<flag_name>",
         action="<store_true|store>",
         help="<help text>"
     )

2. In run_cli() function, after "args = parser.parse_args(argv)":
   - Add: if args.<flag_name>: <do something>

3. Test: python run_packager.py --help
   Verify <flag_name> appears in help.

4. Test: python run_packager.py quiz.txt -o quiz.zip --<flag_name>
   Verify behavior is correct.
```

### Template: "Add a new utility function"

```
TASK: Add new helper function to utils.py

1. In Packager/quizforge/utils.py:
   - At the end of file, add:
     def new_function(arg1, arg2):
         """Brief description."""
         return result

2. Test locally:
   python -c "from quizforge.utils import new_function; print(new_function(...))"

3. Identify which modules need this function.

4. In each module that needs it:
   - Add to imports: from ...utils import new_function
   - Use in code as needed

5. Run full test suite.
```

### Template: "Fix a bug in a specific question type"

```
TASK: Fix <QuestionType> rendering

1. Reproduce the bug:
   - Create quiz with <QuestionType> question
   - python run_packager.py quiz.txt --validate
   - python run_packager.py quiz.txt -o quiz.zip
   - unzip -p quiz.zip */????.xml > quiz.xml
   - Inspect quiz.xml for expected elements

2. Identify layer (parser or renderer):
   - If data is wrong: bug in text_parser.py
   - If XML is wrong: bug in assessment.py or specialized renderer

3. Locate exact problem in code (line number).

4. Make minimal fix (1-3 lines).

5. Test: repeat step 1.

6. Test on Canvas if scoring-related.
```

### Template: "Add support for new question type"

```
TASK: Add <NewType> question type

See Workflow A above. Requires 4 tasks in sequence:
- A1: Domain model in questions.py
- A2: Parser logic in text_parser.py
- A3: Renderer logic in assessment.py
- A4: Canvas import test

Each task is atomic and standalone.
```

---

## State Management: Tracking Progress

### When Starting a Complex Task

Create a progress file (e.g., `dev/TASK_<task_name>.md`):

```markdown
# Task: Add Support for Multiple File Formats

## Goal
Support JSON quiz format in addition to plain text.

## Steps
- [ ] Step 1: Create JsonParser class
- [ ] Step 2: Register with Packager
- [ ] Step 3: Add CLI flag
- [ ] Step 4: Test
- [ ] Step 5: Update docs

## Current Status
Starting with Step 1.

## Notes
- Parser must implement QuizParser protocol
- No changes to renderers needed
```

### When Debugging an Issue

Use `dev/DEBUG_<issue_name>.md`:

```markdown
# Debug: Numerical Bounds Off by 0.5

## Symptom
Numerical questions with 10% tolerance scoring 9.5 as incorrect when it should pass.

## Investigation
- Bounds in parser: 9.0-11.0 ✓
- Bounds in XML: ...

## Root Cause
(fill in as we discover)

## Fix Applied
...

## Verification
- Manual test: ✓
- Canvas test: (pending)
```

---

## Emergency Procedures

### "Everything Broke, Need to Revert"

```bash
cd Packager
git status
git diff  # See what changed
git checkout <file>  # Revert single file
git checkout .  # Revert all
```

### "Agent Made Inconsistent Changes"

Have agent:
1. Report what they changed (git diff)
2. Describe what went wrong (error message or behavior)
3. Undo change (git checkout <file>)
4. Wait for new instruction

### "ZIP Imports but Canvas Won't Grade"

1. Export the quiz from Canvas
2. Unzip and compare XML with local quiz.zip
3. Identify differences (usually metadata or namespace)
4. Fix in renderer
5. Re-test

---

## Validation Pipeline (v2.3+)

### Overview
Post-parsing validation layer that handles mechanical corrections and enhancements. Runs between parser and packagers.

### Components

#### Point Calculator (`validators/point_calculator.py`)
- Automatically assigns point values
- ESSAY/FILEUPLOAD = 2.5x regular questions
- Default total: 100 points
- Ignores any points in LLM output

**Design Decision:** Remove point math from LLM to reduce token usage and prevent miscalculation. Teachers can edit in Canvas if needed.

#### Answer Balancer (`validators/answer_balancer.py`)
- Shuffles MC choices to distribute correct answers across A/B/C/D
- Balances True/False ratio to ~50/50
- Shuffles MA choices randomly
- Updates `correct_index` to track correct answer position

**Design Decision:** LLMs are poor at maintaining answer distribution across multiple questions. Script guarantees balance.

### Integration Point
Orchestrator calls validators after parsing:
```python
quiz_data = parser.parse(text)
quiz_data['questions'] = calculate_points(quiz_data['questions'])
quiz_data['questions'] = balance_answers(quiz_data['questions'])
results = package_quiz(quiz_data, output_folder)
```

### Testing Validation
1. Generate quiz with 12 MC questions
2. Check answer key - should see varied A/B/C/D distribution
3. Check points - essays should be ~2.5x other questions
4. Check log file - distribution stats logged

---

## Physical Packaging (v2.3+)

### Overview
Generates printable DOCX files alongside Canvas QTI packages. Always produces both outputs.

### Outputs

#### 1. Student Quiz DOCX
- Formatted for paper testing
- Smart layout: 2-column for short MC choices, 1-column for long
- Stimulus passages integrated
- Name/date header
- Appropriate spacing

#### 2. Answer Key DOCX
- Simple table: Question # | Correct Answer | Points
- Shows letter for MC (A/B/C/D)
- Shows value for numerical
- Easy scanning for grading

#### 3. Rationale Sheet DOCX
- Question-by-question explanations
- Format: "Q# - [Correct answer embedded in explanation]"
- Space for student hand-copying corrections
- Pedagogical focus

### Formatting Control

**For spacing/layout tweaks:**
- `packagers/physical_handler.py` - Layout logic, spacing application
- `default_styles.py` - Constants (margins, fonts, thresholds)

**Common tweaks:**
- Rationale spacing: Remove/reduce `doc.add_paragraph()` calls in `_create_rationale_sheet()`
- MC column threshold: Adjust `MC_TWO_COLUMN_THRESHOLD` in default_styles.py
- Margins: Change `DOCX_MARGIN_*` constants

### Dependencies
- `python-docx` library
- Office365 (for teacher editing)

### Testing Physical Outputs
1. Generate quiz
2. Open all 3 DOCX files in Word
3. Verify formatting, spacing, readability
4. Print test page to check layout

---

## Token Optimization Strategy

### Goal
Minimize LLM token usage by offloading non-creative work to deterministic scripts.

### What LLM Does (Creative Work)
- Generate educationally sound questions
- Create plausible distractors
- Write explanations/rationales
- Format complex content (LaTeX, code)

### What Script Does (Mechanical Work)
- Calculate point values
- Balance answer distributions
- Shuffle choices
- Validate formats
- Generate XML/DOCX

### QF_BASE.md Changes (v2.3)
**Removed:**
- Point weighting heuristics (~200 tokens)
- Answer distribution instructions (~150 tokens)
- Verbose validation checklist preamble (~100 tokens)
- Point-related examples throughout (~300 tokens)

**Total Savings:** ~750-800 tokens per generation

**Result:** LLM focuses on content quality. Math/formatting handled reliably by script.

### Measuring Impact
- Token count before: [measure old QF_BASE.md]
- Token count after: [measure new QF_BASE.md]
- Reduction: ~15-20%

---

## Production Modules (v2.3)

### Core Pipeline
- ✅ Text Parser (`parsers/text_parser.py`)
- ✅ Point Calculator (`validators/point_calculator.py`) - NEW
- ✅ Answer Balancer (`validators/answer_balancer.py`) - NEW
- ✅ Canvas Packager (`packagers/canvas_handler.py`)
- ✅ Physical Packager (`packagers/physical_handler.py`) - NEW

### Supporting Modules
- ✅ Orchestrator (`orchestrator.py`)
- ✅ Default Styles (`default_styles.py`)
- ✅ File Utilities (`file_utils.py`, `text_utils.py`)

### LLM System
- ✅ QF_BASE.md (slimmed v2.3)

### Status
All core functionality complete. Future work focuses on:
- Additional question types
- Additional LMS packagers (Moodle, Blackboard)
- Enhanced LLM modules (discipline-specific guidance)

---

## Known Issues & Future Enhancements

### Current System (v2.3)
- ✅ Physical packaging complete
- ✅ Validation system complete
- ✅ Token optimization complete

### Potential Future Work
1. **Additional Packagers**
   - Moodle XML export
   - Blackboard QTI export
   - Google Forms export

2. **Enhanced Validators**
   - Distractor quality scoring
   - Reading level analysis
   - Bloom's taxonomy tagging

3. **LLM Enhancements**
   - Discipline-specific modules (STEM, ELA, Social Studies)
   - Differentiation support (IEP accommodations)
   - Multilingual support

4. **Physical Output Enhancements**
   - PDF generation (if Acrobat Pro acquired)
   - Custom templates per subject
   - Student worksheet variants

### Non-Issues (By Design)
- LLM doesn't control points → INTENDED (script handles)
- LLM doesn't balance answers → INTENDED (script handles)
- Both Canvas + Physical always generated → INTENDED (minimize teacher decisions)

---

### Typical Execution Times

- Parse 10-question quiz: ~50ms
- Render to XML: ~20ms
- ZIP creation: ~5ms
- **Total:** ~75ms per quiz

### Scaling Concerns

- Quizzes up to 100 questions: no issue
- Quizzes with large code blocks: HTML rendering might slow (regex-heavy)
- Stimulus groups: no performance impact

### Memory Usage

- Minimal (most work is string processing)
- ZIP creation holds all files in memory briefly
- No streaming (entire ZIP created at once)

---

## Version Control Workflow

### Before an Agent Works on a Task

```bash
git status  # Should be clean
git pull    # Fetch latest
```

### After an Agent Completes a Task

```bash
git add <files>
git commit -m "Brief description of change"
git push
```

### For Complex Tasks (Multi-Step)

```bash
# After each atomic task
git add <files>
git commit -m "Task: <step X>: <brief description>"
```

---

## End of DEVELOPMENT.md

This is Claude's working document. Refer to it when decomposing tasks for VSCode agents.

Key principle: **Atomic instructions, specific line numbers, exact validation steps.**
