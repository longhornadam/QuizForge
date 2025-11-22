"""Quiz aggregate and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .questions import Question


@dataclass
class Quiz:
    title: str
    questions: List[Question]

    def total_points(self) -> float:
        return sum(q.points for q in self.questions)
