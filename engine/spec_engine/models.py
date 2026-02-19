"""Lightweight data structures for the JSON 3.0 newspec sandbox."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

# Supported question types in newspec JSON 3.0
QuestionType = Literal[
    "STIMULUS",
    "STIMULUS_END",
    "MC",
    "MA",
    "TF",
    "MATCHING",
    "FITB",
    "ESSAY",
    "FILEUPLOAD",
    "ORDERING",
    "CATEGORIZATION",
    "NUMERICAL",
]


@dataclass
class RationalesEntry:
    """Single rationale aligned to a scored item."""

    item_id: str
    rationale: str


@dataclass
class QuizPayload:
    """Parsed quiz payload for the newspec JSON format."""

    version: str
    title: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    items: List[Dict[str, Any]] = field(default_factory=list)
    rationales: List[RationalesEntry] = field(default_factory=list)
    instructions: Optional[str] = None


@dataclass
class PackagedQuiz:
    """Lightweight packaged quiz for downstream consumers inside the sandbox."""

    version: str
    title: Optional[str]
    metadata: Dict[str, Any]
    items: List[Dict[str, Any]]
    rationales: List[RationalesEntry]
    experimental: List[Dict[str, Any]] = field(default_factory=list)
    instructions: Optional[str] = None
