"""Validation and reporting helpers."""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from ..domain.questions import Question, StimulusItem
from ..domain.quiz import Quiz


QTI_NS = "{http://www.imsglobal.org/xsd/ims_qtiasiv1p2}"


@dataclass(frozen=True)
class PackageInspection:
    """Summary of a packaged QTI assessment."""

    assessment_path: str
    item_count: int
    question_type_counts: dict[str, int]


def summarize_quiz(quiz: Quiz) -> str:
    lines = [f"Title: {quiz.title}", f"Items: {len(quiz.questions)}"]
    for index, question in enumerate(quiz.questions, start=1):
        parent = getattr(question, "parent_stimulus_ident", None)
        qtype = question.qtype
        points = question.points
        if isinstance(question, StimulusItem):
            lines.append(f"{index:02d}. STIMULUS id={question.forced_ident}")
        else:
            attachment = f" (parent={parent})" if parent else ""
            lines.append(f"{index:02d}. {qtype} ({points:g} pts){attachment}")
    return "\n".join(lines)


def assert_questions_present(questions: Iterable[Question]) -> None:
    if not list(questions):
        raise ValueError("At least one question is required to build a quiz.")


def inspect_qti_package(zip_bytes: bytes) -> PackageInspection:
    """Parse a generated QTI package and ensure baseline structural integrity."""

    try:
        archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        raise ValueError("Generated QTI package is not a valid ZIP archive.") from exc

    with archive:
        names = archive.namelist()
        if not names:
            raise ValueError("Generated QTI package is empty.")
        if "imsmanifest.xml" not in names:
            raise ValueError("imsmanifest.xml missing from QTI package.")

        assessment_name = next(
            (
                name
                for name in names
                if name.endswith(".xml")
                and "/" in name
                and name.count("/") == 1
                and not name.endswith("assessment_meta.xml")
            ),
            None,
        )

        if assessment_name is None:
            raise ValueError("Assessment XML not found in QTI package.")

        try:
            document = archive.read(assessment_name)
        except KeyError as exc:
            raise ValueError("Failed to read assessment XML from package.") from exc

    try:
        root = ET.fromstring(document)
    except ET.ParseError as exc:
        raise ValueError(f"Assessment XML is invalid: {exc}.") from exc

    items = root.findall(f".//{QTI_NS}item")
    if not items:
        raise ValueError("Assessment XML contains no items.")

    counts: Counter[str] = Counter()
    meta_path = f".//{QTI_NS}qtimetadatafield"
    label_path = f"{QTI_NS}fieldlabel"
    entry_path = f"{QTI_NS}fieldentry"

    for item in items:
        qtype = "unknown"
        is_numerical = False
        has_bounds = False
        for field in item.findall(meta_path):
            label = field.find(label_path)
            entry = field.find(entry_path)
            if label is None or entry is None:
                continue
            if (label.text or "").strip() == "question_type":
                candidate = (entry.text or "").strip() or "unknown"
                qtype = candidate
                if qtype == "numerical_question":
                    is_numerical = True
                break
        counts[qtype] += 1

        if is_numerical:
            lower = item.find(f".//{QTI_NS}vargt")
            if lower is None:
                lower = item.find(f".//{QTI_NS}vargte")
            upper = item.find(f".//{QTI_NS}varlte")
            if lower is not None and upper is not None:
                has_bounds = True
            if not has_bounds:
                raise ValueError("Numerical item missing lower/upper bounds in resprocessing block.")

    return PackageInspection(
        assessment_path=assessment_name,
        item_count=len(items),
        question_type_counts=dict(counts),
    )
