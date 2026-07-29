# MVP implementation sprints

This document turns the vertical slices in [`11_implementation_order.md`](../11_implementation_order.md)
into an executable backlog. It is the operational plan for completing the
submittable MVP. Every sprint has one owner-level outcome, explicit target
files, tests, commands, and a gate. A sprint is complete only when its gate is
green and its evidence is recorded in the run or pull request notes.

The plan is based on the repository state observed on 2026-07-27. Existing
contracts are intentionally treated as requirements, not as evidence that the
corresponding implementation exists.

## How to execute a sprint

1. Read the linked contract before changing code.
2. Implement the smallest vertical slice listed under **Work**.
3. Add or update tests before running the gate.
4. Run the exact commands under **Verification** with the frozen environment.
5. Record command output, commit SHA, SDK version, deck hash, and any failure
   count in the sprint evidence.
6. Do not start the next sprint while the current gate is red, except to create
   a clearly linked blocking fix.

The implementation language and repository artifacts remain English. Sprints
are ordered by dependency; parallel work is allowed only within a sprint after
the contract work is agreed.

## Status vocabulary

- `PLANNED`: no implementation evidence yet.
- `IN_PROGRESS`: implementation or tests are being changed.
- `BLOCKED`: a named external or contract dependency prevents progress.
- `DONE`: all tasks and the gate are complete with recorded evidence.

The status below is a planning baseline, not a claim that a contract document
has been implemented.

## Sprint map

| Sprint | Slice | Outcome | Depends on | Gate |
|---|---|---|---|---|
| S0 | F0 | Reproducible preflight and repository baseline | none | environment and static checks pass |
| S1 | F0 | Real deck, `main.py` adapter, and package smoke | S0 | SDK accepts deck and package runs |
| S2 | F1 | Observation normalization and factual state | S1 | golden parser coverage passes |
| S3 | F1 | Legal selections and total deterministic fallback | S2 | 20 smoke matches, zero operational failures |
| S4 | F2 | Configurable, explainable heuristic policy | S3 | heuristic improves or matches baseline without failures |
| S5 | F3 | Real SDK runner and decision-level traces | S3 | one trace-valid match and smoke matrix |
| S6 | F3 | Replayable experiments, reports, and promotion gates | S5 | full report with immutable artifacts |
| S7 | F4 | Belief construction and state evaluation | S4, S6 | belief invariants and evaluator tests pass |
| S8 | F4 | Bounded short search with safe fallback | S7 | search gate passes without latency regressions |
| S9 | F5 | Frozen submission and isolated validation | S6, S8 | final handoff checklist is green |

## Gameplay recovery audit — 2026-07-29

Validation episode `88828439` proved package compatibility but exposed that the
promoted heuristic selected `END` for every main-phase decision and reached its
only win by deck-out. The prior gates measured legality and completion without
measuring gameplay. Historical evidence below remains useful as an operational
record, but it no longer proves the affected sprint complete.

| Sprint | Revised status | Finding | New completion requirement |
|---|---|---|---|
| S2 | `IN_PROGRESS` | synthetic fields did not match real CABT card and option references | golden real-observation fixtures and resolved `cg` card/attack metadata |
| S3 | `IN_PROGRESS` | repeated Energy-cost prompts were rejected as incomplete selections | regression coverage for repeated Energy/damage prompts and zero runtime failures |
| S4 | `IN_PROGRESS` | `PLAY`, `ATTACH`, and `EVOLVE` scored zero while `END` scored positively | behavioral gate with productive actions, attacks, explicit pass reasons, and paired evidence |
| S5 | `IN_PROGRESS` | traces could diagnose decisions but reports did not aggregate gameplay behavior | action, attack, Knock Out, Prize, donk, and termination-reason metrics |
| S6 | `IN_PROGRESS` | the 400-game report promoted operational completion without detecting non-gameplay | rerun at least 200 games with the new behavioral acceptance gate |
| S7 | `IN_PROGRESS` | evaluator evidence predates the corrected factual state and card resolution | revalidate belief/evaluator against real observations before search |
| S8 | `IN_PROGRESS` | search cannot be promoted over a broken or unstable heuristic | wait for the recovered S4/S7 gates and repeat latency/non-regression evidence |
| S9 | `IN_PROGRESS` | submission `55086902` passed remotely but contains the superseded end-turn policy | rebuild and isolate the gameplay package; remote upload requires separate approval |

