# Task index

> Canonical executable backlog. Sprint documents define scope; this file owns
> task status, priority, dependency, and next action.

**Last reviewed:** 2026-08-08

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
| In progress | 7 |
| Ready | 20 |
| Deferred | 8 |
| Total open | 35 |

## Active release queue

| ID | Priority | Status | Outcome | Closes | Next action |
|---|---:|---|---|---|---|
| T-001 | P0 | `IN_PROGRESS` | Complete factual board-development and evolution features | FB-2026-001, S4, H2A | Add backup-attacker and evolution readiness features |
| T-002 | P0 | `READY` | Complete repeated-play, evolution, full-Bench, and immediate-win fixtures | FB-2026-001, S2, S4 | Add real and synthetic golden cases |
| T-003 | P0 | `READY` | Report skipped development, board width, conversion, and replacement readiness | FB-2026-001, S5 | Extend decision and aggregate metrics |
| T-004 | P0 | `READY` | Run the frozen four-opponent, both-side comparison with correct metadata | FB-2026-001, H0, S6 | Freeze matrix and acceptance expression before execution |
| T-005 | P0 | `READY` | Validate Rule Box and PrizeMap tactics | FB-2026-002 | Add tactical fixtures, then run the controlled matrix |
| T-006 | P0 | `READY` | Validate PrizeCheck across zone transitions | FB-2026-003 | Add search/draw/discard/attach/evolve/prize golden sequence |
| T-007 | P1 | `READY` | Rebuild the derived dataset from all 85 raw replays | Replay foundation | Version a new dataset; do not overwrite `v1` |
| T-008 | P1 | `READY` | Revalidate parser, selection, and fallback against current real observations | S2, S3 | Add current replay-derived fixtures and run focused gates |
| T-009 | P1 | `READY` | Revalidate belief and evaluator against corrected factual state | S7 | Add real-observation invariant cases |
| T-011 | P1 | `IN_PROGRESS` | Close the heuristic-only package and handoff checklist | S9 | Resolve unchecked evidence and rebuild after promoted changes |
| T-013 | P1 | `IN_PROGRESS` | Qualify XGBoost and LightGBM ranker candidates | Learned-policy gates | Capture 250 human groups, freeze holdout, and run the controlled matrix |
| T-015 | P1 | `READY` | Validate development-priority placement and discard protection | FB-2026-004, H2A | Run Snover bench/discard fixtures and the controlled comparison |
| T-016 | P1 | `READY` | Validate Evolution-before-Energy and completion attach | FB-2026-005, H2A | Run post-evolution fixtures and the controlled comparison |
| T-017 | P1 | `READY` | Validate search ordering and no Petrel tutoring | FB-2026-006, H2A | Run search-order fixtures and the controlled comparison |
| T-018 | P1 | `READY` | Validate deck-out shuffle-refill attack | FB-2026-007, H2A | Run deck-out fixtures and the controlled comparison |
| T-019 | P1 | `READY` | Validate deck_profile integrity against deck v2 | H2A | Run profile tests and golden gameplay gates |
| T-020 | P1 | `READY` | Validate Item-before-Supporter play ordering | FB-2026-008, H2A | Run item/supporter ordering fixtures and the controlled comparison |
| T-021 | P1 | `READY` | Validate guaranteed-KO attack preference | FB-2026-009, H2A | Run guaranteed-KO fixtures and the controlled comparison |
| T-023 | P1 | `READY` | Validate public-risk retreat and visible Alakazam-line tech branch | FB-2026-011, H2A | Run retreat/mobility and tech-branch fixtures |
| T-024 | P1 | `READY` | Validate conditional Articuno sacrifice and discard priority | FB-2026-012, H2A | Run Articuno attachment/discard fixtures |
| T-026 | P0 | `IN_PROGRESS` | Eliminate Honchkrow/Porygon deck-out losses with committed 350-HP KO, draw-reserve, retreat, and terminal-cause guards | FB-2026-014, FB-2026-015, H2A | Use the resolved attack/discard audit to classify the remaining deck-outs as preventable or unavoidable; `deck_reserve_v2` remains experimental after 2 deck-out losses in 200 bilateral matches |
| T-027 | P1 | `READY` | Measure opponent-sample variance for identical-package submissions | Remote evaluation variance | Compare submissions `55320796` and `55320706` across two distinct opponent samples; report opponent composition, win rate, variance, and confidence intervals before attributing differences to the package |
| T-028 | P0 | `IN_PROGRESS` | Convert every Ignition attachment into a same-turn attack and prioritize game-winning Porygon2 promotion | FB-2026-016, H2A | Run terminal Porygon2, Prize-race, Ignition-commitment, and no-wasted-energy gates, then evaluate the promoted policy against CABT |
| T-029 | P0 | `IN_PROGRESS` | Enforce Factory, Ariana, Roto-Stick, and Factory-effect sequencing | FB-2026-017, H2A | Run ordered draw-engine fixtures and confirm the sequence in bilateral CABT evaluation |
| T-030 | P0 | `IN_PROGRESS` | Enforce persistent turn objectives, setup-aware Supporters, and proven Poké Pad evolution-KO lines | FB-2026-018, H2A | Eliminate the 32 versus 28 deck-out-loss regression, then rerun the frozen comparison |
| T-031 | P0 | `DEFERRED` | Ratify the complete Honchkrow/Porygon strategy with expert interview evidence and produce an implementation-ready plan | Honchkrow expert audit | Resume at Round 4 in `docs/34_honchkrow_expert_interview.md`; keep `expert_rounds_1_3_v1` experimental until comparison evidence is recorded |
| T-033 | P0 | `DONE` | Implement and independently qualify the official `expert_turn_loop` without changing `supporter_resource_v2` | [Dedicated HLV2 index](HONCHKROW_TURN_LOOP_V2_TASK_INDEX.md) | Promoted after 200 bilateral CABT matches with 88.0% wins, zero operational failures, and no deck-out regression |
| T-034 | P0 | `READY` | Explain and eliminate the Owner-observed divergence from the documented game plan and action sequencing | FB-2026-019 | Select representative failing replays, verify exact package provenance, and trace each first causal divergence from documented intent through parse, objective, candidate, scoring, filtering, commitment, fallback, and final selection |
| T-035 | P0 | `READY` | Obtain Owner approval to remove deprecated gameplay-policy branches after the new official package is proven | Release deprecation review | Next Codex session: inventory historical variants, verify immutable baseline reproducibility, and record Igor's explicit removal decision before deleting compatibility code |

