# Heuristic-only improvement sprints

This backlog improves the frozen heuristic-only release without depending on
the pending SDK search adapter. It is the execution plan for work that can
proceed while S8 remains in progress. Search is not reimplemented as a game
engine locally and no sprint may mix hypothetical state into `GameState`.

## Operating rules

- Keep the current heuristic release available as the rollback candidate.
- Preserve simulator option indices and deterministic legal fallback.
- Freeze seeds, deck, opponents, SDK version, and acceptance expressions before
  each comparison.
- Separate training, validation, and temporal holdout data.
- Promote only with zero `INVALID`, `ERROR`, and `TIMEOUT`.
- Record decision-level latency, fallback usage, and feature coverage.
- Do not claim search improvement from tactical estimates or learned rankers.

## Sprint map

| Sprint | Outcome | Depends on | Gate |
|---|---|---|---|
| H0 | Complete measurement and opponent baseline | S6, S9 | four-opponent matrix and decision metrics |
| H1 | Complete card and attack catalog | H0 | deck coverage and catalog integrity |
| H2 | Context-specific heuristic policies | H1 | focused context tests and non-inferiority |
| H2A | Continuous Snover/Abomasnow development | current S4 recovery | zero skipped required development actions |
| H3 | Local tactical feature evaluator | H2 | tactical fixtures and latency gate |
| H4 | Belief-derived scoring features | H1, H3 | calibration and factual separation |
| H5 | Reproducible weight optimization | H2–H4 | validation gain and holdout discipline |
| H6 | Dependency-light supervised ranker | H5 | paired holdout non-inferiority or gain |
| H7 | Matchup-aware profiles | H0, H6 | robust per-matchup result |
| H8 | Hardened heuristic-only promotion | H5–H7 | final matrix, package, manifest, rollback |

## Cross-cutting HD track — Human demonstration capture

**Status:** `IDEA`

The HD0–HD5 stages in
[`28_human_gameplay_capture.md`](../28_human_gameplay_capture.md) define a
parallel track for observing live human decisions and annotating replays. Human
traces may propose H2 rules, H5 weight hypotheses, or H6 preference examples,
but they do not bypass the frozen validation and holdout gates. Live and
post-hoc decisions remain separate datasets.

---

## H0 — Measurement baseline and complete opponent matrix

**Status:** `PLANNED`

**Objective:** establish trustworthy measurements before changing policy
behavior.

### Work

- Run both sides against `random`, `first`, `heuristic`, and self-play.
- Add aggregate metrics by side, matchup, and `SelectContext`.
- Aggregate decision p50, p95, p99, and maximum latency separately from match
  duration.
- Count fallback calls, parser failures, unknown catalog entries, no-signal
  scores, belief inconsistencies, and score margins.
- Persist the declared opponent matrix in the run manifest before execution.
- Fix report terminology so match and decision durations cannot be confused.

### Target files

`src/eval/runner.py`, `src/eval/metrics.py`, `src/eval/reporting.py`,
`src/experiments/orchestrator.py`, `configs/eval_full.yaml`, and evaluation
tests.

### Verification

```bash
uv run --frozen pytest tests/ -v
AGENT_MODE=heuristic scripts/run_full.sh heuristic configs/eval_full.yaml
```

### Exit criteria

- All four opponents and both sides appear in the manifest and report.
- At least 200 valid player-side matches complete with zero operational
  failures.
- Decision and match latency are reported independently.
- A frozen H0 report becomes the comparison baseline for H1–H8.

---

## H1 — Complete card, attack, and deck catalog

**Status:** `PLANNED`

**Objective:** let the policy understand the semantic value of every card and
attack used by the frozen deck.

### Work

- Inventory card identifiers in the deck and observations.
- Record HP, stage, evolution chain, card category, energy type, retreat cost,
  attacks, costs, damage, and relevant effects.
