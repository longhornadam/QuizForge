"""Parser interfaces for QuizForge authoring inputs.

Defines the QuizParser protocol that all input format parsers must implement.
This allows swapping parsers without changing the rest of the system.

Current implementations:
- TextOutlineParser: Plain-text quiz outline format

Future parsers could support:
- JSON quizzes
- YAML quizzes
- Markdown quizzes
- Canvas native exports
"""

from __future__ import annotations

from typing import Optional, Protocol

from ...domain.quiz import Quiz


"""Protocol: all parsers must implement this interface."""
class QuizParser(Protocol):
    """Protocol for converting authoring artifacts into Quiz aggregates."""

    def parse(self, source: str, *, title_override: Optional[str] = None) -> Quiz:
        ...
