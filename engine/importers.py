"""Importer abstraction for swapping between legacy text spec and JSON 3.0 spec."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Protocol, List, Optional
import logging
import os
from engine.config import SPEC_MODE
from engine.core.answers import NumericalAnswer
from engine.core.questions import (
    CategorizationQuestion,
    CategoryMapping,
    EssayQuestion,
    FITBQuestion,
    FileUploadQuestion,
    MAQuestion,
    MCChoice,
    MCQuestion,
    MatchingPair,
    MatchingQuestion,
    NumericalQuestion,
    OrderingItem,
    OrderingQuestion,
    Question,
    StimulusEnd,
    StimulusItem,
    TFQuestion,
)
from engine.core.quiz import Quiz
from engine.parsing.text_parser import TextOutlineParser

from dev.newspec_engine import parser as news_parser
from dev.newspec_engine import packager as news_packager

logger = logging.getLogger(__name__)


@dataclass
class ImportedQuiz:
    quiz: Quiz
    raw: str


class Importer(Protocol):
    def import_quiz(self, raw_spec: str) -> ImportedQuiz:
        ...


class TextImporter:
    """Importer for the legacy text spec."""

    def __init__(self) -> None:
        self.parser = TextOutlineParser()

    def import_quiz(self, raw_spec: str) -> ImportedQuiz:
        quiz = self.parser.parse_text(raw_spec)
        return ImportedQuiz(quiz=quiz, raw=raw_spec)


class JsonImporter:
    """Importer for the JSON 3.0 spec using the dev/newspec_engine sandbox."""

    def import_quiz(self, raw_spec: str) -> ImportedQuiz:
        logger.debug("JSON spec mode active (QUIZFORGE_SPEC_MODE=json)")
        payload = news_parser.parse_news_json(raw_spec)
        logger.debug("Parsed JSON payload version=%s", payload.version)

        packaged = news_packager.package_quiz(payload, context="default")

        experimental_seen = any(item for item in getattr(packaged, "experimental", []) or [])
        if experimental_seen:
            logger.warning("Experimental features present in JSON payload (non-exact numerical modes)")

        quiz = _packaged_to_domain(packaged)
        debug_mode = os.getenv("QUIZFORGE_DEBUG_JSON", "0") == "1"
        if debug_mode:
            logger.debug("Parsed JSON domain model:\n%s", repr(quiz))

        # Preserve raw plus experimental flags info for debugging
        raw_with_flags = raw_spec
        if experimental_seen:
            raw_with_flags += f"\n\n# experimental_flags: {[item.get('experimental_flags', []) for item in getattr(packaged, 'items', []) if item.get('experimental_flags')]}"

        return ImportedQuiz(quiz=quiz, raw=raw_with_flags)


def import_quiz_from_llm(raw_output: str) -> ImportedQuiz:
    """Dispatch to the correct importer based on SPEC_MODE."""
    if SPEC_MODE == "json":
        try:
            logger.info("QUIZFORGE_SPEC_MODE=json: attempting JSON 3.0 import")
            return JsonImporter().import_quiz(raw_output)
        except Exception as e:
            logger.warning(f"JSON import failed, falling back to text importer: {e}")
            return TextImporter().import_quiz(raw_output)
    return TextImporter().import_quiz(raw_output)


def _packaged_to_domain(packaged) -> Quiz:
    """Convert PackagedQuiz (newspec) into the legacy domain Quiz object."""
    questions: List[Question] = []
    current_stimulus_id: Optional[str] = None

    def _points(item: dict) -> float:
        return float(item["points"]) if "points" in item else 0.0

    for item in packaged.items:
        qtype = item.get("type")
        prompt = item.get("prompt", "")
        stim_id = item.get("stimulus_id")
        forced_ident = item.get("id")

        if qtype == "STIMULUS":
            forced_ident = forced_ident or f"stim_{uuid.uuid4().hex[:8]}"
            q = StimulusItem(qtype="STIMULUS", prompt=prompt, points=0.0, points_set=False, forced_ident=forced_ident)
            current_stimulus_id = forced_ident
            questions.append(q)
            continue

        if qtype == "STIMULUS_END":
            q = StimulusEnd(qtype="STIMULUS_END", prompt=prompt, points=0.0, points_set=False)
            current_stimulus_id = None
            questions.append(q)
            continue

        parent_stimulus = stim_id or current_stimulus_id
        pts = _points(item)
        pts_set = "points" in item

        if qtype == "MC":
            choices = [MCChoice(text=c["text"], correct=bool(c.get("correct"))) for c in item.get("choices", [])]
            q = MCQuestion(qtype="MC", prompt=prompt, points=pts, points_set=pts_set, choices=choices, parent_stimulus_ident=parent_stimulus)
        elif qtype == "MA":
            choices = [MCChoice(text=c["text"], correct=bool(c.get("correct"))) for c in item.get("choices", [])]
            q = MAQuestion(qtype="MA", prompt=prompt, points=pts, points_set=pts_set, choices=choices, parent_stimulus_ident=parent_stimulus)
        elif qtype == "TF":
            answer_raw = item.get("answer")
            q = TFQuestion(
                qtype="TF",
                prompt=prompt,
                points=pts,
                points_set=pts_set,
                answer_true=_parse_tf_answer(answer_raw),
                parent_stimulus_ident=parent_stimulus,
            )
        elif qtype == "MATCHING":
            pairs = [MatchingPair(prompt=p["left"], answer=p["right"]) for p in item.get("pairs", [])]
            q = MatchingQuestion(qtype="MATCHING", prompt=prompt, points=pts, points_set=pts_set, pairs=pairs, parent_stimulus_ident=parent_stimulus)
        elif qtype == "FITB":
            variants: List[str] = []
            for variant_group in item.get("accept", []):
                if isinstance(variant_group, list):
                    variants.extend([str(v) for v in variant_group])
            blank_token = uuid.uuid4().hex
            display_token = f"[{blank_token}]"
            prompt_with_token = prompt.replace("[blank]", display_token)
            if prompt_with_token == prompt:
                prompt_with_token = f"{prompt} [{display_token}]"
            q = FITBQuestion(
                qtype="FITB",
                prompt=prompt_with_token,
                points=pts,
                points_set=pts_set,
                variants=variants,
                blank_token=blank_token,
                parent_stimulus_ident=parent_stimulus,
            )
        elif qtype == "ESSAY":
            q = EssayQuestion(qtype="ESSAY", prompt=prompt, points=pts, points_set=pts_set, parent_stimulus_ident=parent_stimulus)
        elif qtype == "FILEUPLOAD":
            q = FileUploadQuestion(qtype="FILEUPLOAD", prompt=prompt, points=pts, points_set=pts_set, parent_stimulus_ident=parent_stimulus)
        elif qtype == "ORDERING":
            items = [OrderingItem(text=text, ident=str(uuid.uuid4())) for text in item.get("items", [])]
            q = OrderingQuestion(
                qtype="ORDERING",
                prompt=prompt,
                points=pts,
                points_set=pts_set,
                items=items,
                header=item.get("header"),
                parent_stimulus_ident=parent_stimulus,
            )
        elif qtype == "CATEGORIZATION":
            categories = item.get("categories", [])
            category_idents = {cat: str(uuid.uuid4()) for cat in categories}
            cat_items: List[CategoryMapping] = []
            for entry in item.get("items", []):
                label = entry.get("label")
                cat = entry.get("category")
                item_ident = str(uuid.uuid4())
                cat_items.append(CategoryMapping(item_text=str(label), item_ident=item_ident, category_name=str(cat)))
            distractors = item.get("distractors", []) or []
            distractor_idents = {d: str(uuid.uuid4()) for d in distractors}
            q = CategorizationQuestion(
                qtype="CATEGORIZATION",
                prompt=prompt,
                points=pts,
                points_set=pts_set,
                categories=categories,
                category_idents=category_idents,
                items=cat_items,
                distractors=list(distractors),
                distractor_idents=distractor_idents,
                parent_stimulus_ident=parent_stimulus,
            )
        elif qtype == "NUMERICAL":
            q = _convert_numerical(item, pts, pts_set, parent_stimulus)
        else:
            logger.warning("Unsupported item type '%s' encountered; skipping", qtype)
            continue

        questions.append(q)

    rationale_strings = []
    for r in packaged.rationales:
        rationale_strings.append(f"{r.item_id}: {r.correct} | {r.distractor}")

    title = packaged.title or "Untitled Quiz"
    return Quiz(title=title, questions=questions, rationales=rationale_strings)


def _convert_numerical(item: dict, pts: float, pts_set: bool, parent_stimulus: Optional[str]) -> NumericalQuestion:
    evaluation = item.get("evaluation", {}) or {}
    mode = evaluation.get("mode", "exact")
    answer_raw = item.get("answer")
    answer = _safe_decimal(answer_raw)

    margin = _safe_decimal(evaluation.get("value")) if "value" in evaluation else None
    range_min = _safe_decimal(evaluation.get("min")) if "min" in evaluation else None
    range_max = _safe_decimal(evaluation.get("max")) if "max" in evaluation else None
    precision = None
    if "value" in evaluation and mode in ("significant_digits", "decimal_places"):
        try:
            precision = int(evaluation.get("value"))
        except (TypeError, ValueError):
            precision = None

    lower, upper, strict_lower = _bounds_for_numerical(answer, mode, margin, range_min, range_max, precision)
    answer_spec = NumericalAnswer(
        answer=answer,
        tolerance_mode=mode,
        margin_value=margin,
        range_min=range_min,
        range_max=range_max,
        precision_value=precision,
        lower_bound=lower,
        upper_bound=upper,
        strict_lower=strict_lower,
    )
    return NumericalQuestion(
        qtype="NUMERICAL",
        prompt=item.get("prompt", ""),
        points=pts,
        points_set=pts_set,
        answer=answer_spec,
        parent_stimulus_ident=parent_stimulus,
    )


def _bounds_for_numerical(answer, mode, margin, range_min, range_max, precision):
    """Reuse text parser logic to keep bounds consistent."""
    try:
        lower, upper, strict_lower = TextOutlineParser._resolve_numerical_bounds(  # type: ignore[attr-defined]
            answer=answer,
            mode=mode,
            margin=margin,
            range_min=range_min,
            range_max=range_max,
            precision=precision,
        )
        return lower, upper, strict_lower
    except Exception:
        # Fallback to exact bounds when inputs are insufficient.
        if answer is None:
            answer = Decimal("0")
        return answer, answer, False


def _safe_decimal(value) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _parse_tf_answer(value) -> bool:
    """Parse TF answer from raw JSON field."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "t", "1", "yes"}:
            return True
        if lowered in {"false", "f", "0", "no"}:
            return False
    # Default to False if unclear, but avoid flipping True -> False
    return bool(value)
