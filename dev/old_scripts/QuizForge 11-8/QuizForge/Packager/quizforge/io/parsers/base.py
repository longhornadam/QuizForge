"""Parser interfaces for QuizForge authoring inputs."""

from __future__ import annotations

from typing import Optional, Protocol

from ...domain.quiz import Quiz


class QuizParser(Protocol):
    """Protocol for converting authoring artifacts into Quiz aggregates."""

    def parse(self, source: str, *, title_override: Optional[str] = None) -> Quiz:
        ...
