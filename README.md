# QuizForge
Python-based automated quiz generator for Canvas New Quizzes (QTI 1.2).

## Directory Highlights

- `engine/`, `DropZone/`, `Finished_Exports/`: local CLI workflow for building and exporting quiz bundles.
- `web/`: Vite/React client served as static assets.
- `server/`: Node wrapper that shells out to the Python orchestrator per request.

## Deploying the Web App

1. Commit changes and push to the branch connected to Render.
2. Render reads `render.yaml` and deploys:
   - `quizforge-api`: Node web service (`server/index.js`) that shells out to the Python orchestrator per request and streams ZIPs (Python never listens on the network).
   - `quizforge-web`: static site built from `web/` via Vite (set `VITE_API_BASE_URL` to the API URL).
3. Downloadable releases still include `web/`; teachers running locally can ignore it and continue using the CLI.
