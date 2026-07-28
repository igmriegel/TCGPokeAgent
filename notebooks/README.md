# Notebooks

Space for lightweight exploratory analysis. Notebooks do not execute the
production pipeline nor are they the single source of a decision.

## Available notebooks

- [`01_card_catalog_overview.py`](01_card_catalog_overview.py) — schema,
  missing values, categories, expansions, and HP distribution for the English
  simulation catalog.
- [`02_dataset_comparison.py`](02_dataset_comparison.py) — row/column counts,
  duplicate checks, cross-track equality, and a basic expansion summary.
- [`03_run_results_dashboard.py`](03_run_results_dashboard.py) — loads JSON
  reports from `reports/` and compares W/D/L, win rate, errors, and duration.
- [`04_heuristic_score_lab.py`](04_heuristic_score_lab.py) — inspects score
  reasons and compares heuristic weight/feature ablations on controlled cases.

Run locally from the project root:

```bash
uv run --frozen marimo edit notebooks/01_card_catalog_overview.py
uv run --frozen marimo edit notebooks/02_dataset_comparison.py
uv run --frozen marimo edit notebooks/03_run_results_dashboard.py
uv run --frozen marimo edit notebooks/04_heuristic_score_lab.py
```

Or start the Docker service:

```bash
docker compose up marimo
```

Stable results migrate to a report and to [`docs/strategy_notes.md`](../docs/strategy_notes.md).
