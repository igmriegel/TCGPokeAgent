# Human decision index

> Canonical interview record for the reasoning a human player wants the generic
> CABT engine to follow. This document describes desired play; it does not report
> active policy rules, task status, or promotion evidence.

**Document status:** `INTERVIEW DRAFT`

**Active interview phase:** `9 — Turn end and opponent plan`

**Confirmed phases:** `8 / 9`

**Runtime impact:** `PARTIAL`

## Purpose and authority

This index captures human decisions in match order, using conditions and
ordinal priorities rather than numeric weights. It is the canonical owner of
the desired human playbook. The following documents retain their existing
authority:

- [gameplay rules](27_gameplay_rules.md) own implemented and proposed runtime
  rules;
- [gameplay feedback](29_gameplay_feedback.md) owns individual feedback
  records and their validation lifecycle;
- [human gameplay capture](28_human_gameplay_capture.md) owns future live
  demonstration data;
- [competitive replay annotations](31_competitive_replay_annotations.md) own
  post-hoc reviews of automated matches;
- [project status](PROJECT_STATUS.md) and the
  [task index](03_tasks/TASK_INDEX.md) own current status and executable work.

CABT 1.32.2 is the executable authority. A difference from the physical TCG
may be recorded as a note, but it cannot override a legal CABT observation or
selection. The scope includes match play and declarative deck profiles, not
deck construction. The engine must remain usable with multiple decks.

No entry in this document changes `AgentPolicy.select() -> list[int]`. A
confirmed human decision becomes a rule or backlog item only after explicit
approval of the consolidated index.

## HDI v1 implementation boundary

The independent `AGENT_MODE=hdi_v1` runtime implements a partial, deterministic
subset of the confirmed records. It validates legal selections through the
shared generator, derives only actor-visible facts, prioritizes guaranteed
wins and Knock Outs, separates guaranteed from potential damage, applies
Rule Box damage prevention, uses declarative attack/cost/resource roles,
prepares attackers, handles promotion and discard ordering, and preserves
original CABT option indices as the final tie-breaker.

The implementation is intentionally `PARTIAL`: complete Trainer chains,
multi-action reservations, every attack effect, every opponent damage
projection, and unobservable or ambiguous conditions remain `TBD`. No new
`BeliefState` is introduced. `HDI-7-04` remains pending and is not implemented
or inferred from current behavior.

## Knowledge boundary

Every decision separates these inputs:

| Input class | Meaning | Runtime examples |
|---|---|---|
| Visible fact | Actor-visible state supplied or derivable without uncertainty | Legal options, original option indices, Active and Bench, HP, attached cards, public discard, hand contents for the actor, hand/deck counts, turn flags |
| Declared deck fact | Versioned information about the player's own deck | Card multiset, roles, Evolution lines, attack Energy targets, critical resources |
| Belief | A hypothesis that may be wrong | Opponent hand contents, remaining response cards, matchup identity, Prize hypotheses, likely next action |
| Later evidence | Information available only after the decision | Opponent's eventual response, final result, cards revealed later |

`GameState` may contain only facts. Hidden information and matchup hypotheses
belong in `BeliefState` or another explicitly probabilistic strategic input.
Later evidence may validate or refute a rule, but must never be inserted into a
runtime feature for the earlier decision.

## Coverage vocabulary

The four coverage dimensions are independent:

| Dimension | Allowed values | Meaning |
|---|---|---|
| Human | `UNREVIEWED`, `DRAFT`, `CONFIRMED` | Whether the player has reviewed and accepted the reasoning |
| CABT | `UNMAPPED`, `MAPPED`, `MECHANICAL` | Whether the decision is associated with CABT prompts, or the prompt only executes an already-made choice |
| Implementation | `NONE`, `PARTIAL`, `COMPLETE` | Whether current policy behavior implements the confirmed conditions, exceptions, and tie-breakers |
| Validation | `NONE`, `FIXTURE`, `REPLAY`, `MATRIX` | Strongest available evidence; stronger evidence does not imply human confirmation |

`COMPLETE` is prohibited while any stated exception or tie-breaker is absent.
`REPLAY` requires a decision-linked replay example, not merely a replay file.
`MATRIX` requires a frozen comparison with the relevant scenario or matchup.

## Decision record contract

Each accepted decision receives a stable `HDI-<phase>-<number>` identifier and
must contain:

1. the question the player is answering;
2. the strategic objective;
3. visible and declared facts used;
4. beliefs about the opponent, matchup, or likely responses;
5. ordered priority conditions;
6. vetoes and exceptions;
7. deterministic tie-breakers;
8. action, turn, or multi-turn horizon;
9. dependencies on the declarative deck profile;
10. corresponding `SelectContext` and `OptionType` values;
11. independent Human, CABT, Implementation, and Validation coverage;
12. evidence links or an explicit `none`.

Until a phase is confirmed, its entries are candidate questions, not approved
rules. Unknown values remain `TBD`; they are not filled from replay frequency
or current heuristic behavior.

## Interview workflow

1. Open only one phase.
2. Present its initial human checklist and current agent coverage.
3. Record corrections, missing decisions, exceptions, and priority order.
4. Resolve contradictions within the phase and with earlier confirmed phases.
5. Write a phase summary and ask for explicit confirmation.
6. After confirmation, sample the replay corpus for examples and exceptions.
7. Freeze the phase and open the next one.

If a later phase contradicts a confirmed earlier decision, both phases return
to `DRAFT` until the reviewer resolves the conflict. Replays test declared
rules; they do not define them.

## Phase register

| Phase | Scope | Human | CABT | Implementation | Validation | Gate to close |
|---:|---|---|---|---|---|---|
| 1 | Deck profile and pre-game plan | `CONFIRMED` | `MAPPED` | `PARTIAL` | `REPLAY` | Closed; replay sampling may add evidence but cannot redefine the phase |
| 2 | Setup | `CONFIRMED` | `MAPPED` | `PARTIAL` | `REPLAY` | Closed; mulligan remains an explicit executable-evidence gap |
| 3 | State reading | `CONFIRMED` | `MAPPED` | `PARTIAL` | `REPLAY` | Closed; replay sampling may add evidence but cannot redefine the phase |
| 4 | Turn plan | `CONFIRMED` | `MAPPED` | `PARTIAL` | `REPLAY` | Closed; replay sampling may add evidence but cannot redefine the phase |
| 5 | Draw, search, and development | `CONFIRMED` | `MAPPED` | `PARTIAL` | `REPLAY` | Closed; replay sampling may add evidence but cannot redefine the phase |
| 6 | Energy and mobility | `CONFIRMED` | `MAPPED` | `PARTIAL` | `FIXTURE` | Closed; replay sampling may add evidence but cannot redefine the phase |
| 7 | Combat | `DRAFT` | `MAPPED` | `PARTIAL` | `FIXTURE` | Reviewer confirms target, attack, Prize-trade, and immediate-win logic |
| 8 | Costs and nested decisions | `CONFIRMED` | `MAPPED` | `PARTIAL` | `FIXTURE` | Closed; replay sampling may add evidence but cannot redefine the phase |
| 9 | Turn end and opponent plan | `CONFIRMED` | `MAPPED` | `PARTIAL` | `FIXTURE` | Closed; replay sampling may add evidence but cannot redefine the phase |

Phase-level evidence is only the strongest evidence for any item in the phase.
It is not proof that the whole phase is covered.

## Phase 1 — Deck profile and pre-game plan

**Interview state:** `CONFIRMED`

### Recorded reviewer input

The first review pass established the following desired behavior for
`mega_abomasnow_kyogre`:

- Mega Abomasnow ex is the primary attacker.
- Snover is the primary setup Pokémon. On the first turn, put as many legally
  available Snover into play as possible so they can evolve on the following
  turn.
- Kyogre is a secondary attacker whose main use is its first attack, `Riptide`,
  when Basic Water Energy has accumulated in the discard pile.
- Kyogre's second attack, `Swirling Waves`, is normally neither the intended
  line nor the strongest line for the deck.
- If setup or another legal constraint forces Kyogre into play, accept it, but
  continue to prioritize the Snover into Mega Abomasnow ex line.
- Play every legally available Snover even when doing so occupies almost the
  entire Bench. A generic reserved-slot preference does not veto Snover
  development for this deck.
- Mega Abomasnow ex normally uses its first attack, `Hammer-lanche`.
  `Frost Barrier` is an exception used only when Mega Abomasnow ex has all
  three required Energy and its damage is sufficient to Knock Out the opposing
  Pokémon.
- Kyogre should replace Mega Abomasnow ex as the attacker when the deck is near
  deck-out, when Mega Abomasnow ex was Knocked Out and no other attacker is
  energized, or when the known Basic Water Energy in the discard makes
  `Riptide` a certain Knock Out.
- For this plan, “near deck-out” means an own deck count from 14 down to 7
  cards. Seven or fewer cards represent an imminent rather than merely
  approaching deck-out risk.
- Kyogre is also the attacker against an opposing effect that prevents damage
  from Pokémon with a Rule Box.
- `Riptide` returns Basic Water Energy from the discard pile to the deck. This
  both reduces own deck-out risk and increases the chance that a later
  `Hammer-lanche` discards Basic Water Energy for damage.
- The intended win conditions are taking all Prize cards before the opponent
  or leaving the opponent with no Pokémon in play. Opponent deck-out is not a
  planned win route.
- Use Kyogre's `Swirling Waves` only if Kyogre used `Riptide` on the previous
  turn, now has all three required Energy, and `Swirling Waves` will certainly
  Knock Out the opposing Pokémon.
- Secret Box is a highest-priority Trainer: when it is in hand and its
  three-card discard cost is legal, use it. Prefer to discard Basic Water
  Energy or redundant Supporters, especially after Team Rocket's Petrel has
  already consumed the turn's Supporter use.
- Team Rocket's Petrel normally searches for Secret Box. Secret Box should
  take every available card category: Item, Pokémon Tool, Supporter, and
  Stadium.
- From Secret Box, choose Ultra Ball as the Item when more Snover development
  is needed, such as having only one Snover in play. Choose Mega Signal when a
  Mega Abomasnow ex is needed. Lillie's Determination is normally the
  Supporter choice, with Team Rocket's Petrel as an alternative.
- Use Lillie's Determination to refresh a hand with no useful playable Items or
  with too many Basic Water Energy. Do not use it when the current hand count
  plus deck count is at most six. At a combined count of seven it leaves
  deck-out on the following turn, so use it only when the same turn will use
  `Riptide` to restore Basic Water Energy to the deck or will win immediately.
- Use Surfing Beach when the damaged Active Water Pokémon can be replaced by a
  Benched Water Pokémon that is already energized to attack. Its primary
  purpose is a free switch that denies the opponent an expected Knock Out.
- Attach Powerglass to Kyogre only for a `Swirling Waves` line. After that
  attack discards two Energy, Powerglass may return one Basic Water Energy from
  the discard to Kyogre at the end of the turn. Powerglass is useless
  immediately after `Riptide`, because `Riptide` has already returned all Basic
  Water Energy from the discard to the deck. Outside a `Swirling Waves` line,
  Powerglass is a strong discard candidate for Ultra Ball or Secret Box.
- If Secret Box is in the deck, use Team Rocket's Petrel to search for it. If
  Secret Box is already in hand, use Secret Box rather than Petrel. If Secret
  Box is unavailable, Petrel searches for Mega Signal when an in-play Pokémon
  still needs to evolve; Ultra Ball when any Pokémon is needed, including
  another Snover, Mega Abomasnow ex, or Kyogre; Surfing Beach when a switch is
  needed; or Lillie's Determination for the following turn when the hand is
  small, contains too many Basic Water Energy, or has too few playable cards.
  When several fallback needs coexist, the order is Surfing Beach to prevent a
  Knock Out, Mega Signal to evolve, Ultra Ball to find any Pokémon, then
  Lillie's Determination for next-turn refresh.
- For Secret Box and Ultra Ball costs, discard in this order: Basic Water
  Energy, an unneeded Powerglass, then a redundant Supporter that cannot
  productively be played. Use lower-priority resources only when the required
  discard count cannot be met from those categories.
- Always put legally available Snover on the Bench. If every opposing Pokémon
  prevents damage from Pokémon with a Rule Box, keep the Snover unevolved and
  use Kyogre rather than creating Mega Abomasnow ex attackers that cannot deal
  damage.
- Productive duplicate cards are cumulative rather than alternatives. If two
  or more Snover can legally enter play, play all of them. If two or more Mega
  Signal or Ultra Ball can be used with useful legal targets, use every copy
  and resolve each search. When interchangeable copies appear at different
  legal-option positions, use the lower original CABT option index first, then
  continue with the remaining copies in later prompts.
- Before using the first of several Ultra Ball, plan the discard costs and
  targets for the entire sequence. A card just searched for as part of that
  plan must not become the discard cost of the next Ultra Ball.
- Never discard the last available copy of any Pokémon, whether Basic or
  Evolution, or a singleton card such as the ACE SPEC Secret Box, except when
  the discard produces an immediate win or prevents an immediate loss. If
  availability is uncertain, keep that uncertainty explicit rather than
  treating the copy as safely replaceable.
- Because this is a simple Evolution deck, prefer to play first in almost every
  match so the deck can evolve before the opponent. This setup choice is
  preserved as early input for Phase 2; its exceptions remain unreviewed.

CABT catalog and deck verification support the factual parts of this input:
the submitted list contains four Snover, four Mega Abomasnow ex, and two
Kyogre; Snover evolves into Mega Abomasnow ex; and `Riptide` scales with Basic
Water Energy in the discard pile. These facts do not establish the strategic
priorities by themselves—the priorities come from the reviewer.

The bundled profile now represents Mega Abomasnow ex as the primary attacker,
Kyogre as the conditional secondary attacker, Snover as the development
priority, and the one-Energy `Riptide` line separately from three-Energy
`Swirling Waves`. It also declares zero reserved Bench slots for this deck.
The runtime coverage remains partial because the complete multi-turn Trainer
and attacker-switch plan is not represented.

The current heuristic can count Basic Water Energy in the discard for
`Riptide` damage and has partial Rule Box prevention handling. It does not
represent `Riptide` as deck-out prevention or as preparation for a later
`Hammer-lanche`, and it does not maintain this reviewed attacker-switch plan
across turns.

Trainer coverage is also partial. The current heuristic does not preserve the
Team Rocket's Petrel → Secret Box → need-specific target sequence, apply
Lillie's Determination's hand-plus-deck veto, or value Surfing Beach by the
Knock Out it can deny. Nested search and discard prompts use generic resource
scores rather than the reviewed category targets and cost order. The policy
also has no general persistent plan that reserves targets and discard costs
across two or more Item uses.

### Initial checklist and current coverage

| Candidate topic | Expected human question | Current agent behavior |
|---|---|---|
| Card roles | What job can each card perform in this matchup and game stage? | `DeckProfile.roles` declares broad roles; the generic builder infers Pokémon, attackers, primary attackers, support, and Evolution basics |
| Win routes | Which reachable route wins: Prizes, board removal, deck-out, or another CABT terminal condition? | `PrizeMap` represents public Prize routes; no complete multi-route pre-game plan exists |
| Attacker plan | Which Pokémon is the primary attacker, backup, pivot, or situational attacker? | Roles and attack Energy targets exist; setup and attachment use simple role/energy preferences |
| Evolution plan | Which Evolution lines must be established, and by when? | Evolution lines are declarative; policy broadly prefers legal Evolution but does not maintain a confirmed timing plan |
| Critical resources | Which cards are required, expendable, recyclable, or safe to discard? | Per-card resource values exist; preservation logic is coarse and context-limited |
| Board targets | How many attackers and free Bench slots should be maintained? | Profile supports `minimum_attackers` and `reserved_bench_slots`; the enforced play-before-attack rule does not honor all exceptions |
| Matchup branches | Which threats and responses change the default plan? | No confirmed matchup plan is represented; current runtime does not use a complete opponent-model branch |

