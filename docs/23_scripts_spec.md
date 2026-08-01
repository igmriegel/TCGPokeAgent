# Operational command inventory

> This page lists commands that exist now. Proposed commands belong in the
> task index, not in the executable inventory.

## Quality and consistency

| Command | Purpose |
|---|---|
| `uv run --frozen pytest tests/ -q` | Unit, integration, package, and documentation gates |
| `uv run --frozen pre-commit run --all-files` | Format, lint, and type checks |
| `uv run --frozen python scripts/audit_documentation.py` | Documentation/code drift audit |
| `uv run --frozen python -m scripts.preflight --config configs/default.yaml` | SDK, deck, package layout, and writable-output checks (`scripts/preflight.py`) |

## Evaluation and replay

| Command | Purpose |
|---|---|
| `scripts/run_smoke.sh heuristic` | Tests plus 20-seed both-side CABT smoke |
| `scripts/run_full.sh heuristic configs/eval_full.yaml` | Immutable full run and reports |
| `uv run --frozen python scripts/compare_agents.py --matches 10` | Baseline/heuristic comparison against random |
| `uv run --frozen python scripts/gameplay_smoke.py --matches 10 --agent-mode heuristic` | Observable-gameplay gate |
| `uv run --frozen python scripts/run_replay.py --agent-one heuristic --agent-two random` | Local visualizer replay |
| `uv run --frozen python -m src.data.replay_ingestor --input DIR --output NEW_DIR --owner-name NAME` | Versioned replay dataset |
| `uv run --frozen python -m src.data.gameplay_annotations --help` | Post-hoc replay inspection and annotation |

## Data, package, and submission

| Command | Purpose |
|---|---|
| `scripts/download_data.sh --check` | Verify official dataset manifest |
| `scripts/download_data.sh --competition simulation` | Download one authorized dataset |
| `scripts/download_all_replays.py` | Download replays from all Kaggle submissions |
| `scripts/sync_replays.py` | Sync downloaded replays to dashboard directory |
| `scripts/generate_investigation_report.py` | Generate HTML investigation report from replays |
| `scripts/build_package.sh submission.tar.gz` | Build the explicit submission allowlist |
| `scripts/build_package.sh submission_hdi_v1.tar.gz hdi_v1` | Build the native HDI v1 experimental archive and SHA-256 sidecar |
| `scripts/build_package.sh submission-xgboost.tar.gz xgboost_ranker MODEL_DIR` | Build one backend-exclusive ranker archive |
| `uv run --frozen --group ranker-xgboost python scripts/train_rankers.py --help` | Train grouped native ranker studies (`scripts/train_rankers.py`) |
| `uv run --frozen python -m src.eval.validation --package submission.tar.gz` | Validate an extracted archive |
| `scripts/submit_simulation.sh --dry-run` | Run all local submission gates without upload |
| `scripts/submit_simulation.sh` | Gate, confirm interactively, and submit |

## Internal helpers

`scripts/cabt_smoke.py` is the Python implementation invoked by
`scripts/run_smoke.sh`. `scripts/submit_simulation.py` implements the guarded
pipeline invoked by `scripts/submit_simulation.sh`. They remain directly
executable for focused debugging, but the shell wrappers are the public
commands.

## Command guarantees

- scripts run from the repository root or normalize their working directory;
- generated run directories and reports do not overwrite an existing run ID;
- policy logic remains in `src/`, not in shell wrappers;
- submission never uploads without `--yes` or an affirmative prompt;
- successful uploads write a credential-free receipt;
- generated data and reports follow the persistence contracts.

There is no standalone freeze, comparison-of-run-files, strategy-export, or
Kaggle-inventory command today. Those capabilities must not be presented as
available until implemented and added to this inventory.
