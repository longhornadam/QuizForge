"""Command-line interface for the QuizForge packager."""

from __future__ import annotations

import argparse
from typing import Optional

from ..services.packager import Packager


def build_arg_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for the CLI.

    Defines all command-line flags:
    - input: Path to .txt quiz file (positional)
    - -o, --output: Output ZIP filename (default: quiz_package.zip)
    - --title: Override quiz title
    - --validate: Parse-only mode (no ZIP)

    Returns:
        argparse.ArgumentParser: Configured parser ready for parse_args()
    """
    parser = argparse.ArgumentParser(description="Convert a simple text quiz to Canvas QTI 1.2 ZIP")
    parser.add_argument("input", help="Path to input .txt file")
    parser.add_argument(
        "-o",
        "--output",
        default="quiz_package.zip",
        help="Output ZIP filename (default: quiz_package.zip)",
    )
    parser.add_argument("--title", help="Override quiz title")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Parse input and print a summary without writing a ZIP",
    )
    return parser


def run_cli(argv: Optional[list[str]] = None) -> None:
    """Run the CLI workflow: parse arguments, execute packager, print results.

    This is the main entry point for command-line usage.

    Args:
        argv: List of command-line arguments (defaults to sys.argv if None)

    Workflow:
    1. Parse command-line arguments
    2. If --validate: Print summary and exit
    3. Otherwise: Package to ZIP, print results and validation data

    Exits with error messages if parsing/packaging fails.
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    packager = Packager()

    if args.validate:
        summary = packager.summarize(args.input, title_override=args.title)
        print(summary)
        return

    result = packager.package(args.input, args.output, title_override=args.title)
    type_summary = ", ".join(f"{qtype}: {count}" for qtype, count in sorted(result.inspection.question_type_counts.items()))
    print(
        f"Wrote {result.output_path} with imsmanifest.xml and folder "
        f"{result.guid}/{{{result.guid}.xml,assessment_meta.xml}}"
    )
    print(f"Validated {result.inspection.item_count} items ({type_summary or 'unknown types'})")


def main() -> None:
    """Entry point for python -m quizforge.cli.main or direct invocation."""
    run_cli()


if __name__ == "__main__":
    main()
