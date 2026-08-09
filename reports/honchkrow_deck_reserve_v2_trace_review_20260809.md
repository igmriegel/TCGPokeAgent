# Deck-reserve v2 terminal trace review

## Scope

This review reads the complete 200-match CABT trace for
`expert_turn_loop_deck_reserve_v2`. The run finished 168W/32L with two
deck-out losses, explicit terminal reasons for all matches, and no execution
failures or partial Mega Abomasnow attacks.

## Observed deck-out losses

| Match | Terminal turn | Low-deck facts | Classification |
|---|---:|---|---|
| `honchkrow_20261114_0` | 37 | At 7 cards, Miracle Headset recovered two Supporters and a 120-damage pressure attack was selected into 150 HP. At 2 cards, there were no hand Supporters and the visible target had 30 HP. The policy ended subsequent low-deck turns without an available attack conversion. | No low-deck lethal conversion was available; no unsafe elective draw was observed after the reserve became critical. |
| `honchkrow_20261180_0` | 41 | Factory reduced the deck from 8 to 6, then three Pokémon-search plays occurred at 6/5 cards. At 2 and 1 cards, the policy converted Rocket Feathers KOs before reaching zero, but could not take the final 350-HP target. | A pre-terminal search-resource pattern is present, but the trace cannot establish that declining it would win the match. |

The second match makes search consumption a valid measurement target. It is
not yet a gameplay-policy defect: a one-decision counterfactual cannot claim a
different result after the game state changes.

## Instrumentation follow-up

The evaluator now records `selected_card_ids` alongside the immutable CABT
option indices. Main-phase options only expose a hand index, so the public hand
snapshot is used to identify the selected card without reading hidden state.

The first post-instrumentation smoke used 20 CABT matches:

- 18 wins, 2 losses, no deck-outs;
- all 20 matches had explicit terminal reasons and `ok` execution status;
- 721 of 730 decision events exposed one or more selected card IDs.

## Next evidence gate

Run a new 200-match `deck_reserve_v2` trace with selected-card telemetry.
For every deck-out loss, compare low-deck Pokémon-search plays with the
remaining reserve and the same-turn visible KO/prize benefit. Only a repeated,
specific violation can justify an isolated search-reserve candidate.
