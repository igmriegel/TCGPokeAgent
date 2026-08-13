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
| `scripts/download_all_replays.sh` | Download replays to `data/raw/kaggle/replays/remote/` from all Kaggle submissions |
| `kaggle competitions logs EPISODE_ID AGENT_INDEX -p data/raw/kaggle/decision_logs/SUBMISSION_ID/raw -q` | Download one submitted agent's captured stdout/stderr log for decision-ledger audit |
| `scripts/generate_investigation_report.sh` | Generate active HTML investigation reports; the legacy Abomasnow output is disabled |
| `scripts/sync_replays.sh` | Refresh the episode-to-submission map from canonical downloaded replays |
| `scripts/audit_turn_planning.py` | Audit Ariana, Proton, Transceiver, Petrel/Factory, and proven Poké Pad KO patterns in JSONL traces |
| `scripts/build_package.sh submissions/submission.tar.gz` | Build the explicit submission allowlist |
| `make build-abomasnow-package` | Build the Abomasnow `submissions/submission.tar.gz` archive |
| `scripts/build_package.sh submissions/submission_hdi_v1.tar.gz hdi_v1` | Build the native HDI v1 experimental archive and SHA-256 sidecar |
| `scripts/build_package.sh submissions/submission-xgboost.tar.gz xgboost_ranker MODEL_DIR` | Build one backend-exclusive ranker archive |
| `scripts/build_honchkrow_porygon_package.sh submissions/honchkrow_porygon_submission.tar.gz` | Build the isolated Honchkrow/Porygon deck archive with its required complete stderr decision ledger |
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
| `uv run --frozen python scripts/generate_investigation_report.py` | Build an active HTML investigation report; the legacy Abomasnow output is disabled |
| `uv run --frozen python scripts/sync_replays.py` | Sync downloaded replays and refresh the submission map |
| `uv run --frozen python scripts/audit_turn_planning.py <trace.jsonl.gz> --output <report.json>` | Emit tactical counters and bounded factual examples from a CABT trace |
| `uv run --frozen python scripts/inspect_replay.py <replay.json> --turn N --player-index P` | Inspect Kaggle replay frames with stable coordinates, logs, and legal options |
| `uv run --frozen python scripts/update_replays_reports.py` | Refresh generated replay investigation reports |
| `bash scripts/build_kaggle_stdout_debug_package.sh <output.tar.gz>` | Compatibility alias for the official auditable package; the complete ledger is emitted to stderr, never stdout |
| `uv run --frozen python scripts/decode_kaggle_decision_ledger.py REPLAY_OR_LOG --output decisions.jsonl` | Verify checksum and decode complete compressed decision-ledger records |
| `uv run --frozen python scripts/download_kaggle_decision_logs.py SUBMISSION_ID` | Resolve the submitted agent's replay seat, download its remote logs, decode compact payloads, and write annotated JSONL with the exact field-description dictionary |
| `scripts/download_all_decision_logs.sh` | Download and decode decision logs for every locally mirrored submission, or the submission named by `SUBMISSION_ID` |
| `uv run --frozen python scripts/export_decision_traces.py` | Export decision traces from evaluation reports for replay and audit analysis |
| `uv run --frozen python scripts/audit_owner_feedback_replays.py <replay-dir> --output <report.json>` | Validate and hash the 14 owner-provided Honchkrow replays and emit reconciled diagnostics |
| `uv run --frozen python scripts/run_honchkrow_porygon_eval.py --matches-per-side 100 --output REPORT.json` | Run the 200-match dedicated CABT evaluation for the canonical policy with prize, deck, board, Supporter, action, and terminal telemetry |
| `uv run --frozen python scripts/compare_honchkrow_reports.py BASELINE.json VARIANT.json` | Compare independent Honchkrow reports with Wilson intervals, side splits, deck-outs, and a two-proportion test; nominal CABT seeds are not treated as paired episodes |
| `uv run --frozen python scripts/analyze_replays.py REPLAY_DIR --output REPORT.json` | Rebuild per-replay damage, KO, resource, and loss diagnostics recursively |
| `uv run --frozen python scripts/audit_submission_55333874.py` | Reproduce the immutable submitted policy over its 26-replay isolated corpus, emit the decision ledger and review bundle, and incorporate completed CABT candidate gates |
| `uv run --frozen python scripts/build_t034_root_cause_report.py` | Build the conservative replay-linked root-cause evidence report; it preserves unknown internal causes when the immutable package lacks candidate traces |
| `uv run --frozen python scripts/restore_t034_replay_corpus.py` | Restore submission `55333874` replays into a staging directory, verify every frozen SHA-256, then publish the exact immutable replay corpus |
| `uv run --frozen python scripts/audit_recent_submission_prompts.py --output REPORT.json` | Reproduce the current policy on curated isolated prompts from the two latest submissions without alternate-outcome inference |
| `uv run --frozen python scripts/create_honchkrow_turn_loop_v2_manifest.py` | Freeze the HLV2 baseline/candidate identities, deck/profile/lock hashes, CABT SDK pin, source state, and 26-replay corpus |
| `uv run --frozen python scripts/build_honchkrow_turn_loop_v2_report.py BASELINE CANDIDATE OUTPUT_DIR` | Build the complete independent HLV2 comparison bundle and emit `HOLD` until every final gate is evidenced |
| `uv run --frozen python scripts/summarize_honchkrow_turn_loop_v2_replays.py BASELINE CANDIDATE OUTPUT_DIR` | Reduce the two 1,434-decision reproductions to a safe single-decision divergence ledger without alternate-outcome claims |

The Honchkrow package entrypoint declares `expert_turn_loop` explicitly; package
manifests record the same value. Historical policy names are not accepted by
the evaluator or package builder.

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
- submission uses the current Kaggle OAuth credentials or an explicit
  `KAGGLE_API_TOKEN` without printing or persisting the credential;
- successful uploads write a credential-free receipt;
- generated data and reports follow the persistence contracts.

There is no standalone freeze, comparison-of-run-files, strategy-export, or
Kaggle-inventory command today. Those capabilities must not be presented as
available until implemented and added to this inventory.
