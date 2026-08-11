# Onboarding

Quick start for a human who wants to work in this repo without reading every
spec first.

## What this project is

This is a Kaggle agent for the Pokemon TCG AI Battle Challenge. Most work is in
`src/`, with tests in `tests/`, runnable scripts in `scripts/`, and project
status in `docs/`.

## Read first

1. [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md)
2. [`docs/CODEBASE_MAP.md`](docs/CODEBASE_MAP.md)
3. [`docs/20_master_index.md`](docs/20_master_index.md)
4. [`docs/03_tasks/TASK_INDEX.md`](docs/03_tasks/TASK_INDEX.md)

## Setup

From the repo root:

```bash
uv sync
```

Optional:

```bash
source .venv/bin/activate
```

## Common commands

Run tests:

```bash
uv run --frozen pytest tests/ -q
```

Run formatting, lint, and type checks:

```bash
uv run --frozen pre-commit run --all-files
```

Run the basic smoke gate:

```bash
scripts/run_smoke.sh heuristic
```

Run a dry-run submission pipeline:

```bash
scripts/submit_simulation.sh --dry-run
```

Run a real submission:

```bash
scripts/submit_simulation.sh
```

## Where things live

- `src/` - agent code and shared runtime
- `tests/` - pytest suite
- `scripts/` - manual entry points for smoke, reports, replay tools, and
  submissions
- `docs/` - project status, gameplay rules, task index, and report contracts
- `submissions/` - built archives
- `data/raw/kaggle/replays/` - downloaded Kaggle replays
- `experiments/` - isolated one-off experiments

## If you want to change gameplay

Work in `src/agents/` first, then add or update tests in `tests/`, then run the
smoke or submission pipeline again.

If you are touching strategy, check `docs/PROJECT_STATUS.md` and
`docs/03_tasks/TASK_INDEX.md` first. The T-034 issue remains open until the
owner accepts replay-based closure.
