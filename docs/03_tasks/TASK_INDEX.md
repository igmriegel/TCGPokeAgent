# Task index

> Canonical executable backlog. Sprint documents define scope; this file owns
> task status, priority, dependency, and next action.

**Last reviewed:** 2026-07-29

## How to read this backlog

- `IN_PROGRESS`: implementation or evidence work has started.
- `READY`: unblocked and suitable for the next work session.
- `DEFERRED`: intentionally outside the current release path.
- `DONE`: exit evidence exists; completed rows move to the archive below.

Counts refer to rows in this file. Do not add checklist bullets from other
documents to these totals.

## Summary

| Queue | Count |
|---|---:|
| In progress | 2 |
| Ready | 8 |
| Deferred | 7 |
| Total open | 17 |

## Active release queue

| ID | Priority | Status | Outcome | Closes | Next action |
|---|---:|---|---|---|---|
| T-001 | P0 | `IN_PROGRESS` | Complete factual board-development and evolution features | FB001-A1, S4, H2A | Add backup-attacker and evolution readiness features |
| T-002 | P0 | `READY` | Complete repeated-play, evolution, full-Bench, and immediate-win fixtures | FB001-A4, S2, S4 | Add real and synthetic golden cases |
| T-003 | P0 | `READY` | Report skipped development, board width, conversion, and replacement readiness | FB001-A5, S5 | Extend decision and aggregate metrics |
| T-004 | P0 | `READY` | Run the frozen four-opponent, both-side comparison with correct metadata | FB001-A6, H0, S6 | Freeze matrix and acceptance expression before execution |
| T-005 | P0 | `READY` | Validate Rule Box and PrizeMap tactics | FB-2026-002 | Add tactical fixtures, then run the paired matrix |
| T-006 | P0 | `READY` | Validate PrizeCheck across zone transitions | FB-2026-003 | Add search/draw/discard/attach/evolve/prize golden sequence |
| T-007 | P1 | `READY` | Rebuild the derived dataset from all 85 raw replays | Replay foundation | Version a new dataset; do not overwrite `v1` |
| T-008 | P1 | `READY` | Revalidate parser, selection, and fallback against current real observations | S2, S3 | Add current replay-derived fixtures and run focused gates |
| T-009 | P1 | `READY` | Revalidate belief and evaluator against corrected factual state | S7 | Add real-observation invariant cases |
| T-011 | P1 | `IN_PROGRESS` | Close the heuristic-only package and handoff checklist | S9 | Resolve unchecked evidence and rebuild after promoted changes |

## Deferred queue

| ID | Status | Outcome | Re-entry condition |
|---|---|---|---|
| T-012 | `DEFERRED` | Verified CABT native search adapter and S8 gate | Heuristic release queue is green |
| HD-00 | `DEFERRED` | Human trace schema and privacy contract | Human capture becomes an active priority |
| HD-01 | `DEFERRED` | Terminal human player and one complete legal match | HD-00 passes |
| HD-02 | `DEFERRED` | Reconnect-safe browser player | HD-01 passes |
| HD-03 | `DEFERRED` | Replay annotation UI with live/post-hoc separation | HD-00 passes |
| HD-04 | `DEFERRED` | Human/agent disagreement report | At least one valid human session exists |
| HD-05 | `DEFERRED` | Leakage-safe preference export | HD-04 produces accepted examples |

## Completed foundation

| ID | Outcome | Evidence |
|---|---|---|
| T-000 | Reproducible environment, deck, wrapper, and package smoke | S0–S1 evidence and release manifest |
| T-010 | Reconcile remote scores and retain `55088176` as reference | Score correction in `strategy_notes.md` |
| FB001-A2 | Pre-terminal ordering layer | `e268c96`, focused gameplay tests |
| FB001-A3 | Generic Pokémon play before attack with open Bench | `e268c96`, replay regression |
| RF-001 | Replay ingestion and leakage-safe dataset foundation | `gameplay_replays/v1` manifest |
| RA-001 | Decision-linked post-hoc replay annotations | `competitive-gameplay-review-v1` records |

## Task update rule

A task may move to `DONE` only when its stated outcome and linked gate both
have evidence. Code without the evaluation gate remains `IN_PROGRESS`. Update
[`PROJECT_STATUS.md`](../PROJECT_STATUS.md) only when the change affects a
release decision, headline metric, or track status.
