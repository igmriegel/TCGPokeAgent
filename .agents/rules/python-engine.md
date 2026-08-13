---
description: Python engine conventions, validation, and gameplay-domain boundaries.
paths:
  - "src/**/*.py"
  - "tests/**/*.py"
  - "scripts/**/*.py"
alwaysApply: false
---

# Python engine rules

- Target Python 3.12 and keep dependency changes synchronized with `pyproject.toml` and `uv.lock`.
- Use deferred annotations, complete public type annotations, dataclasses with slots, and the project's Ruff and mypy configuration.
- Preserve the vertical-slice boundaries: parsing, legal selection generation, scoring, search, and policy selection remain independently testable.
- Keep `GameState` factual and `BeliefState` hypothetical. Never serialize or present hypotheses as observed facts.
- Preserve simulator option indices; never renumber candidates or selections before returning them.
- Every `SelectContext` must have a deterministic legal fallback. External or parser failures must be contained by the engine error hierarchy and must not crash the agent.
- Add focused tests for behavior changes and run the relevant pytest, Ruff, mypy, and package checks before release.
- Treat the Owner-observed strategy divergence as unresolved P0 work. Do not claim strategic compliance from aggregate scores or focused tests; replay-based evidence belongs in the replay-review record.
