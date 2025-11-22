#!/usr/bin/env python
"""Run QuizForge packager with proper sys.path"""

from pathlib import Path
import sys

# Ensure the Packager directory is importable for the `quizforge` package
packager_root = Path(__file__).resolve().parent
sys.path.insert(0, str(packager_root))

# Now import and run
from quizforge.cli.main import run_cli

if __name__ == "__main__":
    run_cli()
