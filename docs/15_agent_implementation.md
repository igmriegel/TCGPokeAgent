# Heuristic and short search implementation

The high-level behavioral intent is maintained separately in
[`27_gameplay_rules.md`](27_gameplay_rules.md). Changes to scoring or sequencing
must identify which accepted gameplay rule they implement and which trace or
metric verifies it.

## Dispatch by context

| Group | Contexts | Initial rule |
|---|---|---|
| setup | `SETUP_ACTIVE_POKEMON`, `SETUP_BENCH_POKEMON` | active with best survival/early attack; bench useful without occupying critical slots |
| start | `IS_FIRST`, `MULLIGAN` | fixed versioned rule dependent on deck |
| mobility | `SWITCH`, `TO_ACTIVE`, `TO_BENCH`, `TO_FIELD` | preserve attacker and promote best post-action state |
| resources | `TO_HAND`, `TO_DECK`, `TO_DECK_BOTTOM`, `TO_PRIZE`, `NOT_MOVE`, `DISCARD` | marginal value and piece rarity |
| targets | `DAMAGE*`, `HEAL`, `REMOVE_DAMAGE_COUNTER*`, `EFFECT_TARGET` | KO/prize, threat, and efficiency |
| evolution | `EVOLVES_FROM`, `EVOLVES_TO`, `DEVOLVE`, `EVOLVE` | immediate gain, survival, and enabled attack |
| attachments | `ATTACH_*`, `DETACH_FROM`, `DISCARD_*`, `SWITCH_*` | enable attack with least waste |
| skills/attacks | `SKILL_ORDER`, `ATTACK`, `DISABLE_ATTACK` | expected value and sequence |
| count | `DRAW_COUNT`, `DAMAGE_COUNTER_COUNT`, `REMOVE_DAMAGE_COUNTER_COUNT` | useful maximum without overpay |
| booleans | `ACTIVATE`, `FIRST_EFFECT`, `MORE_DEVOLVE`, `COIN_HEAD` | net benefit; explicit fallback |
| condition | `AFFECT_SPECIAL_CONDITION`, `RECOVER_SPECIAL_CONDITION` | impact on target and next turn |

Unknown future contexts use cardinality/index fallback and emit `unknown_context`.

## Heuristic score

Use configurable sum, with normalized components and reasons:

```text
score =
  win_now
  + efficient_attack
  + useful_evolution
  + attack_enabling_energy
  + bench_development
  + draw_search
  + resource_preservation
  + safe_end_turn
  - wasted_energy
  - key_piece_discard
  - pointless_evolution
  - blocked_bench
  - premature_end
```

`win_now` dominates any non-winning combination. Beyond that, weights do not replace legality rules. Efficient attack considers effective damage, KO, prizes, observed weakness/resistance, cost, and counter-attack exposure.

## Short search

### Determinization

- own deck: fixed list minus known cards;
- own prizes: stable fill from remainder;
- opponent: versioned reference deck minus public cards;
- hand, prizes, and hidden active: deterministic fill with exact cardinality;
- `manual_coin=False`.

### Algorithm

1. Start monotonic clock.
2. Check gates and build belief.
3. Call `search_begin` with the `Observation` exactly as received.
4. For each of the top 3 heuristic selections, call `search_step`.
5. Continue for at most 4 selections in the branch, using heuristic for intermediate responses.
6. Stop at end of turn, terminal, or budget.
7. Evaluate leaf with `StateEvaluator`.
8. Release every intermediate `searchId` with `search_release`.
9. Execute `search_end()` in `finally`.
10. Choose highest value; tie by index.

### Fallback

Inconsistent `BeliefState`, error return, exception, null state, or timeout returns heuristic top-1. The failure is counted without propagating to the runtime.

## `StateEvaluator`

First version combines difference in remaining prizes, KO threat, useful HP, prepared attackers, useful energy, bench quality, known hand size/quality, and deck-out risk. Hidden features come only from belief and are identified in the trace.

## Tests

- deterministic tie;
- immediate win surpasses all other options;
- premature `END` receives penalty;
- search never opens outside `MAIN`;
- top 3 and depth 4;
- `search_release` and `search_end` even on exception;
- cutoff at 100 ms and below 30 s;
- search failure preserves exactly the heuristic choice.
