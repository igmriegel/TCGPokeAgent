# Project status

> Canonical current-state snapshot. Update this file when a gate, release,
> remote score, or active priority changes. Historical evidence belongs in
> [`strategy_notes.md`](strategy_notes.md), not here.

**Last verified:** 2026-08-06

**Code baseline:** `main`; exact revisions are preserved in Git and release
manifests rather than copied into this self-changing status page

**Current release:** heuristic-only; HDI v1 and learned rankers are unpromoted candidates

## Executive summary

The agent is operational and the dedicated Honchkrow/Porygon package passes
isolated validation. A new remote upload was attempted on 2026-08-06 but was
blocked before upload because the installed Kaggle CLI requires OAuth login or
`~/.kaggle/access_token`. The local 200-game dedicated baseline completed all
games, but instrumented losses identify deck-out as the next P0 strategic
priority. The project is not ready to claim a closed MVP.

The independent HDI v1 candidate was accepted as submission `55119505` and
scored 490.4, compared with 539.2 for reference submission `55088176`. This is
experimental evidence only: the required local 200-match comparison and
promotion matrix have not run, so the release policy remains heuristic.

## Verified snapshot

| Area | Current evidence | Decision |
|---|---|---|
| Quality | 219 tests pass; Ruff and documentation drift audit pass | Green; mypy remains a separate gate |
| Dedicated local evaluation | 200 matches vs CABT `random_agent`: 157W/0D/43L, 78.5% win rate, zero execution failures | Operational baseline; deck-out remains a strategic regression |
| Deck-out monitoring | Instrumented 40-game bilateral sample: 6 losses, 5 deck-outs, 1 other/unclassified | P0 next development |
| Kaggle stable candidate | `55088176`: 539.2 public score | Keep as remote reference |
| Kaggle HDI v1 experiment | `55119505`: 490.4 public score, -48.8 versus reference | Regression; do not promote |
| Prior experimental candidate | `55093119`: 479.8 public score | Do not promote |
| Package | Honchkrow/Porygon package built and isolated validation passed; remote upload blocked by Kaggle authentication | Local artifact usable; remote submission pending |
| Search | Native lifecycle lacks a verified project Python adapter | Disabled and deferred |
| Raw replay corpus | 85 valid replays; 82 attributable matches; 62 distinct opponent decks | Source snapshot is current |
| Derived replay dataset | 31 matches, 2,047 decisions, 27 opponent decks | Stale; rebuild required |
| Human gameplay capture | No live human match captured | HD0–HD5 remain deferred |
| Heuristic priority fixes | Honchkrow/Porygon Proton/Supporter/Energy/Articuno/promotion/terminal-line rules plus Stadium ordering | Implemented with focused tests; full strategic validation pending |
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
| Feedback FB-2026-001–014 | Implemented or accepted, not validated | Core rules, deck-out evidence, and focused tests exist | Deck-out P0 gate T-026 and remaining validation actions |
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
9. Keep the validated heuristic submission as the current release candidate and
   replace it only after a new validated package is ready.
10. Treat deck-out prevention and terminal-cause telemetry as the next P0
    development gate; do not promote the current local baseline on win rate
    alone.

## Next work

The authoritative queue is [`03_tasks/TASK_INDEX.md`](03_tasks/TASK_INDEX.md).
The recommended order is:

1. close T-026: instrument and eliminate Honchkrow/Porygon deck-out losses;
2. authenticate and submit the dedicated package, then collect remote replays;
3. validate the heuristic priority fixes (T-015–T-021) and finish board-development scenarios;
4. validate Rule Box/PrizeMap and PrizeCheck transitions;
5. rebuild the replay dataset and close the release checklist.

## Evidence links

- [Task registry](03_tasks/TASK_INDEX.md)
- [Codebase map](CODEBASE_MAP.md)
- [Roadmap](04_sprint_plan.md)
- [Acceptance checklist](19_final_harness_checklist.md)
- [Feedback register](29_gameplay_feedback.md)
- [Evidence log](strategy_notes.md)
- [Release manifest](../reports/release_heuristic_manifest.json)
- [Full local report](../reports/runs/full_heuristic_final/27d3df870485/report.json)
- [Honchkrow/Porygon local baseline](../reports/honchkrow_porygon_local_eval_20260806.json)