- Represent Trainer, Item, Supporter, Stadium, Tool, and Energy roles.
- Add deck-specific tags for key pieces, search targets, discard value,
  recovery value, and synergy groups.
- Validate duplicate identifiers, missing references, malformed attacks, and
  evolution cycles.
- Record catalog coverage in decision traces.

### Target files

`src/core/catalog.py`, `src/artifacts/`, catalog configuration/data files, and
`tests/test_catalog.py`.

### Verification

```bash
uv run --frozen pytest tests/test_catalog.py -v
uv run --frozen python -m src.eval.validation
```

### Exit criteria

- Every card in the frozen deck resolves deterministically.
- Every attack exposed for the deck has cost and damage metadata.
- Unknown external cards remain safe and produce an explicit trace signal.
- Catalog loading adds no operational failures.

---

## H2 — Context-specific heuristic policies

**Status:** `PLANNED`

**Objective:** replace generic option scoring with auditable behavior for each
decision family.

### Work

- Define independent feature groups for setup, attack, target selection,
  evolution, energy attachment, retreat, switching, bench development,
  draw/search, discard, forced movement, and end-turn decisions.
- Keep legality in the generator/validator and preference in the scorer.
- Add deterministic context-specific tie-breaking.
- Add key-resource preservation and forced-cost handling.
- Emit stable reason codes and score components for every ranked selection.
- Retain total fallback for unknown contexts.

### Target files

`src/agents/heuristic.py`, context scorer modules under `src/agents/`,
`configs/agent_heuristic.yaml`, and focused heuristic tests.

### Verification

```bash
uv run --frozen pytest tests/test_heuristic_agent.py tests/test_context_scorers.py -v
AGENT_MODE=heuristic scripts/run_smoke.sh heuristic
```

### Exit criteria

- Every observed context has a focused ranking fixture.
- Equal inputs produce equal scores, reasons, and indices.
- Unknown contexts remain legal and deterministic.
- The H0 matrix shows no operational or win-rate regression.

---

## H2A — Continuous Snover/Abomasnow board development

**Status:** `IN_PROGRESS`

**Priority:** `P0`

**Source:** human review of Kaggle submission `55088176` on 2026-07-29 found
losses in which the agent stopped placing Pokémon on the Bench and failed to
continue the Snover-to-Mega-Abomasnow development line.

**Objective:** make board development a repeated pre-attack obligation for the
frozen Abomasnow deck instead of a one-time, fixed-score preference.

### Diagnosed gap

The current `MAIN` scorer gives a legal Snover play approximately 330 points,
while Hammer Lanche can receive approximately 500 points. Because attacking
ends the turn, the policy can select damage before placing the available
Snover and never revisit board development. Evolution has a high generic
score, but the scorer does not explicitly model the number of Snover and Mega
Abomasnow ex in play, open Bench slots, or backup-attacker readiness.

### Work

- Add factual board-development features for Bench occupancy, open slots,
  Snover count, Mega Abomasnow ex count, eligible evolution targets, and
  prepared backup attackers.
- Add a deck-specific pre-attack ordering layer: legal Snover plays and
  Snover-to-Mega-Abomasnow evolutions outrank non-winning attacks.
- Re-evaluate development after every `MAIN` action; do not use a permanent
  "setup complete" flag.
- Keep an immediate game-winning action above development and preserve all SDK
  legality and `benchMax` constraints.
- Add stable reason codes for development, evolution, immediate-win override,
  and full-Bench blocking.
- Add golden observations from the Kaggle failure pattern and synthetic
  boundary fixtures.
- Extend decision traces and reports with skipped-development counters,
  Snover-to-Abomasnow conversion, backup-attacker readiness, and board-loss
  termination.
- Re-run the behavioral smoke and the frozen comparison matrix before
  promoting the change or creating another submission.

### Target files

`src/agents/heuristic.py`, `src/core/parser.py`, `src/agents/evaluator.py`,
`src/eval/runner.py`, `src/eval/metrics.py`, focused heuristic tests, and real
observation fixtures.

