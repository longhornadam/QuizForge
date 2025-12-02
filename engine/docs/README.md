# QuizForge Developer Documentation

## Quick Links
- [AGENT_MAP.md](AGENT_MAP.md) - LLM navigation guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design decisions
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Migration history and notes

## For New Developers
Start by reading AGENT_MAP.md to understand the codebase structure and common tasks.

## Spec mode toggle
- `QUIZFORGE_SPEC_MODE=json` (default): JSON 3.0 pipeline via `JsonImporter`.
- `QUIZFORGE_SPEC_MODE=text`: Legacy text spec path (deprecated, for backward compatibility only).
