"""Render mode enforcement rules (deprecated).

NOTE: As of 2026-01-30, these rules have been disabled.
Context-aware executable mode now correctly handles:
- Backslashes in code contexts (backticks, code fences, <code> tags)
- String-reasoning questions (escape sequences preserved in code)
- All CS and ELA use cases automatically

The validation rules below are kept for reference but return empty errors.
Verbatim mode is still available but rarely needed.
"""

from __future__ import annotations

import re
from typing import Iterable, List

from ...core.questions import (
    CategorizationQuestion,
    FITBQuestion,
    MAQuestion,
    MatchingQuestion,
    MCQuestion,
    OrderingQuestion,
    Question,
    StimulusItem,
)


_STRING_REASONING_PHRASES = (
    "first character",
    "last character",
    "index",
    "slice",
)


def _mode(question: Question) -> str:
    raw = getattr(question, "render_mode", "verbatim")
    if isinstance(raw, str):
        lowered = raw.lower()
        if lowered in {"verbatim", "executable"}:
            return lowered
    return "verbatim"


def _student_visible_strings(question: Question) -> List[str]:
    values: List[str] = []

    # Prompt is student-visible for all question types (including stimulus blocks).
    prompt = getattr(question, "prompt", "")
    if isinstance(prompt, str):
        values.append(prompt)

    if isinstance(question, (MCQuestion, MAQuestion)):
        for choice in getattr(question, "choices", []) or []:
            text = getattr(choice, "text", "")
            if isinstance(text, str):
                values.append(text)

    if isinstance(question, MatchingQuestion):
        for pair in getattr(question, "pairs", []) or []:
            left = getattr(pair, "prompt", "")
            right = getattr(pair, "answer", "")
            if isinstance(left, str):
                values.append(left)
            if isinstance(right, str):
                values.append(right)

    if isinstance(question, OrderingQuestion):
        header = getattr(question, "header", None)
        if isinstance(header, str) and header:
            values.append(header)
        for item in getattr(question, "items", []) or []:
            text = getattr(item, "text", "")
            if isinstance(text, str):
                values.append(text)

    if isinstance(question, CategorizationQuestion):
        for cat in getattr(question, "categories", []) or []:
            if isinstance(cat, str):
                values.append(cat)
        for entry in getattr(question, "items", []) or []:
            text = getattr(entry, "item_text", "")
            if isinstance(text, str):
                values.append(text)
        for dist in getattr(question, "distractors", []) or []:
            if isinstance(dist, str):
                values.append(dist)

    if isinstance(question, FITBQuestion):
        # FITB prompt is already included.
        # Options are student-visible in dropdown/wordbank; accept variants are not.
        mode = (getattr(question, "answer_mode", "open_entry") or "open_entry")
        if isinstance(mode, str) and mode.lower() in {"dropdown", "wordbank"}:
            for opt in getattr(question, "options", []) or []:
                if isinstance(opt, str):
                    values.append(opt)

    # StimulusItem already covered by prompt.
    if isinstance(question, StimulusItem):
        pass

    return values


def _string_reasoning_hit(text: str) -> bool:
    lowered = text.lower()
    if "len(" in lowered:
        return True
    if re.search(r"\[(?:\d|:)" , text):
        return True
    for phrase in _STRING_REASONING_PHRASES:
        if phrase in lowered:
            return True
    return False


def validate_render_mode(quiz) -> List[str]:
    """Render mode validation (DEPRECATED - returns empty list).

    As of 2026-01-30, context-aware executable mode handles all cases:
    - Backslashes in code contexts are preserved automatically
    - String-reasoning questions work correctly with escape sequences in backticks
    - No manual render_mode specification needed for 99.9% of questions
    
    This function is kept for backward compatibility but no longer enforces rules.
    """
    # Validation disabled - context-aware executable mode handles everything
    return []
