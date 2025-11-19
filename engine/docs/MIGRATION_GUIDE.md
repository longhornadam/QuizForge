# QuizForge Migration Guide

## Overview

QuizForge has been restructured from a nested `Packager/quizforge/` layout to a flat `engine/` layout for better maintainability and LLM agent navigation.

## Migration Summary

### Old Structure → New Structure

| Old Location | New Location | Changes |
|--------------|--------------|---------|
| `Packager/quizforge/domain/quiz.py` | `engine/core/quiz.py` | Added helper methods |
| `Packager/quizforge/domain/questions.py` | `engine/core/questions.py` | Extracted NumericalAnswer |
| `Packager/quizforge/domain/questions.py` | `engine/core/answers.py` | NumericalAnswer moved here |
| `Packager/quizforge/io/parsers/text_parser.py` | `engine/parsing/text_parser.py` | Updated imports |
| `Packager/quizforge/renderers/qti/` | `engine/rendering/canvas/` | Reorganized, updated imports |
| `Packager/quizforge/services/validation.py` | `engine/validation/` | Expanded into full layer |
| `Packager/quizforge/services/packager.py` | `engine/orchestrator.py` | Enhanced workflow |

### New Components

These did not exist in the old structure:

- `engine/validation/` - Full validation layer with rules and auto-fixers
- `engine/feedback/` - User-facing message generation
- `engine/packaging/` - Output folder management
- `engine/rendering/physical/` - Physical quiz rendering (stub)

## Key Architectural Changes

### 1. Validation is Now a Dedicated Layer

**Old**: Validation was scattered across parser and packager.

**New**: Dedicated validation layer with:
- Structure rules (hard fails)
- Fairness rules (soft fails)
- Auto-fixers (point normalization, choice shuffling)

### 2. Clear Separation of Concerns

**Old**: Parser did some validation, packager did some validation.

**New**:
- Parser: TXT → Quiz (minimal validation)
- Validator: Quiz → Validated Quiz (all validation)
- Renderers: Validated Quiz → Output (no validation)

### 3. Feedback Generation

**Old**: Orchestrator printed messages to console.

**New**: Dedicated feedback generators create files:
- Success logs (`log_PASS_FIXED.txt`)
- Fail prompts (`Quiz_FAIL_REVISE_WITH_AI.txt`)

## Import Path Changes

If you're updating code that referenced the old structure:

```python
# OLD
from Packager.quizforge.domain.quiz import Quiz
from Packager.quizforge.domain.questions import MCQuestion, NumericalAnswer
from Packager.quizforge.io.parsers.text_parser import TextOutlineParser

# NEW
from engine.core.quiz import Quiz
from engine.core.questions import MCQuestion
from engine.core.answers import NumericalAnswer
from engine.parsing.text_parser import TextOutlineParser
```

## Breaking Changes

### None (for users)

The user-facing interface (DropZone → run_quizforge.bat → Finished_Exports) is unchanged.

### For Developers

If you were importing from `Packager/quizforge/`, update your imports as shown above.

## Testing

All functionality has been verified with:
- Unit tests for each component
- Integration tests for full pipeline
- Backwards compatibility tests with old sample quizzes
- Regression tests for edge cases

## Timeline

- Planning: October 2025
- Implementation: TASK_001 through TASK_010 (November 2025)
- Verification: TASK_009 (November 16, 2025)
- Deprecation: TASK_010 (November 16, 2025)
- Old code removal: Future release (after 30 days of stable operation)

## Questions?

See:
- `/engine/docs/ARCHITECTURE.md` - System design
- `/engine/docs/AGENT_MAP.md` - Navigation guide for LLM agents</content>
<parameter name="filePath">d:\Documents\OneDrive - Pearland ISD\Computer Science\QuizForge\engine\docs\MIGRATION_GUIDE.md