### Candidate record HDI-1-01 — Assign card roles

- **Question:** What role or roles does each card have at setup, development,
  combat, recovery, and closing?
- **Objective:** Give later decisions deck-specific meaning without embedding
  card identifiers in generic policy code.
- **Facts:** Own 60-card multiset, CABT catalog text, Evolution lines, attack
  costs and effects, Rule Box traits, and declared profile version.
- **Beliefs:** Matchup-dependent role changes and expected usefulness against
  likely opposing threats.
- **Priority conditions:** For `mega_abomasnow_kyogre`, assign Mega Abomasnow
  ex the primary-attacker role, Snover the primary-setup and Evolution-basic
  roles, and Kyogre the conditional-secondary-attacker role. Kyogre becomes
  relevant when it prevents own deck-out, replaces a Knocked Out Mega
  Abomasnow ex with no energized replacement, earns a certain `Riptide` Knock
  Out from the known discard, or bypasses damage prevention against Rule Box
  Pokémon. There is no fixed minimum discard-Energy count.
- **Vetoes and exceptions:** A card must not receive a role unsupported by
  executable CABT behavior; matchup-specific roles must be labeled as beliefs.
  Do not treat `Swirling Waves` as Kyogre's default line. Use it only after
  `Riptide` on the previous turn, with three attached Energy, and for a certain
  Knock Out.
- **Tie-breakers:** Between otherwise equivalent opening Pokémon-development
  choices, prefer Snover over Kyogre. Among strategically equivalent copies,
  choose the lower original CABT option index first and continue using the
  remaining productive copies in later prompts.
- **Horizon:** Multi-turn and whole match.
- **Deck-profile dependency:** `roles`, `evolution_lines`, and any approved
  extension for phase- or matchup-specific roles.
- **CABT mapping:** Indirectly informs every strategic context; most visible in
  `MAIN`, `SETUP_ACTIVE_POKEMON`, `SETUP_BENCH_POKEMON`, `TO_HAND`,
  `DISCARD`, `ATTACH_TO`, and `ATTACK`.
- **Option types:** `PLAY`, `ATTACH`, `EVOLVE`, `ABILITY`, `CARD`,
  `ENERGY_CARD`, `ENERGY`, `ATTACK`, `DISCARD`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `REPLAY`.
- **Evidence:** Reviewer interview input plus CABT catalog and submitted-deck
  verification. The declarative profile and generic builder are implementation
  references, not validation evidence.

### Candidate record HDI-1-02 — Choose the default win route

- **Question:** What is the default path to victory, and which observable
  conditions justify changing it?
- **Objective:** Align setup, development, resource use, and combat with a
  reachable terminal condition.
- **Facts:** Own deck, Prize counts, public board, deck counts, known attack
  effects, and CABT terminal semantics.
- **Beliefs:** Opponent archetype, likely Prize liabilities, recovery capacity,
  and responses.
- **Priority conditions:** Immediate legal win precedes longer routes. The
  reviewed default combat route develops Snover into Mega Abomasnow ex, then
  wins by taking all Prize cards or leaving the opponent with no Pokémon in
  play. Opponent deck-out is not a planned win route. Kyogre is a conditional
  route-preserving attacker, not a separate terminal objective.
- **Vetoes and exceptions:** Do not call a route reachable when a required
  resource is confirmed unavailable. Do not pursue opponent deck-out instead
  of a reachable Prize or board-removal route.
- **Tie-breakers:** Prefer the line that reaches a confirmed immediate win.
  Non-terminal attack and target ordering belongs to the Phase 7 combat
  review; Phase 1 fixes the permitted win routes without inventing that later
  priority.
- **Horizon:** Whole match, re-evaluated each turn.
- **Deck-profile dependency:** Win conditions, Prize liabilities, recovery
  resources, and matchup branches are not fully represented in profile v1.
- **CABT mapping:** `MAIN`, `ATTACK`, `TO_PRIZE`, `DAMAGE`,
  `DAMAGE_COUNTER`, `EFFECT_TARGET`, `DRAW_COUNT`, and `END` through the
  `MAIN` option set.
- **Option types:** `ATTACK`, `PLAY`, `ABILITY`, `CARD`, `NUMBER`, `END`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `NONE`.
- **Evidence:** Reviewer interview input identifies the default attacker line.
  `PrizeMap` and termination metrics are implementation support, not a
  confirmed terminal-route priority order.

### Candidate record HDI-1-03 — Define attacker and resource sequence

- **Question:** Which attacker, backup attacker, Evolution line, and critical
  resources must be ready at each stage?
- **Objective:** Avoid isolated Active development, board collapse, and spending
  resources that make the next attacker unreachable.
- **Facts:** Declared roles, attack costs, Evolution lines, board targets, card
  counts, and visible resource zones.
- **Beliefs:** Expected KO timing, gust/switch pressure, disruption, and
  matchup-specific attacker value.
- **Priority conditions:** On the first turn, put the greatest legally
  available number of Snover into play, up to the four copies in the submitted
  deck, even if this occupies almost the entire Bench, to maximize next-turn
  Mega Abomasnow ex Evolution opportunities. Continue to prioritize this line
  if Kyogre is forced into play. Mega Abomasnow ex normally uses
  `Hammer-lanche`; use `Frost Barrier` only with all three required Energy and
  enough damage for a certain Knock Out. Switch to Kyogre when (1) the own deck
  has 14 down to 7 cards and `Riptide` can return Basic Water Energy, (2) Mega
  Abomasnow ex was Knocked Out and no other attacker is energized, (3) known
  discard Energy makes `Riptide` a certain Knock Out, or (4) the opposing
  Pokémon prevents damage from Pokémon with a Rule Box. Use `Swirling Waves`
  only after using `Riptide` on the previous turn, with all three Energy
  attached, and when its damage produces a certain Knock Out.
- **Vetoes and exceptions:** Immediate victory may supersede future setup;
  legal setup constraints may force Kyogre into play. Do not reserve a Bench
  slot at the cost of declining a legal Snover. Confirmed-unavailable-resource
  exceptions still apply. An own deck count of six or fewer is already a
  critical draw/discard state rather than the normal 14-to-7 Kyogre trigger
  range.
- **Tie-breakers:** Prefer a line that creates an additional next-turn Mega
  Abomasnow ex Evolution opportunity. Among equivalent Snover copies, play the
  lower original CABT option index first, then play the remaining copies
  through later `MAIN` prompts.
- **Horizon:** Current turn through the next replacement cycle.
- **Deck-profile dependency:** `roles`, `evolution_lines`,
  `attack_energy_targets`, `board_targets`, and `resource_values`.
- **CABT mapping:** `SETUP_ACTIVE_POKEMON`, `SETUP_BENCH_POKEMON`, `MAIN`,
  `EVOLVE`, `EVOLVES_FROM`, `EVOLVES_TO`, `ATTACH_TO`, `ATTACH_ENERGY`,
  `TO_ACTIVE`, and `SWITCH`.
- **Option types:** `PLAY`, `EVOLVE`, `ATTACH`, `CARD`, `ENERGY`,
  `ENERGY_CARD`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `REPLAY`.
- **Evidence:** Reviewer interview input establishes the Snover-first
  development plan. Episode 88879568 shows a missed replacement attacker and
  supports the need for development, but it does not settle all exceptions.

### Candidate record HDI-1-04 — Define matchup branches

- **Question:** Which observed or inferred opponent characteristics change the
  default win route, attacker plan, board size, or resource valuation?
- **Objective:** Make matchup adaptation explicit while keeping uncertainty out
  of factual state.
- **Facts:** Revealed opposing cards, public board, discard, actions, Prize and
  deck counts, and the actor's own deck.
- **Beliefs:** Opponent deck identity, hidden responses, likely target order,
  and confidence in each hypothesis.
- **Priority conditions:** Use the default plan until a declared evidence
  threshold supports a branch. A visible effect that prevents damage from
  Pokémon with a Rule Box is a factual branch: use non-Rule-Box Kyogre rather
  than attacking into the prevention with Mega Abomasnow ex. If every opposing
  Pokémon has that protection, continue putting Snover on the Bench but do not
  evolve them into Mega Abomasnow ex. No other Phase 1 matchup branch changes
  the Snover-first development plan.
- **Vetoes and exceptions:** Never treat an inferred list, hand, or response as
  a fact. Fall back to the default branch when beliefs are inconsistent.
- **Tie-breakers:** Apply the Rule Box-protection branch only from a visible
  effect. Otherwise retain the default Snover-first plan rather than promoting
  an uncertain matchup belief to fact.
- **Horizon:** Multi-turn and whole match.
- **Deck-profile dependency:** Requires a declarative matchup section not
  present in profile v1.
- **CABT mapping:** Indirect input to all strategic contexts, especially
  `MAIN`, `TO_HAND`, `DISCARD`, `ATTACH_TO`, `SWITCH`, `ATTACK`, and
  `EFFECT_TARGET`.
- **Option types:** Potentially all strategic option types.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `REPLAY`.
- **Evidence:** The replay corpus contains varied opponent decks, but no replay
  is accepted here until the conceptual branch is confirmed.

### Candidate record HDI-1-05 — Assign Trainer and resource roles

- **Question:** Which Trainers are mandatory, conditional, expendable, or
  protected, and what should each search effect take?
- **Objective:** Convert the simple attacker plan into a deterministic setup,
  refresh, mobility, and resource-recycling sequence.
- **Facts:** Submitted card counts, actor-visible hand and deck counts, public
  board and damage, Supporter/Stadium/attachment flags, legal options, and CABT
  card text.
- **Beliefs:** Whether the damaged Active is likely to be Knocked Out and
  whether a searched card can remain useful through the opponent's response.
- **Priority conditions:** Use a legal Secret Box in hand. Team Rocket's
  Petrel normally searches for Secret Box. Pay Secret Box's three-card cost
  first with Basic Water Energy, then an unneeded Powerglass, then a redundant
  unusable Supporter, before lower-priority cards. Take every available
  category from Secret Box. Choose Ultra Ball when the board needs more
  Snover, Mega Signal when it needs Mega Abomasnow ex, Lillie's Determination
  as the normal Supporter, and Team Rocket's Petrel as the alternative
  Supporter. If Secret Box is unavailable, Petrel chooses Mega Signal for an
  unevolved in-play Pokémon, Ultra Ball for any needed Pokémon, Surfing Beach
  for a needed switch, or Lillie's Determination as next-turn hand refresh.
  When several needs coexist, choose Surfing Beach to prevent a Knock Out,
  then Mega Signal, then Ultra Ball, then Lillie's Determination.
  Attach Powerglass to Kyogre only as part of a `Swirling Waves` line;
  otherwise treat it as a preferred discard-cost candidate. Use Lillie's
  Determination for an unproductive hand or excess Basic Water Energy. Use
  Surfing Beach to move a damaged Active into safety when an attack-ready
  Benched Water Pokémon can replace it.
- **Vetoes and exceptions:** Do not use Lillie's Determination when current
  hand count plus deck count is at most six. A combined count of seven creates
  known next-turn deck-out risk; use Lillie at seven only if the same turn
  restores Basic Water Energy with `Riptide` or wins immediately. Do not attach
  Powerglass for `Riptide`, because that attack leaves no eligible Basic Water
  Energy in the discard for the Tool's end-of-turn effect. Do not spend the
  turn's Supporter use on Team Rocket's Petrel merely to obtain Secret Box when
  Secret Box is already in hand; play Secret Box directly. Never discard the
  last available copy of any Basic or Evolution Pokémon, or a singleton such
  as Secret Box, unless doing so wins immediately or prevents an immediate
  loss.
- **Tie-breakers:** For Secret Box's Item, current board need decides between
  Ultra Ball for Snover and Mega Signal for Mega Abomasnow ex. The confirmed
  discard order is Basic Water Energy, unneeded Powerglass, then unusable
  duplicate Supporters. Petrel's fallback order is defensive Surfing Beach,
  Mega Signal, Ultra Ball, then next-turn Lillie's Determination.
- **Horizon:** Current turn through the next attack and draw.
- **Deck-profile dependency:** Requires explicit search targets, discard-cost
  preferences, hand-refresh vetoes, mobility roles, and cross-turn Tool
  sequences not represented in profile v1.
- **CABT mapping:** `MAIN`, `TO_HAND`, `DISCARD`,
  `DISCARD_CARD_OR_ATTACHED_CARD`, `ATTACH_TOOL`, `SWITCH`, `TO_ACTIVE`,
  `TO_BENCH`, and nested card-selection contexts.
- **Option types:** `PLAY`, `CARD`, `DISCARD`, `TOOL_CARD`, `ATTACH`,
  `YES`, and `NO`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `REPLAY`.
- **Evidence:** Reviewer interview input and CABT catalog text. The revised
  Powerglass sequence is conceptually consistent but still has no dedicated
  executable fixture.

### Candidate record HDI-1-06 — Repeat productive copies safely

- **Question:** After resolving one useful copy, should the turn continue with
  additional legal copies, and which future costs must the first action
  preserve?
- **Objective:** Complete all useful same-turn development and searches without
  allowing an early cost choice to destroy a later planned action.
- **Facts:** Current hand, board and Bench capacity, legal options and original
  indices, remaining searchable Pokémon, already-used cards, and the discard
  costs of every Item still intended for the turn.
- **Beliefs:** None are required for identical setup searches; opponent-response
  beliefs may matter only when the searched targets differ strategically.
- **Priority conditions:** Play every legally available Snover. Use every legal
  Mega Signal and Ultra Ball that still has a useful target. Resolve repeated
  cards through successive CABT prompts rather than treating the first selected
  copy as the only desired action.
- **Vetoes and exceptions:** Do not use a repeated search with no useful legal
  target. Before the first of multiple Ultra Ball uses, reserve the cards and
  discard costs required by later uses. Do not discard a newly searched card
  that belongs to the declared multi-search plan as the cost of the next Ultra
  Ball.
- **Tie-breakers:** Strategic target need decides before copy order. For truly
  interchangeable copies, play the lower original CABT option index first,
  accept the next prompt, and continue until every productive planned copy has
  been used.
- **Horizon:** Entire current turn across successive `MAIN`, search, and
  discard prompts.
- **Deck-profile dependency:** Requires repeated-action targets and protected
  cross-action resources not represented in profile v1.
- **CABT mapping:** `MAIN`, `TO_HAND`, `DISCARD`, and nested search/cost
  contexts.
- **Option types:** `PLAY`, `CARD`, and `DISCARD`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `REPLAY`.
- **Evidence:** Reviewer interview input, focused repeated-Pokémon fixture, and
  replay examples for repeated Snover and Mega Signal. Repeated Ultra Ball
  planning and cross-action cost reservation still have no fixture or
  adjudicable replay.

### Phase 1 confirmation summary

The reviewed pre-game plan is:

1. declare a preference to play first in almost every match so the deck can
   evolve before the opponent; its setup exceptions remain for Phase 2;
2. put every legally available Snover into play, using lower original CABT
   indices first only as a mechanical order;
3. make Mega Abomasnow ex the primary attacker and `Hammer-lanche` its default
   attack; use `Frost Barrier` only with three Energy and a certain Knock Out;
4. use Kyogre and primarily `Riptide` for the declared deck-out, replacement,
   certain-KO, and Rule Box-prevention branches;
5. pursue only Prize completion or removal of every opposing Pokémon as win
   routes;
6. prioritize Secret Box and resolve Petrel, search targets, repeated Items,
   discard costs, Lillie, Powerglass, and Surfing Beach according to
   `HDI-1-05` and `HDI-1-06`;
7. preserve the last available copy of every Pokémon and singleton cards unless
   spending one wins immediately or prevents an immediate loss;
8. keep facts and beliefs separate, and retain the default plan unless visible
   Rule Box damage prevention activates the confirmed matchup branch.

