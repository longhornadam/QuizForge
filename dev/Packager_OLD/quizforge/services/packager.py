"""Service orchestrating parse, validation, render, and packaging.

The Packager class is the main orchestrator. It coordinates the entire workflow:
1. Parse: Convert text file/string → Quiz object
2. Validate: Inspect quiz structure (validation-only mode)
3. Render: Convert Quiz → QTI XML (assessment, manifest, metadata)
4. Package: Create QTI 1.2 ZIP archive ready for Canvas

Entry points:
- package(input_file, output_file): File-based packaging
- package_text(content): Text-based packaging (web-compatible)
- summarize(input_file): Validation-only mode (no ZIP)
- parse(source): Parser access (rarely used directly)

Data structures:
- PackageResult: File-based result (output path + metadata)
- PackageBytesResult: Text-based result (ZIP bytes + metadata)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from ..domain.quiz import Quiz
from ..io.parsers.base import QuizParser
from ..io.parsers.text_parser import TextOutlineParser
from ..renderers.qti import build_assessment_meta_xml, build_assessment_xml, build_manifest_xml
from . import validation
from ..infrastructure.zip_writer import create_zip_bytes


"""Result of file-based packaging: path, GUID, parsed Quiz, and validation inspection data."""
@dataclass
class PackageResult:
    output_path: str
    guid: str
    quiz: Quiz
    inspection: validation.PackageInspection


"""Result of text-based packaging: ZIP bytes, GUID, parsed Quiz, and validation inspection data."""
@dataclass
class PackageBytesResult:
    zip_bytes: bytes
    guid: str
    quiz: Quiz
    inspection: validation.PackageInspection


class Packager:
    """Coordinate each step of the QuizForge packaging workflow."""

    def __init__(
        self,
        parser: Optional[QuizParser] = None,
    ) -> None:
        """Initialize packager with optional custom parser (defaults to TextOutlineParser)."""
        self.parser = parser or TextOutlineParser()

    def parse(self, source: str, *, title_override: Optional[str] = None) -> Quiz:
        """Parse source into Quiz object. Does not render or package."""
        return self.parser.parse(source, title_override=title_override)

    def summarize(self, source: str, *, title_override: Optional[str] = None) -> str:
        """Parse quiz and return human-readable summary (validation mode, no ZIP)."""
        quiz = self.parse(source, title_override=title_override)
        return validation.summarize_quiz(quiz)

    def package(
        self,
        source: str,
        output_path: str,
        *,
        title_override: Optional[str] = None,
    ) -> PackageResult:
        """Parse quiz from file, render to QTI XML, create ZIP, write to disk. Returns PackageResult."""
        quiz = self.parse(source, title_override=title_override)
        guid = str(uuid.uuid4())
        assessment_xml = build_assessment_xml(quiz)
        manifest_xml = build_manifest_xml(quiz.title, guid)
        meta_xml = build_assessment_meta_xml(quiz.title, quiz.total_points(), guid)
        zip_bytes = create_zip_bytes(manifest_xml, assessment_xml, meta_xml, guid)
        inspection = validation.inspect_qti_package(zip_bytes)
        with open(output_path, "wb") as handle:
            handle.write(zip_bytes)
        return PackageResult(output_path=output_path, guid=guid, quiz=quiz, inspection=inspection)

    def parse_text(self, content: str, *, title_override: Optional[str] = None) -> Quiz:
        """Parse quiz from string (for web apps). Does not render or package."""
        return self.parser.parse_text(content, title_override=title_override)

    def summarize_text(self, content: str, *, title_override: Optional[str] = None) -> str:
        """Parse quiz from string and return summary (validation mode, no ZIP)."""
        quiz = self.parse_text(content, title_override=title_override)
        return validation.summarize_quiz(quiz)

    def package_text(self, content: str, *, title_override: Optional[str] = None) -> PackageBytesResult:
        """Package quiz from text content, returning bytes and validation metadata."""
        quiz = self.parse_text(content, title_override=title_override)
        guid = str(uuid.uuid4())
        assessment_xml = build_assessment_xml(quiz)
        manifest_xml = build_manifest_xml(quiz.title, guid)
        meta_xml = build_assessment_meta_xml(quiz.title, quiz.total_points(), guid)
        zip_bytes = create_zip_bytes(manifest_xml, assessment_xml, meta_xml, guid)
        inspection = validation.inspect_qti_package(zip_bytes)
        return PackageBytesResult(zip_bytes=zip_bytes, guid=guid, quiz=quiz, inspection=inspection)
