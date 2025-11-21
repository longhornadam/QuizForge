"""Parser for the JSON 3.0 newspec format (sandbox, non-production)."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from .models import QuestionType, QuizPayload, RationalesEntry

TAG_OPEN = "<QUIZFORGE_JSON>"
TAG_CLOSE = "</QUIZFORGE_JSON>"
SUPPORTED_TYPES: Tuple[QuestionType, ...] = (
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
)


def extract_tagged_payload(text: str) -> str:
    """Extract the JSON payload between the newspec tags.

    Friendly chatter outside the tags is ignored; only the tagged JSON is returned.
    Raises ValueError when tags are missing or empty.
    """
    start = text.find(TAG_OPEN)
    end = text.find(TAG_CLOSE)
    if start == -1 or end == -1 or end <= start:
        raise ValueError("QUIZFORGE_JSON tags not found or malformed.")
    payload = text[start + len(TAG_OPEN) : end].strip()
    if not payload:
        raise ValueError("Tagged JSON payload is empty.")
    return payload


def _sanitize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Apply lightweight validation/sanitization rules for a single item."""
    if "type" not in item:
        raise ValueError("Item missing required 'type' field.")
    qtype = item["type"]
    if qtype not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported item type '{qtype}'.")

    # STIMULUS/END are never scored or rationalized.
    if qtype in ("STIMULUS", "STIMULUS_END") and "points" in item:
        item = {k: v for k, v in item.items() if k != "points"}

    # Points are only honored if the teacher explicitly supplied them.
    # We accept the field when present but do not infer or inject defaults.
    if "metadata" not in item:
        item["metadata"] = {}
    if not isinstance(item.get("metadata"), dict):
        item["metadata"] = {}
    if "extensions" not in item["metadata"] or not isinstance(item["metadata"].get("extensions"), dict):
        item["metadata"]["extensions"] = {}

    # Tag experimental numerical modes
    if qtype == "NUMERICAL":
        evaluation = item.get("evaluation", {})
        if isinstance(evaluation, dict):
            mode = evaluation.get("mode", "exact")
            if mode != "exact":
                flags = item.get("experimental_flags") if isinstance(item.get("experimental_flags"), list) else []
                flags.append("numerical_non_exact_mode")
                item["experimental_flags"] = flags

    return item


def _parse_rationales(raw: Any) -> List[RationalesEntry]:
    """Convert raw rationales list into RationalesEntry objects, skipping invalid shapes."""
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("Rationales must be a list when provided.")
    entries: List[RationalesEntry] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        item_id = entry.get("item_id")
        correct = entry.get("correct")
        distractor = entry.get("distractor")
        if not (isinstance(item_id, str) and isinstance(correct, str) and isinstance(distractor, str)):
            continue
        rationale = RationalesEntry(item_id=item_id, correct=correct, distractor=distractor)
        entries.append(rationale)
    return entries


def parse_news_json(text: str) -> QuizPayload:
    """Parse raw LLM output into a structured QuizPayload for the newspec JSON format."""
    payload_text = extract_tagged_payload(text)
    data = json.loads(payload_text)
    if not isinstance(data, dict):
        raise ValueError("Top-level JSON must be an object.")

    version = data.get("version")
    if not isinstance(version, str):
        raise ValueError("Top-level 'version' must be provided as a string.")

    title = data.get("title")
    metadata = data.get("metadata") or {}
    if not isinstance(metadata, dict):
        raise ValueError("'metadata' must be an object when present.")
    if "extensions" not in metadata or not isinstance(metadata.get("extensions"), dict):
        metadata["extensions"] = {}

    items_raw = data.get("items")
    if not isinstance(items_raw, list) or not items_raw:
        raise ValueError("'items' must be a non-empty list.")

    sanitized_items = [_sanitize_item(dict(item)) for item in items_raw if isinstance(item, dict)]

    # Rationale list is optional; stimuli/structural markers should not be rationalized by the LLM.
    rationales_raw = data.get("rationales")
    rationales = _parse_rationales(rationales_raw)

    return QuizPayload(
        version=version,
        title=title if isinstance(title, str) else None,
        metadata=metadata,
        items=sanitized_items,
        rationales=rationales,
    )