No policy or deck profile changes are authorized by this summary. Reviewer
confirmation authorizes replay sampling; promotion to rules or backlog still
requires separate explicit approval.

**Reviewer confirmation:** Accepted on 2026-07-30. Later evidence may annotate
support, contradiction, or non-adjudicable cases, but changing the playbook
requires reopening Phase 1.

### Phase 1 replay sample

All 91 JSON files in the local raw replay snapshot were screened. Eighty-nine
expose the standard initial deck payload; they contain 95 player sides using
the exact Mega Abomasnow/Kyogre list and 2,391 parseable decisions for those
sides. Episodes
[`88823545`](../data/raw/kaggle/kaggle_gameplay_runs/88823545.json)
and
[`88825809`](../data/raw/kaggle/kaggle_gameplay_runs/88825809.json)
contain only two initialization steps and no deck payload, so they are
non-adjudicable for this phase.

These are behavior examples, not demonstrations of optimal play:

| Decision family | Decision-linked evidence | Interpretation |
|---|---|---|
| Snover-first repeated development | Episode [`88882619`](../data/raw/kaggle/kaggle_gameplay_runs/88882619.json), side 1, decisions `8`, `9`, and `10`, plays three Snover successively on turn 2 | Supports the executable shape of `HDI-1-03` and `HDI-1-06`; it does not prove every available Snover was found |
| Repeated search Items | Episode [`88836243`](../data/raw/kaggle/kaggle_gameplay_runs/88836243.json), side 1, decisions `12` and `14`, plays two Mega Signal on turn 2 | Supports repeated Item resolution; no repeated-Ultra-Ball example was found |
| Rule Box-prevention branch | Episode [`88836301`](../data/raw/kaggle/kaggle_gameplay_runs/88836301.json), side 0, decision `20`, uses Kyogre's `Riptide` against Active Crustle with visible prevention against attacks from Pokémon ex | Supports using non-Rule-Box Kyogre rather than Mega Abomasnow ex in that factual branch |
| Kyogre second-attack transition | Episode [`88840528`](../data/raw/kaggle/kaggle_gameplay_runs/88840528.json), side 0, decision `45`, uses `Swirling Waves` after the previous `Riptide` against an opposing Pokémon at 50 HP | Matches the confirmed transition and certain-KO condition |
| Mega Abomasnow attack exception | Episode [`88879568`](../data/raw/kaggle/kaggle_gameplay_runs/88879568.json), side 0, decision `100`, uses `Frost Barrier` against an opposing Pokémon at 70 HP | The attack satisfies the damage condition, but the accepted annotation still marks the preceding failure to develop Kyogre as a sequencing mistake |
| Secret Box full-category resolution | Episode [`88836827`](../data/raw/kaggle/kaggle_gameplay_runs/88836827.json), side 1, decisions `18`–`22`, pays three discards and takes Ultra Ball, Powerglass, Lillie's Determination, and Surfing Beach | Supports taking every available category; the exact discard preservation rule is not fully adjudicable from this sequence |
| Petrel before an in-hand Secret Box | Episode `88836827`, side 1, decision `15`, plays Petrel while Secret Box is visibly in hand, then plays Secret Box at decision `17` | Direct counterexample to the confirmed order and evidence that current behavior is not complete |

No selected `Riptide` occurred with own deck count from 14 through 7 in the
screened target decisions. The sample also contains no adjudicable example for
the Lillie seven-card boundary, repeated Ultra Ball cost reservation,
Powerglass after `Swirling Waves`, protection of a last available Pokémon or
singleton, or the all-opposing-Pokémon protection branch. Those remain
evidence gaps, not contradictions.

## Phase 2 — Setup

**Interview state:** `CONFIRMED`

| Candidate decision | Initial checklist | Current implementation |
|---|---|---|
| Mulligan | Redraw is mandatory only when the opening hand has no Basic Pokémon; opening quality does not create a voluntary mulligan | Generic yes/no heuristic prefers `NO` in `MULLIGAN`; this may conflict with the required redraw and needs a CABT fixture |
| First player | Choose first/second from deck plan, matchup, and first-turn restrictions. Early reviewer input says this Evolution deck should play first in almost every match so it can evolve first; exceptions await Phase 2 | Parsed and exposed; no deck- or matchup-aware rule |
| Active | Prefer survivability, mobility, attack timing, Evolution value, and donk resistance in declared order | Prefers an Evolution basic by a small fixed score |
| Initial Bench | Balance setup consistency, replacement attacker, liabilities, and reserved slots | Prefers Pokémon candidates; no complete liability or slot logic |
| Opening floor | Define the minimum keepable opening and recovery plan | Not represented |

### Recorded reviewer input

- Mulligan is not a strategic or optional hand-quality decision.
- An opening hand with no Basic Pokémon must be redrawn.
- An opening hand with at least one Basic Pokémon proceeds to setup; missing
  Snover, Energy, search, or other desirable cards does not independently
  permit a mulligan.
- Always choose to play first. There is no matchup or opening-hand exception
  for this deck.
- If both Snover and Kyogre are available for the initial Active, choose
  Snover.
- Put every remaining legally available Basic Pokémon on the Bench, including
  both Snover and Kyogre. Kyogre has special setup value as a replacement that
  prevents a donk loss if the Active is Knocked Out.
- The submitted deck's four Snover and two Kyogre fit exactly into one Active
  position plus the normal five Bench positions. If an abnormal CABT effect
  constrains capacity, preserve a Kyogre replacement before using the remaining
  slots for Snover.

The local CABT enum labels `MULLIGAN` as a yes/no redraw prompt, but neither the
Python surface nor the attributable replay sample establishes its trigger
condition. The physical-game rule supplied by the reviewer therefore defines
the desired handling, while an executable CABT fixture must verify which
option represents the mandatory redraw. No target-deck `MULLIGAN` prompt was
found in the replay sample.

### Candidate record HDI-2-01 — Resolve mulligan mechanically

- **Question:** Does the opening hand contain at least one Basic Pokémon?
- **Objective:** Reach a legal setup without discarding a playable opening for
  subjective hand-quality reasons.
- **Facts:** Actor-visible opening hand, Basic-Pokémon traits from the CABT
  catalog, legal `MULLIGAN` options, and the prompt cardinality.
- **Beliefs:** None. Hidden draws and desired opening quality do not change the
  forced rule.
- **Priority conditions:** If no Basic Pokémon is in hand, take the CABT option
  that redraws the hand. If at least one Basic is present, proceed with setup;
  do not seek a voluntary redraw because Snover, Energy, search, or another
  desirable card is missing.
- **Vetoes and exceptions:** Never keep an opening with no Basic Pokémon.
  Never represent a legal but weak opening as a mulligan opportunity.
- **Tie-breakers:** None; the Basic-Pokémon condition determines the outcome.
- **Horizon:** Setup action.
- **Deck-profile dependency:** Basic-Pokémon identification only; no
  deck-specific quality threshold.
- **CABT mapping:** `MULLIGAN`.
- **Option types:** `YES`, `NO`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `NONE`.
- **Evidence:** Reviewer correction and local enum text. No attributable replay
  or executable fixture currently establishes CABT's exact yes/no direction.

### Candidate record HDI-2-02 — Choose to play first

- **Question:** Should this deck play first or second?
- **Objective:** Reach Mega Abomasnow ex Evolution before the opponent can
  establish its own Evolution tempo.
- **Facts:** Declared Evolution line, CABT `IS_FIRST` options, and first-turn
  Evolution restrictions.
- **Beliefs:** None. Matchup identity and opening quality do not create an
  exception.
- **Priority conditions:** Always choose to play first.
- **Vetoes and exceptions:** Do not choose second for this deck.
- **Tie-breakers:** None.
- **Horizon:** Setup through the first Evolution turn.
- **Deck-profile dependency:** The deck is an Evolution deck centered on
  Snover into Mega Abomasnow ex.
- **CABT mapping:** `IS_FIRST`.
- **Option types:** `YES`, `NO`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `COMPLETE`;
  Validation `REPLAY`.
- **Evidence:** Reviewer input and all 43 attributable replay decisions, each
  of which selected `YES`.

### Candidate record HDI-2-03 — Choose the initial Active

- **Question:** Which opening Basic Pokémon should occupy the Active Spot?
- **Objective:** Start the primary Snover into Mega Abomasnow ex line while
  using the Bench for replacements.
- **Facts:** Basic Pokémon in the opening hand, original CABT option indices,
  declared Evolution roles, and legal Active candidates.
- **Beliefs:** None. Donk risk does not override Snover when Kyogre can instead
  be placed on the Bench.
- **Priority conditions:** Choose Snover over Kyogre whenever Snover is a legal
  initial Active. If no Snover is available, use the legal Kyogre.
- **Vetoes and exceptions:** Never fail setup while a legal Basic exists.
- **Tie-breakers:** Among equivalent Snover or Kyogre copies, use the lower
  original CABT option index.
- **Horizon:** Setup through the next-turn Evolution opportunity.
- **Deck-profile dependency:** Snover is `evolution_basic`; Mega Abomasnow ex
  is the primary attacker; Kyogre is the conditional secondary attacker.
- **CABT mapping:** `SETUP_ACTIVE_POKEMON`.
- **Option types:** `CARD`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `REPLAY`.
- **Evidence:** Reviewer input and the Phase 2 replay sample. When both
  candidates were legal, the observed behavior chose Snover in 13 of 16
  decisions and Kyogre in three; the counterexamples keep implementation
  coverage partial.

### Candidate record HDI-2-04 — Fill the initial Bench and prevent donk

- **Question:** Which remaining opening Basic Pokémon should enter the Bench?
- **Objective:** Maximize Snover Evolution opportunities and retain a
  replacement Pokémon so loss of the Active does not immediately end the
  match.
- **Facts:** Remaining Basic Pokémon in hand, occupied and maximum Bench slots,
  Active choice, original option indices, and declared roles.
- **Beliefs:** None under normal capacity; Kyogre's anti-donk value does not
  require predicting a specific opponent attack.
- **Priority conditions:** Bench every legally available remaining Snover and
  Kyogre. If abnormal capacity makes every placement impossible, preserve one
  Kyogre replacement first, then use remaining slots for Snover.
- **Vetoes and exceptions:** Do not leave a legal Basic in hand during setup
  when a Bench slot is available. Do not leave the Active as the only Pokémon
  when Kyogre can legally be Benched.
- **Tie-breakers:** For strategically equivalent copies, select lower original
  CABT indices first without removing any remaining copy from the setup plan.
- **Horizon:** Setup through the opponent's first attack and the first
  Evolution turn.
- **Deck-profile dependency:** All four Snover, both Kyogre,
  `evolution_lines`, and normal five-slot Bench capacity.
- **CABT mapping:** `SETUP_BENCH_POKEMON`.
- **Option types:** `CARD`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `REPLAY`.
- **Evidence:** Reviewer input and the Phase 2 replay sample. The observed
  behavior selected every offered Basic in 24 of 29 prompts but declined all
  offered Basics in five, including one prompt offering two Snover and one
  Kyogre.

### Initial Phase 2 replay inventory

The confirmed Phase 1 sample also establishes a setup baseline for the target
deck. This is automated behavior evidence, not the desired setup policy:

- all 43 observed `IS_FIRST` decisions selected `YES`;
- 95 `SETUP_ACTIVE_POKEMON` selections chose Snover 65 times and Kyogre 30
  times;
- the observed `SETUP_BENCH_POKEMON` selections placed Snover 11 times and
  Kyogre 15 times;
- no target-deck `MULLIGAN` decision appeared in the attributable sample.

These counts do not show whether another legal Basic was available, whether
the opening was vulnerable to a donk, or whether each Bench selection was
strategically correct. Exact decisions will be linked only after the human
setup rules are declared.

Required records: `HDI-2-01` mulligan, `HDI-2-02` first player,
`HDI-2-03` Active choice, and `HDI-2-04` initial Bench and donk protection.

### Phase 2 confirmation summary

The reviewed setup plan is:

1. redraw only when the opening hand contains no Basic Pokémon; this is a
   mandatory legality rule, not a hand-quality choice;
2. always choose to play first;
3. choose Snover as the initial Active when available, otherwise use Kyogre;
4. Bench every other legally available Snover and Kyogre;
5. value a Benched Kyogre as anti-donk protection and, under abnormal capacity,
   preserve one Kyogre replacement before allocating remaining slots to
   Snover;
6. use lower original CABT option indices only to order equivalent copies.

No policy change is authorized.

**Reviewer confirmation:** Accepted on 2026-07-30. Later evidence may annotate
the setup records, but changing them requires reopening Phase 2.

### Phase 2 replay sample

The same 91-file corpus screened for Phase 1 was rescanned after the setup
rules were confirmed. It contains 95 attributable target-deck setup sides.
The following results describe recorded automated behavior; they do not define
the human rule:

| Confirmed decision | Screen result | Representative evidence | Interpretation |
|---|---:|---|---|
| `HDI-2-01` mandatory mulligan only | No target-deck `MULLIGAN` prompt | None | Executable CABT trigger and yes/no direction remain an evidence gap |
| `HDI-2-02` always play first | 43 of 43 `IS_FIRST` decisions selected `YES` | Episode [`88836301`](../data/raw/kaggle/kaggle_gameplay_runs/88836301.json), side 0, decision `1` | Supports the desired outcome across every attributable prompt |
| `HDI-2-03` prefer Snover when both are legal | Snover selected in 13 of 16 prompts offering both Snover and Kyogre | Episode [`88838414`](../data/raw/kaggle/kaggle_gameplay_runs/88838414.json), side 1, decision `2`, selects Snover at index 1 over Kyogre at index 0 | Shows the declared role can override lower-index fallback behavior |
| `HDI-2-03` forced Kyogre fallback | 27 prompts offered only Kyogre | Episode `88836301`, side 0, decision `2` | Supports the legal fallback shape but does not test a choice |
| `HDI-2-03` historical counterexamples | Kyogre selected in 3 of 16 prompts offering both | Episode [`88829569`](../data/raw/kaggle/kaggle_gameplay_runs/88829569.json), side 0, decision `3`, selects Kyogre at index 0 over Snover at index 1 | Direct counterexample; desired Active policy is not completely implemented |
| `HDI-2-04` Bench every offered Basic | Every offered option selected in 24 of 29 Bench prompts | Episode [`88837361`](../data/raw/kaggle/kaggle_gameplay_runs/88837361.json), side 0, decision `4`, Benches the offered Kyogre | Supports normal placement and anti-donk board width |
| `HDI-2-04` historical counterexamples | No offered option selected in 5 of 29 Bench prompts | Episode [`88832361`](../data/raw/kaggle/kaggle_gameplay_runs/88832361.json), side 1, decision `5`, declines two Snover and one Kyogre despite three legal slots | Direct counterexample to both maximum Snover development and Kyogre anti-donk protection |

For `SETUP_ACTIVE_POKEMON`, the remaining inventory consists of 52
Snover-only prompts and 27 Kyogre-only prompts. For
`SETUP_BENCH_POKEMON`, each percentage above is per CABT prompt, not per card
in the opening hand. The replay observation can prove which candidates CABT
offered in that prompt, but it cannot prove that a missing card was absent
from every hidden or unparsed setup source.

## Phase 3 — State reading

**Interview state:** `CONFIRMED`

| Candidate decision | Initial checklist | Current implementation |
|---|---|---|
| Immediate threats | Detect opponent win, KO, lock, gust, and board-collapse threats | Public HP/board and some damage signals exist; no complete threat model |
| Prize race | Compare remaining Prizes, liabilities, reachable KOs, and tempo | `PrizeMap` supplies partial public target value |
| Deck-out | Compare remaining draws, forced draw, recovery, and turn horizon | A factual `deck_out_risk` feature uses own deck count at most three |
| Resource state | Count available, committed, discarded, prized, and recyclable resources | Public zones and own `PrizeCheck` are partial |
| Belief update | Update opponent and Prize hypotheses without promoting them to facts | `BeliefState` contract exists; heuristic policy does not use a complete belief loop |