## Active-track coverage

This table prevents roadmap work from existing without an executable owner.

| Track | Owning tasks |
|---|---|
| S2 | T-002, T-008 |
| S3 | T-008 |
| S4 | T-001, T-002, T-005, T-006 |
| S5 | T-003 |
| S6 and H0 | T-004 |
| S7 | T-009 |
| S9 | T-011 |
| H2A | T-001–T-004, T-015–T-021, T-023–T-026, T-028–T-030, T-034 |
| HLV2 | [HLV2-001–HLV2-025](HONCHKROW_TURN_LOOP_V2_TASK_INDEX.md) |

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
| T-022 | Reinterpreted attacker-target gate; legal attacks are no longer blocked by board target | Policy revision in `docs/27_gameplay_rules.md` and `docs/29_gameplay_feedback.md` |
| T-025 | Promoted the Honchkrow/Porygon committed-switch, Giovanni, Miracle Headset, and projected Porygon2/Ignition policy as the development baseline | 264 tests; two independent 200-match blocks per policy; 0/44 unconverted retreats; `reports/honchkrow_v3_retreat_guard_audit_20260807.md` |
| T-032 | Audited submission `55333874`, reproduced 1,434 decisions, froze 26 replay hashes, screened two candidates, and completed the independent final gate | `reports/replay_audits/55333874/`; no candidate promoted and no package built |
| FB001-A2 | Pre-terminal ordering layer | `e268c96`, focused gameplay tests |
| FB001-A3 | Generic Pokémon play before attack with open Bench | `e268c96`, replay regression |
| RF-001 | Replay ingestion and leakage-safe dataset foundation | `gameplay_replays/v1` manifest |
| RA-001 | Decision-linked post-hoc replay annotations | `competitive-gameplay-review-v1` records |
| T-014 | Independent HDI v1 experimental submission | `55119505`: 490.4 public score; local smoke and extracted-package validation passed; do not promote |

## Task update rule

A task may move to `DONE` only when its stated outcome and linked gate both
have evidence. Code without the evaluation gate remains `IN_PROGRESS`. Update
[`PROJECT_STATUS.md`](../PROJECT_STATUS.md) only when the change affects a
release decision, headline metric, or track status.
