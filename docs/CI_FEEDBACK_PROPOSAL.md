# CI feedback proposal

This repository does not add or activate CI in the current cycle. The
following proposal is retained for a future decision.

## Lightweight pull-request gate

Run on every `push` and `pull_request` with Python 3.12 and a frozen uv
environment:

```bash
uv sync --frozen
uv run --frozen pytest tests/ -q
uv run --frozen ruff format --check .
uv run --frozen ruff check .
uv run --frozen mypy --config-file=pyproject.toml src/
uv run --frozen python scripts/audit_documentation.py
uv run --frozen python -m scripts.preflight --config configs/default.yaml
```

The gate should fail explicitly on any test, quality, documentation, or
package-validation error. A clean extracted-package smoke test should also
run in an isolated environment.

## Extended evaluation

CABT evaluations, 200/300-match comparisons, Kaggle downloads, Docker runs,
and uploads should remain manual, nightly, or in a separately authorized
workflow. They are too slow or externally dependent for a mandatory pull-
request gate and may require protected credentials.

Before activating the lightweight gate, repair the currently known
documentation-audit failure caused by links to historical artifacts that are
not present in this checkout.
