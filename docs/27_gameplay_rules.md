# Living gameplay rules

**Status:** `DRAFT`

This document is the high-level behavioral contract for the agent. It is
intentionally easier to edit than the implementation contracts: humans add
game knowledge here first, then code, tests, traces, and metrics derive from the
accepted rule. A rule is not implemented merely because a scorer contains a
similarly named weight.

The rules describe intent, not simulator legality. The CABT option list remains
the authority for what can be selected at each decision.

## Primary game plan

The primary win condition is to take all six Prize cards through Knock Outs.
This may require six Knock Outs against single-Prize Pokémon, fewer against
multi-Prize Pokémon, or one decisive Knock Out when the opponent has no
remaining Pokémon in play (a donk). Deck-out is a legal alternate outcome, but
it is not the default plan for this agent.

At every decision, preserve legal output first and then maximize progress
toward:

1. an attacker that can attack this turn;
2. a second attacker that can take over next turn;
3. a stable support board and hand;
4. an efficient Prize trade;
5. a Knock Out, multi-Prize Knock Out, or donk.

## Turn decision sequence

The sequence is a priority model. Card effects can interrupt it with nested
selection contexts, and the agent must finish those contexts before returning
to the main phase.

### 1. Draw and draw abilities

The simulator performs the mandatory draw for the turn. The agent then
re-evaluates the complete hand and board rather than acting from the previous
turn's plan.

Before spending the Supporter for the turn:

- identify legal abilities that draw cards, refill the hand, or improve hand
  quality;
- prefer low-cost or once-per-turn draw abilities when they do not consume a
  resource needed by the attack plan;
- sequence search and draw effects so known useful cards are not shuffled away
  unnecessarily;
- reduce draw priority when the deck is close to deck-out;
- record the hand count before and after each draw effect.

The agent must distinguish guaranteed draw, conditional draw, hand refresh,
discard-and-draw, and search/tutor effects. They do not have the same value.

### 2. Develop Pokémon in play

Evaluate whether more Pokémon should enter play.

If there is already a viable Active attacker, look for:

- a second attacker that can be prepared before the Active Pokémon is Knocked
  Out;
- a support Pokémon whose Ability materially improves draw, search, Energy
  acceleration, switching, healing, or damage;
- the Basic Pokémon required for an Evolution already available or likely to
  be found this turn.

Under normal rules the Bench limit is five. The agent must:

- never exceed the limit exposed by `benchMax`;
- preserve a Bench slot when a later support Pokémon, attacker, or forced
  movement is more valuable than the currently available Basic;
- avoid redundant support Pokémon whose usable effects do not stack;
- avoid filling the Bench with low-value liabilities that worsen the Prize
  trade;
- prioritize enough board presence to prevent losing when the Active Pokémon
  is Knocked Out.

Evolution is part of board development. Prefer Evolution when it improves
survival, enables a stronger attack, increases Prize pressure, or activates a
needed Ability. Do not evolve automatically when the lower stage has a
strategically required attack or effect.

#### Confirmed deck rule: continuous Snover/Abomasnow development

**Status:** `ACTIVE DEVELOPMENT — P0`

Kaggle gameplay feedback showed that the current agent can attack while
leaving Snover in hand and then lose after failing to maintain a developed
Bench. The current fixed scores explain this failure mode: a high-damage attack
can outrank playing Snover, and the attack ends the turn before the agent can
return to board development.

Rule:

- On every `MAIN` decision, re-evaluate board development before choosing an
  attack.
- If playing Snover is legal and a Bench slot is available, play it before a
  non-winning attack.
- If evolving an in-play Snover into Mega Abomasnow ex is legal, evolve it
  before a non-winning attack.
- Repeat this evaluation after every action. Playing one Pokémon or completing
  one evolution must not mark board development as finished for the turn or
  match.
- Never choose `END` or a non-winning attack while a required legal Snover play
  or Snover-to-Abomasnow evolution remains.
- An immediate game-winning action may override development. Legality,
  `benchMax`, and card-specific restrictions always remain authoritative.

