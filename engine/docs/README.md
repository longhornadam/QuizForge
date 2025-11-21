# QuizForge Developer Documentation

## Quick Links
- [AGENT_MAP.md](AGENT_MAP.md) - LLM navigation guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design decisions
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Migration history and notes

## For New Developers
Start by reading AGENT_MAP.md to understand the codebase structure and common tasks.

## Spec mode toggle
- `QUIZFORGE_SPEC_MODE=text` (default): Legacy text spec path.
- `QUIZFORGE_SPEC_MODE=json`: Routes through `dev/newspec_engine` via `JsonImporter`.
