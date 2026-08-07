# Honchkrow/Porygon v3 Retreat Guard Audit

Date: 2026-08-07

## Scope

The evaluation isolated the candidate behind
`HONCHKROW_POLICY_VARIANT=ko_priority_v3_retreat_guard`. After reviewing the
results, the user promoted this behavior to `baseline`; the evaluated prior
behavior is now available as `legacy_baseline`. The changes cover:

- voluntary retreat only with a committed same-turn attacker;
- Giovanni preferred over paid retreat when the opponent has no Bench;
- exact switch target binding by Pokémon serial;
- projected post-Ignition damage before promoting Honchkrow or Porygon2;
- committed promotion, Ignition attachment, and attack execution;
- Miracle Headset used only for an exact two-Supporter immediate-KO recovery;
- preservation of dedicated MAIN-phase telemetry reasons.

The CABT observation already expands attached Energy into effective units. An Ignition Energy
attached to an Evolution Pokémon is represented by three entries in `energies`. The defect was
therefore the missing pre-attachment projection, not attached-Energy accounting.

## Validation

- 264 tests passed.
- Ruff passed.
- mypy passed for all 62 source files.
- `git diff --check` passed.
- Both evaluation policies completed with zero `INVALID`, `ERROR`, and `TIMEOUT` results.
- A promoted-baseline package was built in temporary storage and passed
  extracted archive, 60-card deck, entry-point, and CABT file-agent validation.

## Method

CABT 1.32.2 does not expose a seed in its environment specification and does not forward the
configured evaluation seed to `battle_start`. The random opponent also consumes global random
state. Consequently, nominally equal seeds do not create paired episodes. McNemar and episode
conversion tables would be invalid for these runs.

Two contemporary independent blocks were run for each policy. Every block contained 200 matches,
100 from each agent side. Aggregate evidence therefore contains 400 matches per policy.

## Results by block

| Block | Legacy baseline | Promoted baseline | Win delta | Legacy deck-out losses | Promoted deck-out losses |
|---|---:|---:|---:|---:|---:|
| 1 | 157-43 | 162-38 | +5 | 27 | 23 |
| 2 | 151-49 | 151-49 | 0 | 37 | 33 |
| Total | 308-92 | 313-87 | +5 | 64 | 56 |

## Aggregate metrics

| Metric | Legacy baseline | Promoted baseline | Delta |
|---|---:|---:|---:|
| Wins | 308 | 313 | +5 |
| Losses | 92 | 87 | -5 |
| Win rate | 77.00% | 78.25% | +1.25 pp |
| Wilson 95% | 72.63-80.86% | 73.95-82.01% | overlapping |
| Side 0 | 159-41 | 166-34 | +7 wins |
| Side 1 | 149-51 | 147-53 | -2 wins |
| Deck-out losses | 64 | 56 | -8 (-12.5%) |
| Losses with zero Pokémon in play | 0 | 0 | unchanged |
| Partial Mega Abomasnow attacks | 0 | 0 | unchanged |
| Operational status | 400 OK | 400 OK | unchanged |
| Mean decision latency | 5.097 ms | 5.139 ms | +0.8% |
| Decision P50 | 4.395 ms | 4.437 ms | +1.0% |
| Decision P95 | 9.015 ms | 9.021 ms | +0.1% |

The independent two-proportion comparison gives `z=0.424`, two-sided `p=0.671`. The observed win
gain is therefore preliminary and not statistically distinguishable from random variation.

## Tactical contract evidence

| Metric | Legacy baseline | Promoted baseline | Delta |
|---|---:|---:|---:|
| Paid retreats selected | 230 | 44 | -186 (-80.9%) |
| Retreats followed by a same-turn attack | 37 | 44 | +7 |
| Retreats without a same-turn attack | 193 | 0 | -193 |
| R Command executions | 12 | 53 | +41 |
| R Command KOs | 10 | 35 | +25 |
| R Command observed damage | 960 | 6,260 | +5,300 |
| Exact two-Supporter Headset recoveries | not committed | 106/106 | contract satisfied |

The primary regression is eliminated in the observed sample: every selected v3 retreat converted
to an attack in the same turn. Porygon2 usage also increased materially after adding projected
Ignition damage and the promotion/attachment/attack commitment.

## Decision

Promote the committed-switch policy as the development `baseline` by explicit
user decision and preserve the prior behavior as `legacy_baseline`. The
tactical invariants are materially better, deck-out losses fell in both blocks,
and aggregate W/L did not regress. The win-rate gain remains too small and
uncertain to claim statistical superiority. The next gate is an independent
1,000-match run of the promoted baseline, with special attention to the small
Side 1 regression and the five additional Active Pokémon KOs observed across
the aggregate sample. This promotion does not itself submit a new Kaggle
package.
