"""Fairness validation rules (Weak Fails).

These rules check for patterns that may indicate bias:
- Longest answer is always correct
- Same answer position repeated (e.g., C-C-C)
- Unbalanced correct answer distribution
"""

from typing import List
from ...core.quiz import Quiz
from ...core.questions import MCQuestion, MAQuestion


def check_fairness(quiz: Quiz) -> List[str]:
    """Check for fairness issues (patterns, bias).
    
    Args:
        quiz: Quiz object to check
        
    Returns:
        List of warning messages (empty if fair)
    """
    warnings: List[str] = []
    
    # Check MC questions for patterns
    mc_questions = [q for q in quiz.questions if isinstance(q, MCQuestion)]
    if mc_questions:
        warnings.extend(_check_longest_answer_bias(mc_questions))
        warnings.extend(_check_shortest_answer_bias(mc_questions))
        warnings.extend(_check_answer_position_pattern(mc_questions))
    
    return warnings


def _check_longest_answer_bias(questions: List[MCQuestion]) -> List[str]:
    """Check if longest answer is correct too often."""
    warnings: List[str] = []
    
    longest_correct_count = 0
    for question in questions:
        if not question.choices:
            continue
        
        longest = max(question.choices, key=lambda c: len(c.text))
        if longest.correct:
            longest_correct_count += 1
    
    if len(questions) > 0:
        percentage = (longest_correct_count / len(questions)) * 100
        if percentage >= 60:
            warnings.append(
                f"Longest answer is correct in {percentage:.0f}% of MC questions "
                f"({longest_correct_count}/{len(questions)}). This may indicate bias."
            )
    
    return warnings


def _check_shortest_answer_bias(questions: List[MCQuestion]) -> List[str]:
    """Check if shortest answer is correct too often."""
    warnings: List[str] = []
    
    shortest_correct_count = 0
    for question in questions:
        if not question.choices:
            continue
        
        shortest = min(question.choices, key=lambda c: len(c.text))
        if shortest.correct:
            shortest_correct_count += 1
    
    if len(questions) > 0:
        percentage = (shortest_correct_count / len(questions)) * 100
        if percentage >= 60:
            warnings.append(
                f"Shortest answer is correct in {percentage:.0f}% of MC questions "
                f"({shortest_correct_count}/{len(questions)}). This may indicate bias."
            )
    
    return warnings


def _check_answer_position_pattern(questions: List[MCQuestion]) -> List[str]:
    """Check if same answer position appears 3+ times in a row."""
    warnings: List[str] = []
    
    # Get correct answer positions (A=0, B=1, C=2, etc.)
    positions: List[int] = []
    for question in questions:
        if not question.choices:
            continue
        for i, choice in enumerate(question.choices):
            if choice.correct:
                positions.append(i)
                break
    
    # Check for runs of 3+
    if len(positions) >= 3:
        for i in range(len(positions) - 2):
            if positions[i] == positions[i+1] == positions[i+2]:
                letter = chr(ord('A') + positions[i])
                warnings.append(
                    f"Answer position '{letter}' appears 3 times in a row "
                    f"(questions {i+1}, {i+2}, {i+3}). Consider re-shuffling."
                )
                break  # Only report first occurrence
    
    return warnings
