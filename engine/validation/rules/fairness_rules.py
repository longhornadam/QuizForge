"""Fairness validation rules.

These rules check for patterns that may indicate bias:
- Longest answer is always correct
- Shortest answer is always correct

Answer-position balancing is handled by the auto-fixer (answer_balancer) to avoid
user-facing noise about shuffling the user cannot control.
"""

from typing import List
from ...core.quiz import Quiz
from ...core.questions import MCQuestion, MAQuestion


def check_fairness(quiz: Quiz) -> List[str]:
    """Return fairness warnings (currently none; length bias is treated as an error elsewhere)."""
    return []


def check_length_bias(quiz: Quiz) -> List[str]:
    """Check for length bias in MC questions; returns error messages if biased."""
    errors: List[str] = []
    mc_questions = [q for q in quiz.questions if isinstance(q, MCQuestion)]
    # Skip tiny sets; length bias is meaningless on very small samples
    if len(mc_questions) < 3:
        return errors

    longest_correct_count = 0
    shortest_correct_count = 0
    for question in mc_questions:
        if not question.choices:
            continue
        longest = max(question.choices, key=lambda c: len(c.text))
        shortest = min(question.choices, key=lambda c: len(c.text))
        if longest.correct:
            longest_correct_count += 1
        if shortest.correct:
            shortest_correct_count += 1

    total = len(mc_questions)
    if total == 0:
        return errors

    longest_pct = (longest_correct_count / total) * 100
    shortest_pct = (shortest_correct_count / total) * 100

    if longest_pct >= 60:
        errors.append(
            f"Longest answer is correct in {longest_pct:.0f}% of MC questions "
            f"({longest_correct_count}/{total}). Balance answer lengths by shortening correct answers or lengthening distractors so the right answer is not obviously the longest."
        )
    if shortest_pct >= 60:
        errors.append(
            f"Shortest answer is correct in {shortest_pct:.0f}% of MC questions "
            f"({shortest_correct_count}/{total}). Balance answer lengths by padding distractors or tightening the correct answer so it is not obviously the shortest."
        )

    return errors


def _check_answer_position_pattern(questions: List[MCQuestion]) -> List[str]:
    """Deprecated: answer-position streak warnings are suppressed (see check_fairness)."""
    return []
