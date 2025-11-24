"""
Simple CLI entrypoint for QuizForge newspec.

Usage:
  python run_quizforge.py --input spec/inputs/example.txt --output out_dir

Defaults:
  QUIZFORGE_SPEC_MODE=json
  Writes Canvas QTI + DOCX quiz/key/rationale into the output folder.
"""

import argparse
import os
from pathlib import Path
from typing import Optional

from engine.importers import import_quiz_from_llm
from engine.validation.validator import QuizValidator
from engine.validation.point_calculator import calculate_points
from engine.validation.answer_balancer import balance_answers
from engine.rendering.physical.styles.default_styles import DEFAULT_QUIZ_POINTS
from engine.packagers.packager import package_quiz


def run_quizforge_job(spec_text: str, output_dir: str) -> str:
    """
    Run the QuizForge pipeline for a single spec payload.

    Args:
        spec_text: Raw spec text (QUIZFORGE-wrapped) to process.
        output_dir: Directory to write outputs into.

    Returns:
        Path to the primary output artifact (prefers Canvas QTI).
    """
    if not spec_text or not spec_text.strip():
        raise ValueError("spec_text is required")

    os.environ["QUIZFORGE_SPEC_MODE"] = "json"

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    imported = import_quiz_from_llm(spec_text)
    quiz = imported.quiz

    # Auto-assign points and balance choices
    quiz.questions = calculate_points(quiz.questions, total_points=DEFAULT_QUIZ_POINTS)
    quiz.questions = balance_answers(quiz.questions)

    validator = QuizValidator()
    result = validator.validate(quiz)
    print("Validation status:", result.status)
    if getattr(result, "errors", None):
        print("Errors:", result.errors)
    if getattr(result, "warnings", None):
        print("Warnings:", result.warnings)

    package_results = package_quiz(quiz, str(output_path))
    print("Package results:", package_results)

    output_file: Optional[str] = None
    if package_results.get("canvas"):
        output_file = package_results["canvas"].get("qti_path") or package_results["canvas"].get("log_path")
    if not output_file and package_results.get("physical"):
        output_file = package_results["physical"].get("quiz_path") or package_results["physical"].get("key_path")

    if not output_file:
        raise RuntimeError("QuizForge completed but no output file was returned.")

    return str(Path(output_file).resolve())


def main():
    parser = argparse.ArgumentParser(description="QuizForge newspec packager")
    parser.add_argument("--input", required=True, help="Path to newspec JSON 3.0 input file (wrapped in QUIZFORGE tags)")
    parser.add_argument("--output", required=True, help="Directory to write outputs")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    raw = input_path.read_text(encoding="utf-8")
    result_file = run_quizforge_job(raw, str(output_dir))
    print("Primary output:", result_file)


if __name__ == "__main__":
    main()

