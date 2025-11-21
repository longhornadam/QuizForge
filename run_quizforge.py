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

from engine.importers import import_quiz_from_llm
from engine.validation.validator import QuizValidator
from engine.validation.point_calculator import calculate_points
from engine.validation.answer_balancer import balance_answers
from engine.rendering.physical.styles.default_styles import DEFAULT_QUIZ_POINTS
from engine.packagers.packager import package_quiz


def main():
    parser = argparse.ArgumentParser(description="QuizForge newspec packager")
    parser.add_argument("--input", required=True, help="Path to newspec JSON 3.0 input file (wrapped in QUIZFORGE tags)")
    parser.add_argument("--output", required=True, help="Directory to write outputs")
    args = parser.parse_args()

    os.environ["QUIZFORGE_SPEC_MODE"] = "json"

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw = input_path.read_text(encoding="utf-8")
    imported = import_quiz_from_llm(raw)
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

    package_results = package_quiz(quiz, str(output_dir))
    print("Package results:", package_results)


if __name__ == "__main__":
    main()

