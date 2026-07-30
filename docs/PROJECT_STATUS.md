# Project status

> Canonical current-state snapshot. Update this file when a gate, release,
> remote score, or active priority changes. Historical evidence belongs in
> [`strategy_notes.md`](strategy_notes.md), not here.

**Last verified:** 2026-07-30

**Code baseline:** `main`; exact revisions are preserved in Git and release
manifests rather than copied into this self-changing status page

**Current release:** heuristic-only; search disabled

## Executive summary

The agent is operational, packaged, and remotely accepted by Kaggle. The
heuristic plays productive actions and completes evaluation without operational
failures. The project is not ready to claim a fully closed MVP because the
four-opponent matrix, decision-level gameplay metrics, several feedback
validation gates, and the final checklist remain open.

The latest candidate must not be promoted: submission `55093119` currently
scores below the accepted gameplay-recovery submission `55088176`.

## Verified snapshot

| Area | Current evidence | Decision |
|---|---|---|
| Quality | 101 tests pass; Ruff, formatting, mypy, and documentation drift audit pass | Green |
| Local evaluation | 400 matches vs `random`: 239W/0D/161L, 59.75% win rate, zero operational failures | Operational baseline only |
| Kaggle stable candidate | `55088176`: 516.3 public score | Keep as remote reference |
| Kaggle experimental candidate | `55093119`: 503.2 public score | Do not promote |
| Package | Isolated heuristic-only package validation passed | Usable rollback artifact |
| Search | Native lifecycle lacks a verified project Python adapter | Disabled and deferred |
| Raw replay corpus | 85 valid replays; 82 attributable matches; 62 distinct opponent decks | Source snapshot is current |
| Derived replay dataset | 31 matches, 2,047 decisions, 27 opponent decks | Stale; rebuild required |
| Human gameplay capture | No live human match captured | HD0–HD5 remain deferred |
| Documentation integrity | All `src` modules inventoried; internal links, task IDs, counts, and stale claims checked automatically | Living gate |

The local 400-match artifact reports `agent_mode: baseline` although its path
and project evidence describe the heuristic evaluation. Treat the result as
operational evidence until that metadata discrepancy is resolved.

## Delivery status

| Track | Status | What is complete | What closes the track |
|---|---|---|---|
| MVP S0–S1 | Done | Environment, SDK, deck, wrapper, package smoke | None |
| MVP S2–S7 | In progress | Core implementation and focused tests exist | Revalidate real observations, gameplay metrics, opponent matrix, and belief evidence |
| Search S8 | Deferred | Gate, limits, fallback, and cleanup logic exist | Verified native adapter plus latency/non-regression gate |
| Release S9 | In progress | Heuristic-only package and remote submissions exist | Final checklist and stable promotion evidence |
| Feedback FB-2026-001–003 | Implemented, not validated | Core rules and focused tests exist | Six open validation/measurement actions |
| Human capture HD0–HD5 | Deferred | Design only; post-hoc agent replay review is separate | First live human trace and staged delivery gates |
| Learned policies | Not promoted | Replay-learning foundation exists | Data volume, temporal holdout, paired evaluation, and package gates |

## Current decisions

1. Keep `55088176` as the remote comparison reference.
2. Do not submit another candidate before the frozen comparison gate.
3. Finish board-development evidence before adding more heuristic rules.
4. Rebuild the derived replay dataset from the 85-file raw snapshot.
5. Keep search and human-capture delivery outside the immediate release path.
6. Require `scripts/audit_documentation.py` to pass with every code or
   documentation change.

## Next work

The authoritative queue is [`03_tasks/TASK_INDEX.md`](03_tasks/TASK_INDEX.md).
The recommended order is:

1. finish board-development scenarios and metrics;
2. run the frozen four-opponent comparison and correct report metadata;
3. validate Rule Box/PrizeMap and PrizeCheck transitions;
4. rebuild the replay dataset;
5. close the heuristic-only release checklist.

## Evidence links

- [Task registry](03_tasks/TASK_INDEX.md)
- [Codebase map](CODEBASE_MAP.md)
- [Roadmap](04_sprint_plan.md)
- [Acceptance checklist](19_final_harness_checklist.md)
- [Feedback register](29_gameplay_feedback.md)
- [Evidence log](strategy_notes.md)
- [Release manifest](../reports/release_heuristic_manifest.json)
- [Full local report](../reports/runs/full_heuristic_final/27d3df870485/report.json)
