"""Engine configuration flags."""

import os

# Switch between legacy text spec and new JSON spec.
# "text" - legacy (default; robust for teacher-facing text imports).
# "json" - newspec JSON 3.0 pipeline (requires QUIZFORGE_JSON tags).
SPEC_MODE = os.getenv("QUIZFORGE_SPEC_MODE", "text")

