# Heuristic and short search implementation

The high-level behavioral intent is maintained separately in
[`27_gameplay_rules.md`](27_gameplay_rules.md). Changes to scoring or sequencing
must identify which accepted gameplay rule they implement and which trace or
metric verifies it.

**Current implementation note:** `HybridAgent.select()` delegates directly to
the heuristic. The algorithm below is the S8 target and must not be reported
as active search behavior.

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

## MAIN action priority ladder

`_main_action_score` orders legal `MAIN` actions by a fixed ladder that
implements GR-001 to GR-017:

```text
EVOLVE                           500 (+ energy on target)
ABILITY                          450
attach completing Active attack  ~460–485
guaranteed-KO attack             ≥530 (200 base + damage + 200 bonus)
development-priority play        400
Item search                      340
generic Pokémon play             320
Item                             240
Supporter search                 230
Supporter                        210
weak attack                      210
END                            -1000 (only when nothing better)
```

The conditional Bench filter restricts a decision to Pokémon `PLAY`
selections only when no priority action is legal. Priority actions are
Evolution, Ability, search/Trainer `PLAY`, an attach that completes the Active
attack, and an attack with a guaranteed Knock Out.

## Deterministic attack damage

`_guaranteed_attack_damage` computes the deterministic part of an attack: the
`deck_profile` `attack_plans` guaranteed damage first (including discard-pile
based damage from the public discard count), then option and catalog metadata;
top-of-deck based damage stays probabilistic and returns zero. Guaranteed-KO
attacks exempt the decision from the Bench filter, gain `GUARANTEED_KO_BONUS`
when their damage reaches the opponent Active HP, and prefer refill attacks
near deck-out via the `deck_refill` reason.

## Resource and attachment scoring

- `_card_selection_score` `TO_HAND` follows the profile `resource_values` and
  penalizes `trainer_search` targets (`avoid_redundant_supporter_search`).
- `_card_selection_score` `DISCARD` penalizes `development_priority` Pokémon
  (`preserve_development_pokemon`), then favors Energy, then non-Pokémon.
- `_attachment_score` classifies by metadata `cardType`: Tool (2) scores
  `attach_useful_tool`; Energy (5/6) scores by deficit with an Active-attack
  completion bonus; anything else emits `attach_unrecognized_card` and never
  pretends to be a useful tool.

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
3. Call `search_begin` with the opaque `search_begin_input` exactly as
   received.
4. For each of the top 3 heuristic selections, call `search_step`.
5. Continue for at most 4 selections in the branch, using heuristic for intermediate responses.
6. Stop at end of turn, terminal, or budget.
7. Evaluate the adapter score; the standalone `StateEvaluator` remains a
   deferred leaf-evaluation component and is not wired to this adapter.
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