Initial recovery evidence:

- the competition `cg` catalog is now used to resolve real cards and attacks;
- the remote main-turn observation is preserved as
  `tests/fixtures/cabt_main_turn.json`;
- repeated `DISCARD_ENERGY` prompts select one legal Energy per SDK call;
- 200 balanced games against `random`: 200/200 completed, 179 wins, 472
  attacks, attacks in 200/200 games, 1,942 productive main actions, and 9.34%
  `END`;
- 10 balanced heuristic self-play games: 10/10 completed, attacks in 10/10
  games, and 7.38% `END`;
- these are recovery smoke results, not the final 200-game promotion evidence.

---

## S0 — Reproducible baseline and preflight

**Status:** `DONE`
**Objective:** make the repository self-checking before gameplay logic is
changed.

### Work

- Confirm `.python-version`, `pyproject.toml`, and `uv.lock` describe Python
  3.12 and `kaggle-environments==1.32.2`.
- Implement a preflight command in `src/eval/validation.py` that checks the
  installed distribution, importability of `cabt`, writable run/output
  directories, and the expected package layout.
- Make preflight errors use one stable exception type and an actionable
  message; do not leak SDK exceptions through the agent runtime.
- Add a small fixture factory for empty, single-option, multiple-option, and
  initial-deck observations.
- Add tests for exact SDK version, missing SDK, invalid deck length, malformed
  observation, and missing output directory.

### Target files

`src/eval/validation.py`, `src/core/exceptions.py`, `tests/conftest.py`,
`tests/test_validation.py`, `scripts/` command wrapper, and `docs/17_operational_support.md`.

### Verification

```bash
uv run --frozen pytest tests/test_validation.py tests/test_config_loader.py -v
uv run --frozen ruff check src/ tests/
uv run --frozen mypy src/
```

### Exit criteria

- The preflight reports the installed SDK version and deck/package checks.
- All negative checks fail deterministically with a project exception.
- No command silently uses a different Python or dependency environment.

### Evidence

Save the preflight output, Python version, SDK version, and current commit SHA.

## S1 — SDK deck, wrapper, and package smoke

**Status:** `DONE`
**Objective:** make the smallest real agent accepted by the installed `cabt`
environment.

### Work

- Obtain the canonical 60-card list from `cabt.first_agent` and store the
  approved copy in `src/artifacts/deck.csv`.
- Validate card count, card identifiers, deck rules, and deterministic deck
  ordering at startup/preflight.
- Replace the placeholder paths in `main.py` with a thin adapter that accepts
  the SDK observation, returns the deck on the initial call, and delegates all
  selections to one persistent policy object.
- Add a runtime output validator for `list[int]` and a last-resort legal
  fallback; stdout must contain only the JSON result.
- Build the package with `scripts/build_package.sh` and test it after extraction
  from a temporary directory.

### Target files

`main.py`, `src/artifacts/deck.csv`, `src/eval/validation.py`,
`scripts/build_package.sh`, `tests/test_main.py`, and package smoke tests.

### Verification

```bash
uv run --frozen python -m src.eval.validation
uv run --frozen pytest tests/ -v
scripts/build_package.sh /tmp/pokemon-agent.tar.gz
tar tzf /tmp/pokemon-agent.tar.gz
```

Run one `cabt` match against `random` on each side and retain the raw result.

### Exit criteria

- The installed SDK accepts the exact deck.
- Initial deck selection and at least one in-game selection execute.
- Extracted package imports without the repository working directory.
- No invalid output, uncaught exception, or non-JSON stdout occurs.

### Evidence

