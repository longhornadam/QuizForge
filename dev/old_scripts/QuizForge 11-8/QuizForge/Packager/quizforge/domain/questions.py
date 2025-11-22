"""Domain models representing QuizForge question types."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional


@dataclass
class MCChoice:
    text: str
    correct: bool = False


@dataclass
class Question:
    qtype: str
    prompt: str
    points: float = 10.0
    points_set: bool = False
    parent_stimulus_ident: Optional[str] = None
    forced_ident: Optional[str] = None


@dataclass
class MCQuestion(Question):
    choices: List[MCChoice] = field(default_factory=list)


@dataclass
class TFQuestion(Question):
    answer_true: bool = True


@dataclass
class EssayQuestion(Question):
    pass


@dataclass
class FileUploadQuestion(Question):
    pass


@dataclass
class MAQuestion(Question):
    choices: List[MCChoice] = field(default_factory=list)


@dataclass
class MatchingPair:
    prompt: str
    answer: str


@dataclass
class MatchingQuestion(Question):
    pairs: List[MatchingPair] = field(default_factory=list)


@dataclass
class FITBQuestion(Question):
    variants: List[str] = field(default_factory=list)
    blank_token: Optional[str] = None


@dataclass
class StimulusItem(Question):
    pass


@dataclass
class StimulusEnd(Question):
    """Sentinel block used by authoring format to close a stimulus scope."""


@dataclass
class OrderingItem:
    text: str
    ident: str


@dataclass
class OrderingQuestion(Question):
    items: List[OrderingItem] = field(default_factory=list)
    header: Optional[str] = None


@dataclass
class CategoryMapping:
    item_text: str
    item_ident: str
    category_name: str


@dataclass
class CategorizationQuestion(Question):
    categories: List[str] = field(default_factory=list)
    category_idents: dict = field(default_factory=dict)  # category_name -> UUID
    items: List[CategoryMapping] = field(default_factory=list)
    distractors: List[str] = field(default_factory=list)
    distractor_idents: dict = field(default_factory=dict)  # distractor_text -> UUID


@dataclass
class NumericalAnswer:
    answer: Optional[Decimal] = None
    tolerance_mode: str = "exact"
    margin_value: Optional[Decimal] = None
    range_min: Optional[Decimal] = None
    range_max: Optional[Decimal] = None
    precision_value: Optional[int] = None
    lower_bound: Optional[Decimal] = None
    upper_bound: Optional[Decimal] = None
    strict_lower: bool = False


@dataclass
class NumericalQuestion(Question):
    answer: NumericalAnswer = field(default_factory=NumericalAnswer)

    def validate(self) -> List[str]:
        errors: List[str] = []
        spec = self.answer
        mode = spec.tolerance_mode

        if mode != "range" and spec.answer is None:
            errors.append("Numerical question requires answer")

        if mode == "percent_margin":
            if spec.margin_value is None:
                errors.append("Percent margin requires tolerance value")
            elif spec.margin_value < 0:
                errors.append("Percent margin must be non-negative")
        elif mode == "absolute_margin":
            if spec.margin_value is None:
                errors.append("Absolute margin requires tolerance value")
            elif spec.margin_value < 0:
                errors.append("Absolute margin must be non-negative")
        elif mode == "significant_digits":
            if spec.precision_value is None:
                errors.append("Significant digits mode requires precision value")
            elif spec.precision_value < 0:
                errors.append("Precision must be non-negative")
        elif mode == "decimal_places":
            if spec.precision_value is None:
                errors.append("Decimal places mode requires precision value")
            elif spec.precision_value < 0:
                errors.append("Precision must be non-negative")
        elif mode == "range":
            if spec.range_min is None or spec.range_max is None:
                errors.append("Range mode requires both minimum and maximum values")
            elif spec.range_min >= spec.range_max:
                errors.append("Range minimum must be less than maximum")

        if spec.lower_bound is None or spec.upper_bound is None:
            errors.append("Computed bounds missing for numerical question")
        elif spec.lower_bound > spec.upper_bound:
            errors.append("Lower bound cannot exceed upper bound")

        return errors

