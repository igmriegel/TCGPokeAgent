# Codebase map

> Canonical map from shipped code to its consumers, tests, and delivery
> status. The automated documentation audit requires every Python module under
> `src/` to appear here.

**Last audited:** 2026-07-30

## Runtime paths

| Path | Entry point | Status |
|---|---|---|
| Competition agent | `main.py` → parser → legal selections → selected policy → fallback | Active, packaged |
| HDI experiment | `AGENT_MODE=hdi_v1` → factual context → ordinal rules | Implemented; experimental, not promoted |
| Learned candidates | shared features → XGBoost or LightGBM → exact heuristic fallback | Implemented; not promoted |
| Local evaluation | `scripts/run_smoke.sh`, `scripts/run_full.sh`, `scripts/gameplay_smoke.py` | Active; opponent matrix incomplete |
| Replay operations | `scripts/run_replay.py`, replay ingestion and annotation CLIs | Active tooling |
| RFL profile | Local `AGENT_MODE=rfl` → deck profile → heuristic agent | Local-only; excluded from current package |
| Native search | `AGENT_MODE=hybrid` → heuristic pass-through | Adapter class tested but not connected |
| Human gameplay | No entry point | Deferred design only |

## Production agent

| Modules | Responsibility | Direct evidence |
|---|---|---|
| `src/__init__.py`, `src/agents/__init__.py`, `src/agents/factory.py` | Package boundaries and centralized mode/deck/model factory | Package smoke |
| `src/agents/baseline.py` | Deterministic context fallback | `tests/test_baseline_agent.py` |
| `src/agents/hdi.py` | HDI v1 ordinal policy, factual combat context, and deterministic tie-breaking | `tests/test_hdi_agent.py`, HDI package smoke |
| `src/agents/heuristic.py` | Scoring and board-development ordering | `tests/test_heuristic_agent.py`, CABT golden gameplay |
| `src/agents/search.py` | Bounded adapter scaffold and heuristic pass-through wrapper | `tests/test_search.py`; not integrated into decisions |
| `src/core/candidate.py`, `src/core/parsed_decision.py`, `src/core/policy_decision.py` | Parsed and auditable policy decision vocabulary | Parser, heuristic, and ranking tests |
| `src/core/parser.py`, `src/core/catalog.py` | Observation normalization and card metadata | `tests/test_parser.py`, CABT golden gameplay |
| `src/core/selection.py`, `src/core/selection_generator.py` | Legal index combinations and validation | `tests/test_selection_generator.py` |
| `src/core/state.py`, `src/core/belief.py` | Factual state and separate hidden-state hypotheses | parser and belief tests |
| `src/core/deck.py`, `src/core/prize.py`, `src/core/strategy.py` | Deck roles, PrizeCheck/PrizeMap, strategic context | prize, heuristic, and RFL profile tests |
| `src/core/types.py`, `src/core/exceptions.py`, `src/core/interfaces.py`, `src/core/feature_schema.py`, `src/core/__init__.py` | Shared enums, typed failures, feature contract, interfaces, exports | Imported throughout tests and runtime |

`main.py` is the only competition entry point. It returns the deck for the
initial request, delegates decisions to the selected policy, validates output,
and catches all policy failures with a minimal cardinality-safe fallback.

## Evaluation and release

| Modules | Responsibility | Direct evidence |
|---|---|---|
| `src/eval/__init__.py`, `src/eval/validation.py` | SDK, deck, legality, package, and archive gates | validation, preflight, package tests |
| `src/eval/runner.py`, `src/eval/metrics.py`, `src/eval/gameplay.py` | Match records, aggregates, and gameplay observability | runner, metrics, gameplay tests |
| `src/eval/reporting.py`, `src/eval/comparison.py` | Stable reports and paired/composite comparisons | runner and metrics tests |
| `src/experiments/__init__.py`, `src/experiments/orchestrator.py` | Immutable run directories and manifests | exercised by full-run scripts; end-to-end gate remains open |
| `src/config/__init__.py`, `src/config/loader.py` | YAML includes, deep merge, and supported invariants | `tests/test_config_loader.py` |

The runner currently supports `random`, `first`, `baseline`, `heuristic`, and
self-play opponents. The declared four-opponent release matrix has not yet
been captured in one frozen report.

## Data and replay tooling

| Modules | Responsibility | Direct evidence |
|---|---|---|
| `src/data/__init__.py`, `src/data/downloader.py` | Kaggle dataset download and manifest verification | CLI/preflight usage; network-dependent |
| `src/data/replay_outcomes.py` | W/D/L and termination classification | `tests/test_replay_outcomes.py`, Marimo dashboard |
| `src/data/replay_ingestor.py` | Leakage-safe replay decision datasets | `tests/test_replay_ingestor.py` |
| `src/data/gameplay_annotations.py` | Decision-linked post-hoc review records | `tests/test_gameplay_annotations.py` |
| `src/data/replay_deep_analysis.py` | Deep replay analysis with damage/evolution/bench tracking | Used by investigation report generation |
| `scripts/download_all_replays.py` | Download replays from all Kaggle submissions | Active; produces `data/raw/kaggle/kaggle_gameplay_runs/` |
| `scripts/sync_replays.py` | Sync downloaded replays to dashboard directory | Active; populates `episode_to_submission.json` |
| `scripts/generate_investigation_report.py` | Generate HTML investigation report from replays | Active; produces `perf_reports/INVESTIGATION_REPORT_ABOMASNOW.html` |

