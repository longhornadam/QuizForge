# QuizForge QTI Packager - Backward Compatibility Wrapper
#
# This file provides backward compatibility for the legacy command-line interface.
# The actual implementation has been refactored into a modular package structure
# located in the 'quizforge/' directory.
#
# Legacy usage (still supported):
#     python Packager/quizforge_packager.py input.txt -o output.zip
#
# Preferred usage:
#     python Packager/run_packager.py input.txt -o output.zip

from __future__ import annotations


def main() -> None:
    from quizforge.cli.main import run_cli
    run_cli()


if __name__ == "__main__":
    main()
