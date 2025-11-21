import os
from pathlib import Path
import sys

os.environ["QUIZFORGE_SPEC_MODE"] = "json"

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.importers import import_quiz_from_llm
from engine.validation.validator import QuizValidator
from engine.validation.point_calculator import calculate_points
from engine.validation.answer_balancer import balance_answers
from engine.rendering.physical.styles.default_styles import DEFAULT_QUIZ_POINTS
from engine.packaging.folder_creator import create_quiz_folder
from engine.packagers.packager import package_quiz


def main():
    input_path = Path("dev/newspec/newspec_inputs/firsttest.txt")
    raw = input_path.read_text(encoding="utf-8")

    imported = import_quiz_from_llm(raw)
    quiz = imported.quiz

    quiz.questions = calculate_points(quiz.questions, total_points=DEFAULT_QUIZ_POINTS)
    quiz.questions = balance_answers(quiz.questions)

    validator = QuizValidator()
    result = validator.validate(quiz)
    print("Validation status:", result.status)
    if getattr(result, "errors", None):
        print("Errors:", result.errors)
    if getattr(result, "warnings", None):
        print("Warnings:", result.warnings)

    out_base = Path("dev/newspec/newspec_outputs")
    out_base.mkdir(parents=True, exist_ok=True)
    folder = create_quiz_folder(out_base, quiz.title)

    package_results = package_quiz(quiz, str(folder))
    print("Package results:", package_results)


if __name__ == "__main__":
    main()