### Recorded reviewer input

- Read the state in this order:
  1. possibility of losing immediately;
  2. risk that the Active will be Knocked Out;
  3. existence of another attacker;
  4. risk of having no Pokémon left in play;
  5. Prize race;
  6. available resources;
  7. deck-out risk.
- The practical board-collapse signals are having only one Pokémon in play,
  having no Snover available to evolve, and having no attacker that can be
  energized. Each signal independently counts as board collapse.
- Compare the opponent's remaining Prizes with the Prize value of the Pokémon
  being considered for the Active Spot. If the opponent needs three Prizes,
  avoid promoting Mega Abomasnow ex and try to use Kyogre. If the opponent
  needs two, avoid promoting a two-Prize Rule Box Pokémon.
- The Prize-liability warning is strongest when the opposing Active can Knock
  Out the proposed Active in one attack: its publicly available attack damage
  is at least the proposed Active's remaining HP.
- Surviving the attack and then having a line to win on the next turn may
  justify exposing a Pokémon whose Prize value matches the opponent's
  remaining Prizes. A next-turn line never overrides an opponent win that
  happens first.
- A replacement attacker exists if it can already attack or can be made ready
  during the current turn. An attacker that will become ready only on the
  following turn counts only when at least one required Energy is already in
  hand.
- Audit resources in this provisional order: Snover and Mega Abomasnow ex,
  Kyogre, Energy by zone, Secret Box, Petrel/Mega Signal/Ultra Ball, Lillie,
  and already energized attackers.
- Predict the opponent's response only from public game information: cards
  revealed by search, attached Energy, and cards in the discard pile.
  Inferring the last copy from three or four discarded copies is an advanced
  belief and is explicitly deferred from the current playbook.

### Candidate record HDI-3-01 — Read immediate threats in order

- **Question:** What can cause a loss before the normal development plan can
  succeed?
- **Objective:** Prevent a terminal loss before evaluating lower-priority
  development or resource improvements.
- **Facts:** Remaining Prizes, Pokémon in play, Active remaining HP, public
  opposing attacks and effects, attached Energy, legal replacement Pokémon,
  own deck count, and known turn restrictions.
- **Beliefs:** None in the current scope. An opposing line is considered only
  when its enabling information is public.
- **Priority conditions:** Check immediate loss, Active Knock Out, replacement
  attacker, loss of the last Pokémon, Prize race, resources, and deck-out risk
  in that exact order. An empty deck with an unavoidable next draw is an
  immediate-loss condition in the first check; the seventh check covers the
  preventive 14-to-7-card risk band.
- **Vetoes and exceptions:** A certain terminal loss vetoes a normal setup or
  efficiency line.
- **Tie-breakers:** Use the confirmed threat-scan order. Action-level ties
  between equally effective answers remain for the turn-plan phase.
- **Horizon:** Current turn through the opponent's next turn.
- **Deck-profile dependency:** Mega Abomasnow ex is the primary attacker and
  Kyogre is the lower-Prize replacement.
- **CABT mapping:** Cross-cutting input to `MAIN`, `TO_ACTIVE`, `SWITCH`,
  `ATTACK`, and terminal choices.
- **Option types:** `PLAY`, `ATTACH`, `EVOLVE`, `RETREAT`, `ATTACK`, `END`,
  and `CARD`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `REPLAY`.
- **Evidence:** Reviewer ordering and the Phase 3 replay sample. The replay
  sequence can expose threat facts and subsequent behavior, but cannot prove
  the policy evaluated them in the confirmed order.

### Candidate record HDI-3-02 — Read board collapse and the Prize race

- **Question:** Can the proposed board or Active survive without giving the
  opponent its remaining Prizes?
- **Objective:** Preserve a viable attacker and avoid presenting a game-ending
  Prize liability.
- **Facts:** Pokémon in play, Snover available to evolve, attackers that are
  ready or can receive Energy, both players' remaining Prizes, each proposed
  Active's Prize value and remaining HP, and the opposing Active's public
  one-attack damage.
- **Beliefs:** None in the current scope.
- **Priority conditions:** Treat one Pokémon in play, no Snover to evolve, or
  no attacker that can be energized as board-collapse warnings. If the
  opponent needs three Prizes, avoid promoting Mega Abomasnow ex and prefer
  Kyogre. If the opponent needs two, avoid a two-Prize Rule Box Pokémon. Give
  this avoidance its greatest force when the opposing Active can take the
  Knock Out in one attack. A replacement counts when it is already ready, can
  be made ready during the current turn, or can be ready on the following turn
  while at least one required Energy is already in hand.
- **Vetoes and exceptions:** A proposed Active whose Prize value would end the
  game for the opponent may be exposed only if it survives the public attack.
  After survival is established, a next-turn winning line strengthens that
  choice. A next-turn win never overrides a certain opponent win that happens
  first.
- **Tie-breakers:** Among lines that survive, prefer the lower Prize liability;
  further readiness tie-breakers remain for Phase 6.
- **Horizon:** Opponent's next turn through the player's following turn.
- **Deck-profile dependency:** Mega Abomasnow ex gives three Prizes; Kyogre is
  the intended lower-liability alternative. The two-Prize rule is generic for
  other profiles.
- **CABT mapping:** Cross-cutting input to `MAIN`, `TO_ACTIVE`, `SWITCH`, and
  `ATTACK`.
- **Option types:** `CARD`, `PLAY`, `RETREAT`, `ATTACK`, and `END`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `REPLAY`.
- **Evidence:** Reviewer examples and the Phase 3 replay sample. The sample
  contains a forced exact-Prize promotion and a later exact-Prize one-attack
  threat, but no choice between Mega Abomasnow ex and Kyogre at the promotion
  prompt.

### Candidate record HDI-3-03 — Audit available resources

- **Question:** Which visible resources can still support the current and next
  attacker?
- **Objective:** Know whether the normal Mega Abomasnow ex line, a Kyogre
  fallback, or a recovery line is executable before choosing a turn plan.
- **Facts:** Actor-visible hand, field, deck and discard information, known
  revealed cards, Energy by zone, Evolution lines, search cards, Supporters,
  and attackers with attached Energy.
- **Beliefs:** Unknown Prize contents and unobserved cards are not facts.
- **Priority conditions:** Audit, in order, Snover and Mega Abomasnow ex;
  Kyogre; Energy in hand, field, discard, and deck; Secret Box;
  Petrel/Mega Signal/Ultra Ball; Lillie; and already energized attackers.
  After the resource audit, apply the confirmed deck-out bands: 14 through
  seven cards in the deck is near deck-out. Separately, a combined hand-plus-
  deck count of six or fewer vetoes Lillie, while a combined count of seven
  creates next-turn deck-out risk unless another same-turn action prevents it.
- **Vetoes and exceptions:** Do not count a hidden or merely inferred card as
  available. Do not use Lillie across the confirmed unsafe boundary.
- **Tie-breakers:** The listed audit order is provisional; action choice and
  resource preservation are resolved in Phases 4, 5, 6, and 8.
- **Horizon:** Current turn and the next attacker cycle.
- **Deck-profile dependency:** Card roles and thresholds from the confirmed
  Mega Abomasnow ex/Kyogre profile.
- **CABT mapping:** Cross-cutting input to `MAIN` and nested search, discard,
  attachment, and Evolution contexts.
- **Option types:** All resource-bearing action and card option types.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `REPLAY`.
- **Evidence:** Reviewer approval, confirmed Phase 1 deck-out thresholds, and
  Phase 3 replay examples inside and beyond the preventive deck band.

### Candidate record HDI-3-04 — Project only public opponent responses

- **Question:** What can the opponent do next using information already made
  public by the game?
- **Objective:** Anticipate demonstrable responses without treating a hidden
  card guess as game state.
- **Facts:** Opposing Pokémon and attacks, attached Energy, discard pile,
  cards revealed by search, public effects, and public action history.
- **Beliefs:** Copy-count inference and the possible location of an unobserved
  fourth copy are advanced beliefs and are deferred.
- **Priority conditions:** Project responses supported by public attacks,
  Energy, revealed search cards, and discard contents. Do not add an
  unsupported hidden-hand or hidden-deck response to the current decision
  rule.
- **Vetoes and exceptions:** If CABT does not retain a historical reveal in the
  current observation, do not silently serialize model memory of that reveal
  as a current `GameState` fact; any such memory must remain explicitly
  provenance-bearing.
- **Tie-breakers:** Prefer the response requiring fewer public prerequisites;
  no probability ranking is authorized in the current scope.
- **Horizon:** Primarily the opponent's next turn.
- **Deck-profile dependency:** None; this is a generic information-boundary
  rule.
- **CABT mapping:** Cross-cutting input to strategic contexts; it does not
  create a new selection context.
- **Option types:** No direct option type; it conditions strategic scoring.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `REPLAY`.
- **Evidence:** Reviewer instruction and replay-visible public zones. No
  decision-linked replay can establish whether recorded behavior internally
  projected only public responses. The advanced four-copy inference is
  deferred, not an implemented belief rule.

Required records: `HDI-3-01` immediate threat, `HDI-3-02` race and collapse,
`HDI-3-03` resource audit, and `HDI-3-04` public response projection.

### Phase 3 confirmation summary

The reviewed state-reading procedure is:

1. check immediate loss, including an empty deck with an unavoidable next
   draw;
2. check whether the Active can be Knocked Out from public information;
3. check for an attacker that is ready, can become ready this turn, or can
   become ready next turn with at least one required Energy already in hand;
4. independently flag board collapse when only one Pokémon is in play, no
   Snover is available to evolve, or no attacker can be energized;
5. compare the opponent's remaining Prizes with the proposed Active's Prize
   liability and public one-attack survival;
6. audit the confirmed ordered resource list;
7. apply preventive deck-out handling, including the 14-to-7 deck band and
   the separate Lillie hand-plus-deck boundary;
8. project opponent responses only from public information and defer
   copy-count probability inference.

If a proposed Active gives the opponent its remaining Prizes and can certainly
be Knocked Out before the player's next turn, a next-turn winning plan cannot
justify that promotion. No policy change is authorized.

**Reviewer confirmation:** Accepted on 2026-07-30. Later evidence may annotate
the state-reading records, but changing them requires reopening Phase 3.

### Phase 3 replay sample

The post-confirmation screen covered the same 91 replay files, 95 exact
target-deck sides, 1,498 target `MAIN` prompts, and 29 target
`TO_ACTIVE` prompts. Repeated prompts within one turn are not independent game
situations. The screen uses only actor-visible state and CABT's printed base
attack damage; it does not assume hidden modifiers or future draws.

| Confirmed decision | Screen result | Representative evidence | Interpretation |
|---|---:|---|---|
| `HDI-3-01` and `HDI-3-02` one-Pokémon collapse | 875 `MAIN` prompts had only one Pokémon in play; 25 immediately selected a legal Snover or Kyogre play | Episode [`88840528`](../data/raw/kaggle/kaggle_gameplay_runs/88840528.json), side 0, decision `12`, plays Snover from hand while Kyogre is the only Pokémon in play | Supports widening a collapsing board, but repeated prompt counts do not measure independent adherence |
| `HDI-3-02` exact-Prize promotion | One of 29 promotions selected a Pokémon whose Prize value equaled the opponent's remaining Prizes | Episode [`88841554`](../data/raw/kaggle/kaggle_gameplay_runs/88841554.json), side 0, decision `19`, must promote the only candidate, Mega Abomasnow ex, while the opponent needs three Prizes | Mechanically forced and therefore not a strategic counterexample; it shows the consequence of reaching promotion without a lower-liability replacement |
| `HDI-3-02` exact-Prize one-attack threat | Seven repeated `MAIN` prompts in one turn exposed the same 90-HP Mega Abomasnow ex to Dragapult ex's printed 200 damage while the opponent needed three Prizes | Episode [`88849310`](../data/raw/kaggle/kaggle_gameplay_runs/88849310.json), side 0, decisions `35` and `41`, plays Kyogre but ultimately has only `END` legal with Mega Abomasnow ex still Active | Counterexample to achieved threat prevention; the final prompt has no escape, so the replay does not by itself identify the earlier decision where the line became avoidable |
| `HDI-3-03` no ready attacker | 33 `MAIN` prompts met the conservative automated screen for no ready, current-turn, or one-Energy-supported next attacker | Episode `88841554`, side 0, decisions `20` and `22`, attaches Water Energy to the only Mega Abomasnow ex and then plays Kyogre | Supports rebuilding Energy and board width after the forced promotion; exact next-turn readiness still needs a fixture |
| `HDI-3-03` preventive deck band | 64 `MAIN` prompts occurred with 14 through seven cards in the deck | Episode [`88848795`](../data/raw/kaggle/kaggle_gameplay_runs/88848795.json), side 0, decisions `47` and `50`, chooses Frost Barrier over the deck-discarding Hammer-lanche at deck counts nine and eight | Supports preserving the deck when a non-milling attack is legal |
| `HDI-3-03` deck-band counterexample | A target action used Hammer-lanche with 11 cards remaining while Kyogre was already in play | Episode [`88862505`](../data/raw/kaggle/kaggle_gameplay_runs/88862505.json), side 1, decision `27` | Counterexample to achieved preventive behavior; the immediate prompt offered no switch, so earlier pivot timing remains unlocated |
| `HDI-3-01` empty-deck terminal state | Nine `MAIN` prompts showed an empty deck; several belong to degenerate long-run sequences | Episode [`88881422`](../data/raw/kaggle/kaggle_gameplay_runs/88881422.json), side 1, decisions `51` and `52`, attaches Energy and uses zero-output Hammer-lanche with an empty deck before losing | Demonstrates the terminal state but offers no legal rescue in the final prompt |
| `HDI-3-04` public-only response projection | Public Energy, discard, and revealed-card state is present, but internal reasoning is not observable | No adjudicable decision-linked example | Remains a fixture or instrumentation gap, not evidence that hidden-card beliefs were used |

No prompt offered a choice between Mega Abomasnow ex and Kyogre while the
opponent needed exactly three Prizes. No Lillie play was offered at a combined
hand-plus-deck count of seven or fewer. Those conditions remain explicit
validation gaps.

## Phase 4 — Turn plan

**Interview state:** `CONFIRMED`

| Candidate decision | Initial checklist | Current implementation |
|---|---|---|
| Primary objective | State the one result the turn must achieve | No persistent explicit turn objective |
| Success condition | Define an observable test for success | No general representation |
| Mandatory actions | Identify actions that must precede attack or end | Pokémon play before terminal action is enforced in one broad scenario |
| Alternatives | Preserve a second legal line when the first fails | No persistent alternative plan |
| General order | Order information gain, development, commitments, and terminal actions | Fixed scoring approximates an order; nested prompts do not carry a confirmed plan |

Required records: `HDI-4-01` objective and success, `HDI-4-02` mandatory
actions, `HDI-4-03` alternatives, and `HDI-4-04` sequencing.

### Recorded reviewer input

- Select one primary turn objective in this order:
  1. win immediately;
  2. prevent a certain loss on the opponent's next turn;
  3. take a Knock Out or advance the Prize race;
  4. prepare or attack with Mega Abomasnow ex;
  5. prepare Kyogre when a confirmed Kyogre condition is active;
  6. develop Snover for the following turn.
- If no attack is possible, the minimum success conditions are, in order:
  1. finish with an attacker ready or able to become ready next turn;
  2. finish with at least one Snover ready to evolve;
  3. retain a replacement Pokémon so loss of the Active does not remove the
     entire board.
- Before a non-immediate-win attack or pass, complete every legal applicable
  mandatory action: use Secret Box or Petrel to find it, play every Snover,
  make every desired Evolution, use the turn's Energy attachment, and play
  Kyogre when it is needed as attacker or board protection.
