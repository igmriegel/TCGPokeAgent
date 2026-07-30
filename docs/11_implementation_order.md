# MVP dependency order

This document defines dependency order only. Current status is in
[`PROJECT_STATUS.md`](PROJECT_STATUS.md); executable work is in
[`03_tasks/TASK_INDEX.md`](03_tasks/TASK_INDEX.md).

| Slice | Capability | Depends on | Gate |
|---|---|---|---|
| F0 | Environment, SDK, deck, wrapper, isolated package | None | Structural validity and zero failures |
| F1 | Parser, factual state, candidates, legal selections, fallback | F0 | Real fixtures and zero invalid decisions |
| F2 | Explainable heuristic | F1 | Focused behavior plus non-regression |
| F3 | Runner, traces, metrics, immutable reports | F1 | Reproducible full matrix |
| F4 | Belief, evaluator, bounded search | F2, F3 | Latency, cleanup, fallback, and non-regression |
| F5 | Frozen release | F3; F4 only when search is enabled | Acceptance checklist and isolated package |

## Rules

- Finish the gate for a dependency before promoting a dependent slice.
- A heuristic-only release may omit F4 search when search is explicitly
  disabled and documented.
- Passing tests proves implementation integrity, not gameplay promotion.
- Operational completion against one opponent does not replace the declared
  opponent matrix.
- Evidence is immutable; status is updated only in the canonical roadmap and
  task index.
