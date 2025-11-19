# QuizForge
Python-based automated quiz generator for Canvas New Quizzes (QTI 1.2).

## Directory Highlights

- `engine/`, `DropZone/`, `Finished_Exports/`: local CLI workflow for building and exporting quiz bundles.
- `web/`: production web client served via Render. Static assets live here and can be updated independently from the engine.

## Deploying the Web App

1. Commit changes and push to the branch connected to Render.
2. Render reads `render.yaml` and deploys the `web/` directory as a static site (no build step required).
3. Downloadable releases still include `web/`; teachers running locally can simply ignore that folder.
