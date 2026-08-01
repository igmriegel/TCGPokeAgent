# Heuristic-only improvement specifications

This track improves the stable heuristic without depending on native search.
Current status and priorities are owned by the
[`roadmap`](../04_sprint_plan.md) and
[`task index`](../03_tasks/TASK_INDEX.md).

## Operating rules

- Keep the stable remote candidate available for rollback.
- Freeze deck, opponents, side allocation, acceptance expression, and artifact.
- Preserve simulator indices and deterministic legal fallback.
- Promote only with zero operational failures and paired evidence.
- Keep deck-specific knowledge in profiles, not policy branches.

## H0 — Measurement baseline and complete opponent matrix

**Outcome:** trustworthy per-side, per-matchup, per-context, and decision
metrics against `random`, `first`, baseline/heuristic, and self-play.

**Gate:** complete immutable report with decision latency, fallback, parser,
catalog, belief, score-margin, gameplay, and termination metrics.

## H1 — Complete card, attack, and deck catalog

**Outcome:** every frozen-deck card and attack has validated metadata, roles,
costs, effects, and coverage reporting.

**Gate:** catalog integrity report and focused unknown/edge-case tests pass.

## H2 — Context-specific heuristic policies

**Outcome:** deterministic scorers for each observed `SelectContext`, with
stable reasons and legal fallback for unknown contexts.

**Gate:** focused fixtures cover every context and H0 shows non-inferiority.

## H2A — Continuous deck-agnostic board development

**Outcome:** required Pokémon plays and Evolutions occur before non-winning
attacks or `END`, with re-evaluation after every `MAIN` action, and Bench
development is restricted only when no priority action exists.

**Required coverage:** open/full Bench, repeated plays, eligible Evolution,
backup attacker, target reached, reserved slot, liability, immediate-win
override, development-priority placement, search ordering, and deck-out
refill.

**Gate:** zero skipped required development in focused fixtures and no
regression in the frozen matrix. The conditional Bench filter and the
priority ladder are implemented; open validation actions are tracked as
T-001–T-004 and T-015–T-021.

## H3 — Local tactical feature evaluator

**Outcome:** bounded estimates for immediate damage, Knock Out, Prize trade,
retreat, and resource consequences without pretending to simulate CABT.

**Gate:** tactical fixtures and decision-latency budget pass.

## H4 — Belief-derived scoring features

**Outcome:** calibrated hidden-information signals that never enter factual
`GameState`.

**Gate:** consistency, calibration, ablation, and fallback evidence pass.

## H5 — Reproducible heuristic weight optimization

**Outcome:** versioned, deterministic weight studies with validation and
temporal holdout separation.

**Gate:** selected weights improve validation and remain non-inferior on
holdout and match evaluation.

## H6 — Dependency-light supervised selection ranker

**Outcome:** compact legal-selection ranker with deterministic preprocessing,
model/schema hashes, and heuristic fallback.

**Gate:** data-volume threshold, temporal holdout, latency, package, and paired
non-regression gates pass.

## H7 — Matchup-aware profiles

**Outcome:** public-information matchup features select declarative profiles
without identity leakage.

**Gate:** robust improvement across the frozen opponent matrix.

## H8 — Hardened heuristic-only promotion

**Outcome:** frozen package, report, manifest, remote receipt, and rollback.

**Gate:** the final acceptance checklist is green and the candidate does not
regress against the stable remote reference.
