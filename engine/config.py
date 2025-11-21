"""Engine configuration flags."""

import os

# Switch between legacy text spec and new JSON spec.
# "text" – legacy (use only if explicitly needed).
# "json" – newspec JSON 3.0 pipeline (default).
SPEC_MODE = os.getenv("QUIZFORGE_SPEC_MODE", "json")

