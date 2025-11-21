"""Engine configuration flags."""

import os

# Switch between legacy text spec and new JSON spec.
# "text" → current production behavior (legacy text spec).
# "json" → experimental pipeline using dev/newspec_engine.
SPEC_MODE = os.getenv("QUIZFORGE_SPEC_MODE", "text")
