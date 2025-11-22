"""Domain models representing QuizForge question types.

This module contains dataclasses for all question types supported by QuizForge.
Each question type inherits from the base Question class and adds type-specific fields.

Key classes:
- Question: Base class with common fields (qtype, prompt, points)
- MCQuestion, TFQuestion, MAQuestion: Multiple choice variants
- NumericalQuestion: Math questions with tolerance/precision/range scoring
- EssayQuestion, FileUploadQuestion: Manual-grading questions
- MatchingQuestion, OrderingQuestion, CategorizationQuestion: Complex interaction types
- StimulusItem: Special 0-point content block for grouping questions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional



"""A single choice option in a multiple-choice or multiple-answer question."""
@dataclass
class MCChoice:
    text: str
    correct: bool = False



"""Base class for all question types. Contains common fields like prompt, points, and stimulus linking."""
@dataclass
class Question:
    qtype: str
    prompt: str
    points: float = 10.0
    points_set: bool = False
    parent_stimulus_ident: Optional[str] = None
    forced_ident: Optional[str] = None



"""Multiple choice question: select one correct answer from 2-7 choices."""
@dataclass
class MCQuestion(Question):
    choices: List[MCChoice] = field(default_factory=list)



"""True/False question: student selects true or false."""
@dataclass
class TFQuestion(Question):
    answer_true: bool = True



"""Essay question: student types free-form response (manual grading required)."""
@dataclass
class EssayQuestion(Question):
    pass



"""File upload question: student uploads an artifact (manual grading required)."""
@dataclass
class FileUploadQuestion(Question):
    pass



"""Multiple answers question: select all correct answers (select all that apply)."""
@dataclass
class MAQuestion(Question):
    choices: List[MCChoice] = field(default_factory=list)



"""A single prompt-answer pair in a matching question."""
@dataclass
class MatchingPair:
    prompt: str
    answer: str



"""Matching question: student pairs prompts with answers (e.g., term with definition)."""
@dataclass
class MatchingQuestion(Question):
    pairs: List[MatchingPair] = field(default_factory=list)



"""Fill-in-the-blank question: student types text to complete a sentence (case-insensitive matching)."""
@dataclass
class FITBQuestion(Question):
    variants: List[str] = field(default_factory=list)
    blank_token: Optional[str] = None



"""Stimulus content block (0 points): visual prompt that precedes and groups related questions."""
@dataclass
class StimulusItem(Question):
    pass


"""Sentinel marker: signals the end of a stimulus group. Not rendered as a question."""
@dataclass
class StimulusEnd(Question):
    pass



"""A single item in an ordering (sequencing) question."""
@dataclass
class OrderingItem:
    text: str
    ident: str



"""Ordering question: student arranges items in the correct sequence."""
@dataclass
class OrderingQuestion(Question):
    items: List[OrderingItem] = field(default_factory=list)
    header: Optional[str] = None



"""Maps an item to its correct category in a categorization question."""
@dataclass
class CategoryMapping:
    item_text: str
    item_ident: str
    category_name: str



"""Categorization question: student sorts items into named categories (partial credit per category)."""
@dataclass
class CategorizationQuestion(Question):
    categories: List[str] = field(default_factory=list)
    category_idents: dict = field(default_factory=dict)  # category_name -> UUID
    items: List[CategoryMapping] = field(default_factory=list)
    distractors: List[str] = field(default_factory=list)
    distractor_idents: dict = field(default_factory=dict)  # distractor_text -> UUID



"""Scoring spec for a numerical question: stores answer + tolerance/precision/range rules."""
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



"""Numerical question: student enters a number, graded with tolerance, precision, or range rules."""
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