Record deck SHA-256, SDK version, package size, both-side match results, and
the extracted-package command.

### Evidence recorded 2026-07-28

- SDK: `kaggle-environments==1.32.2`
- Deck SHA-256: `1156379af39e71bc83eecb50d1e04c5cc480501d293621fcc89c2d355d99be78`
- Package: `/tmp/pokemon-agent-s1.tar.gz`, 17,115 bytes
- `agent-first`: `DONE/DONE`, rewards `[-1, 1]`, no operational failures
- `agent-second`: `DONE/DONE`, rewards `[-1, 1]`, no operational failures
- Extracted package smoke: initial deck output accepted, 37 tests passing

## S2 — Observation parser and factual state

**Status:** `IN_PROGRESS`
**Objective:** normalize real SDK dataclasses and dictionaries without
inventing hidden information.

### Work

- Implement conversion through the official observation dataclass when the SDK
  provides it, while retaining the original object for future search calls.
- Parse `current`, `logs`, `select`, and `search_begin_input` with explicit
  missing-field behavior.
- Build `GameState`, `PlayerState`, and `PokemonState` from official fields;
  preserve `None` for hidden opponent cards and face-down prizes.
- Build one `Candidate` per option using `enumerate`; never renumber indices.
- Resolve card and attack metadata through a loaded `CardCatalog`, leaving
  unresolved metadata as `None`.
- Add golden fixtures captured from real `cabt` decisions, not only hand-made
  dictionaries.

### Target files

`src/core/parser.py`, `src/core/state.py`, `src/core/candidate.py`,
`src/core/catalog.py`, `src/core/parsed_decision.py`, and `tests/test_parser.py`.

### Verification

```bash
uv run --frozen pytest tests/test_parser.py -v
uv run --frozen pytest tests/ -v
```

Add assertions for hidden hands, `None` cards, all selection fields, and exact
option index preservation.

### Exit criteria

- Dataclass and dictionary payloads produce equivalent factual state.
- Hidden information remains unknown in `GameState`.
- Every candidate maps to exactly one original option index.
- Malformed payloads produce a structured parse failure that the wrapper can
  recover from.

### Evidence recorded 2026-07-28

- Parser tests: 10 passing, including dictionary/dataclass equivalence,
  hidden hands/active/prizes, metadata resolution and malformed payloads
- Full test suite: 43 passing
- Static checks: Ruff and mypy passing

## S3 — Legal selection generation and total fallback

**Status:** `IN_PROGRESS`
**Objective:** guarantee a legal deterministic answer for every observed
`SelectContext`.

### Work

- Implement cardinality generation for zero, one, and multiple selections;
  use stable index-tuple ordering.
- Apply context-specific legality for energy cost, damage counters, targets,
  counts, booleans, setup, attacks, attachments, discard, and movement.
- Separate legality from preference: the generator must not discard a legal
  option because it scores poorly.
- Add a `SelectionValidator` used both before scoring and immediately before
  returning from `main.py`.
- Implement `BaselineAgent` dispatch by context with a deterministic lexicographic
  fallback for unknown contexts.
- Ensure empty selection is returned only where `minCount == 0` and the
  context permits it.
- Add an error boundary around parser, generator, scorer, and output validation.

### Target files

`src/core/selection_generator.py`, `src/core/selection.py`,
`src/agents/baseline.py`, `src/core/exceptions.py`, `main.py`, and tests for
every context family in `docs/15_agent_implementation.md`.

### Verification

```bash
uv run --frozen pytest tests/test_selection_generator.py tests/test_baseline_agent.py -v
uv run --frozen pytest tests/ -v
scripts/run_smoke.sh baseline
```

### Exit criteria

- Every fixture returns a legal `list[int]`.
- Unknown contexts still return a legal deterministic choice.
- A forced parser/scorer exception does not crash the agent.
- The 20-match smoke gate has zero `INVALID`, `ERROR`, and `TIMEOUT`.

### Evidence

Store the context coverage table, smoke report, and one fallback trace per
context family.

