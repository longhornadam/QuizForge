"""Quiz aggregate and helpers.

A Quiz is the top-level container: it holds a title and a list of questions.
This is the primary data structure that flows through the system:
    Text file → TextOutlineParser → Quiz → Renderers → QTI XML → ZIP

Key class:
- Quiz: Aggregate holding all questions and metadata (title, total points)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .questions import Question


"""A quiz: title + list of questions. Primary data structure flowing through the packager."""
@dataclass
class Quiz:
    title: str
    questions: List[Question]

    def total_points(self) -> float:
        return sum(q.points for q in self.questions)