- If the Mega Abomasnow ex line fails, try search repair, then Kyogre, then
  next-turn Mega Abomasnow ex preparation, then wider board and resource
  preservation, and pass only when no action or attack improves the state.

The higher objective in the confirmed ordinal list governs lower checklist
items. An immediate winning action or the only action preventing certain loss
does not wait for a lower-priority development action. Detailed card-order
dependencies remain for Phase 5.

### Candidate record HDI-4-01 — Choose the primary objective and success test

- **Question:** What single result should the current turn achieve?
- **Objective:** Keep every action aligned with the highest reachable outcome
  instead of scoring unrelated improvements independently.
- **Facts:** Confirmed Phase 3 threat scan, legal current actions, reachable
  damage and Knock Outs, remaining Prizes, attacker readiness, Evolution
  state, hand resources, and replacement Pokémon.
- **Beliefs:** None beyond the public-only response boundary confirmed in
  Phase 3.
- **Priority conditions:** Choose, in order, immediate win; prevention of
  certain next-turn loss; Knock Out or Prize progress; Mega Abomasnow ex
  preparation or attack; a confirmed Kyogre line; then Snover development.
  If attacking is impossible, test success by attacker readiness, then Snover
  Evolution readiness, then replacement-board survival.
- **Vetoes and exceptions:** Do not pursue a lower objective while a higher
  reachable objective remains unresolved. An immediate win overrides
  nonessential development.
- **Tie-breakers:** Prefer the line satisfying the earliest success condition;
  action-level ties remain for later phases.
- **Horizon:** Current turn with an explicit next-turn success state.
- **Deck-profile dependency:** Confirmed Mega Abomasnow ex primary line,
  Kyogre conditions, and Snover Evolution plan.
- **CABT mapping:** Cross-cutting parent plan for `MAIN` and every strategic
  nested context entered during the turn.
- **Option types:** All strategic action and nested option types.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `REPLAY`.
- **Evidence:** Reviewer confirmation and the Phase 4 replay sample. Current
  scoring does not persist the objective between prompts.

### Candidate record HDI-4-02 — Complete mandatory actions before termination

- **Question:** Which applicable actions must be completed before attacking or
  passing?
- **Objective:** Avoid ending a turn while legal setup, Evolution, attachment,
  or replacement actions still advance the selected plan.
- **Facts:** Secret Box and Petrel location, legal Snover plays, desired legal
  Evolutions, attachment availability, Kyogre need and legality, and whether a
  terminal higher-priority line is immediately available.
- **Beliefs:** None.
- **Priority conditions:** Before a non-immediate-win attack or pass, use
  Secret Box or Petrel for Secret Box, play every Snover, make every desired
  Evolution, use the Energy attachment, and play Kyogre when required as
  attacker or protection.
- **Vetoes and exceptions:** An immediate win or the only line preventing a
  certain loss overrides a lower mandatory action. The all-opposing-Pokémon
  Rule Box-prevention exception may veto Mega Evolution as confirmed in
  Phase 1. A merely legal action that does not apply to the selected plan is
  not mandatory.
- **Tie-breakers:** Satisfy prerequisite dependencies first; Phase 5 owns the
  detailed order among search and development actions.
- **Horizon:** Current turn before `ATTACK` or `END`.
- **Deck-profile dependency:** Secret Box/Petrel, Snover, Mega Abomasnow ex,
  Water Energy, and conditional Kyogre roles.
- **CABT mapping:** `MAIN`, with nested search, Evolution, attachment, and
  placement contexts.
- **Option types:** `PLAY`, `ATTACH`, `EVOLVE`, `ATTACK`, `END`, and related
  nested card selections.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `REPLAY`.
- **Evidence:** Reviewer confirmation and decision-linked Phase 4 replay
  sequences.

### Candidate record HDI-4-03 — Fall back without abandoning the turn

- **Question:** What should replace the primary Mega Abomasnow ex line when it
  cannot be completed?
- **Objective:** Preserve the best reachable present or future attack rather
  than pass after the first line fails.
- **Facts:** Search actions and targets, Kyogre condition and readiness, Mega
  Abomasnow ex next-turn requirements, board capacity, resources worth
  preserving, and all remaining legal actions.
- **Beliefs:** None beyond public response projection.
- **Priority conditions:** Try search repair; then prepare or use Kyogre; then
  prepare Mega Abomasnow ex for the next turn; then widen the board and
  preserve resources; pass only when no legal action or attack improves the
  position.
- **Vetoes and exceptions:** Do not force Kyogre outside its confirmed
  conditions merely because the first Mega line failed. Do not spend a
  protected last copy or singleton solely to make an otherwise non-improving
  action.
- **Tie-breakers:** Prefer the earliest executable fallback in the confirmed
  list; detailed resource ties remain for Phases 5, 6, and 8.
- **Horizon:** Current turn through the next turn's attacker.
- **Deck-profile dependency:** Mega Abomasnow ex primary line and conditional
  Kyogre fallback.
- **CABT mapping:** Cross-cutting parent plan for `MAIN`, search, placement,
  attachment, mobility, and combat contexts.
- **Option types:** All action types required by the selected fallback.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `REPLAY`.
- **Evidence:** Reviewer confirmation. Replays can show action sequences but
  not whether an unchosen fallback was consciously retained.

### Candidate record HDI-4-04 — Carry the plan across nested decisions

- **Question:** Does each nested selection still serve the confirmed primary
  objective or fallback?
- **Objective:** Prevent a tutor, discard, attachment, or target choice from
  becoming detached from the plan that caused it.
- **Facts:** Parent action, current `SelectContext`, legal original option
  indices, remaining mandatory actions, achieved success conditions, and
  whether the parent line has failed.
- **Beliefs:** The same public-only opponent projection used by the parent
  plan.
- **Priority conditions:** Read state, select the primary objective, attempt
  its prerequisites, enter the confirmed fallback order if it fails, complete
  applicable mandatory actions, and only then take the terminal attack or
  `END`. Every nested choice inherits that plan.
- **Vetoes and exceptions:** Never renumber CABT options or let a generic
  nested preference contradict the parent objective. A newly revealed public
  fact may cause a return to the Phase 3 scan and a new primary objective.
- **Tie-breakers:** Preserve the option that keeps the greatest number of
  earlier confirmed objectives reachable; otherwise keep original CABT index
  order until a later phase supplies a strategic tie-breaker.
- **Horizon:** Entire turn, including all nested prompts.
- **Deck-profile dependency:** Parent objectives are profile-specific; plan
  propagation is generic.
- **CABT mapping:** All strategic and mechanical-after-plan contexts.
- **Option types:** All 17 `OptionType` values when produced by the parent
  action.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `REPLAY`.
- **Evidence:** Reviewer confirmation and current architecture inspection; no
  persistent plan object exists in the heuristic path.

### Phase 4 confirmation summary

The turn begins with one primary objective chosen from the confirmed ordinal
list. If attacking is impossible, the turn must leave the best reachable
attacker, Evolution, and replacement state in that order. Applicable Secret
Box/Petrel, Snover, Evolution, Energy, and Kyogre actions precede a
non-immediate-win attack or pass. Failure of the Mega Abomasnow ex line enters
the confirmed search, Kyogre, future-Mega, board-preservation, then pass
fallback sequence. Higher terminal objectives override lower development, and
nested decisions must retain the parent plan.

No policy change is authorized.

**Reviewer confirmation:** Accepted on 2026-07-30. Later evidence may annotate
the turn-plan records, but changing them requires reopening Phase 4.

### Phase 4 replay sample

The post-confirmation screen covered the same 91 files and 95 exact
target-deck sides. It aligned each target `MAIN` prompt with the action stored
in the following Kaggle step, producing 1,498 `MAIN` prompts and 690 terminal
`ATTACK` or `END` choices. A legal action in the terminal prompt proves
availability at that moment; it does not prove that every generic legal action
would improve the selected plan.

| Confirmed decision | Screen result | Representative evidence | Interpretation |
|---|---:|---|---|
| `HDI-4-01` immediate win overrides development | One attack was directly encoded as a next-step target win by the strict terminal screen | Episode [`88844732`](../data/raw/kaggle/kaggle_gameplay_runs/88844732.json), side 1, decision `21`, selects Hammer-lanche and wins while Energy attachment and Surfing Beach remain legal | Supports taking the terminal win without completing lower-priority development |
| `HDI-4-02` complete mandatory actions | 103 terminal prompts still offered Secret Box; 175 still offered Snover; 102 still offered Mega Evolution; 389 still offered a Water Energy attachment | Episode [`88839991`](../data/raw/kaggle/kaggle_gameplay_runs/88839991.json), side 1, decision `10`, selects non-terminal Hammer-lanche while Snover, Secret Box, and multiple Water attachments remain legal | Direct counterexample to the confirmed mandatory-action gate |
| `HDI-4-02` play every Snover before termination | A Snover remained legal at 175 terminal prompts | Episode [`88837361`](../data/raw/kaggle/kaggle_gameplay_runs/88837361.json), side 0, decision `17`, attacks while Snover, Ultra Ball, and Water attachment remain legal | Direct counterexample to board development before a non-winning attack |
| `HDI-4-02` use in-hand Secret Box | Secret Box remained legal at 103 terminal prompts | Episode [`88850842`](../data/raw/kaggle/kaggle_gameplay_runs/88850842.json), side 1, decision `15`, attacks after attaching Energy while Secret Box remains playable | Direct counterexample to the confirmed Secret Box priority |
| `HDI-4-03` use required Kyogre fallback | Kyogre was legal at 140 terminal prompts, but need is not implied by legality alone | Episode [`88879568`](../data/raw/kaggle/kaggle_gameplay_runs/88879568.json), side 0, decision `42`, uses Frost Barrier with deck count 12 while two Kyogre plays and Water attachments remain legal | Matches the previously accepted failure to develop the required Kyogre fallback; generic Kyogre counts are not adherence counts |
| `HDI-4-03` pass after exhausting improvements | 68 `END` selections had no other legal option in their final prompt | Episode [`88839469`](../data/raw/kaggle/kaggle_gameplay_runs/88839469.json), side 0, decision `18`, reaches an `END`-only prompt after attaching Energy, playing Snover, using Secret Box and Mega Signal, and completing nested effects | Supports passing after the observable action sequence is exhausted |
| `HDI-4-04` persistent parent plan | Replays expose sequences but not the objective retained between prompts | No adjudicable decision-linked example | Requires explicit plan instrumentation or a fixture spanning parent and nested selections |

The direct mandatory-action counts are behavior counters, not independent
matches, and can include multiple target turns from one episode. Petrel
legality was not treated as a mandatory violation because Petrel may have a
confirmed non-Secret-Box target after Secret Box has left the deck. The strict
next-step win detector is intentionally conservative and is not a corpus win
count.

## Phase 5 — Draw, search, and development

**Interview state:** `CONFIRMED`

| Candidate decision | Initial checklist | Current implementation |
|---|---|---|
| Draw/search | Choose Supporters, Items, Abilities, and search targets from explicit need | Supporters and search cards receive broad preferences; exact unavailable tutor targets can be rejected |
| Information order | Take reversible information-gaining actions before commitments where appropriate | No confirmed general ordering |
| Pokémon/Evolution | Establish required board and Evolution lines without creating liabilities | Broad development and Evolution preferences; one enforced open-Bench rule |
| Stadium/Tools | Evaluate replacement, denial, target value, and timing | Legal Stadium and Tool plays receive coarse scores |
| Slot preservation | Reserve Bench, Tool, hand, and Stadium capacity for the turn plan | Profile declares reserved Bench slots; policy does not fully apply them |

Required records: `HDI-5-01` draw/search choice, `HDI-5-02` information
order, `HDI-5-03` board development, and `HDI-5-04` slot management.

### Recorded reviewer input

- Use Secret Box immediately when it is in hand and playable; if it remains in
  the deck, use Petrel to fetch it.
- Resolve repeated Ultra Balls one at a time and, where possible, play or
  evolve the fetched Pokémon before using the next Ultra Ball, so a newly
  fetched card is not discarded as the next cost.
- With one remaining Bench slot, prefer Snover in the normal line. Choose
  Kyogre instead only when a confirmed Kyogre condition is active: deck-out
  prevention, replacement-attacker need, or Rule Box protection.
- Surfing Beach precedes normal search when it can move a damaged Active to a
  ready, energized Bench Pokémon and deny a Knock Out.
- Powerglass is useful only on a Kyogre that used Swirling Waves; otherwise it
  is a strong discard candidate. Lillie comes after useful hand actions and
  obeys the confirmed hand-plus-deck deck-out boundary.

### Candidate records HDI-5-01 through HDI-5-04

The four confirmed records are:

1. **Draw/search choice:** Secret Box from hand first; Petrel fetches it when
   it remains in deck; Mega Signal finds needed Mega Abomasnow ex; Ultra Ball
   finds required Pokémon; Lillie refreshes the hand under its confirmed
   conditions. Unknown deck contents and Prize cards remain beliefs, not
   facts. Mapping: MAIN, LOOK, TO_HAND, EVOLVE, and nested search contexts.
2. **Information and repeated-search order:** Resolve one Ultra Ball fully,
   play or evolve its fetched Pokémon when applicable, then resolve the next
   Ultra Ball. Never discard a newly fetched required Pokémon as the next
   search cost when another legal cost exists. Mapping: LOOK, TO_HAND,
   DISCARD, EVOLVE, and nested search contexts.
3. **Pokémon/Evolution development:** With one Bench slot, play Snover in the
   normal line; choose Kyogre only for an active deck-out, replacement, or Rule
   Box-protection condition. Evolve every eligible Snover except the confirmed
   all-opposing-Pokémon protection branch. Mapping: TO_BENCH, TO_FIELD, EVOLVE,
   EVOLVES_FROM, and EVOLVES_TO.
4. **Stadium/Tool and slot management:** Put Surfing Beach ahead of ordinary
   search when it prevents an imminent KO. Put Powerglass on Kyogre only after
   Swirling Waves; otherwise preserve it as a discard candidate. Do not reserve
   a Bench slot at the expense of a legal Snover. Mapping: MAIN, ATTACH_TOOL,
   TO_FIELD, TO_BENCH, and DISCARD_TOOL.

For all four records, the objective is the confirmed turn plan; facts are
visible zones, legal options, and public effects; beliefs are hidden cards;
vetoes are deck-out, unavailable tutors, Rule Box prevention, and immediate
KO threats; the horizon is the current turn through the next development
turn; option types are the corresponding PLAY, CARD, EVOLVE, ATTACH,
TOOL_CARD, DISCARD, SKILL, YES, and NO values. Human coverage is CONFIRMED,
CABT mapping is MAPPED, implementation is PARTIAL, and validation is REPLAY.

### Phase 5 confirmation summary

Search and development follow the confirmed profile: Secret Box first when
playable, Petrel when it remains in deck, repeated searches resolved without
discarding newly fetched requirements, Snover favored over Kyogre for a single
slot unless a Kyogre condition is active, and Lillie late in the sequence.
Surfing Beach is urgent KO prevention; Powerglass is conditional on the
preceding Swirling Waves attack. No policy change is authorized.

**Reviewer confirmation:** Accepted on 2026-07-30. Later evidence may annotate
the draw/search/development records, but changing them requires reopening
Phase 5.

### Phase 5 replay sample

The post-confirmation screen reused the 91 replay files and 95 exact
target-deck sides, including the aligned 1,498 target MAIN prompts. This is
behavior evidence, not a new policy definition.

