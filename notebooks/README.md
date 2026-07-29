# Notebooks

Space for lightweight exploratory analysis. Notebooks do not execute the
production pipeline nor are they the single source of a decision.

## Available notebooks

- [`01_card_catalog_overview.py`](01_card_catalog_overview.py) — schema,
  missing values, categories, expansions, and HP distribution for the English
  simulation catalog.
- [`02_dataset_comparison.py`](02_dataset_comparison.py) — row/column counts,
  duplicate checks, cross-track equality, and a basic expansion summary.
- [`03_run_results_dashboard.py`](03_run_results_dashboard.py) — compares
  experiment reports and monitors explicit Prize, deck-out, and empty-board
  termination reasons from competitive CABT replays.
- [`04_heuristic_score_lab.py`](04_heuristic_score_lab.py) — inspects score
  reasons and compares heuristic weight/feature ablations on controlled cases.

Run locally from the project root:

```bash
uv run --frozen marimo edit notebooks/01_card_catalog_overview.py
uv run --frozen marimo edit notebooks/02_dataset_comparison.py
uv run --frozen marimo edit notebooks/03_run_results_dashboard.py
uv run --frozen marimo edit notebooks/04_heuristic_score_lab.py
```

Set `KAGGLE_OWNER_NAME` or enter the owner agent name in the run-results
dashboard to classify replay results as wins and losses. Validation episodes
where both sides have the same name remain `unknown`; their termination reason
is still counted, but the notebook does not invent an owner side.

Or start the Docker service:

```bash
docker compose up marimo
```

Stable results migrate to a report and to [`docs/strategy_notes.md`](../docs/strategy_notes.md).
