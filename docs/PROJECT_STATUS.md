# Project status

> Canonical current-state snapshot. Update this file when a gate, release,
> remote score, or active priority changes. Historical evidence belongs in
> [`strategy_notes.md`](strategy_notes.md), not here.

**Last verified:** 2026-08-02

**Code baseline:** `main`; exact revisions are preserved in Git and release
manifests rather than copied into this self-changing status page

**Current release:** heuristic-only; HDI v1 and learned rankers are unpromoted candidates

## Executive summary

The agent is operational, packaged, and remotely accepted by Kaggle. The
heuristic plays productive actions and completes evaluation without operational
failures. The project is not ready to claim a fully closed MVP because the
four-opponent matrix, decision-level gameplay metrics, several feedback
validation gates, and the final checklist remain open.

The independent HDI v1 candidate was accepted as submission `55119505` and
scored 490.4, compared with 539.2 for reference submission `55088176`. This is
experimental evidence only: the required local 200-match comparison and
promotion matrix have not run, so the release policy remains heuristic.

## Verified snapshot

| Area | Current evidence | Decision |
|---|---|---|
| Quality | 158 tests pass; Ruff, formatting, mypy, and documentation drift audit pass | Green |
| Local evaluation | 400 matches vs `random`: 239W/0D/161L, 59.75% win rate, zero operational failures | Operational baseline only |
| Kaggle stable candidate | `55088176`: 539.2 public score | Keep as remote reference |
| Kaggle HDI v1 experiment | `55119505`: 490.4 public score, -48.8 versus reference | Regression; do not promote |
| Prior experimental candidate | `55093119`: 479.8 public score | Do not promote |
| Package | Isolated heuristic and HDI v1 package validation passed | Usable artifacts |
| Search | Native lifecycle lacks a verified project Python adapter | Disabled and deferred |
| Raw replay corpus | 85 valid replays; 82 attributable matches; 62 distinct opponent decks | Source snapshot is current |
| Derived replay dataset | 31 matches, 2,047 decisions, 27 opponent decks | Stale; rebuild required |
| Human gameplay capture | No live human match captured | HD0–HD5 remain deferred |
| Heuristic priority fixes | Conditional Bench filter, Snover/search/attachment/refill scoring, guaranteed-KO attack bonus, Item-first play ordering, and deck v2 profile integrity fix | Implemented with focused tests; validation pending |
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
| Feedback FB-2026-001–010 | Implemented, not validated | Core rules and focused tests exist | Thirteen open validation/measurement actions |
| Human capture HD0–HD5 | Deferred | Design only; post-hoc agent replay review is separate | First live human trace and staged delivery gates |
| Learned policies | Runtime implemented, not promoted | Shared schema, grouped datasets, XGBoost/LightGBM native runtime, fallback, and separate extracted-package smoke | Required human data, temporal holdout, paired CABT matrix, and promotion gates |
| HDI v1 | Experimental, not promoted | Ordinal runtime, declarative profile, 40-episode smoke, extracted package, and remote score | Full reproducible local comparison and formal promotion decision |

## Current decisions

1. Keep `55088176` as the remote comparison reference.
2. Treat `55119505` as an HDI v1 experiment, not an automatic promotion.
3. Run the frozen local comparison before deciding whether HDI v1 can replace
   the heuristic release policy.
4. Finish board-development evidence before adding more heuristic rules.
5. Rebuild the derived replay dataset from the 85-file raw snapshot.
6. Keep search and human-capture delivery outside the immediate release path.
7. Require `scripts/audit_documentation.py` to pass with every code or
   documentation change.
8. Keep heuristic as the release policy until an alternative passes its full
   promotion gate.
9. Build and validate a new heuristic package from the conditional Bench and
   priority fixes; do not submit it automatically.

## Next work

The authoritative queue is [`03_tasks/TASK_INDEX.md`](03_tasks/TASK_INDEX.md).
The recommended order is:

1. run the frozen HDI v1 versus heuristic comparison and correct report metadata;
2. validate the heuristic priority fixes (T-015–T-021) and finish board-development scenarios;
3. validate Rule Box/PrizeMap and PrizeCheck transitions;
4. rebuild the replay dataset;
5. close the release checklist.

## Evidence links

- [Task registry](03_tasks/TASK_INDEX.md)
- [Codebase map](CODEBASE_MAP.md)
- [Roadmap](04_sprint_plan.md)
- [Acceptance checklist](19_final_harness_checklist.md)
- [Feedback register](29_gameplay_feedback.md)
- [Evidence log](strategy_notes.md)
- [Release manifest](../reports/release_heuristic_manifest.json)
- [Full local report](../reports/runs/full_heuristic_final/27d3df870485/report.json)
