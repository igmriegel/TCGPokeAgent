# Handoff specification

## Frozen decisions

- Python 3.12 and dependencies from `pyproject.toml`/`uv.lock`;
- `kaggle-environments==1.32.2`;
- official 60-card deck;
- `Observation` input and `list[int]` output;
- `Selection` as the decision unit;
- factual `GameState`, separate hypothetical `BeliefState`;
- deterministic legal fallback;
- heuristic before optional search or learned policies;
- zero `INVALID`, `ERROR`, and `TIMEOUT`;
- package validation after clean extraction.

## Required delivery

1. source and configuration for the selected policy;
2. root `main.py` and `deck.csv`;
3. frozen release manifest with code, deck, SDK, config, and package hashes;
4. focused tests and quality-gate results;
5. both-side frozen evaluation report;
6. isolated package smoke;
7. remote submission receipt when promotion is requested;
8. rollback reference;
9. evidence-log entry for experimental claims.

## Acceptance

The handoff is complete only when every applicable row in
[`19_final_harness_checklist.md`](19_final_harness_checklist.md) is `PASS`.
Search and learned-model gates may be `N/A` only when explicitly excluded from
the release scope.

Task status belongs in [`03_tasks/TASK_INDEX.md`](03_tasks/TASK_INDEX.md);
current release status belongs in [`PROJECT_STATUS.md`](PROJECT_STATUS.md).
