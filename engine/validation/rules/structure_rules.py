"""Structural validation rules (Hard Fails).

These rules check for non-negotiable errors that cannot be auto-fixed:
- Missing required fields
- Invalid question types
- Malformed structure
- Type-specific validation errors
"""

from typing import List
from ...core.quiz import Quiz
from ...core.questions import (
    MCQuestion,
    MAQuestion,
    TFQuestion,
    NumericalQuestion,
    MatchingQuestion,
    FITBQuestion,
    OrderingQuestion,
    CategorizationQuestion,
    StimulusEnd,
    StimulusItem,
)


def validate_structure(quiz: Quiz) -> List[str]:
    """Check for structural errors that cause hard fails.
    
    Args:
        quiz: Quiz object to validate
        
    Returns:
        List of error messages (empty if valid)
    """
    errors: List[str] = []
    
    # Check quiz has at least one question
    if not quiz.questions:
        errors.append("Quiz must contain at least one question")
        return errors
    
    # Validate each question
    for i, question in enumerate(quiz.questions, 1):
        q_errors = _validate_question(question, i)
        errors.extend(q_errors)
    
    return errors


def _validate_question(question, index: int) -> List[str]:
    """Validate a single question.
    
    Args:
        question: Question object to validate
        index: Question number (for error messages)
        
    Returns:
        List of error messages
    """
    errors: List[str] = []
    prefix = f"Question #{index}"
    
    # Check prompt is not empty (STIMULUS and STIMULUS_END are exempt; prompts may be empty/placeholder)
    if not isinstance(question, (StimulusItem, StimulusEnd)):
        # Auto-fix: if prompt is empty but a header exists (e.g., ORDERING), reuse header as prompt
        if (not question.prompt or not question.prompt.strip()) and getattr(question, "header", None):
            question.prompt = getattr(question, "header")

        if not question.prompt or not question.prompt.strip():
            errors.append(f"{prefix}: Prompt cannot be empty")
    
    # Type-specific validation
    if isinstance(question, MCQuestion):
        errors.extend(_validate_mc(question, prefix))
    elif isinstance(question, MAQuestion):
        errors.extend(_validate_ma(question, prefix))
    elif isinstance(question, TFQuestion):
        errors.extend(_validate_tf(question, prefix))
    elif isinstance(question, NumericalQuestion):
        errors.extend(_validate_numerical(question, prefix))
    elif isinstance(question, MatchingQuestion):
        errors.extend(_validate_matching(question, prefix))
    elif isinstance(question, FITBQuestion):
        errors.extend(_validate_fitb(question, prefix))
    elif isinstance(question, OrderingQuestion):
        errors.extend(_validate_ordering(question, prefix))
    elif isinstance(question, CategorizationQuestion):
        errors.extend(_validate_categorization(question, prefix))
    
    return errors


def _validate_mc(question: MCQuestion, prefix: str) -> List[str]:
    """Validate multiple choice question."""
    errors: List[str] = []
    
    if not question.choices:
        errors.append(f"{prefix}: MC question missing Choices field")
        return errors
    
    if len(question.choices) < 2:
        errors.append(f"{prefix}: MC question must have at least 2 choices")
    
    if len(question.choices) > 7:
        errors.append(f"{prefix}: MC question can have at most 7 choices")
    
    correct_count = sum(1 for c in question.choices if c.correct)
    if correct_count == 0:
        errors.append(f"{prefix}: MC question must have exactly 1 correct choice (found 0)")
    elif correct_count > 1:
        errors.append(f"{prefix}: MC question must have exactly 1 correct choice (found {correct_count})")
    
    return errors


def _validate_ma(question: MAQuestion, prefix: str) -> List[str]:
    """Validate multiple answers question."""
    errors: List[str] = []
    
    if not question.choices:
        errors.append(f"{prefix}: MA question missing Choices field")
        return errors
    
    if len(question.choices) < 2:
        errors.append(f"{prefix}: MA question must have at least 2 choices")
    
    correct_count = sum(1 for c in question.choices if c.correct)
    if correct_count == 0:
        errors.append(f"{prefix}: MA question must have at least 1 correct choice")
    
    return errors


def _validate_tf(question: TFQuestion, prefix: str) -> List[str]:
    """Validate true/false question."""
    # TF questions always valid if they have a prompt
    return []


def _validate_numerical(question: NumericalQuestion, prefix: str) -> List[str]:
    """Validate numerical question."""
    errors: List[str] = []
    
    # Delegate to NumericalAnswer validation
    answer_errors = question.validate()
    for error in answer_errors:
        errors.append(f"{prefix}: {error}")
    
    return errors


def _validate_matching(question: MatchingQuestion, prefix: str) -> List[str]:
    """Validate matching question."""
    errors: List[str] = []
    
    if not question.pairs:
        errors.append(f"{prefix}: Matching question missing Pairs field")
        return errors
    
    if len(question.pairs) < 2:
        errors.append(f"{prefix}: Matching question must have at least 2 pairs")
    
    return errors


def _validate_fitb(question: FITBQuestion, prefix: str) -> List[str]:
    """Validate fill-in-the-blank question."""
    errors: List[str] = []
    
    if not question.variants:
        errors.append(f"{prefix}: FITB question missing Accept/Answers field")
    
    return errors


def _validate_ordering(question: OrderingQuestion, prefix: str) -> List[str]:
    """Validate ordering question."""
    errors: List[str] = []
    
    if not question.items:
        errors.append(f"{prefix}: Ordering question missing Items field")
        return errors
    
    if len(question.items) < 2:
        errors.append(f"{prefix}: Ordering question must have at least 2 items")
    
    return errors


def _validate_categorization(question: CategorizationQuestion, prefix: str) -> List[str]:
    """Validate categorization question."""
    errors: List[str] = []
    
    if not question.categories:
        errors.append(f"{prefix}: Categorization question missing Categories field")
    elif len(question.categories) < 2:
        errors.append(f"{prefix}: Categorization question must have at least 2 categories")
    
    if not question.items:
        errors.append(f"{prefix}: Categorization question missing Items field")
    elif len(question.items) < 1:
        errors.append(f"{prefix}: Categorization question must have at least 1 item")
    
    return errors