### Evidence recorded 2026-07-28

- Commits: `e3ff065` (selection legality), `d27938a` (baseline fallback),
  `a543524` (legality and fallback tests), `4ee3b23` (cabt smoke gate)
- Selection generation covers optional empty, single, multiple, stable
  lexicographic ordering, sparse indices, duplicate rejection, and energy or
  damage count requirements.
- Baseline fallback covers known and unknown contexts, parser failures, and
  unavailable options; output validation is applied at the runtime boundary.
- Focused tests: 15 passing; full suite: 50 passing with one unrelated Python
  deprecation warning.
- Required baseline smoke: 20 matches on each side (40 games total), `40
  completed, 0 failed`; no `INVALID`, `ERROR`, or `TIMEOUT` operational
  failures.

## S4 — Explainable heuristic policy

**Status:** `IN_PROGRESS`
**Objective:** replace the zero-score stub with a configurable policy whose
decisions can be audited and measured.

### Work

- Create normalized feature extraction from factual state, candidates, card
  catalog, and the proposed selection.
- Implement the ordered score components in `docs/15_agent_implementation.md`:
  immediate win, attack efficiency, evolution, energy enablement, bench,
  draw/search, preservation, safe end, and penalties.
- Keep legality out of scoring and make the immediate-win component dominate
  all non-winning actions.
- Load weights and feature flags from the agent profile; validate unknown or
  non-numeric values before execution.
- Attach stable reason codes/text to every ranked selection and tie-break by
  index tuple.
- Add ablation switches with one-family-at-a-time comparison support.

### Target files

`src/agents/heuristic.py`, `src/core/catalog.py`, `src/config/loader.py`,
`configs/agent_heuristic.yaml`, `src/agents/baseline.py`, and heuristic tests.

### Verification

```bash
uv run --frozen pytest tests/ -v
uv run --frozen ruff check src/ tests/
scripts/run_smoke.sh heuristic
```

Construct focused board fixtures proving: win-now priority, KO preference,
attack-enabling energy, useful evolution, key-card preservation, and safe
fallback.

### Exit criteria

- Equal inputs produce equal scores, reasons, and selected indices.
- Every score has at least one reason or an explicit `no_signal` reason.
- Heuristic smoke has no operational regression against baseline.
- A measurable comparison protocol exists before claiming improvement.

### Evidence recorded 2026-07-28

- Commits: `a3a03a1` (heuristic scoring and profile integration), `e053865`
  (heuristic tests), `eca8f11` (comparison protocol)
- Full suite: 56 passing; Ruff and mypy passing.
- Baseline smoke: 40/40 completed, 0 failed.
- Heuristic smoke: 40/40 completed, 0 failed.
- Paired protocol: `scripts/compare_agents.py --matches 10` ran 20 games per
  policy, with baseline `13W/0D/7L` and heuristic `13W/0D/7L` against random.
  This supports parity, not a claim of improvement.

## S5 — Real runner and decision-level observability

**Status:** `IN_PROGRESS`
**Started:** 2026-07-28
**Objective:** execute actual candidate policies through the SDK and preserve
enough trace data to diagnose every match.

### Work

- Replace string agent placeholders in `MatchRunner` with callable policies
  and explicit opponent factories (`random`, `first`, heuristic, self-play).
- Pass the evaluation case identifier (seed) and side into the environment
  using the supported `cabt` API; treat the identifier as metadata because the
  native SDK RNG is not seedable.
- Record match lifecycle, result, turns, status, exception category, and
  duration.
- Record every decision: context, options, selected indices, legality result,
  score/reasons, duration, overage balance, and search fields.
- Make one failed match isolate cleanly while preserving prior and subsequent
  records.
- Implement a real smoke matrix of 20 balanced games and a full matrix of at
  least 200 games.

### Target files

`src/eval/runner.py`, `src/eval/validation.py`, `src/eval/metrics.py`,
`src/core/types.py`, `tests/test_runner.py`, and `scripts/run_smoke.sh`.

### Verification

