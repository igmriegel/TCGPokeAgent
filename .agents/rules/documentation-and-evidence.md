---
description: Documentation language, canonical status, and evidence requirements.
paths:
  - "docs/**/*.md"
  - "AGENTS.md"
  - "reports/**/*.md"
alwaysApply: false
---

# Documentation and evidence rules

- Write documentation, reports, identifiers, and configuration prose in English.
- Treat `docs/PROJECT_STATUS.md` as the canonical current-state snapshot and `docs/03_tasks/TASK_INDEX.md` as the canonical task registry.
- Keep historical evidence in the appropriate evidence or report document rather than copying it into the status snapshot.
- Do not mark a task or implementation slice complete without the stated gate and linked evidence.
- Preserve the distinction between Owner observations, verified replay facts, technical hypotheses, and experimental results.
- For the open strategy-divergence P0, record representative replay traces end to end under T-034 before proposing runtime conclusions.
- Keep internal links, task references, dates, metrics, and artifact paths accurate when changing documentation.
