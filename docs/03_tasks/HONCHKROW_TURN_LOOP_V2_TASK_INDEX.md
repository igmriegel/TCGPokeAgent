# Honchkrow Turn Loop v2 task index

> Canonical status source for HLV2 tasks. The general task index contains only
> the umbrella link.

**Last reviewed:** 2026-08-08

## Summary

| Status | Count |
|---|---:|
| Done | 7 |
| In progress | 4 |
| Ready | 4 |
| Blocked by prerequisite | 10 |
| Total | 25 |

## Tasks

| ID | Sprint | Status | Depends on | Outcome / next gate |
|---|---|---|---|---|
| HLV2-001 | S0 | `DONE` | — | Foundation manifest freezes baseline, candidate, hashes, SDK and 26-replay corpus |
| HLV2-002 | S0 | `DONE` | 001 | Annotation matrix records preconditions, exceptions, telemetry, fixtures and hidden-information rejection |
| HLV2-003 | S1 | `DONE` | 001 | Public turn ledger records stages, objectives, Supporter damage, attackers, Energy and deck reserve from observation facts |
| HLV2-004 | S1 | `IN_PROGRESS` | 003 | Candidate-only invalidation implemented; finish repeated-prompt and draw-transition goldens |
| HLV2-005 | S2 | `READY` | 003 | Complete empty/one/developed-board and lethal exception fixtures |
| HLV2-006 | S2 | `READY` | 005 | Existing expert Proton behavior; add prompt reproduction and late-use rejection gate |
| HLV2-007 | S2 | `READY` | 005 | Complete exact search-purpose and discard/deck-out fixtures |
| HLV2-008 | S3 | `IN_PROGRESS` | 003 | Existing KO/objective foundation; complete Supporter precedence matrix |
| HLV2-009 | S3 | `DONE` | 008 | Golden tests distinguish Factory-before-Ariana from Factory-drawn-by-Ariana and defer the effect until productive |
| HLV2-010 | S3 | `BLOCKED` | 008 | Complete prior-KO and productive-hand Archer fixtures |
| HLV2-011 | S3 | `BLOCKED` | 008 | Complete lethal/nonlethal Roto preservation and post-resolution recomputation |
| HLV2-012 | S3 | `BLOCKED` | 011 | Complete exact recovery, Ariana preservation and waste metrics |
| HLV2-013 | S4 | `BLOCKED` | 008, 011 | Complete productive-horizon and immediate-loss exception fixtures |
| HLV2-014 | S4 | `BLOCKED` | 003, 013 | Complete terminal promotion/Prize consistency gate |
| HLV2-015 | S4 | `BLOCKED` | 008, 013 | Complete Giovanni/paid-retreat/wait precedence fixtures |
| HLV2-016 | S4 | `BLOCKED` | 015 | Add explicit Confusion fixtures without text inference |
| HLV2-017 | S5 | `DONE` | 004–016 | Integrate official `expert_turn_loop` without changing simulator indices |
| HLV2-018 | S5 | `IN_PROGRESS` | 017 | Emit canonical stage, exception, Factory-effect and Headset-reason telemetry |
| HLV2-019 | S6 | `BLOCKED` | 005–018 | Run complete unit/golden/lint/type/pre-commit gate |
| HLV2-020 | S6 | `BLOCKED` | 017, 019 | Reproduce frozen 26-replay corpus for both policies |
| HLV2-021 | S7 | `DONE` | 020 | Screening complete: 600 bilateral episodes per policy, zero execution failures, equal deck-out losses, no tactical counter regression; `reports/honchkrow_turn_loop_v2/cabt_screening_20260808/comparison/` |
| HLV2-022 | S7 | `READY` | 021 | Run independent 1,000-match block per policy; screening is `HOLD` because the 95% difference interval includes zero |
| HLV2-023 | S7 | `BLOCKED` | 021, 022 | Generate full comparison and human review bundle |
| HLV2-024 | S8 | `DONE` | 023 | `PROMOTE_WITH_USER_OVERRIDE`: operational promotion authorized despite screening `HOLD`; old package retained for rollback |
| HLV2-025 | S8 | `DONE` | 024 | Canonical package built from `2c554dc`, validated, submitted, and recorded in `reports/honchkrow_turn_loop_v2/release_manifest.json`; prior package retained for rollback |

## Current evidence

- Foundation manifest: `reports/honchkrow_turn_loop_v2/foundation/manifest.json`
- Historical replay hashes: `reports/replay_audits/55333874/replay_hashes.json`
- Candidate constructor and evaluation selection are explicit; the baseline
  default remains `supporter_resource_v2`.
- Existing `expert_rounds_1_3_v1` evidence is implementation context, not an
  HLV2 promotion result.
- Current local verification: 297 full-suite tests pass; focused HLV2 Ruff and
  mypy gates pass; a two-match bilateral CABT smoke completed with 2/2 `ok`,
  zero fallback, zero Ignition-without-attack and zero superior-line Torment.
- Pre-gate replay evidence: baseline reproduced 1,434/1,434 decisions; candidate
  completed 1,434 decisions with 20 single-decision divergences; both had zero
  invalid index, fallback and exception. This does not close HLV2-020 before
  HLV2-019 and its prerequisite goldens pass.
- CABT screening evidence: baseline 511W/89L and candidate 518W/82L over 600
  bilateral episodes each; both policies had 600/600 `ok`, 27 deck-out losses,
  no Ignition-without-attack or partial Mega Abomasnow attacks, and independent
  win-rate difference +1.17 p.p. with 95% CI [-2.79, +5.12] p.p. The result is
  screening `HOLD`, not promotion.
- Promotion decision: the user explicitly authorized operational promotion with
  the screening limitation recorded; this is not a claim that the statistical
  promotion gate passed. The prior package remains available for rollback.
- HLV2 final 1,000-match block has not run; package build and remote submission
  remain a statistical follow-up, not a condition hidden from the release record.
- Official release: `expert_turn_loop`; historical HLV2 manifests remain audit artifacts.