```bash
uv run --frozen pytest tests/ -v
scripts/run_smoke.sh heuristic
```

Run one fixed evaluation case and validate the normalized match and decision
trace schema. Do not require byte-identical outcomes from repeated native
`cabt` runs; use captured traces as the replay/audit source.

### Exit criteria

- Every match has a stable case identifier, ordered trace, policy/deck/SDK
  metadata, and sufficient raw data for audit or action replay.
- All four required opponents can be selected by configuration.
- A single error is classified and does not abort batch accounting.
- Smoke produces 20 match records, both sides represented, and zero failures.

### Progress evidence recorded 2026-07-28

- `MatchRunner` now executes callable policies against `cabt`, supports random
  and first opponents, preserves seed metadata, isolates failed matches, and
  records decision context, indices, legality, duration, and overage balance.
- Focused runner tests, Ruff, and mypy pass; full suite: 59 passing with one
  unrelated Python deprecation warning.
- Heuristic smoke: 40/40 completed, 0 failed.
- The original same-seed requirement was removed because `cabt` `libcg.so`
  uses C++ `std::random_device` and exposes no seed hook. The revised contract
  keeps the case identifier for matrix accounting and makes captured traces the
  audit/replay source.

### Completion evidence recorded 2026-07-28

- Match traces now include lifecycle timestamps, termination reason, final
  statuses, policy/opponent, SDK version, deck hash, and ordered decisions.
- Decision traces include original option payloads, selected simulator indices,
  legality, score/reason/search fields, duration, and overage balance.
- Opponent factory supports `random`, `first`, `baseline`, `heuristic`, and
  `self_play`; failed matches remain isolated from batch accounting.
- Full suite: 61 passing with one unrelated Python deprecation warning; Ruff
  and mypy pass; heuristic smoke: 40/40 completed, 0 failed.

## S6 — Reproducible experiments and reports

**Status:** `IN_PROGRESS`
**Objective:** make every comparison replayable, immutable, and promotable by
an explicit gate.

### Work

- Migrate YAML files to the schema in `docs/22_config_spec.md`, including
  profile precedence, fixed seed lists, matchups, search settings, and output
  policy.
- Define `ExperimentSpec`, `ExperimentRun`, and a unique experiment/run ID.
- Persist `manifest.json` before execution and write atomic JSONL, JSON, CSV,
  Markdown, replay, and error artifacts under `runs/<experiment>/<run>/`.
- Implement W/D/L, Wilson intervals, percentiles, per-side/per-matchup
  metrics, operational failure counts, and paired comparison.
- Evaluate acceptance expressions and reject incomplete or incompatible runs.
- Update the Docker and local commands so `AGENT_MODE` selects the effective
  candidate configuration rather than only changing a report filename.

### Target files

`src/config/loader.py`, `configs/*.yaml`, `src/experiments/orchestrator.py`,
`src/eval/metrics.py`, `src/eval/comparison.py`, `src/eval/reporting.py`,
`src/eval/runner.py`, and experiment tests.

### Verification

```bash
uv run --frozen pytest tests/ -v
EVAL_CONFIG=eval_small AGENT_MODE=heuristic scripts/run_full.sh heuristic
```

Inspect the resulting manifest and assert that it contains the effective
agent, seed list, matchup matrix, versions, hashes, and acceptance decision.

### Exit criteria

- A completed run never overwrites another run.
- Reports can be regenerated from stored raw records without changing values.
- Incompatible seeds/decks/configurations cannot be compared.
- Full evaluation executes at least 200 games only after smoke is green.

### Evidence recorded 2026-07-29

- Run manifest: `reports/runs/full_heuristic_final/27d3df870485/manifest.json`.
- Report: 400 player-side matches over seeds 42–241, both sides represented;
  239 wins, 161 losses, 0 draws, 0 errors, 0 invalid, 0 timeouts.
- Wilson 95% interval: `[0.5487, 0.6444]`; match-duration p50/p95:
  `270.75/1033.70 ms`. Decision-level aggregation remains part of H0.