| Confirmed decision | Representative evidence | Interpretation |
|---|---|---|
| Secret Box and category search | Episode [`88836827`](../data/raw/kaggle/kaggle_gameplay_runs/88836827.json), side 1, decisions `18`–`22`, takes Ultra Ball, Powerglass, Lillie's Determination, and Surfing Beach from Secret Box | Supports resolving all available Secret Box categories; discard preservation is not fully observable |
| Repeated search Items | Episode [`88836243`](../data/raw/kaggle/kaggle_gameplay_runs/88836243.json), side 1, decisions `12` and `14`, plays two Mega Signal | Supports repeated search resolution; no direct repeated-Ultra-Ball cost example was found |
| Snover development | Episode [`88840528`](../data/raw/kaggle/kaggle_gameplay_runs/88840528.json), side 0, decision `12`, plays Snover while Kyogre is the only Pokémon in play | Supports Snover over a normal single-slot Kyogre choice |
| Search before development counterexample | Episode [`88839991`](../data/raw/kaggle/kaggle_gameplay_runs/88839991.json), side 1, decision `10`, attacks while Snover, Secret Box, and multiple Energy attachments remain legal | Shows that current implementation does not enforce the confirmed development gate |
| Kyogre fallback | Episode [`88879568`](../data/raw/kaggle/kaggle_gameplay_runs/88879568.json), side 0, decision `42`, uses Frost Barrier while Kyogre plays remain legal and the deck has 12 cards | Supports the previously annotated failure to develop Kyogre; it does not prove Kyogre was strategically required at that exact prompt |
| Surfing Beach emergency use | Target replay prompts contain Surfing Beach choices, but no representative case simultaneously proves damaged Active, ready energized Bench, and denied KO | Remains a direct fixture gap |
| Powerglass after Swirling Waves | No adjudicable target replay linked the confirmed post-Swirling-Waves Powerglass condition | Remains a direct fixture gap |
| Lillie boundary | No target replay offered Lillie at the combined hand-plus-deck boundary of seven or fewer | Remains a direct fixture gap |

The sample confirms useful search and Snover-development examples while also
showing that the current heuristic can attack before Secret Box, Snover,
Evolution, or Energy actions. It does not establish the intended repeated
Ultra-Ball cost reservation, emergency Surfing Beach timing, or conditional
Powerglass use.

## Phase 6 — Energy and mobility

**Interview state:** `CONFIRMED`

| Candidate decision | Initial checklist | Current implementation |
|---|---|---|
| Current attacker | Attach only when it changes a reachable current-turn line or protects tempo | Uses attack Energy targets and favors Active, but does not prove line reachability |
| Future attacker | Build a replacement without starving the current plan | Energy count and declared targets provide partial signals |
| Waste | Detect excess, wrong type, stranded Energy, and discard/recovery synergy | Limited count- and metadata-based penalties/preferences |
| Retreat/switch | Compare retreat cost, switch effects, status recovery, promotion target, and once-per-turn constraints | Promotion favors HP plus attached Energy; retreat is only a low legal-action preference |
| Special Conditions | Decide whether to cure, pivot, accept, or exploit a condition | Conditions are parsed; complete policy is absent |

Required records: `HDI-6-01` attachment target, `HDI-6-02` Energy
preservation, `HDI-6-03` retreat/switch, and `HDI-6-04` Special Conditions.

### Recorded reviewer input

For the turn's Energy attachment, first complete a reachable current-turn
attack when doing so is strategically useful. If that line is not available,
build the next attacker without starving the current plan. Kyogre is a valid
future or current target only when it makes sense in the Prize trade or Prize
race, or when one of its attacks can Knock Out the opposing Pokémon.

Attach to the Active when the Active is expected to survive for more than one
turn, even if it cannot attack immediately. Otherwise attach to the Bench to
build the replacement attacker. If the Active is the only Pokémon in play,
attach to it regardless of the lack of an immediate attack.

### Candidate record HDI-6-01 — Choose the Energy attachment target

- **Question:** Which Pokémon should receive the available Energy this turn?
- **Objective:** Preserve or improve the Prize race by completing the strongest
  reachable attack line, then prepare a replacement attacker without wasting
  the attachment.
- **Facts:** Legal attachment options, current and required attack Energy,
  Active and Bench, expected survivability from visible board state, opposing
  Pokémon and HP, Prize counts, and declared deck attack targets.
- **Beliefs:** Hidden opposing responses and uncertain future damage; these may
  affect expected survival but cannot be treated as facts.
- **Priority conditions:** (1) complete a useful current-turn attack; (2) if
  that is unavailable, build the next attacker; (3) consider Kyogre only when
  its Prize trade/race value is meaningful or one of its attacks can certainly
  Knock Out the opposing Pokémon.
- **Vetoes and exceptions:** Do not attach to a fragile Active that is not
  expected to survive beyond the turn when a legal Bench target can be built.
  Attach to the Active when it is expected to survive more than one turn even
  without an immediate attack. If it is the only Pokémon in play, attach to
  the Active.
- **Tie-breaker:** When the same priority applies to multiple targets, prefer
  the target with the clearer attack requirement and then the lower original
  CABT option index.
- **Horizon:** Current turn and the next attack/development turn.
- **Deck dependency:** Uses the declarative attack Energy targets and attacker
  roles, while allowing the reviewed Kyogre exception to override a generic
  primary-attacker preference.
- **Mapping:** `ATTACH_ENERGY`, `ATTACH_TO`, `ENERGY`, `ENERGY_CARD`, and
  `MAIN`/nested attachment contexts.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `FIXTURE`.

### Candidate record HDI-6-02 — Preserve or spend Energy

- **Question:** When should an Energy card be kept, recovered, attached, or
  discarded as a cost?
- **Objective:** Put every legally usable Energy into play while retaining
  only the minimum needed to execute the next legal attachment or a certain
  `Riptide` Knock Out.
- **Facts:** Legal attachment availability, Energy by zone, attack costs,
  discard costs, Basic Water Energy count in the discard, and whether `Riptide`
  can certainly Knock Out the opposing Pokémon.
- **Beliefs:** Hidden Energy or recovery cards in the opponent's zones remain
  hypotheses and cannot justify preserving an Energy.
- **Priority conditions:** (1) attach a legally usable Energy rather than
  leaving it stranded in hand; (2) when paying a Secret Box or Ultra Ball
  discard cost, prefer Energy in most cases; (3) preserve Basic Water Energy in
  the discard only when the current or reachable `Riptide` line will certainly
  Knock Out; (4) recover from the discard only when the hand lacks an Energy
  for the current turn's legal attachment.
- **Vetoes and exceptions:** Keep at least one Energy available for the legal
  attachment of the current turn before spending Energy as a discard cost.
  There is no general reservation for Mega Abomasnow ex, Kyogre, or a specific
  attack, and no exception that justifies leaving an attachable Energy dead in
  hand. Energy is not recovered from the field. The last available Energy may
  be spent only subject to the current-turn attachment requirement; otherwise
  an Energy in play is preferable to one stranded in hand.
- **Tie-breaker:** When several Energy cards are interchangeable, use the
  lower original CABT option index after satisfying the attachment and
  `Riptide` conditions.
- **Horizon:** Current turn through the next legal attachment and attack.
- **Deck dependency:** Uses the declared Basic Water Energy type and attack
  requirements but does not reserve a fixed quantity for either attacker.
- **Mapping:** `ATTACH_ENERGY`, `ATTACH_FROM`, `TO_HAND_ENERGY`,
  `TO_DECK_ENERGY`, `DISCARD_ENERGY_CARD`, `DISCARD_CARD_OR_ATTACHED_CARD`,
  `ENERGY`, `ENERGY_CARD`, and nested cost/recovery contexts.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `FIXTURE`.

### Candidate record HDI-6-03 — Choose retreat or switch

- **Question:** When should the Active retreat or be switched, and which
  Pokémon should be promoted?
- **Objective:** Preserve the board and improve the Prize race by promoting a
  ready attacker or denying an expected Knock Out.
- **Facts:** Active HP and status, visible Knock Out risk, legal retreat and
  switch options, retreat cost, attached Energy, Bench attackers and their
  attack readiness, opposing Pokémon, and public Prize counts.
- **Beliefs:** Unrevealed opposing responses remain hypotheses and cannot by
  themselves force a switch.
- **Priority conditions:** (1) switch when another attacker is ready and the
  Active is at risk of being Knocked Out; (2) use a free switch such as
  Surfing Beach to avoid a Knock Out, enable a situational Kyogre `Riptide`
  line, or change the Prize trade; (3) when paying retreat, prefer lines that
  place additional Energy in the discard for `Riptide`; (4) otherwise keep the
  Active if it can continue attacking and no ready replacement improves the
  position.
- **Promotion choice:** Promote the Pokémon that is ready to attack; if none
  is ready, prefer the legal Pokémon that gives the opponent the smaller Prize
  gain.
- **Vetoes and exceptions:** Do not switch merely because the Active can be
  replaced. Accept the exposed Active when retreat is not legal or no useful
  continuation is available. There is no additional exception for an
  immediate Knock Out or Prize-race result beyond the free-switch conditions
  above.
- **Tie-breaker:** Among equally ready candidates, prefer the one conceding
  fewer Prizes and then the lower original CABT option index.
- **Horizon:** Current turn through the opponent's next attack and the next
  available `Riptide` line.
- **Deck dependency:** Uses declared retreat costs, attack readiness, Kyogre's
  `Riptide`, and Prize values; it does not create a generic Bench reservation.
- **Mapping:** `SWITCH`, `TO_ACTIVE`, `TO_FIELD`, `RETREAT`, `ENERGY`,
  `ENERGY_CARD`, and `CARD` in mobility and nested switch contexts.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `FIXTURE`.

### Candidate record HDI-6-04 — Resolve Special Conditions

- **Question:** Should the Active be cured, switched, or left under a Special
  Condition?
- **Objective:** Remove the condition while preserving the attack plan and
  avoiding an unnecessary Knock Out or high-cost sacrifice.
- **Facts:** Active Special Condition, legal recovery effects, legal switch and
  retreat options, Bench attackers, visible Knock Out risk, and the cost of
  each recovery or pivot line.
- **Beliefs:** Hidden opposing effects do not justify exploiting or accepting a
  condition as though it were certain future value.
- **Priority conditions:** (1) remove the condition whenever possible when a
  ready alternative attacker exists or the recovery is a low-cost sacrifice;
  (2) prefer Surfing Beach when it can remove the condition through a free
  switch; (3) switch to the Bench to remove the condition, avoid a Knock Out,
  or enable a situational Knock Out; (4) accept the condition only as a last
  resort.
- **Recovery costs:** It is correct to spend a card, Energy, or switch effect
  to cure the condition when the resulting line is lower cost than remaining
  exposed or losing the attack plan.
- **Promotion choice:** Promote the Pokémon that is ready to attack; if none
  is ready, choose the legal Pokémon with the lower sacrifice cost.
- **Vetoes and exceptions:** Special Conditions are not strategic effects to
  exploit, and their specific type does not change the priority order. Remain
  with the affected Active only when no legal switch is available or every
  available sacrifice has a higher cost.
- **Tie-breaker:** Among equivalent recovery lines, prefer the free switch,
  then the lower original CABT option index.
- **Horizon:** Current turn through the next attack and expected opponent
  response.
- **Deck dependency:** Uses declared attacker readiness, retreat and switch
  effects, and the cost profile of the deck; it does not grant conditions
  matchup-specific value.
- **Mapping:** `AFFECT_SPECIAL_CONDITION`, `RECOVER_SPECIAL_CONDITION`,
  `SWITCH`, `TO_ACTIVE`, `TO_FIELD`, `CARD`, `SPECIAL_CONDITION`, and nested
  recovery contexts.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `FIXTURE`.

### Phase 6 confirmation summary

Energy is attached whenever legally possible rather than left stranded in
hand. The first priority is a reachable current-turn attack, followed by
building a future attacker. Kyogre is considered only when it has clear
Prize-trade/race value or a possible Knock Out. The Active receives Energy when
it is expected to survive beyond the turn or is the only Pokémon in play;
otherwise the Bench receives it. No fixed Energy reserve exists for either
attacker. Energy is the preferred discard cost while preserving the current
turn's legal attachment, and Basic Water Energy in the discard is preserved
only for a certain `Riptide` Knock Out. Recovery comes only from the discard
when the hand lacks an Energy for that attachment. Retreat and switching serve
ready-attacker promotion, Knock Out prevention, situational `Riptide`, and
Prize-trade improvement. Special Conditions are removed whenever a ready
alternative or low-cost recovery exists, with Surfing Beach preferred; they
are never exploited and are accepted only as a last resort.

**Reviewer confirmation:** Accepted on 2026-07-30. Later evidence may annotate
the Energy and mobility records, but changing them requires reopening Phase 6.

## Phase 7 — Combat

**Interview state:** `OPEN — awaiting reviewer answers`

| Candidate decision | Initial checklist | Current implementation |
|---|---|---|
| Immediate win | Check all legal terminal wins before longer plans | Explicit option win flags dominate when present; exhaustive detection is absent |
| Attack and target | Calculate damage, effects, prevention, target legality, and follow-up state | Catalog damage and a few attack-text cases are handled; full effects are not |
| KO and Prize trade | Compare Prize gain/loss, Rule Box liability, replacement, and multi-turn exchange | Rule Box and base Prize traits are partial |
| Preventive attack | Value lock, denial, protection, setup, and non-damage effects | Mostly absent |
| Pass versus attack | Attack unless an explicit strategic reason makes passing better | `END` is strongly penalized; reasons for a strategic pass are not modeled |

Required records: `HDI-7-01` immediate win, `HDI-7-02` damage/effects,
`HDI-7-03` target and Prize trade, and `HDI-7-04` preventive combat.

**Pending reviewer decision:** `HDI-7-04` remains `TBD`. No sufficiently
elaborated preventive-combat strategy has been established for attack denial,
damage reduction, protection, resource lock, or setup effects. Do not infer a
rule from the current heuristic or replay frequency; keep this record open
until the reviewer supplies an explicit priority order and exceptions.

**Partial phase closure:** `HDI-7-01`, `HDI-7-02`, and `HDI-7-03` are confirmed.
Only `HDI-7-04` remains open; Phase 7 stays in `DRAFT` until that record is
resolved.

### Candidate record HDI-7-01 — Verify immediate victory

- **Question:** Which terminal win should be selected, and when does it alter
  the normal action sequence?
- **Objective:** End the game as soon as a legal, certain victory is available
  while preserving the same consistent sequencing when intervening actions do
  not prevent that victory.
- **Facts:** All legal options, current and opposing Prize counts, opposing
  Pokémon in play, attack damage and effects, and explicit terminal indicators
  supplied by CABT.
- **Beliefs:** Hidden cards or future responses are not needed to reject an
  apparent win; CABT legality and the visible terminal result are decisive.
- **Valid wins:** Taking all remaining Prize cards and leaving the opponent
  with no Pokémon in play are both valid objectives. A legal Knock Out that
  takes the opponent's last Prize has immediate priority.
- **Priority conditions:** Inspect every legal option for both terminal win
  conditions before selecting. If a legal terminal action is available and
  another action could prevent it, choose the win. If intervening actions do
  not prevent the win, keep the established action sequence rather than
  inventing a special ordering exception.
- **Vetoes and exceptions:** Do not reject an apparent victory because of an
  uncertain hidden response, an ordinary cost, or a possible later effect;
  reject only when CABT legality or the visible result shows that it is not a
  real terminal win.
- **Tie-breaker:** Among equivalent terminal wins, use the lower original CABT
  option index after applying the normal sequencing rule.
- **Horizon:** Current prompt and terminal state.
- **Deck dependency:** Uses Prize objectives and the deck's attack/effect
  capabilities, without adding an opponent-deck assumption.
- **Mapping:** `MAIN`, `ATTACK`, `CARD`, `YES`, `NO`, and terminal option flags
  or equivalent combat contexts.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `FIXTURE`.

### Candidate record HDI-7-02 — Evaluate attack damage and effects

- **Question:** How should damage, Knock Outs, and attack effects be compared?
- **Objective:** Maximize the attack's immediate and follow-up value while
  preserving the established turn plan.
