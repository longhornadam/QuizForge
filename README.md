# QuizForge
Python-based automated quiz generator for Canvas New Quizzes (QTI 1.2).

## Directory Highlights

- `engine/`, `DropZone/`, `Finished_Exports/`: local CLI workflow for building and exporting quiz bundles.
- `web/`: Vite/React client served as static assets.
- `server/`: Node wrapper that shells out to the Python orchestrator per request.

## Release channel & versioning

- Current stable checkpoint: **1.0-beta2-stable** (see `VERSION`).
- Always decide: deploy `--stable` or `--development`. For Unraid/Dockge, prefer `--stable` unless testing new changes.

## Deploying the Web App (beta-ready)

- **Docker/Unraid (single container)**: `docker compose up -d quizforge-webapp` then visit `http://<host>:8000`. The container serves the Vite UI and the Express API together; Cloudflare Tunnel can point straight at port 8000. Health check: `GET /api/health`.
- **Render (existing flow)**: see `render.yaml` (separate API + static site). Set `VITE_API_BASE_URL` to the deployed API URL if hosting the client separately.
- **Unraid + Cloudflare Tunnel**: place the repo in an Unraid share, run `docker compose up -d quizforge-webapp`, and configure your tunnel HTTP hostname to `http://quizforge-webapp:8000` (or the Unraid host IP + mapped port) on the same Docker network.

## Development (JSON/QF_Base default)
- Requires Python 3.11+
- Install dependencies: `pip install -r requirements.txt`
- To run sample flow: `python spec/run_firsttest.py`
 - QF_Base (JSON 3.0) spec lives at `LLM_Modules/NEWBASE.md` (reference example in `LLM_Modules/quiz_example.txt`)

## Docker (JSON/QF_Base)
- Web beta: `docker compose up -d quizforge-webapp` (serves UI + API on 8000).
- CLI runner (optional): `docker compose run --rm quizforge-cli --input /app/input/attempt9_docx_all_types_13q.txt --output /app/output/demo` (see volumes in `docker-compose.yml`).
- Images default to `QUIZFORGE_SPEC_MODE=json` and bundle the full Python orchestrator.
