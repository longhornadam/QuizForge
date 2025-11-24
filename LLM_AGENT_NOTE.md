For every build/release/deploy request, ask whether to tag as `--development` or `--stable`.
- Current stable checkpoint: `1.0-beta2-stable` (see VERSION). Unraid/Dockge stack pulls `ghcr.io/longhornadam/quizforge:stable` via Watchtower.
- Default to `--stable` for teacher-facing deployments (Unraid/Dockge/Cloudflare). Use `--development` only for work not yet promoted.
- Current dev focus: expand numerical/math question types for Canvas New Quizzes (support more numeric variants for math teachers).
