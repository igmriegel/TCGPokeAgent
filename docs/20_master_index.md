# Documentation hub

This is the canonical entry point. Each kind of information has one owner;
other documents link to it instead of copying it.

## Start here

| Question | Canonical source |
|---|---|
| What is the current project state? | [`PROJECT_STATUS.md`](PROJECT_STATUS.md) |
| Which code is active, manual, or deferred? | [`CODEBASE_MAP.md`](CODEBASE_MAP.md) |
| What should be done next? | [`03_tasks/TASK_INDEX.md`](03_tasks/TASK_INDEX.md) |
| Which tracks and gates exist? | [`04_sprint_plan.md`](04_sprint_plan.md) |
| Is the release acceptable? | [`19_final_harness_checklist.md`](19_final_harness_checklist.md) |
| Which gameplay rules are active? | [`27_gameplay_rules.md`](27_gameplay_rules.md) |
| What feedback was received? | [`29_gameplay_feedback.md`](29_gameplay_feedback.md) |
| What evidence supports a decision? | [`strategy_notes.md`](strategy_notes.md) |

## Information ownership

| Information | Owner | Update rule |
|---|---|---|
| Current metrics, scores, release decision | `PROJECT_STATUS.md` | Update after verification |
| Code ownership, consumers, tests, maturity | `CODEBASE_MAP.md` | Update with module lifecycle changes |
| Task priority and status | `TASK_INDEX.md` | Update when work changes state |
| Track dependencies and gates | `04_sprint_plan.md` | Update only when planning changes |
| Acceptance criteria | `19_final_harness_checklist.md` and `24_handoff_spec.md` | Check only with evidence |
| Gameplay policy | `27_gameplay_rules.md` | Update with rule implementation |
| Human feedback lifecycle | `29_gameplay_feedback.md` | Append or explicitly supersede |
| Experiment history | `strategy_notes.md` | Append-only evidence; never current status |
| External and internal contracts | Layer contract documents | Update from authoritative source |

## Core contracts

Read these before changing runtime behavior:

1. [`06_harness_spec.md`](06_harness_spec.md) — CABT and package boundary.
2. [`07_core_contracts.md`](07_core_contracts.md) — domain vocabulary.
3. [`10_agent_contracts.md`](10_agent_contracts.md) — policy behavior.
4. [`08_eval_contracts.md`](08_eval_contracts.md) — evaluation records.
5. [`09_experiment_contracts.md`](09_experiment_contracts.md) — experiment identity and promotion.
6. [`22_config_spec.md`](22_config_spec.md) — configuration precedence.
7. [`24_handoff_spec.md`](24_handoff_spec.md) — delivery acceptance.

## Implementation guides

- [`01_architecture.md`](01_architecture.md) — vertical architecture.
- [`11_implementation_order.md`](11_implementation_order.md) — dependency order.
- [`12_core_implementation.md`](12_core_implementation.md) — parser, state, and selections.
- [`13_eval_implementation.md`](13_eval_implementation.md) — runner and metrics.
- [`14_experiment_implementation.md`](14_experiment_implementation.md) — immutable runs.
- [`15_agent_implementation.md`](15_agent_implementation.md) — heuristic, belief, and search.
- [`16_persistence_and_outputs.md`](16_persistence_and_outputs.md) — output layout.
- [`17_operational_support.md`](17_operational_support.md) — diagnostics.
- [`18_config_and_runs.md`](18_config_and_runs.md) — configuration usage.
- [`23_scripts_spec.md`](23_scripts_spec.md) — commands.

## Gameplay and learning

- [`27_gameplay_rules.md`](27_gameplay_rules.md) — active and proposed rules.
- [`28_human_gameplay_capture.md`](28_human_gameplay_capture.md) — live human capture specification.
- [`29_gameplay_feedback.md`](29_gameplay_feedback.md) — canonical feedback records.
- [`30_replay_learning_and_deck_agnostic_engine.md`](30_replay_learning_and_deck_agnostic_engine.md) — replay-learning foundation.
- [`31_competitive_replay_annotations.md`](31_competitive_replay_annotations.md) — post-hoc agent replay reviews.
- [`25_rfl_experiments.md`](25_rfl_experiments.md) — learned-policy experiment runbook.

## Planning detail

The roadmap owns status. These documents only define detailed scope and gates:

- [`02_sprints/mvp_implementation_sprints.md`](02_sprints/mvp_implementation_sprints.md)
- [`02_sprints/heuristic_only_improvement_sprints.md`](02_sprints/heuristic_only_improvement_sprints.md)
- [`02_sprints/post_mvp_research_sprints.md`](02_sprints/post_mvp_research_sprints.md)

## Supporting references

- [`00_harness_overview.md`](00_harness_overview.md) — product summary.
- [`02_experiment_protocol.md`](02_experiment_protocol.md) — comparison protocol.
- [`03_metrics.md`](03_metrics.md) — metric definitions.
- [`05_writeup_outline.md`](05_writeup_outline.md) — final writeup structure.
- [`21_persistence_contracts.md`](21_persistence_contracts.md) — data provenance.
- [`26_sdk_fallback_plan.md`](26_sdk_fallback_plan.md) — capability fallbacks.
- [`../notebooks/README.md`](../notebooks/README.md) — Marimo notebooks.

## Authority

The competition and CABT API define the external protocol. Internal conflicts
resolve in this order: contracts, acceptance criteria, active gameplay rules,
task registry, current status, implementation guides, historical evidence.
Historical evidence records what was true at a past timestamp and never
overrides a newer verified status snapshot.
