# QuizForge Web Client (Vite + React)

Thin UI that uploads or pastes a QuizForge-ready text file (.txt/.json/.md), calls the Express API wrapper, and downloads the resulting `Finished_Exports` as a ZIP (mirrors `python engine/orchestrator.py`).

## Beta/Prod (single container)

```bash
docker compose up -d quizforge-webapp   # serves static UI + API on :8000
# visit http://localhost:8000 (or your host/Cloudflare tunnel)
```

## Local development

1) Install Node (>=18) and Python (>=3.11).  
2) Install Python deps (for the orchestrator) and run the Node API locally:
```bash
python -m pip install -r requirements.txt
npm install --prefix server
node server/index.js
```
3) In another shell, run the web client:
```bash
cd web
npm install
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```
4) Open `http://localhost:5173` and upload/paste your TXT/JSON/MD file. The ZIP downloads when the job finishes.

## Build

```bash
cd web
npm install
npm run build   # outputs to web/dist
```
Set `VITE_API_BASE_URL` at build time if the API lives at a different origin (e.g., the Render web service URL). Defaults to relative `/api`.

## Rollback (remove web surface)

If you need to revert to the prior static page, delete the Vite files in `web/` and restore the old `index.html`, and remove or disable the web service definition from `render.yaml`. The CLI flow remains unchanged.
