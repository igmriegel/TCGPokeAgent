# Canonical index

## Reading to implement

1. [`00_harness_overview.md`](00_harness_overview.md) — product and definition of submittable.
2. [`06_harness_spec.md`](06_harness_spec.md) — actual environment contract.
3. [`07_core_contracts.md`](07_core_contracts.md) — single vocabulary.
4. [`11_implementation_order.md`](11_implementation_order.md) — vertical slices.
5. [`02_sprints/mvp_implementation_sprints.md`](02_sprints/mvp_implementation_sprints.md) — detailed MVP sprints S0–S9.
6. [`03_tasks/sprint_traceability.md`](03_tasks/sprint_traceability.md) — objective-to-code checklist.
7. [`12_core_implementation.md`](12_core_implementation.md) — parser, selection and belief.
8. [`15_agent_implementation.md`](15_agent_implementation.md) — heuristic and search.
9. [`13_eval_implementation.md`](13_eval_implementation.md) — runner and metrics.
10. [`14_experiment_implementation.md`](14_experiment_implementation.md) — experiments.
11. [`24_handoff_spec.md`](24_handoff_spec.md) — handoff and gates.
12. [`25_rfl_experiments.md`](25_rfl_experiments.md) — RFL experiment runbook.
13. [`02_sprints/heuristic_only_improvement_sprints.md`](02_sprints/heuristic_only_improvement_sprints.md) — heuristic-only improvement sprints H0–H8.
14. [`27_gameplay_rules.md`](27_gameplay_rules.md) — living high-level gameplay behavior.
15. [`28_human_gameplay_capture.md`](28_human_gameplay_capture.md) — monitored human demonstrations and insight extraction.
16. [`29_gameplay_feedback.md`](29_gameplay_feedback.md) — canonical gameplay feedback, generalization, and development register.
17. [`30_replay_learning_and_deck_agnostic_engine.md`](30_replay_learning_and_deck_agnostic_engine.md) — replay dataset, generic deck strategy, and learned-policy gates.
18. [`31_competitive_replay_annotations.md`](31_competitive_replay_annotations.md) — post-hoc review of automated Kaggle agent matches.

## Product and research

- [`01_architecture.md`](01_architecture.md) — vertical architecture.
- [`02_experiment_protocol.md`](02_experiment_protocol.md) — comparison and promotion.
- [`03_metrics.md`](03_metrics.md) — metric definitions.
- [`04_sprint_plan.md`](04_sprint_plan.md) — M0 to M8.
- [`02_sprints/post_mvp_research_sprints.md`](02_sprints/post_mvp_research_sprints.md) — detailed post-MVP research sprints R1–R8.
- [`02_sprints/heuristic_only_improvement_sprints.md`](02_sprints/heuristic_only_improvement_sprints.md) — executable non-search improvement backlog H0–H8.
- [`05_writeup_outline.md`](05_writeup_outline.md) — Strategy structure.
- [`strategy_notes.md`](strategy_notes.md) — evidence log.
- [`27_gameplay_rules.md`](27_gameplay_rules.md) — collaboratively maintained gameplay rules and behavioral metrics.
- [`28_human_gameplay_capture.md`](28_human_gameplay_capture.md) — live human play, replay annotation, and preference-data design.
- [`29_gameplay_feedback.md`](29_gameplay_feedback.md) — observed gameplay findings, deck rules, general principles, and traceable actions.
- [`30_replay_learning_and_deck_agnostic_engine.md`](30_replay_learning_and_deck_agnostic_engine.md) — implemented replay-learning foundation and model promotion sequence.
- [`31_competitive_replay_annotations.md`](31_competitive_replay_annotations.md) — decision-linked loss annotations for agent-versus-agent replays.

## Contracts by layer

- [`08_eval_contracts.md`](08_eval_contracts.md)
- [`09_experiment_contracts.md`](09_experiment_contracts.md)
- [`10_agent_contracts.md`](10_agent_contracts.md)

## Operation

- [`16_persistence_and_outputs.md`](16_persistence_and_outputs.md)
- [`17_operational_support.md`](17_operational_support.md)
- [`18_config_and_runs.md`](18_config_and_runs.md)
- [`19_final_harness_checklist.md`](19_final_harness_checklist.md)
- [`21_persistence_contracts.md`](21_persistence_contracts.md) — data and provenance.
- [`22_config_spec.md`](22_config_spec.md) — configuration.
- [`23_scripts_spec.md`](23_scripts_spec.md) — commands.
- [`../notebooks/README.md`](../notebooks/README.md) — lightweight Marimo EDA notebooks.

## Authority

In conflict, the API/competition defines the external protocol; `07` defines the internal vocabulary; `22` defines configuration; `24` defines acceptance. Vision documents do not override these contracts.
