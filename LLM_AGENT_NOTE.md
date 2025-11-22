For every build/release/deploy request, ask whether to tag as `--development` or `--stable`.
- Current stable checkpoint: `1.0-beta2-stable` (see VERSION).
- Default to `--stable` for teacher-facing deployments (Unraid/Dockge/Cloudflare).
- Only use `--development` for testing changes not yet promoted to stable.
