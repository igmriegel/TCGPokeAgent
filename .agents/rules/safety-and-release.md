---
description: Safe configuration, container, build, and submission practices.
paths:
  - "Dockerfile"
  - "docker-compose.yml"
  - "configs/**/*"
  - "Makefile"
  - "scripts/**/*"
alwaysApply: false
---

# Safety and release rules

- Never commit credentials, private keys, certificates, tokens, or local credential directories. Keep only clearly named example templates.
- Do not add integrations, uploads, or external services without explicit authorization and a documented secret-handling path.
- Preserve `uv.lock`; dependency edits require a deliberate lockfile update and reproducible `uv sync --frozen` validation.
- Keep build and submission commands deterministic, scoped to explicit artifacts, and safe to rerun. Do not delete broad directories or overwrite release evidence silently.
- Validate a submission package after extraction and confirm its entrypoint, dependencies, and tracked contents before distribution.
- Keep CI, Kaggle downloads, uploads, and long evaluations outside this change unless explicitly requested.