Required implementation signals:

- open Bench slots;
- Snover and Mega Abomasnow ex counts in the Active Spot and on the Bench;
- legal Snover `PLAY` options in the current hand;
- legal Mega Abomasnow ex `EVOLVE` options and their targets;
- presence of a prepared backup attacker;
- whether the candidate attack wins the game or only deals damage.

Required reason codes:

- `develop_snover_before_attack`;
- `evolve_abomasnow_before_attack`;
- `maintain_backup_attacker`;
- `immediate_win_overrides_development`;
- `bench_full_blocks_development`.

Golden scenarios:

- one open Bench slot, Snover in hand, and a legal damaging attack selects
  Snover;
- multiple Snover plays remain legal across consecutive `MAIN` decisions and
  each is reconsidered;
- an eligible Benched Snover is evolved before a non-winning attack;
- a game-winning attack remains preferred over Snover development;
- a full Bench never produces an invalid play;
- `END` is rejected while a required Snover play or evolution remains legal.

### 3. Choose the Supporter and tutor plan

Only one Supporter can normally be played per turn, so Supporter selection must
follow an explicit needs assessment.

Classify available Supporters by role:

- draw or hand refresh;
- direct Pokémon search;
- Item, Tool, Stadium, or Energy search;
- gust or opponent-board manipulation;
- recovery from the discard pile;
- disruption or hand denial;
- healing, switching, or defensive support.

Build a per-turn need vector before choosing:

- `board_presence_need`: no attacker, no backup attacker, or missing support;
- `evolution_need`: missing evolution piece for a Pokémon already in play;
- `energy_need`: attack cost not met this turn or next turn;
- `draw_need`: hand lacks useful actions or has too few cards;
- `stadium_need`: a Stadium is required for the current plan;
- `switch_need`: the desired attacker is not Active;
- `gust_need`: a reachable Knock Out exists on the opponent's Bench;
- `recovery_need`: key pieces or Energy are in the discard pile;
- `prize_pressure`: an action can take the last Prize cards or improve the
  Prize trade.

Examples of derived behavior:

- with insufficient Pokémon in play, prefer Pokémon tutors or Items that lead
  to Pokémon;
- with the attacker ready but no Energy, prefer Energy access;
- with the required Pokémon and Energy already available, prefer draw,
  disruption, gust, or recovery according to the matchup;
- use a Stadium tutor only when the Stadium has positive immediate or planned
  value;
- do not spend the Supporter merely because one is legal.

The needs calculation must be traceable: record the need values, selected role,
rejected alternatives, and final reason codes.

### 4. Sequence Items, Tools, Stadiums, and Evolution

Before committing to an attack:

- use deterministic search Items before broad random draw when that preserves
  draw quality;
- play hand-reducing Items before a hand refresh when their effect remains
  useful;
- preserve discard costs until the agent has selected the least valuable legal
  resources;
- attach Tools to the Pokémon expected to benefit for more than one turn;
- replace or play a Stadium only when its net board value is positive;
- evolve before evaluating final attack damage and survivability;
- avoid consuming a once-per-turn effect before its target or follow-up action
  is available.

### 5. Attach Energy

Evaluate the single normal Energy attachment separately from effect-based
Energy acceleration.

Priority:

1. enable the selected Active attacker to attack this turn;
2. complete the Active attack with the best Prize or damage value;
3. prepare the next attacker on the Bench;
4. prepare a support Pokémon only when its attack or retreat plan matters;
5. avoid over-attaching Energy that does not improve an attack, retreat, or
   protected future plan.

For each target, calculate:

- current attached Energy;
- Energy still required for each legal attack;
- whether the attachment makes an attack legal immediately;
- expected survival until the next turn;
- retreat and attack-discard costs;
- risk of losing the Energy through a Knock Out;
- Energy acceleration or recovery available later.

### 6. Attack or end the turn

Attacking is the final main decision. If a legal attack exists, the default is
to attack. Ending the turn without attacking requires an explicit strategic
reason.

Rank legal attacks by:

