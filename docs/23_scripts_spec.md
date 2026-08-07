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
| `uv run --frozen python scripts/compare_agents.py --matches 10` | Baseline/heuristic win-loss comparison against `random` only |
| `uv run --frozen python scripts/gameplay_smoke.py --matches 10 --agent-mode heuristic` | Observable-gameplay gate from runner decision traces |
| `uv run --frozen python scripts/run_replay.py --agent-one heuristic --agent-two random` | Local visualizer replay |
| `uv run --frozen python -m src.data.replay_ingestor --input DIR --output NEW_DIR --owner-name NAME` | Versioned replay dataset |
| `uv run --frozen python -m src.data.gameplay_annotations --help` | Post-hoc replay inspection and annotation |

## Data, package, and submission

| Command | Purpose |
|---|---|
| `scripts/download_data.sh --check` | Verify official dataset manifest |
| `scripts/download_data.sh --competition simulation` | Download one authorized dataset |
| `scripts/download_all_replays.sh` | Download replays from all Kaggle submissions |
| `scripts/generate_investigation_report.sh` | Generate HTML investigation report from replay JSON files |
| `scripts/sync_replays.sh` | Sync downloaded replays to dashboard directory |
| `scripts/build_package.sh submissions/submission.tar.gz` | Build the explicit submission allowlist |
| `make build-abomasnow-package` | Build the Abomasnow `submissions/submission.tar.gz` archive |
| `scripts/build_package.sh submissions/submission_hdi_v1.tar.gz hdi_v1` | Build the native HDI v1 experimental archive and SHA-256 sidecar |
| `scripts/build_package.sh submissions/submission-xgboost.tar.gz xgboost_ranker MODEL_DIR` | Build one backend-exclusive ranker archive |
| `scripts/build_honchkrow_porygon_package.sh submissions/honchkrow_porygon_submission.tar.gz` | Build the isolated Honchkrow/Porygon deck archive |
| `uv run --frozen --group ranker-xgboost python scripts/train_rankers.py --help` | Train grouped native ranker studies (`scripts/train_rankers.py`) |
| `uv run --frozen python -m src.eval.validation --package submissions/submission.tar.gz` | Validate an extracted archive |
| `scripts/submit_simulation.sh --dry-run` | Run all local submission gates without upload |
| `scripts/submit_simulation.sh` | Gate, confirm interactively, and submit using the configured `~/.kaggle` login |
| `scripts/submit_simulation.sh --package-kind honchkrow_porygon --archive submissions/honchkrow_porygon_submission.tar.gz --skip-smoke --yes` | Build, validate, and submit the dedicated Honchkrow/Porygon package after its separate CABT smoke |
| `make submit-kaggle` | Run the guarded Kaggle submission workflow for `submissions/submission.tar.gz` |

## Operational Python scripts

| Command | Purpose |
|---|---|
| `uv run --frozen python scripts/download_all_replays.py` | Download all available Kaggle replays into the local mirror |
| `uv run --frozen python scripts/generate_investigation_report.py` | Build the HTML investigation report from replay JSON files |
| `uv run --frozen python scripts/sync_replays.py` | Sync downloaded replays and refresh the submission map |
| `uv run --frozen python scripts/update_replays_reports.py` | Refresh generated replay investigation reports |
| `uv run --frozen python scripts/run_honchkrow_porygon_eval.py --matches-per-side 100 --policy-variant supporter_resource_v2 --output REPORT.json` | Run the 200-match dedicated CABT evaluation with explicit policy selection and prize, deck, board, Supporter, action, and terminal telemetry |
| `uv run --frozen python scripts/compare_honchkrow_reports.py BASELINE.json VARIANT.json` | Compare independent Honchkrow reports with Wilson intervals, side splits, deck-outs, and a two-proportion test; nominal CABT seeds are not treated as paired episodes |
| `uv run --frozen python scripts/analyze_replays.py REPLAY_DIR --output REPORT.json` | Rebuild per-replay damage, KO, resource, and loss diagnostics recursively |

`HONCHKROW_POLICY_VARIANT=supporter_resource_v2` is the promoted Supporter-resource
policy and is also the default. Use `baseline` for the prior committed-switch
policy, or `legacy_baseline` only for rollback/regression measurement.
`ko_priority_v3_retreat_guard` remains an accepted alias so prior
evaluation commands remain reproducible.

## Internal helpers

`scripts/cabt_smoke.py` is the Python implementation invoked by
`scripts/run_smoke.sh`. `scripts/submit_simulation.py` implements the guarded
pipeline invoked by `scripts/submit_simulation.sh`, including explicit package
selection for dedicated decks. They remain directly
executable for focused debugging, but the shell wrappers are the public
commands.

## Command guarantees

- scripts run from the repository root or normalize their working directory;
- generated run directories and reports do not overwrite an existing run ID;
- policy logic remains in `src/`, not in shell wrappers;
- submission never uploads without `--yes` or an affirmative prompt;
- submission uses `KAGGLE_API_TOKEN`, `~/.kaggle/access_token`, or the ignored
  repository-root `kaggle.json` fallback without printing or persisting the
  credential;
- successful uploads write a credential-free receipt;
- generated data and reports follow the persistence contracts.

There is no standalone freeze, comparison-of-run-files, strategy-export, or
Kaggle-inventory command today. Those capabilities must not be presented as
available until implemented and added to this inventory.