- Raw match records are persisted as `matches.jsonl` and the run identity is
  content-addressed so an existing run is never overwritten.

## S7 — Belief builder and state evaluator

**Status:** `IN_PROGRESS`
**Objective:** model hidden information separately from observed facts and
provide a deterministic leaf evaluator for search.

### Work

- Build a known-card multiset from the approved deck and public events.
- Incorporate logs exactly once and track the incorporated event count.
- Fill hidden hand, prize, and opponent-active hypotheses in stable order with
  exact cardinality.
- Validate negative counts, impossible setup, and cardinality closure; mark
  inconsistent beliefs without raising through the runtime.
- Implement `StateEvaluator` using prizes remaining, KO threat, useful HP,
  prepared attackers, energy, bench quality, known hand quality, and deck-out
  risk.
- Make hidden features explicit in traces and never serialize them as facts in
  `GameState` snapshots.

### Target files

`src/core/belief.py`, `src/core/state.py`, `src/agents/heuristic.py` or a new
`src/agents/evaluator.py`, `src/core/interfaces.py`, and belief/evaluator tests.

### Verification

```bash
uv run --frozen pytest tests/test_belief.py tests/test_evaluator.py -v
uv run --frozen pytest tests/ -v
```

### Exit criteria

- Identical input/history yields identical belief and evaluation.
- Inconsistent belief disables search but leaves heuristic fallback available.
- Snapshot output contains facts only; belief is represented separately.
- All hidden-zone cardinality and subtraction invariants are tested.

### Evidence recorded 2026-07-29

- `DefaultBeliefBuilder` preserves factual `GameState` snapshots, produces
  deterministic hypotheses, and marks impossible public card counts.
- `StateEvaluator` returns a deterministic leaf value and disables evaluation
  for inconsistent beliefs.
- Focused and full tests pass.

## S8 — Bounded short search

**Status:** `IN_PROGRESS`
**Objective:** add search as a safe decorator around the heuristic, never as a
new failure mode.

### Work

- Verify the documented Python signatures and native ABI for `search_begin`,
  `search_step`, `search_release`, and `search_end`.
- Implement a project-owned adapter without modifying installed
  `site-packages`; fail closed to the heuristic when the adapter probe fails.
- Implement the search gate: `MAIN`, multiple legal choices, relevant
  candidates, available `search_begin_input`, consistent belief, and at least
  30 seconds of overage.
- Call `search_begin` with the original raw observation and use the supported
  `search_step`, `search_release`, and `search_end` lifecycle.
- Search at most top 3 heuristic candidates, depth 4, and 100 ms total.
- Stop at terminal/end-turn states and evaluate leaves with `StateEvaluator`.
- Put release and `search_end` in `finally` blocks for success, timeout, and
  exception paths.
- On every search failure, return exactly the heuristic top-1 selection and
  record a typed failure.
- Add configuration to disable search without changing policy code.

### Target files

`src/agents/search.py`, a project-owned `cabt` search adapter,
`src/agents/evaluator.py`, `src/core/belief.py`, `src/agents/heuristic.py`,
`src/core/interfaces.py`, `main.py`, and search tests.

### Verification

```bash
uv run --frozen pytest tests/test_search.py tests/test_belief.py -v
EVAL_CONFIG=eval_small AGENT_MODE=hybrid scripts/run_full.sh hybrid
```

Measure p50/p95/p99 decision duration and search coverage. Compare identical
seeds with search off and on.

### Exit criteria

- Search never opens outside the declared gate.
- The adapter probe verifies the installed Python wrapper and native symbols
  without guessing undocumented ctypes signatures.
- All intermediate states are released and `search_end` always executes.
- Maximum search time is 100 ms and fallback latency remains within budget.
- Search has zero operational failures and does not reduce the stable
  heuristic gate; otherwise keep search disabled.

### Progress evidence recorded 2026-07-29

- Gate, depth/top-k/budget limits, typed statistics, and release/end cleanup
  are implemented in `src/agents/search.py`.
