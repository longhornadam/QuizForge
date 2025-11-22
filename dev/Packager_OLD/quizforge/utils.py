"""Utility helpers shared across QuizForge modules."""

from __future__ import annotations

import uuid


def rand8() -> str:
    """Return an 8-character hex string for lightweight identifiers."""
    return uuid.uuid4().hex[:8]


def sanitize_text(value: str) -> str:
    """Normalize author-provided text to Canvas-safe ASCII characters."""
    if not value:
        return value

    mapping = {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2014": "-",
        "\u2013": "-",
        "\u2026": "...",
        "\u00a0": " ",
    }

    sanitized = value
    for bad, good in mapping.items():
        sanitized = sanitized.replace(bad, good)
    return sanitized
