# MVP sprint specifications

These specifications define scope and closure gates for S0–S9. Current status
is in [`../04_sprint_plan.md`](../04_sprint_plan.md); executable work is in
[`../03_tasks/TASK_INDEX.md`](../03_tasks/TASK_INDEX.md); historical evidence
is in [`../strategy_notes.md`](../strategy_notes.md).

## Execution rule

Freeze the applicable inputs and acceptance expression before running a gate.
Passing unit tests proves implementation integrity, not gameplay promotion.
Never promote a sprint from evidence belonging to an earlier policy version.

## S0 — Reproducible baseline and preflight

**Objective:** reproduce the exact Python, SDK, dependency, and filesystem
environment.

**Scope:** frozen `uv` environment, SDK version probe, deck/output checks,
actionable errors, and negative preflight tests.

**Gate:** preflight, Ruff, mypy, and focused tests pass from a clean checkout.

## S1 — SDK deck, wrapper, and package smoke

**Objective:** produce the smallest portable CABT agent package.

**Scope:** official 60-card deck, `main.py` stdin/stdout adapter, deterministic
mode selection, package allowlist, clean extraction, and both-side smoke.

**Gate:** extracted package runs using only packaged content with zero
operational failures.

## S2 — Observation parser and factual state

**Objective:** normalize CABT observations without inventing hidden facts.

**Scope:** preserve raw observations; parse state, logs, selections, and search
input; preserve `None` for hidden information; resolve catalog metadata; retain
simulator option indices.

**Gate:** real golden fixtures cover observed shapes, hidden fields, malformed
input, and current Kaggle replay decisions.

## S3 — Legal selection generation and total fallback

**Objective:** return a legal deterministic `list[int]` for every decision.

**Scope:** zero/one/many selections, sparse indices, cardinality, repeated
Energy and damage costs, every observed context family, parser failure, and
runtime output validation.

**Gate:** focused legality tests and both-side smoke complete with zero
`INVALID`, `ERROR`, and `TIMEOUT`.

## S4 — Explainable heuristic policy

**Objective:** rank legal selections with deterministic, traceable gameplay
signals.

**Scope:** productive actions, attack value, Evolution, Energy, board
development, draw/search, preservation, safe ending, penalties, and explicit
reasons. Required development must be sequenced before non-winning terminal
actions.

**Gate:** focused ranking fixtures plus frozen comparison show no operational
or win-rate regression against the stable reference.

## S5 — Real runner and decision-level observability

**Objective:** execute real CABT matches and preserve auditable decisions.

**Scope:** opponent factories, side/case metadata, isolated failures, lifecycle
records, raw options, selected indices, legality, score reasons, duration,
overage, gameplay actions, Knock Outs, Prizes, donks, and termination causes.

**Gate:** trace schema is complete and a both-side smoke matrix has zero
operational failures.

## S6 — Reproducible experiments and reports

**Objective:** make comparisons immutable, attributable, and promotable.

**Scope:** content-addressed run identity, manifest, JSONL records, aggregate
metrics, Wilson interval, decision latency, opponent matrix, acceptance
expression, comparison, and rollback reference.

**Gate:** at least 200 matches across the declared both-side opponent matrix,
with complete metadata and no overwritten artifacts.

## S7 — Belief builder and state evaluator

**Objective:** model hidden information separately from factual state and
evaluate search leaves safely.

**Scope:** deterministic known-card subtraction, hidden-zone cardinality,
inconsistency handling, public-event incorporation, and deterministic state
evaluation.

**Gate:** real-observation invariants pass; inconsistent belief disables search
without affecting heuristic fallback; factual snapshots contain no hypotheses.

## S8 — Bounded short search

**Objective:** decorate the heuristic with safe, bounded CABT search.

**Scope:** verified native adapter, `MAIN` gate, top three candidates, depth
four, 100 ms budget, overage cutoff, release/end cleanup, typed failures, and
exact heuristic fallback.

**Gate:** lifecycle, latency, leak, and failure tests pass; paired comparison
shows no regression. If the adapter is unavailable, search remains disabled and
does not block a heuristic-only release.

## S9 — Frozen submission and isolated handoff

**Objective:** freeze and validate the release artifact.

**Scope:** release manifest, deck/code/config hashes, package safety and size,
clean extraction, both-side smoke, report links, rollback, and remote receipt.

**Gate:** the applicable sections of
[`../19_final_harness_checklist.md`](../19_final_harness_checklist.md) are green.

## Cross-sprint completion

A sprint is complete only when:

1. code and failure paths have tests;
2. required quality gates pass;
3. declared evaluation evidence belongs to the current version;
4. the task registry is updated;
5. a release-level change updates `PROJECT_STATUS.md`;
6. experimental evidence is appended to `strategy_notes.md`.
