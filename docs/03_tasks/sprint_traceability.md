# Sprint traceability

This compatibility page no longer owns status. Use:

- [`TASK_INDEX.md`](TASK_INDEX.md) for executable work and counts;
- [`../04_sprint_plan.md`](../04_sprint_plan.md) for track status and gates;
- [`../20_master_index.md`](../20_master_index.md) for contract navigation.

| Sprint area | Primary implementation | Primary verification |
|---|---|---|
| S0–S1 | `src/eval/validation.py`, `main.py`, package scripts | Preflight and isolated package smoke |
| S2–S3 | `src/core/parser.py`, selection generator, baseline | Golden observations and legality tests |
| S4 | `src/agents/heuristic.py` | Focused rankings and gameplay regressions |
| S5–S6 | `src/eval/`, `src/experiments/` | Trace schema and frozen comparison |
| S7 | `src/core/belief.py`, evaluator | Cardinality and factual-separation tests |
| S8 | `src/agents/search.py`, native adapter | Lifecycle, timeout, fallback, latency |
| S9 | package and submission scripts | Final checklist and extracted-content smoke |
| H0–H8 | heuristic, metrics, profiles, RFL | Paired non-regression and package gates |
| HD0–HD5 | future human capture components | Live trace, privacy, and leakage gates |
