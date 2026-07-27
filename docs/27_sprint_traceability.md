# Sprint traceability and implementation checklist

This page connects project objectives, executable sprints, source locations,
tests, and acceptance documents. It is the checklist for a human or coding
agent starting work in a fresh checkout.

## MVP traceability

| Objective | Sprint | Primary code | Required tests/evidence | Acceptance source |
|---|---|---|---|---|
| Reproducible SDK and package baseline | S0 | `src/eval/validation.py` | preflight, exact SDK, negative checks | `06`, `19` |
| Approved deck and initial wrapper | S1 | `main.py`, `src/artifacts/deck.csv` | both-side SDK smoke, extracted package | `06`, `24` |
| Factual observation/state model | S2 | `src/core/parser.py`, `state.py` | real golden fixtures, hidden fields | `07`, `12` |
| Legal selection combinations | S3 | `selection.py`, `selection_generator.py` | cardinality, energy, damage, indices | `07`, `15` |
| Total deterministic fallback | S3 | `src/agents/baseline.py`, `main.py` | all context families, 20 smoke matches | `10`, `19` |
| Explainable heuristic | S4 | `src/agents/heuristic.py` | focused ranking and ablations | `10`, `15` |
| Real match execution | S5 | `src/eval/runner.py` | reproducibility and failure isolation | `08`, `13` |
| Immutable experiment artifacts | S6 | `src/experiments`, `src/eval/reporting.py` | manifest, JSONL, reports, gates | `09`, `14`, `16` |
| Hidden-information model | S7 | `src/core/belief.py`, evaluator | cardinality and consistency | `07`, `12`, `15` |
| Bounded search | S8 | `src/agents/search.py` | lifecycle, timeout, fallback, comparison | `08`, `10`, `15` |
| Submission readiness | S9 | `scripts/`, `src/eval/validation.py` | extracted package and final matrix | `19`, `24` |

## Post-MVP traceability

| Roadmap milestone | Sprint | Promotion evidence |
|---|---|---|
| M1 configurable heuristics/ablations | R1 | rule-level paired report |
| M2 linear NumPy ranker | R2 | temporal holdout and model hash |
| M3 LightGBM LambdaRank | R3 | SHAP/ablation and isolated package |
| M4 NumPy MLP fallback | R4 | >=95% retained gain and latency |
| M5 PPO | R5 | masked actions, curriculum, fixed pool |
| M6 GRU-PPO/belief model | R6 | calibrated hidden-state gain |
| M7 ISMCTS/PUCT | R7 | search trace, budget, justified gain |
| M8 joint deck/policy/priors | R8 | robust pool and rollback |

## Agent handoff checklist

Before editing:

- [ ] Read [`AGENTS.md`](../AGENTS.md).
- [ ] Read the relevant contract in [`20_master_index.md`](20_master_index.md).
- [ ] Check `git status --short` and preserve unrelated user changes.
- [ ] Identify the current sprint and its dependency gate.

While editing:

- [ ] Keep `GameState` factual and `BeliefState` hypothetical.
- [ ] Preserve simulator option indices.
- [ ] Keep fallback legal for every context.
- [ ] Add tests for every new behavior and failure path.
- [ ] Keep configuration, seeds, hashes, and reports reproducible.

Before closing:

- [ ] Run the sprint's exact verification commands.
- [ ] Run `uv run --frozen pre-commit run --all-files` when source changes.
- [ ] Record evidence and update the sprint status.
- [ ] Update [`19_final_harness_checklist.md`](19_final_harness_checklist.md)
  only when the corresponding evidence exists.
- [ ] Use an atomic commit with the required `type: description` format.

## Current baseline

As of 2026-07-27, the repository has contract documents, scaffolding, basic
unit tests, and data integrity checks. The operational sprint statuses remain
`PLANNED` until their implementation gates are executed. In particular, a
passing scaffold test suite is not evidence for real `cabt` match execution,
heuristic quality, search correctness, or submission readiness.

