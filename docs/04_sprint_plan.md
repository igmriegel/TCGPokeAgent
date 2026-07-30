# Canonical roadmap

> This file owns track-level status, dependencies, and gates. Action-level
> status belongs in [`03_tasks/TASK_INDEX.md`](03_tasks/TASK_INDEX.md).

**Last reviewed:** 2026-07-30

## Immediate objective

Close the heuristic-only release with trustworthy gameplay evidence. Search,
human capture, and learned policies remain outside the immediate release path.

## MVP track

| Sprint | Outcome | Status | Closure gate |
|---|---|---|---|
| S0 | Reproducible environment and preflight | `DONE` | Exact SDK and static checks |
| S1 | Deck, wrapper, and isolated package smoke | `DONE` | Both-side package execution |
| S2 | Factual parser and real observation coverage | `IN_PROGRESS` | Current real golden fixtures |
| S3 | Legal selections and deterministic fallback | `IN_PROGRESS` | Revalidated contexts; zero operational failures |
| S4 | Explainable gameplay heuristic | `IN_PROGRESS` | Board-development rules plus frozen non-regression |
| S5 | Runner, traces, and gameplay metrics | `IN_PROGRESS` | Decision and termination metrics |
| S6 | Immutable experiments and promotion gates | `IN_PROGRESS` | Four-opponent, both-side report |
| S7 | Belief and leaf evaluation | `IN_PROGRESS` | Real-observation invariants |
| S8 | Bounded native search | `DEFERRED` | Verified adapter, latency, cleanup, and non-regression |
| S9 | Frozen heuristic-only release | `IN_PROGRESS` | Final acceptance checklist |

## Heuristic improvement track

| Sprint | Outcome | Status | Dependency |
|---|---|---|---|
| H0 | Complete measurement baseline | `READY` | T-004; S5–S6 |
| H1 | Catalog integrity and deck coverage | `BLOCKED` | H0 |
| H2 | Context-specific scoring | `BLOCKED` | H1 |
| H2A | Continuous board development | `IN_PROGRESS` | Current S4 recovery |
| H3 | Local tactical evaluator | `DEFERRED` | H2 |
| H4 | Belief-derived signals | `DEFERRED` | H1, H3 |
| H5 | Weight optimization | `DEFERRED` | H2–H4 |
| H6 | Supervised ranker | `DEFERRED` | H5 and more data |
| H7 | Matchup-aware profiles | `DEFERRED` | H0, H6 |
| H8 | Hardened heuristic release | `BLOCKED` | H0 and selected improvements |

## Human gameplay track

| Stage | Outcome | Status |
|---|---|---|
| HD0 | Trace schema and privacy contract | `DEFERRED` |
| HD1 | Terminal human player | `DEFERRED` |
| HD2 | Browser player | `DEFERRED` |
| HD3 | Replay annotation UI | `DEFERRED` |
| HD4 | Human/agent disagreement report | `DEFERRED` |
| HD5 | Preference export | `DEFERRED` |

Post-hoc reviews of automated Kaggle matches are implemented separately and do
not count as human demonstrations.

## Research track

R1–R8 remain `DEFERRED` until the MVP comparison and release gates are green:
configurable ablations, linear ranker, LambdaRank, NumPy MLP, PPO, recurrent
belief model, information-set search, and joint deck/policy optimization.

## Promotion rules

Every promoted candidate must:

1. preserve zero `INVALID`, `ERROR`, and `TIMEOUT`;
2. use a frozen deck, opponent matrix, acceptance expression, and artifact;
3. compare both sides against the stable reference;
4. pass package isolation and latency gates;
5. retain a rollback candidate and append evidence to `strategy_notes.md`.

Detailed sprint scope is available under [`02_sprints/`](02_sprints/README.md).
Every non-deferred, non-done track must have an owner in the
[`task index`](03_tasks/TASK_INDEX.md#active-track-coverage).