- immediate game win;
- donk;
- Knock Out and Prize cards taken;
- effective damage after Weakness, Resistance, and effects;
- damage efficiency relative to discarded Energy, self-damage, deck discard,
  or other costs;
- protection or setup created for the next turn;
- exposure to the opponent's likely counterattack;
- deck-out risk.

`END` is selected only when:

- no legal attack exists;
- every legal attack has a demonstrably worse consequence than passing;
- a mandatory effect has already ended the useful action sequence; or
- a documented matchup rule intentionally declines the attack.

The reason for passing must be emitted in the decision trace. A generic
`safe_end_turn` reason is insufficient.

## Nested selection rules

Actions can open additional decisions for search targets, discard costs,
Energy costs, switching, damage counters, and yes/no effects. The agent must:

- preserve the original option positions;
- satisfy the cardinality for the current prompt only;
- recognize that `remainEnergyCost` and `remainDamageCounter` may be fulfilled
  through repeated prompts;
- resolve each option against its referenced zone, player, and card;
- use the parent action plan when selecting targets and costs;
- fall back deterministically without converting a legal repeated prompt into
  an empty selection.

## Behavioral monitoring

Every evaluation report should track at least:

- `PLAY`, `ATTACH`, `EVOLVE`, `ABILITY`, `RETREAT`, `ATTACK`, and `END` counts;
- productive-main-action rate;
- end-turn rate;
- matches with at least one attack;
- attacks per match;
- turns to first attack;
- Energy attachments that enable an attack;
- Bench occupancy and prepared backup attackers;
- legal Snover plays skipped before an attack or `END`;
- legal Snover-to-Abomasnow evolutions skipped before an attack or `END`;
- Snover-to-Mega-Abomasnow conversion rate and turns to first backup attacker;
- losses caused by having no replacement Pokémon after an Active Knock Out;
- Supporter usage by role;
- Knock Outs and Prize cards taken;
- donks;
- wins by Prizes, board elimination, deck-out, and other causes;
- invalid repeated-cost selections;
- decision latency by context.

A candidate that completes matches but produces no attacks or wins only by
deck-out fails the gameplay gate even when `INVALID`, `ERROR`, and `TIMEOUT`
remain zero.

## Current implementation coverage

The recovery implementation started after validation episode `88828439`
exposed an end-turn-only policy.

Currently covered:

- real CABT option and card resolution through the competition `cg` catalog;
- productive main-action priority over `END`;
- basic board development, Evolution, attachment, Supporter/Item, Ability, and
  attack priorities;
- deck-specific attack estimates for Mega Abomasnow ex and Kyogre;
- repeated Energy-cost prompt handling;
- behavioral smoke metrics for productive actions, attacks, and end-turn rate.

Latest recovery evidence on 2026-07-29: 200 balanced games against `random`
completed with zero operational failures, attacks in 200/200 games, 472 total
attacks, 1,942 productive main actions, a 9.34% end-turn rate, and 179 wins.
This proves minimum observable gameplay against that opponent, not optimal play
or promotion across the required matchup matrix.

Still incomplete:

- explicit Supporter need-vector calculation;
- persistent turn plan shared across nested selections;
- reliable attack damage including all card effects;
- Prize, Knock Out, donk, and termination-reason metrics;
- continuous Snover/Abomasnow development before non-winning attacks;
- board-aware Bench management and resource preservation;
- strategic pass rules;
- full 200-match promotion evidence against a fixed opponent matrix.

## Rule proposal template

Additions should use this structure:

```text
Rule:
Trigger:
Desired action:
Exceptions:
Required observation/card knowledge:
Reason codes:
Metrics:
Golden scenarios:
```

Every accepted rule should eventually have at least one real-observation
fixture and one evaluation metric.

## Human demonstrations

Rules may also be proposed from monitored human gameplay. The capture workflow,
trace schema, live-player interfaces, reasoning annotations, and safeguards are
defined in [`28_human_gameplay_capture.md`](28_human_gameplay_capture.md).
Human choices are treated as preference evidence rather than automatic
ground-truth labels.
