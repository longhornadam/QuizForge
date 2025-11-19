"""Point allocation calculator for QuizForge.

Assigns point values to Quiz question model objects using a simple weight-based
distribution logic. Designed to keep point logic out of the LLM by applying
deterministic, easy-to-audit rules.
"""
from __future__ import annotations

from typing import List, Optional
from pathlib import Path

from engine.core.questions import Question
from engine.rendering.physical.styles.default_styles import (
    DEFAULT_QUIZ_POINTS,
    HEAVY_QUESTION_WEIGHT,
    HEAVY_QUESTION_TYPES,
)


def calculate_points(questions: List[Question], total_points: int = DEFAULT_QUIZ_POINTS, log_path: Optional[str] = None) -> List[Question]:
    """Assign point values to a list of Question model objects.

    Rules:
    - ESSAY and FILEUPLOAD types count as heavy and receive HEAVY_QUESTION_WEIGHT multiplier
    - Other supported types receive 1x weight
    - Rounding uses integer rounding and any rounding error is corrected on the first scorable question

    Args:
        questions: List of Question model objects (will be mutated in-place)
        total_points: Target total points (defaults to DEFAULT_QUIZ_POINTS)
        log_path: Optional path to a log file to append calculation details

    Returns:
        The list of question objects with their ``points`` attributes modified
    """
    # Work with scorable questions only (ignore StimulusItem/StimulusEnd)
    from engine.core.questions import StimulusItem

    scorable = [q for q in questions if not isinstance(q, StimulusItem)]

    if not scorable:
        return questions

    # Partition weighted vs regular by question qtype string
    heavy_types = set(HEAVY_QUESTION_TYPES)
    heavy = [q for q in scorable if q.qtype in heavy_types]
    regular = [q for q in scorable if q.qtype not in heavy_types]

    if heavy:
        weight = HEAVY_QUESTION_WEIGHT
        total_units = len(regular) + (len(heavy) * weight)
        base_points = total_points / total_units

        for q in regular:
            q.points = int(round(base_points))
        for q in heavy:
            q.points = int(round(base_points * weight))
    else:
        base_points = total_points / len(scorable)
        for q in scorable:
            q.points = int(round(base_points))

    # Adjust rounding error by modifying first scorable question
    _adjust_for_rounding(scorable, total_points)

    # Optionally append a log
    if log_path:
        _write_log(questions, total_points, heavy, regular, base_points, log_path)

    return questions


def _adjust_for_rounding(questions: List[Question], target_total: int) -> None:
    """Adjust the first scorable question to guarantee the target_total exactly."""
    current_total = sum(int(q.points) for q in questions)
    difference = target_total - current_total

    if difference != 0 and questions:
        questions[-1].points = int(questions[-1].points) + difference

def _write_log(questions: List[Question], total_points: int, heavy: List[Question], regular: List[Question], base_points: float, log_path: str) -> None:
    p = Path(log_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('a', encoding='utf-8') as log:
        log.write('\n' + '=' * 60 + '\n')
        log.write('POINT ALLOCATION\n')
        log.write('=' * 60 + '\n')
        log.write(f'Total points: {total_points}\n')
        log.write(f'Heavy questions ({HEAVY_QUESTION_TYPES}): {len(heavy)}\n')
        log.write(f'Regular questions: {len(regular)}\n')
        if heavy:
            log.write(f'Base point value: {base_points:.2f}\n')
            log.write(f'Heavy multiplier: {HEAVY_QUESTION_WEIGHT}x\n')
        log.write('\nQuestion breakdown:\n')
        for idx, q in enumerate(questions, start=1):
            log.write(f"  Q{idx} ({q.qtype}): {int(q.points)} pts\n")
        log.write(f"\nTotal assigned: {sum(int(q.points) for q in questions)}\n\n")