- Hybrid smoke: 40/40 completed, 0 failed.
- Search remains disabled because the project has not integrated a verified
  Python adapter for the native lifecycle; no search-approved claim is made.

### Capability correction recorded 2026-07-29

The official `cabt` documentation exposes:

- `search_begin(agent_observation, your_deck, your_prize, opponent_deck,
  opponent_prize, opponent_hand, opponent_active, manual_coin=False)`;
- `search_step(search_id, select)`;
- `search_release(search_id)`;
- `search_end()`.

Local inspection of `kaggle-environments==1.32.2` found that its
`cg/sim.py` wrapper does not bind these functions, while the bundled
`libcg.so` exports `SearchBegin`, `SearchStep`, `SearchRelease`, and
`SearchEnd`. S8 is therefore `IN_PROGRESS`, not blocked: the remaining work is
to verify the native ABI or obtain the matching Python wrapper, implement the
adapter, and execute the real search gate.

Sources verified on 2026-07-29:
[cabt API](https://matsuoinstitute.github.io/cabt/api.html) and
[cabt sim module](https://matsuoinstitute.github.io/cabt/sim.html).

## S9 — Frozen submission and isolated handoff

**Status:** `IN_PROGRESS`
**Objective:** produce the smallest reproducibly validated submission artifact.

### Work

- Freeze deck, source marker, configuration, dependency versions, feature
  schema, and selected policy in a release manifest.
- Extend package validation to reject absolute paths, traversal, external
  imports, oversized archives, and missing root `main.py`/`deck.csv`.
- Build the tarball, extract it into a clean temporary directory, and run both
  initial-deck and in-game smoke using only extracted content.
- Run final matrix on both sides against all required opponents.
- Compute package and artifact hashes and link the final report from
  `strategy_notes.md`.
- Update [`19_final_harness_checklist.md`](../19_final_harness_checklist.md) only
  from evidence, never by assumption.

### Target files

`scripts/build_package.sh`, new package validation command, `src/eval/validation.py`,
`docs/19_final_harness_checklist.md`, `docs/24_handoff_spec.md`, and
`docs/strategy_notes.md`.

### Verification

```bash
uv run --frozen pre-commit run --all-files
scripts/build_package.sh submission.tar.gz
uv run --frozen python -m src.eval.validation --package submission.tar.gz
```

Run the final smoke and full gates from an extracted directory with repository
imports unavailable.

### Exit criteria

- All MVP integrated, search-approved, and submission-approved checklist items
  are green.
- The archive is below 197.7 MiB and has no unsafe paths.
- The extracted artifact passes both-side smoke with zero operational failures.
- Release manifest, hashes, report, and Strategy evidence are linked.

### Progress evidence recorded 2026-07-29

- Isolated package validation passed for `submission.tar.gz`: 38,394 bytes,
  root `main.py`/`deck.csv`, 60-card deck, no unsafe paths.
- Full evaluation report: `reports/runs/full_heuristic_final/27d3df870485/`;
  400 matches, 239 wins, 0 operational failures.
- Final release is frozen as heuristic-only; search approval is intentionally
  excluded from this release scope.
- Gameplay-recovery package `ee0a20585a42` is 513,976 bytes, includes the
  competition `cg` catalog, passed the CABT file-agent gate, and completed
  remote validation as submission `55088176`, episode `88836243`, without
  stdout/stderr. Its initial public score was `600.0`; this is provisional
  until Kaggle finishes any additional evaluation.

### Heuristic-only release decision recorded 2026-07-29

The project accepts a heuristic-only S9 release. S8 is not a prerequisite for
this explicitly scoped release because search is disabled and documented as an
unintegrated optional capability. S8 may continue independently after the
project-owned adapter and lifecycle tests are complete.

## Cross-sprint definition of done

The MVP is complete only when S0–S9 are `DONE`. A passing unit test suite alone
does not satisfy the project: the SDK, both sides, operational failure gate,
full report, and extracted package are mandatory evidence.