Post-hoc annotations describe human review of agent games. They are not live
human gameplay demonstrations.

## RFL and research surface

| Modules | Responsibility | Status |
|---|---|---|
| `src/rfl/__init__.py`, `src/rfl/schemas.py`, `src/rfl/annotations.py` | Versioned traces and expert labels | Tested foundation |
| `src/rfl/feedback.py` | Immutable FeedbackEventV2, insight lifecycle, and active-review priority | `tests/test_ranking.py` |
| `src/rfl/dataset.py`, `src/rfl/rewards.py` | Leakage-safe splits and hybrid rewards | Tested foundation |
| `src/rfl/profiles.py` | Deck-bound heuristic profile loading | Active in `AGENT_MODE=rfl` |
| `src/rfl/promotion.py` | Preference, operational, latency, and declared package gates | Tested; RFL-aware package validation not implemented |
| `src/rfl/optimizer.py`, `src/rfl/visualization.py` | Manual study optimization and optional plots | Runbook-only tooling; not wired to release automation |
| `src/agents/evaluator.py` | Search leaf evaluator | Focused tests; not connected to current bounded-search adapter |
| `src/ranking/__init__.py`, `src/ranking/features.py`, `src/ranking/rankers.py` | Shared leakage-safe vectors and three runtime rankers | ranking and extracted-package tests |
| `src/ranking/dataset.py`, `src/ranking/training.py` | Grouped qid/group-size datasets, native training, metrics, and model manifests | ranking tests; native toy smoke |

The learned runtime is implemented but remains candidate infrastructure, not
release evidence. Promotion requires the holdout and package gates in
[`32_learning_to_rank.md`](32_learning_to_rank.md).

## Non-Python runtime assets

| Area | Canonical location | Status |
|---|---|---|
| Active deck and role profile | `src/artifacts/` | Packaged |
| Native CABT bindings | `cg/` | Vendored package runtime |
| Agent/evaluation profiles | `configs/` | Executable flat schema |
| Operational commands | `scripts/` | Active; inventory in `scripts/README.md` |
| Marimo analysis | `notebooks/` | Active, non-production |
| Investigation reports | `perf_reports/` | Generated HTML; `INVESTIGATION_REPORT_ABOMASNOW.html` is canonical |
| Raw/derived evidence | `data/`, `reports/`, `replays/`, `runs/` | Generated/versioned according to persistence contracts |

## Dead and dormant code policy

- Delete a module when it has no runtime, CLI, notebook, test, or documented
  manual consumer and is not an accepted deferred contract.
- Mark deferred scaffolding here with its re-entry gate; do not describe it as
  active.
- A test-only component is not release-active. It must be linked to a task or
  classified as deferred.
- The 2026-07-30 audit removed the unused `src/logging_setup.py` module and its
  sole `structlog` dependency.
- The same audit removed an RFL archive helper that could pass after silently
  falling back to the heuristic while the RFL files were absent.
- Typed search failures and RFL study utilities remain because their deferred
  contracts and re-entry gates are explicit above.

## 2026-07-30 audit disposition

| Finding | Disposition |
|---|---|
| `src/logging_setup.py` and `structlog` had no consumer | Removed |
| RFL archive helper validated fallback, not RFL loading | Removed; RFL packaging explicitly blocked |
| `TurnPhase`, `MatchResult`, `AgentMode`, `MatchupLabel`, and `TurnTrace` were export-only types with no consumer | Removed; runtime continues to use its actual string fields and `DecisionTrace` |
| `study_is_resumable` had no caller, test, or documented operation | Removed; optimizer-created SQLite artifacts remain inspectable by standard tools |
| `CandidateBuilder` and `src/core/action.py` existed only in stale docs | Documentation corrected to the real parser/candidate/selection flow |
| Config docs described executable YAML as placeholders and specified a different schema | Rewritten to match `ConfigLoader` and current profiles |
| T-001–T-004 referenced removed `FB001-A*` action IDs | Re-linked to `FB-2026-001` |
| H1, H2, and H8 were marked ready despite unmet dependencies and no task owner | Marked blocked |
| Search evaluator and RFL optimization/plot modules are not on the active release path | Retained and explicitly classified as deferred/manual |
| Release code, local evaluation, replay tooling, RFL, and human-capture status were mixed together | Split into the runtime-path sections above |

## Automated drift gate

Run:

```bash
uv run --frozen python scripts/audit_documentation.py
```

The gate checks internal Markdown links and anchors, canonical-file presence,
source-module inventory coverage, stale claims, unique task IDs, and task
summary counts. It also runs in pytest through
`tests/test_documentation_audit.py`.