### Verification

```bash
uv run --frozen pytest tests/test_heuristic_agent.py tests/test_cabt_golden_gameplay.py -v
AGENT_MODE=heuristic scripts/run_smoke.sh heuristic
```

### Exit criteria

- With an open Bench slot, every legal Snover play is selected before a
  non-winning attack or `END`.
- Every legal Snover-to-Mega-Abomasnow evolution is selected before a
  non-winning attack or `END`.
- Consecutive `MAIN` prompts prove that development is re-evaluated after each
  action.
- Immediate game wins still dominate and full-Bench states remain valid.
- Evaluation reports zero skipped required development actions.
- The frozen match matrix has zero `INVALID`, `ERROR`, and `TIMEOUT`, and does
  not regress the accepted gameplay baseline.

---

## H3 — Local tactical feature evaluator

**Status:** `PLANNED`

**Objective:** estimate immediate tactical consequences without pretending to
be the SDK simulator.

### Work

- Estimate immediate damage, KO availability, useful HP, energy after an
  action, retreat affordability, prepared attackers, and bench development.
- Estimate one-turn KO exposure and resource tempo from factual state only.
- Add deck-out risk, prize pressure, and premature-end penalties.
- Keep estimates as scorer features; never serialize them as simulator facts.
- Version the tactical feature schema and trace every component.

### Target files

`src/agents/evaluator.py`, `src/agents/heuristic.py`,
`src/core/catalog.py`, and `tests/test_tactical_evaluator.py`.

### Verification

```bash
uv run --frozen pytest tests/test_tactical_evaluator.py -v
uv run --frozen pytest tests/ -v
```

### Exit criteria

- Fixtures prove KO, survival, energy, retreat, and tempo ordering.
- Tactical evaluation is deterministic and finite for malformed/partial state.
- Decision p95 remains inside the declared non-search budget.
- The full matrix is non-inferior to H0.

---

## H4 — Belief-derived scoring features

**Status:** `PLANNED`

**Objective:** use hidden-information estimates as explicit score signals while
preserving factual separation.

### Work

- Estimate remaining energy, evolution pieces, recovery cards, and critical
  resources from the frozen deck and public events.
- Add draw/search hit probability, deck-out risk, and opponent-response bands.
- Incorporate each public log event exactly once.
- Calibrate or bucket uncertain estimates instead of exposing false precision.
- Disable belief features on inconsistency and return the factual heuristic.
- Trace belief feature values separately from factual snapshots.

### Target files

`src/core/belief.py`, `src/agents/evaluator.py`,
`src/agents/heuristic.py`, and belief/calibration tests.

### Verification

```bash
uv run --frozen pytest tests/test_belief.py tests/test_evaluator.py -v
uv run --frozen pytest tests/ -v
```

### Exit criteria

- Hidden-zone cardinality closes for all fixtures.
- Repeated history does not double-count events.
- Inconsistent belief never crashes or changes factual state.
- Belief-on is non-inferior to belief-off on the frozen matrix.

---

## H5 — Reproducible heuristic weight optimization

**Status:** `PLANNED`

**Objective:** tune context and feature weights without overfitting the final
holdout.

### Work

- Freeze train, validation, and temporal holdout match identifiers.
- Optimize weights with deterministic search or Optuna when available.
- Penalize operational failures and latency violations as hard constraints.
- Run one-family-at-a-time ablations after optimization.
- Prefer the simplest profile inside the confidence bound.
- Save trials, data/config hashes, best profile, rollback profile, and report.

### Target files

`src/rfl/optimizer.py`, `src/rfl/profiles.py`, heuristic profiles under
`configs/decks/`, experiment scripts, and optimizer tests.

### Verification

```bash
uv run --frozen pytest tests/test_rfl.py tests/test_rfl_promotion.py -v
```

Run the frozen validation matrix for all finalists and evaluate the temporal
holdout once.

### Exit criteria