- **Facts:** Legal attacks, guaranteed damage, potential damage, Knock Out
  status, attack effects, prevention, attached Energy, opposing HP, and the
  visible follow-up board state.
- **Beliefs:** Hidden responses may affect potential lines but do not convert
  potential damage into guaranteed damage.
- **Priority conditions:** (1) take an immediate Knock Out; (2) prefer the
  highest guaranteed damage when no Knock Out is available; (3) use an effect
  that prevents or reduces the opponent's next attack; (4) protect the Active;
  (5) prepare damage or board state for the next turn; (6) discard or recover
  Energy when it improves the line; (7) use lower-damage effects only when
  their strategic value exceeds the raw damage line.
- **Attack-specific exception:** `Riptide` may be preferred over a higher
  immediate-damage line when returning Basic Water Energy to the deck improves
  the chance of revealing Energy for a later `Hammer-lanche`. `Frost Barrier`
  should preferably be used only when its damage guarantees a Knock Out, as
  established in Phase 1.
- **Damage certainty:** Evaluate guaranteed damage first, then potential
  damage. Potential damage may break a tie or support a preparation line but
  cannot replace a guaranteed result when the two outcomes differ materially.
- **Tie-breaker:** If two attacks produce the same result, preserve the status
  quo and choose the lower original CABT option index.
- **Vetoes and exceptions:** Do not choose a lower-damage effect merely because
  it is novel or situational; it must improve control, protection, preparation,
  Energy cycling, or another declared objective.
- **Horizon:** Current attack through the opponent's next turn and the next
  `Hammer-lanche` or attack line.
- **Deck dependency:** Uses declared attack effects, `Riptide`,
  `Hammer-lanche`, and `Frost Barrier`; it does not infer unverified effects
  from hidden cards.
- **Mapping:** `ATTACK`, `ATTACK_EFFECT`, `DAMAGE`, `KNOCK_OUT`,
  `AFFECT_SPECIAL_CONDITION`, `RECOVER_SPECIAL_CONDITION`, `ENERGY`, and
  combat-resolution contexts.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `FIXTURE`.

### Candidate record HDI-7-03 — Choose the target and Prize trade

- **Question:** Which legal opposing Pokémon should be targeted when several
  targets are available?
- **Objective:** Maximize Prize gains while removing the greatest threat at
  the lowest resource cost and avoiding an imminent counter-Knock Out.
- **Facts:** Target legality, Prize value, HP and damage requirement, opposing
  attack threat, Rule Box status, our available attacks and resources, and the
  likely promoted Pokémon after the Knock Out.
- **Beliefs:** Hidden responses remain hypotheses; target selection must use
  visible threat and Prize information.
- **Priority conditions:** (1) prefer a Knock Out that takes the most Prizes;
  (2) among profitable targets, prefer the easier Knock Out and/or the target
  with the greatest future threat; (3) prefer a lower-Prize target only when it
  is the best available way to maximize gains, remove a threat, or stabilize
  the board; (4) a non-Prize Knock Out is acceptable when it removes a threat
  or prevents the opponent's next attack and thereby stabilizes our position.
- **Vetoes and exceptions:** Do not accept an imminent counter-Knock Out from
  the promotion caused by the attack when another legal target avoids it. Rule
  Box status is not an independent reason to avoid a profitable target; the
  objective is to maximize our gains.
- **Tie-breaker:** Choose the target requiring the least effort and preserving
  the most resources, then use the lower original CABT option index.
- **Horizon:** Current attack, resulting promotion, and the opponent's next
  attack.
- **Deck dependency:** Uses declared Prize values, attack costs, and attacker
  roles; it does not impose a separate Rule Box penalty.
- **Mapping:** `ATTACK`, `DAMAGE`, `KNOCK_OUT`, `TARGET`, `EFFECT_TARGET`,
  `CARD`, and combat target-selection contexts.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `FIXTURE`.

## Phase 8 — Costs and nested decisions

**Interview state:** `QUEUED`

| Candidate decision | Initial checklist | Current implementation |
|---|---|---|
| Discard cost | Preserve line-critical pieces and prefer recoverable or synergistic costs | Energy is often preferred; Pokémon are coarsely protected |
| Card/Energy choice | Pay exactly the legal cost while choosing the least harmful objects | Legal generator respects counts and costs; strategic object choice is partial |
| Counters and healing | Place/remove counters according to KO, survival, and future-effect thresholds | Targets vulnerable opponents or most damaged friendly Pokémon |
| Effect order | Order effects to preserve legality, information, and optional exits | `SKILL_ORDER` and `FIRST_EFFECT` have no dedicated complete logic |
| Optional/count choices | Decide `YES_NO`, counts, continued effects, and coin-related prompts from the parent plan | Generic behavior prefers `YES` and larger numbers, except mulligan |

Required records: `HDI-8-01` discard/cost, `HDI-8-02` counter allocation,
`HDI-8-03` effect order, and `HDI-8-04` optional/count choices.

### Recorded reviewer input

- Discard costs follow this order: Basic Water Energy, an unneeded Powerglass,
  a redundant Supporter, a duplicate Pokémon, and only then a unique Pokémon
  or another protected card. Preserve the last Pokémon in a line, the last
  Trainer copy, cards needed next turn, and enough Energy for the turn's legal
  attachment. A unique card or final Pokémon copy may be discarded only when
  the resulting advantage is greater than the value of keeping it in hand.
- Damage counters should first be concentrated toward a Knock Out, then used
  to prepare the next-turn Knock Out, avoid an opposing finish, and preserve
  the board. Healing should favor the Pokémon with the greatest strategic
  value, considering whether it is Active, has high remaining HP, is the main
  attacker, or concedes the most Prizes.
- Resolve multi-effect cards in the established order: obtain information,
  search before discarding when legal, discard before drawing when required,
  evolve before attaching Energy, attach before attacking, and resolve
  mandatory effects before optional ones. Preserve a legal exit before making
  irreversible choices.
- Accept beneficial optional effects and choose the largest beneficial count.
  Choose only the necessary amount when a larger count would consume an
  important resource. Refuse an optional effect when its cost or consequence
  creates a material disadvantage. Continue a repeatable sequence until the
  next repetition would cause a disadvantage; no separate coin strategy was
  specified.

### Candidate record HDI-8-01 — Choose discard costs

- **Question:** Which cards should be discarded to pay a legal cost?
- **Objective:** Pay the cost while preserving the attack, development, and
  next-turn lines with the greatest strategic value.
- **Facts:** Legal cost combinations, card copies by role, Energy attachment
  availability, active search/evolution requirements, and next-turn needs.
- **Beliefs:** Unknown replacement cards remain hypotheses and cannot make a
  unique card safely disposable.
- **Priority conditions:** Discard Basic Water Energy, then unneeded Powerglass,
  redundant Supporter, duplicate Pokémon, and finally a unique Pokémon or
  other protected card.
- **Vetoes and exceptions:** Preserve the last Pokémon in a line, last Trainer
  copy, next-turn requirements, and enough Energy for the current attachment.
  Discard a unique card or final Pokémon only when the immediate advantage of
  the cost exceeds its retention value.
- **Mapping:** `DISCARD`, `DISCARD_CARD_OR_ATTACHED_CARD`,
  `DISCARD_ENERGY_CARD`, `CARD`, `ENERGY_CARD`, `TOOL_CARD`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `FIXTURE`.

### Candidate record HDI-8-02 — Allocate counters and healing

- **Question:** Where should damage counters be placed or removed?
- **Objective:** Convert damage into a Knock Out or future advantage while
  preserving the most valuable Pokémon.
- **Facts:** Damage, HP, Knock Out thresholds, attack targets, Prize values,
  Active/Bench position, attacker role, and legal counter or healing effects.
- **Priority conditions:** Concentrate counters for a Knock Out; otherwise
  prepare the next-turn Knock Out, prevent an opposing finish, and preserve
  the board. Heal the Pokémon with the greatest strategic value, considering
  Active status, HP, main-attacker role, and Prize value.
- **Mapping:** `DAMAGE_COUNTER`, `HEAL`, `CARD`, `DAMAGE`, `HP`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `FIXTURE`.

### Candidate record HDI-8-03 — Order nested effects

- **Question:** In which order should a multi-effect card or ability resolve?
- **Objective:** Preserve legality, information, and optional exits before
  committing irreversible resources.
- **Priority conditions:** Information first; search before discard when legal;
  discard before draw when required; evolve before attaching Energy; attach
  before attack; mandatory effects before optional effects.
- **Vetoes:** Do not choose an irreversible effect while it would remove every
  legal continuation.
- **Mapping:** `SKILL_ORDER`, `FIRST_EFFECT`, `LOOK`, `TO_HAND`, `DISCARD`,
  `EVOLVE`, `ATTACH_ENERGY`, `ATTACK`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `FIXTURE`.

### Candidate record HDI-8-04 — Select optional effects and counts

- **Question:** How should optional effects, counts, repetitions, and
  `YES`/`NO` prompts be resolved?
- **Objective:** Take the greatest beneficial effect without creating a
  material resource disadvantage.
- **Priority conditions:** Accept beneficial effects; choose the largest count
  when the additional amount remains beneficial; otherwise choose only the
  necessary amount. Continue repeatable effects until the next repetition
  would cause a disadvantage.
- **Vetoes and exceptions:** Refuse an optional effect when its cost or result
  creates a material disadvantage. No separate coin-outcome policy was
  specified.
- **Mapping:** `YES`, `NO`, `COUNT`, `CONTINUE`, and nested optional-effect
  contexts.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `FIXTURE`.

### Phase 8 confirmation summary

Costs preserve line-critical resources: discard Basic Water Energy first,
followed by unneeded Powerglass, redundant Supporters, and duplicate Pokémon;
unique cards and final Pokémon copies are protected unless the immediate
advantage outweighs their retention value. Damage counters are concentrated
for Knock Outs and healing favors the Pokémon with the greatest strategic
value. Nested effects resolve in the order that preserves information and
legality, with mandatory effects before optional ones. Beneficial optional
effects are accepted at the largest beneficial count, while repetition stops
when it would create a material disadvantage.

**Reviewer confirmation:** Accepted on 2026-07-30. Later evidence may annotate
the cost and nested-decision records, but changing them requires reopening
Phase 8.

## Phase 9 — Turn end and opponent plan

**Interview state:** `OPEN — awaiting reviewer answers`

| Candidate decision | Initial checklist | Current implementation |
|---|---|---|
| Attack or pass | End only after checking immediate win, mandatory setup, harmful attacks, and strategic pass reasons | Attack generally outranks `END`; explicit pass reasons are absent |
| Preserve resources | Keep recovery, switch, Energy, search, and protected pieces needed next turn | Partial resource scores; no confirmed next-turn reservation |
| Replacement | End with a viable response to the Active being removed | One broad Bench-development rule; readiness is incomplete |
| Board exposure | Evaluate gust targets, Prize liabilities, Bench damage, lock, and slot pressure | Partial public features; no complete exposure model |
| Opponent response | Enumerate likely responses as beliefs and retain a robust next line | No complete response model |

Required records: `HDI-9-01` terminal action, `HDI-9-02` resource and
replacement state, and `HDI-9-03` opponent-response branches.

### Candidate record HDI-9-01 — Continue or end the turn

- **Question:** When should the agent continue making legal selections and
  when should it choose `END`?
- **Objective:** Complete every action that improves or materially preserves
  the position, while ending only when no safe improvement remains.
- **Facts:** All legal options, terminal win indicators, available Energy,
  Evolution, development, search, mobility, Special Condition, and attack
  actions, plus visible board exposure.
- **Priority conditions:** (1) check for a guaranteed win and advance it;
  (2) if a win can be secured through preparation without being endangered,
  keep the normal sequence and complete those preparations; (3) complete legal
  actions that materially improve or preserve the board, including attachment,
  Evolution, Snover development, search, mobility, condition recovery, and
  next-attacker preparation; (4) choose `END` only when no safe improvement
  remains.
- **Attack rule:** Do not attack merely to avoid passing. Pass when an attack
  causes no relevant damage, does not prepare a Knock Out, exposes the Active,
  spends important resources, or fails to improve the Prize race.
- **Preservation rule:** There is no separate cost threshold that makes
  passing preferable while productive legal actions remain. Sequence all
  useful actions rather than ending early to preserve Energy, unique Pokémon,
  search cards, switching options, or next-turn resources.
- **Vetoes and exceptions:** Normally avoid ending the turn while any legal
  action materially improves or preserves the position. A likely opposing
  Knock Out alone does not justify `END` if a legal action can improve the
  position or create a better response.
- **Tie-breaker:** Follow the established action order and then choose the
  lower original CABT option index among equivalent actions.
- **Horizon:** Remainder of the current turn and the opponent's next response.
- **Mapping:** `MAIN`, `ATTACK`, `ATTACH`, `EVOLVE`, `TO_BENCH`, `PLAY`,
  `SEARCH`, `SWITCH`, `RECOVER_SPECIAL_CONDITION`, and `END`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `FIXTURE`.

### Candidate record HDI-9-02 — Desired state at turn end

- **Question:** Once no immediate win remains, what board state should be
  established before choosing `END`?
- **Objective:** End with a full, attack-capable board and the strongest
  practical response to the next turn, prioritizing the next turn while
  considering the short continuation beyond it.
- **Facts:** Legal attachment and preparation actions, Active and Bench
  readiness, attached Energy, retreat and switch options, Prize values, HP,
  available search and recovery cards, Bench occupancy, and declared deck
  roles.
- **Priority conditions:** (1) retain next-turn Energy whenever possible; if
  only one Energy line is feasible, prioritize the guaranteed attack on the
  next turn; (2) prepare a Bench attacker rather than reinforce a sacrificial
  Active; (3) leave a replacement whenever possible, prioritizing a ready
  attacker, then a one-Energy attacker, then the lower-Prize liability; (4)
  keep a low-Prize Bench Pokémon as a possible sacrifice; (5) maintain a full
  Bench with ready attackers and Energy links, adapting attacker variety to
  the matchup; (6) use search and unique cards immediately when they improve
  the current position, but preserve a switch card even when a switch is
  currently legal.
- **Replacement and exposure rule:** The Bench should not be left empty or
  without a ready attacker. If the Active is at risk of a Knock Out, either
  switch immediately or prepare the replacement while remaining Active; no
  third risk posture is defined. A final state is preferred when it has lower
  Knock Out risk and preserves more attack possibilities.
- **Resource rule:** No fixed list of resources is reserved beyond the
  practical next-turn Energy, replacement, switch, and attack lines. The
  equal-priority objective is to maximize Bench attackers, Energy in play, and
  reduction of Knock Out risk. A search card or unique card may be spent before
  `END` to make an attacker ready.
- **Vetoes and exceptions:** Do not reserve a Bench slot for a named Pokémon;
  the current deck has no such slot-reservation strategy. Filling the final
  Bench slot is acceptable. Bench development without attack capability is
  justified when it prevents losing because no Pokémon would remain in play.
  No additional forbidden final configuration or explicit acceptable-risk
  threshold was identified; unknown cases remain `TBD`.
- **Tie-breaker:** If final states are otherwise equivalent, choose lower
  Knock Out exposure, then the state preserving more attack possibilities.
- **Horizon:** Primarily the opponent's next turn/attack, with at most a
  two-turn continuation.
- **Mapping:** `MAIN`, `ATTACH`, `EVOLVE`, `TO_BENCH`, `PLAY`, `SEARCH`,
  `SWITCH`, `TO_ACTIVE`, and `END`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `FIXTURE`.

### Candidate record HDI-9-03 — Projected opponent response

- **Question:** How should the agent account for the opponent's likely next
  response before choosing `END`?
- **Objective:** Consider a low-cost, publicly supported response projection
  without allowing an unverified threat hypothesis to override the strongest
  rewarding line.
- **Facts:** Public opponent board, visible attacks and damage, known Energy,
  public discard, remaining Prizes, and revealed cards or effects.
