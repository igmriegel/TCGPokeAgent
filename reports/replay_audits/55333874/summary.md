# Submission 55333874 replay audit

Generated: `2026-08-08T04:38:58Z`
Remote rating: **357.2** (2026-08-08T01:13:52-03:00, 26 episodes)
Immutable source: `f6a7c94e7cc94e6507c9db965f29845b141ae0b047e504e839884067547e4fac`

## Reproduction gate

The submitted package reproduced **1434/1434** real policy decisions with 0 divergences, 0 invalid selections, and 0 fallbacks.

## Outcomes

- 8 wins, 18 losses, 0 draws
- 2 effective deck-out losses; 3 games where the deck merely reached zero
- 26/26 explicit terminal reasons
- 26/26 reconciled result/reason/final states

## Candidate replay divergences

- `supporter_resource_v2_replay_fix_v1`: 0 intentional single-decision divergences; 0 invalid; 0 fallbacks
- `expert_rounds_1_3_replay_fix_v1`: 20 intentional single-decision divergences; 0 invalid; 0 fallbacks

## CABT validation

- baseline: 251W/49L in 300 matches; 14 deck-out losses; 0 operational failures
- candidate_a: 254W/46L in 300 matches; 12 deck-out losses; 0 operational failures; passed screening
- candidate_b: 247W/53L in 300 matches; 9 deck-out losses; 0 operational failures; failed screening

Final independent gate: baseline 840/1000 (84.0%) versus candidate A 862/1000 (86.2%).
Difference: +2.2%; 95% interval [-0.9%, +5.3%].
Tactical no-regression gate: False.

No replay divergence is interpreted as an alternate win after the observed state would have diverged. Unproven strategic root causes remain `unknown`.

## Promotion status

No candidate passed every final gate; keep the immutable submitted package as the technical reference and do not build a new package.