- The study can be reproduced from its manifest.
- Train, validation, and holdout IDs do not overlap.
- The selected profile is non-inferior or better than H0 with zero failures.
- The previous heuristic profile remains a tested rollback.

---

## H6 — Dependency-light supervised selection ranker

**Status:** `PLANNED`

**Objective:** rank legal selections from validated traces without SDK search.

### Work

- Version a candidate-ranking dataset with one group per decision.
- Build labels from outcomes and expert preferences without future-state
  leakage.
- Implement deterministic feature ordering and a regularized linear NumPy
  ranker first.
- Preserve heuristic fallback for absent models, unknown features, non-finite
  scores, and invalid output.
- Export only small inference artifacts into the package.
- Compare heuristic, optimized heuristic, and ranker on identical holdout cases.

### Target files

New ranker modules under `src/agents/` or `src/rfl/`, dataset/schema modules,
model artifacts, runtime configuration, and ranker tests.

### Verification

Test dataset leakage, serialization round-trip, feature ordering, malformed
models, deterministic inference, latency, package size, and isolated loading.

### Exit criteria

- The model never changes the legal candidate set.
- Inference remains within the heuristic-only decision budget.
- Promotion requires paired holdout non-inferiority or improvement.
- Any failure returns the optimized heuristic decision exactly.

---

## H7 — Matchup-aware profiles

**Status:** `PLANNED`

**Objective:** improve robustness across opponent styles without fragile
mid-match guessing.

### Work

- Define stable matchup labels from allowed public observations.
- Start with configured opponent profiles; add runtime classification only when
  calibration evidence exists.
- Train or tune profiles for aggressive, control, evolution, energy-heavy,
  wide-bench, and deck-out patterns.
- Use the general profile below a confidence threshold.
- Report per-matchup gain, worst-matchup result, and profile-selection accuracy.

### Target files

Profile configuration, `src/agents/heuristic.py`, optional classifier modules,
evaluation grouping, and matchup tests.

### Verification

Run the frozen four-opponent matrix with the general profile and every candidate
profile. Verify fallback to the general profile on unknown opponents.

### Exit criteria

- No declared matchup regresses beyond the configured tolerance.
- Worst-matchup performance improves or remains non-inferior.
- Profile selection is deterministic and traceable.
- Package and latency gates remain green.

---

## H8 — Hardened heuristic-only promotion

**Status:** `PLANNED`

**Objective:** freeze the best non-search candidate as a reproducible,
competition-ready release.

### Work

- Freeze deck, catalog, feature schema, profile/model, source marker, SDK, and
  evaluation matrix.
- Aggregate decision and match metrics with all failure categories.
- Build a normalized archive with deterministic metadata where practical.
- Validate root files, safe paths, size, imports, initial deck, and in-game
  decisions using only extracted content.
- Record archive, code, deck, catalog, configuration, and model hashes.
- Link the final report and release decision from `strategy_notes.md`.
- Preserve the previous release archive and manifest as rollback.

### Target files

`scripts/build_package.sh`, package validation, release manifest generation,
`docs/19_final_harness_checklist.md`, and `docs/strategy_notes.md`.

### Verification

```bash
uv run --frozen pre-commit run --all-files
scripts/build_package.sh submission.tar.gz
uv run --frozen python -m src.eval.validation --package submission.tar.gz
```

Run the frozen full matrix and extracted-package smoke before accepting the
manifest.

### Exit criteria

- All heuristic-only checklist items are green.
- The four-opponent, both-side matrix has zero operational failures.
- The promoted candidate is non-inferior or better than the previous release.
- The release manifest contains complete hashes, evidence, and rollback.

## Program completion gate

The heuristic-only improvement program is complete when H0–H8 are `DONE` or
explicitly `REJECTED` with evidence. S8 remains independently `IN_PROGRESS`
until the documented native lifecycle is available through a verified Python
adapter and passes its gates. Completion of H0–H8 must not be presented as
search approval.