- **Priority conditions:** (1) always check a direct Knock Out on the Active;
  (2) against a spread deck, account for Bench Knock Outs and damage spread;
  (3) retain an active attacker and Bench Energy-link targets even while
  reducing exposure; (4) if the opponent is near victory, keep an attacker
  capable of winning immediately, then reduce Active Prize value, protect a
  specific Pokémon, and only then accept a low-value sacrifice; (5) abandon
  long-term preparation when necessary to survive the next turn; (6) sometimes
  prefer a state preventing the next Knock Out even without increasing damage.
- **Belief boundary:** Use only publicly supported, provable response lines.
  An unguaranteed probable threat does not change the decision for now. When
  information is insufficient, observe and develop our own game rather than
  inventing hidden cards or matchup assumptions.
- **Robustness rule:** Prefer the line with the greatest reward if the
  opponent does not respond; minimizing the worst result is the secondary
  criterion. A predictable opposing Knock Out may be accepted when it enables
  a better promotion response. Avoid `END` while an attack or another legal
  action remains; `END` is reserved for the point at which no attack or useful
  continuation is available.
- **Exposure exceptions:** Leaving the Active exposed is acceptable when it
  gives few Prizes, can counter-attack, has no better replacement, switching
  would consume important resources, or the Knock Out would not change the
  Prize race. These cases have equal validity.
- **Updating and horizon:** A revealed opponent card, attack, or preference
  does not automatically alter the current plan. Re-evaluate when a relevant
  threat appears, projecting primarily the next turn/attack and at most two
  turns. No specific response is currently designated as always ignorable or
  as an additional forced `END` exception.
- **Tie-breaker:** For equivalent expected outcomes, choose lower overall
  risk, then lower Active exposure, then lower Prize value conceded.
- **Mapping:** `MAIN`, `ATTACK`, `SWITCH`, `TO_ACTIVE`, `TO_BENCH`, `PLAY`,
  `SEARCH`, and `END`.
- **Coverage:** Human `CONFIRMED`; CABT `MAPPED`; Implementation `PARTIAL`;
  Validation `FIXTURE`.

### Phase 9 confirmation summary

The reviewer confirms that turn end is not an early-pass decision. The agent
should continue useful legal sequencing, finish with a full board and a ready
attacker whenever possible, preserve a practical next-turn line, and project
only low-cost, public opponent responses. Reward maximization comes before
worst-case minimization; defensive Prize-race adjustments apply when the
opponent is close to winning. No additional exceptions were supplied for
previously unanswered edge cases, so those remain `TBD` rather than inferred.

**Confirmation date:** 2026-07-30.

## CABT `SelectContext` appendix

This table maps all 51 contexts declared in `src/core/types.py`. `Strategic`
means the prompt can choose between materially different game states.
`Mechanical after plan` means the prompt normally executes a parent decision,
but still needs deterministic legal handling. A prompt with only one legal
selection is mechanically forced regardless of classification.

| `SelectContext` | Class | Phase / candidate decision | Relevant `OptionType` | Current handling |
|---|---|---|---|---|
| `MAIN` | Strategic | 4, 5, 6, 7, 9 | `PLAY`, `ATTACH`, `EVOLVE`, `ABILITY`, `DISCARD`, `RETREAT`, `ATTACK`, `END` | Partial action scoring and one development filter |
| `SETUP_ACTIVE_POKEMON` | Strategic | `HDI-2-03` | `CARD` | Partial role preference |
| `SETUP_BENCH_POKEMON` | Strategic | `HDI-2-04` | `CARD` | Partial Pokémon preference |
| `IS_FIRST` | Strategic | `HDI-2-02` | `YES`, `NO` | Generic yes preference; no deck plan |
| `MULLIGAN` | Mechanical | `HDI-2-01` | `YES`, `NO` | Generic no preference may conflict with mandatory redraw; fixture required |
| `SWITCH` | Strategic | `HDI-6-03` | `CARD` | Prefers HP and attached Energy |
| `TO_ACTIVE` | Strategic | `HDI-6-03` | `CARD` | Prefers HP and attached Energy |
| `TO_BENCH` | Strategic | `HDI-5-03` | `CARD` | Generic card resource value |
| `TO_FIELD` | Strategic | `HDI-5-03`, `HDI-6-03` | `CARD` | Prefers HP and attached Energy |
| `TO_HAND` | Strategic | `HDI-5-01` | `CARD` | Resource value; rejects confirmed unavailable search target |
| `TO_DECK` | Strategic | `HDI-8-01` | `CARD` | Generic card resource value |
| `TO_DECK_BOTTOM` | Strategic | `HDI-8-01` | `CARD` | Generic card resource value |
| `TO_PRIZE` | Strategic | `HDI-7-03`, `HDI-8-01` | `CARD` | Generic card resource value |
| `NOT_MOVE` | Mechanical after plan | `HDI-8-03` | `CARD` | Generic card resource value |
| `DISCARD` | Strategic | `HDI-8-01` | `CARD`, `DISCARD` | Prefers Energy and protects Pokémon coarsely |
| `DAMAGE` | Strategic | `HDI-7-02` | `CARD` | Prefers vulnerable opponent target |
| `DAMAGE_COUNTER` | Strategic | `HDI-8-02` | `CARD`, `NUMBER` | Partial vulnerable-target and larger-count preferences |
| `DAMAGE_COUNTER_ANY` | Strategic | `HDI-8-02` | `CARD`, `NUMBER` | Partial vulnerable-target and larger-count preferences |
| `HEAL` | Strategic | `HDI-8-02` | `CARD` | Prefers greatest missing HP |
| `REMOVE_DAMAGE_COUNTER` | Strategic | `HDI-8-02` | `CARD`, `NUMBER` | Prefers greatest missing HP and larger count |
| `EFFECT_TARGET` | Strategic | `HDI-7-02`, `HDI-8-03` | `CARD` | Uses vulnerable-target heuristic |
| `EVOLVES_FROM` | Mechanical after plan | `HDI-5-03` | `CARD` | Generic card resource value |
| `EVOLVES_TO` | Strategic | `HDI-5-03` | `CARD` | Generic card resource value |
| `DEVOLVE` | Strategic | `HDI-7-02`, `HDI-8-03` | `CARD` | Generic card resource value |
| `EVOLVE` | Strategic | `HDI-5-03` | `CARD`, `EVOLVE` | Broad Evolution preference |
| `ATTACH_FROM` | Mechanical after plan | `HDI-6-01`, `HDI-8-01` | `CARD`, `ENERGY_CARD`, `ENERGY` | Generic resource/count preference |
| `ATTACH_TO` | Strategic | `HDI-6-01` | `CARD` | Generic card resource value |
| `ATTACH_ENERGY` | Strategic | `HDI-6-01` | `ENERGY`, `ENERGY_CARD` | Prefers larger represented count |
| `ATTACH_TOOL` | Strategic | `HDI-5-04` | `TOOL_CARD`, `CARD` | No dedicated target logic |
| `DETACH_FROM` | Strategic | `HDI-8-01` | `CARD` | Generic card resource value |
| `LOOK` | Mechanical after plan | `HDI-5-01`, `HDI-8-03` | `CARD` | Generic card resource value |
| `DISCARD_ENERGY_CARD` | Strategic | `HDI-8-01` | `ENERGY_CARD` | Generic Energy count preference |
| `DISCARD_TOOL_CARD` | Strategic | `HDI-8-01` | `TOOL_CARD` | No dedicated preservation logic |
| `DISCARD_TOOL` | Strategic | `HDI-8-01` | `CARD`, `TOOL_CARD` | No dedicated preservation logic |
| `DISCARD_CARD_OR_ATTACHED_CARD` | Strategic | `HDI-8-01` | `CARD`, `TOOL_CARD`, `ENERGY_CARD` | Partial Energy/Pokémon preference |
| `DISCARD_ENERGY` | Strategic | `HDI-8-01` | `ENERGY` | Legal cost generation and count preference |
| `TO_HAND_ENERGY` | Strategic | `HDI-6-02` | `ENERGY`, `ENERGY_CARD` | Generic count preference |
| `TO_DECK_ENERGY` | Strategic | `HDI-6-02` | `ENERGY`, `ENERGY_CARD` | Generic count preference |
| `SWITCH_ENERGY` | Strategic | `HDI-6-01`, `HDI-6-03` | `ENERGY`, `ENERGY_CARD` | Generic count preference |
| `SKILL_ORDER` | Strategic | `HDI-8-03` | `SKILL`, `CARD` | No dedicated order logic |
| `ATTACK` | Strategic | `HDI-7-01`–`HDI-7-04` | `ATTACK` | Partial damage and prevention logic |
| `DISABLE_ATTACK` | Strategic | `HDI-7-04` | `ATTACK`, `CARD` | No dedicated denial logic |
| `DRAW_COUNT` | Strategic | `HDI-5-01`, `HDI-8-04` | `NUMBER` | Prefers larger number |
| `DAMAGE_COUNTER_COUNT` | Mechanical after plan | `HDI-8-02` | `NUMBER` | Prefers larger number |
| `REMOVE_DAMAGE_COUNTER_COUNT` | Mechanical after plan | `HDI-8-02` | `NUMBER` | Prefers larger number |
| `ACTIVATE` | Strategic | `HDI-5-02`, `HDI-8-04` | `YES`, `NO`, `SKILL` | Generic yes preference |
| `FIRST_EFFECT` | Strategic | `HDI-8-03` | `SKILL`, `CARD`, `YES`, `NO` | Generic type-based preference only |
| `MORE_DEVOLVE` | Strategic | `HDI-8-04` | `YES`, `NO`, `NUMBER` | Generic yes/larger preference |
| `COIN_HEAD` | Mechanical | `HDI-8-04` | `NUMBER`, `YES`, `NO` | Generic larger/yes preference; CABT semantics require fixture verification |
| `AFFECT_SPECIAL_CONDITION` | Strategic | `HDI-6-04`, `HDI-7-04` | `SPECIAL_CONDITION`, `CARD` | No dedicated condition valuation |
| `RECOVER_SPECIAL_CONDITION` | Strategic | `HDI-6-04` | `SPECIAL_CONDITION`, `CARD` | No dedicated recovery valuation |

All option indices remain simulator-owned. Mechanical handling must preserve
the original indices and CABT cardinality even when no strategic preference
exists.

## CABT `OptionType` appendix

| `OptionType` | Strategic question |
|---|---|
| `PLAY` | Which card should be played now, and what must happen first or afterward? |
| `ATTACH` | Which resource goes to which target for the current or future plan? |
| `EVOLVE` | Which line should advance now, and what timing or liability exception applies? |
| `ABILITY` | Which Ability should be used, in what order, and is using it optional? |
| `DISCARD` | Is the discard action worthwhile, and what is the least harmful legal cost? |
| `RETREAT` | Is retreat better than switch, attack, or pass, and what should become Active? |
| `ATTACK` | Which attack and target best satisfy the win route and turn objective? |
| `END` | Is there an explicit reason to stop without another productive action? |
| `CARD` | Which card or Pokémon best satisfies the parent prompt? |
| `TOOL_CARD` | Which Tool is expendable, recoverable, or best attached/removed? |
| `ENERGY_CARD` | Which Energy card should move or be paid as a cost? |
| `ENERGY` | Which attached Energy unit should move or be paid? |
| `SKILL` | Which effect or order preserves the parent plan? |
| `NUMBER` | What count satisfies the effect without unnecessary cost or risk? |
| `YES` | Is the optional branch better than declining under the parent plan? |
| `NO` | Is preserving state or declining a cost better than the optional branch? |
| `SPECIAL_CONDITION` | Which condition or recovery choice changes combat most favorably? |

## Initial gap matrix

This matrix is an inventory, not a backlog authorization.

| Phase | Human playbook | Factual/belief features | Heuristic | Learned rankers | Fixtures | Replay evidence | Metrics |
|---:|---|---|---|---|---|---|---|
| 1 | Six confirmed records | Deck facts partial; matchup beliefs absent | Partial deck profile use | Consume shared factual schema; no promoted model | Repeated-development fixture only | Decision-linked support, one Petrel-order counterexample, and explicit gaps | No plan adherence metric |
| 2 | Four confirmed records | Setup context, candidates, and first-player fact | First-player outcome complete; Active, Bench, and mulligan handling partial | Setup flag available | Parser/setup coverage is partial; no mulligan direction fixture | Decision-linked support plus three Active and five Bench-prompt counterexamples | No setup-quality metric |
| 3 | Four confirmed records | Public board, zones, Prize/deck counts; belief contract separate | Partial Prize/deck signals; deck-out flag starts too late | Public counts and deck-out flag available | Prize-focused tests exist; exact threat-order fixture absent | Decision-linked support, forced exposure, threat/deck-band counterexamples, and explicit gaps | Terminal reasons exist; threat/race metrics incomplete |
| 4 | Four confirmed records | No explicit persistent turn plan | Fixed scores plus one mandatory development filter | Rank individual selections, not a confirmed plan | Board-development cases; no parent-plan propagation fixture | Immediate-win support, mandatory-action counterexamples, pass support, and an instrumentation gap | Productive actions measured; plan success absent |
| 5 | Four confirmed records | Card metadata, roles, availability | Coarse search/play/evolve logic | Selection features available | Search/development cases partial; repeated-Ultra-Ball and Tool fixtures absent | Secret Box, repeated Mega Signal, Snover support, and explicit search/development gaps | Bench width/conversion incomplete |
| 6 | Unreviewed | Energy counts, targets, conditions, turn flags | Partial attachment/promotion logic | Energy signals available | Repeated Energy-cost fixture | None accepted | Readiness/waste/mobility incomplete |
| 7 | Unreviewed | Damage metadata, Rule Box traits, Prize targets | Partial damage and prevention | Attack/damage/Prize signals available | Focused attack/Prize tests | None linked to confirmed combat rule | Attack and termination metrics partial |
| 8 | Unreviewed | Legal counts and cost fields | Generic larger/yes and limited target logic | Context and selection features available | Selection-generator and Energy-cost fixtures | None accepted | Nested legality is operational, not strategic |
| 9 | Unreviewed | Turn actions and board visible; response beliefs absent | Strong anti-`END` preference | End and board features available | Premature-end unit test | Board-collapse example is relevant | End-turn rate exists; strategic-pass reasons absent |

The current XGBoost and LightGBM rankers are unpromoted. Their ability to
consume a feature does not establish that the feature is strategically correct
or that a human decision is implemented.

## Replay sampling protocol

The workspace currently contains 91 JSON replay files under
`data/raw/kaggle/kaggle_gameplay_runs`. This is a candidate corpus count, not a
schema-valid or independent-match claim.

For each confirmed decision family:

1. define observable inclusion and exclusion conditions from the confirmed
   record;
2. locate candidate decisions without using future state as an input;
3. sample wins, losses, both player sides, and relevant matchups when present;
4. record supporting examples, counterexamples, and cases that cannot be
   adjudicated;
5. link exact episode, step, actor, legal indices, and actor-visible snapshot;
6. keep automated behavior and post-hoc human judgment distinct;
7. raise an exception to the interview before changing the confirmed record.

No replay is a human demonstration unless it was captured through the separate
live-human workflow. No repeated action becomes a desired rule merely because
it is frequent.

## Consolidation and promotion gate

The index is consolidated only when:

- all nine phases are explicitly confirmed;
- all 51 `SelectContext` values remain mapped or classified as mechanical;
- every confirmed record has facts, beliefs, priorities, exceptions,
  tie-breakers, horizon, profile dependencies, and evidence status;
- implementation and validation claims have been rechecked against current
  code, tests, and artifacts;
- each executable strategic family has a representative fixture or
  decision-linked replay when available;
- contradictions and `TBD` fields are resolved.

After consolidation, the reviewer must separately approve conversion of gaps
into gameplay rules or task-registry entries. That later work must preserve the
public selection contract and pass the normal operational and evaluation
gates.
