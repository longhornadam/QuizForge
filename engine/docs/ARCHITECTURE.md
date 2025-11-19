# QuizForge Architecture

## System Overview

QuizForge is a pipeline-based system that converts plain-text quiz definitions into LMS-ready packages.

## Data Flow

```
┌──────────────┐
│  TXT File    │  User creates quiz with LLM assistance
└──────┬───────┘
       │
       ↓
┌──────────────┐
│   Parser     │  engine/parsing/text_parser.py
└──────┬───────┘  Converts TXT → Quiz domain objects
       │
       ↓
┌──────────────┐
│  Validator   │  engine/validation/validator.py
└──────┬───────┘  Checks structure, fairness, applies auto-fixes
       │
       ├─→ [FAIL] → Feedback Generator → _FAIL_REVISE_WITH_AI.txt
       │
       └─→ [PASS] → Renderers
                    ├─→ Canvas Packager → .zip
                    ├─→ Physical Packager → .docx (future)
                    └─→ Log Generator → log_PASS_FIXED.txt
```

## Layer Responsibilities

### Core (`engine/core/`)
Domain models representing quizzes and questions. No business logic, just data structures.

### Parsing (`engine/parsing/`)
Converts input formats (TXT, JSON, etc.) into Quiz domain objects. Minimal validation.

### Validation (`engine/validation/`)
The quality gatekeeper. Checks structure, fairness, and applies auto-fixes.

**Rules** (what to check):
- Structure: Missing fields, malformed questions
- Fairness: Pattern detection, bias analysis

**Fixers** (how to fix):
- Point normalization
- Choice randomization
- Text cleaning
- Bounds calculation

### Rendering (`engine/rendering/`)
Converts validated Quiz objects into output formats. No validation.

**Canvas**: QTI 1.2 XML generation
**Physical**: DOCX generation (future)

### Packaging (`engine/packaging/`)
Bundles rendered outputs into final deliverables (ZIP files, folder structures).

### Feedback (`engine/feedback/`)
Generates user-facing messages:
- Success logs
- Failure prompts for LLM revision

### Orchestration (`engine/orchestrator.py`)
High-level workflow coordinator. The only component that touches user directories.

## Trust Boundaries

Only the **Validator** is skeptical of data. All downstream components trust their inputs.

This prevents redundant validation and makes the system easier to reason about:
- Parser output → may have semantic errors
- Validator output → guaranteed valid
- Renderer input → can assume valid structure

## Extension Points

### Adding a Question Type
1. Add model to `engine/core/questions.py`
2. Add parsing logic to `engine/parsing/text_parser.py`
3. Add validation to `engine/validation/rules/question_rules.py`
4. Add Canvas renderer to `engine/rendering/canvas/question_renderers/`
5. Add physical formatter to `engine/rendering/physical/` (when implemented)

### Adding an Output Format
1. Create `engine/rendering/{format}/`
2. Implement packager interface
3. Update `engine/orchestrator.py` to call new packager

### Adding a Validation Rule
1. Add rule function to `engine/validation/rules/`
2. Update `engine/validation/validator.py` to call rule
3. (Optional) Add auto-fixer if correctable

## Design Patterns

**Strategy Pattern**: Parser protocol allows swapping input formats
**Pipeline Pattern**: Orchestrator coordinates sequential transformations
**Separation of Concerns**: Each layer has single, clear responsibility
**Fail-Fast**: Validator stops at first hard error

## Performance Considerations

- Parsing: O(n) where n = file size
- Validation: O(m) where m = number of questions
- Rendering: O(m) where m = number of questions
- Overall: Linear time complexity

Expected performance:
- 10-question quiz: < 1 second
- 100-question quiz: < 5 seconds

## Security Considerations

- No arbitrary code execution
- All file operations use Path objects (prevents directory traversal)
- No network requests (fully offline)
- Input sanitization via `sanitize_text()`

## Testing Strategy

**Unit Tests**: Each component tested in isolation
**Integration Tests**: Full pipeline tested end-to-end
**Regression Tests**: Known edge cases locked in
**Performance Tests**: Large quizzes benchmarked

## Future Enhancements

- Physical quiz rendering (DOCX)
- JSON input format
- Moodle output format
- Web-based interface
- Batch processing optimizations</content>
<parameter name="filePath">d:\Documents\OneDrive - Pearland ISD\Computer Science\QuizForge\engine\docs\ARCHITECTURE.md