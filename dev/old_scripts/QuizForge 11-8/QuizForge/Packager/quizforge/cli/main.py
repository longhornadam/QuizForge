"""Command-line interface for the QuizForge packager."""

from __future__ import annotations

import argparse
from typing import Optional

from ..services.packager import Packager


def build_arg_parser() -> argparse.ArgumentParser:
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
    run_cli()


if __name__ == "__main__":
    main()
