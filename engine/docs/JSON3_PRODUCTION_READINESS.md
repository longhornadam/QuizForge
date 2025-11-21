# JSON 3.0 Production Readiness (Feature-Flagged)

## Feature flag
- Env var: `QUIZFORGE_SPEC_MODE`
  - `text` (default): legacy TXT pipeline
  - `json`: JSON 3.0 pipeline via `dev/newspec_engine`
- Fallback: JSON path auto-falls back to text on any parse/packager error (logged warning).

## What’s supported
- All existing question types supported in TXT path.
- JSON 3.0 supports the same set; STIMULUS/END are never scored and excluded from rationales.
- Metadata/notes are free-form; extensions may nest under `metadata.extensions` and are ignored if unknown.

## Experimental
- NUMERICAL modes other than `exact` are marked experimental. Tools may ignore or skip them; they do not block imports.

## Testing
- Newspec tests: `pytest dev/newspec_engine/tests -q`
- Dual-mode integration: `pytest engine/tests/integration/test_spec_modes.py -q`

## Safe rollout steps
1) Keep default `QUIZFORGE_SPEC_MODE=text` in production.
2) To trial JSON, set `QUIZFORGE_SPEC_MODE=json` in a controlled environment.
3) Monitor logs for fallback warnings or experimental item notices.
4) Exporters consume only the domain quiz object; they do not inspect raw specs.
5) Unknown extensions are ignored; no failures on unrecognized keys.
