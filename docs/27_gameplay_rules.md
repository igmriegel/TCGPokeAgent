# Gameplay rule registry

> Canonical policy-level rules. Feedback explains why a rule exists; this file
> states what the agent should do.

**Last reviewed:** 2026-08-07

## Status vocabulary

- `ACTIVE`: implemented and allowed in the current heuristic.
- `ACTIVE / UNVALIDATED`: implemented but not promotion-proven.
- `PROPOSED`: accepted direction without complete implementation.
- `REJECTED`: retained for history but not used.

## Rule summary

| ID | Rule | Status | Evidence or task |
|---|---|---|---|
| GR-001 | Prefer productive legal actions over unexplained `END` | `ACTIVE` | Gameplay recovery smoke |
| GR-002 | Sequence `MAIN` by phase: evolve, attach, bench, items, supporter, attack, end | `ACTIVE / UNVALIDATED` | FB-2026-001, T-001–T-004, T-015–T-021 |
| GR-003 | Continue required Evolution before Energy and Bench decisions | `ACTIVE / UNVALIDATED` | FB-2026-005, T-001–T-002, T-016 |
| GR-004 | Apply Rule Box damage prevention and Prize value | `ACTIVE / UNVALIDATED` | FB-2026-002, T-005 |
| GR-005 | Respect exact and probabilistic searchable-card availability | `ACTIVE / UNVALIDATED` | FB-2026-003, T-006 |
| GR-006 | Complete nested costs without renumbering options | `ACTIVE` | Selection/fallback tests |
| GR-007 | Choose Supporters from a factual need vector | `PROPOSED` | Future H2 work |
| GR-008 | Preserve a turn plan across nested selections | `PROPOSED` | Future H2 work |
| GR-009 | Pass only with an explicit strategic reason | `PROPOSED` | Future H2 work |
| GR-010 | Estimate all relevant attack effects reliably | `PROPOSED` | Future H3 work |
| GR-011 | Place the `development_priority` Pokémon before generic development; never discard it | `ACTIVE / UNVALIDATED` | FB-2026-004, T-015 |
| GR-012 | Prefer Item search/draw over generic Bench filling | `ACTIVE / UNVALIDATED` | FB-2026-006, T-017 |
| GR-013 | Never tutor a `trainer_search` card (Petrel) | `ACTIVE / UNVALIDATED` | FB-2026-006, T-017 |
| GR-014 | Attach the Energy that completes the Active attack before Bench development | `ACTIVE / UNVALIDATED` | FB-2026-005, T-016 |
| GR-015 | Near deck-out, prefer attacks that shuffle discarded Basic Energy back into the deck | `ACTIVE / UNVALIDATED` | FB-2026-007, T-018 |
| GR-016 | Play all legal Items before any Supporter; Supporters are a last-resort search | `ACTIVE / UNVALIDATED` | FB-2026-008, T-020 |
| GR-017 | Prefer an attack with guaranteed Knock Out over probabilistic or non-KO attacks | `ACTIVE / UNVALIDATED` | FB-2026-009, T-021 |
| GR-018 | Do not block a legal attack behind attacker-target development | `ACTIVE / UNVALIDATED` | FB-2026-010 |
| GR-019 | Retreat only when public Knock Out risk exists and a ready replacement improves the board; keep Kyogre active when Riptide is the better line | `ACTIVE / UNVALIDATED` | FB-2026-011, T-023 |
| GR-020 | Define a dedicated Abra/Kadabra/Alakazam gameplay branch, including evolution timing, attack line, and target selection | `PENDING / OUT OF SCOPE FOR THIS AUDIT` | FB-2026-011, T-023 |
| GR-021 | Without Alakazam-line evidence, do not search, Bench, energize, or retreat Team Rocket's Articuno unless a ready evolved attacker can replace it; accept the sacrifice | `ACTIVE / UNVALIDATED` | FB-2026-012, T-024 |
| GR-022 | Honchkrow/Porygon Proton, Supporter, Energy, matchup, and attack restrictions | `ACTIVE` | FB-2026-013, completed T-025 |
| GR-023 | Productive terminal, exact committed switching, projected Ignition damage, Giovanni, Miracle Headset, Stadium, and Roto Stick ordering | `ACTIVE` | FB-2026-013, completed T-025; 400-match promotion audit |
| GR-024 | Instrument terminal causes and prioritize deck-out prevention before promotion | `ACTIVE / UNVALIDATED` | FB-2026-014, T-026 |
| GR-025 | Persist the highest reachable turn objective and prove setup, Supporter, and evolution-KO lines from public facts | `ACTIVE / UNVALIDATED` | FB-2026-018, T-030 |

## Turn order

For a normal `MAIN` decision:

1. take forced or nested selections legally;
2. evaluate an immediate game-winning action;
3. sequence legal `MAIN` actions by phase instead of comparing them globally;
4. evolve first;
5. attach Energy, especially when it completes the Active attack;
6. place the declared `development_priority` Pokémon (Snover) on the Bench;
7. play search and draw Items before any Stadium or Supporter;
8. play Stadium before a Supporter when both are legal;
9. play a Supporter only when no earlier-phase action is playable, preferring search Supporters;
10. retreat only when public Knock Out risk exists and the promoted replacement is ready, keeping Kyogre on board when Riptide is the better line; the dedicated Honchkrow/Porygon baseline additionally requires a specific same-turn attacker and attack;
11. attack as the terminal action of the turn, preferring guaranteed Knock Outs and, near deck-out, shuffle-refill attacks;
12. choose `END` only when no attack, refill, or higher-value pre-attack action remains, and record the terminal reason.

Steps not represented by an active rule remain heuristic preferences, not
guaranteed behavior.

## Active rules

### GR-001 — Productive action before unexplained end

When legal productive actions exist, `END` must not win solely from a fixed
positive score. Any pass must carry a reason that can be audited.

### GR-002 — Bench development when no priority action exists

In `MAIN`, legal selections are sequenced by phase. Earlier phases do not
compete with later ones. A legal Pokémon `PLAY` is only prioritized while the
Bench has open capacity. Priority actions are Evolution, attach actions that
complete the Active attack, search/draw Items, and Supporters in that order. An
attack is terminal: once selected, the turn ends and no later action is taken.
A guaranteed Knock Out is prioritized by its own score, but the attacker target
does not block a legal attack. Parse the resulting observation and repeat.
Full Bench and illegal plays are safe exits.

### GR-003 — Evolution before Energy and Bench decisions

When a legal `EVOLVE` exists, it precedes Energy attachment and Bench
development. Post-Evolution energy needs drive the attachment decision, so the
agent resolves Evolution before deciding where Energy goes.

### GR-004 — Rule Box and Prize value

Use catalog-derived Rule Box traits and contextual Prize value. Known damage
prevention reduces expected damage to zero and emits
`attack_damage_prevented`.

### GR-005 — Searchable-card availability

Use ranges and probability until a complete deck search permits exact counts.
A confirmed prized card is unavailable to a tutor. Keep this knowledge in
strategic context or belief, never factual public state.

### GR-006 — Nested selection integrity

Preserve simulator option indices and declared cardinality. Repeated Energy or
damage-cost prompts select only the required legal amount for that SDK call.

### GR-011 — Development-priority Pokémon placement

The declared `development_priority` Pokémon (Snover) is placed on the Bench
before any other Pokémon and must never be discarded or left in hand when a
legal `PLAY` exists. Discarding it is legal only when it is the sole option.

### GR-012 — Item search before generic Bench filling

Search, draw, and hand-refresh Items (Ultra Ball, Poké Pad, Mega Signal) are
played before filling the Bench with a generic Pokémon. `Pokémon Search`,
`evolution search`, and `general search` Item roles qualify. Supporter search is
ordered separately by GR-016.

### GR-013 — No redundant Supporter search

A `trainer_search` target (Petrel) is never fetched by a tutor; the tutor
prefers Items and `hand_refresh` Supporters instead.

### GR-014 — Attach that completes the Active attack

An Energy attachment that brings the Active attacker to its required attack
cost precedes Bench development and generic attachment. The `deck_profile`
`attack_energy_targets` defines the required count.

### GR-015 — Shuffle-refill near deck-out

When the own deck is below the refill threshold, attacks that shuffle discarded
Basic Energy back into the deck (Riptide) gain a bonus proportional to the
discarded Energy count, in addition to their damage value.

### GR-016 — Items before Supporters

Every legal Item is played before any Supporter. A Supporter is played only when
no Item is playable, as a last-resort search; search Supporters (Lillie,
Petrel) are preferred over non-search Supporters.

Ultra Ball may search Mega Abomasnow ex only when a Snover is already on the
own Bench and can be evolved. Without Bench Snover, prefer another legal
Pokémon target.

### GR-017 — Guaranteed Knock Out attacks

When an attack's deterministic damage (the `deck_profile` `attack_plans`
guaranteed damage, or public discard-pile based damage) reaches the opponent
Active's HP, that attack gains a bonus and is preferred over probabilistic
attacks. When no deterministic KO exists, Hammer-lanche is evaluated with a
hypergeometric estimate for the six top cards, using the declared Energy count
and visible/inferred Energy in the deck, Prizes, discard, hand, and attached to
the board. Its expected damage and KO probability are compared with fixed-damage
attacks such as Frost Barrier.

### GR-018 — Do not block legal attacks behind attacker target

The board's attacker target is not a hard gate for legal attacks. If an attack
is legal, the agent may select it on its own score while development, evolution,
and attachment priorities continue to apply through their separate rules. Near
deck-out shuffle-refill attacks and guaranteed-KO attacks keep their own score
bonuses.

### GR-019 — Retreat only under public risk

Retreat and switch are only preferred when the public board shows Knock Out
risk and the promoted Bench Pokémon is ready to attack or otherwise improve
the line. Do not retreat just because the Active can be replaced. Keep Kyogre
active when Riptide or another shuffle-refill line is the clearly better
public plan.

### GR-020 — Visible Alakazam-line tech branch

When Abra, Kadabra, or Alakazam is publicly visible in the opponent's Active or
Bench, Team Rocket's Articuno becomes the tech branch for the turn. Prefer
searching, playing, promoting, and attaching Energy to Articuno instead of
continuing the default Snover/Kyogre development line in that branch.

### GR-021 — Articuno as a conditional sacrifice

Without public evidence of the Alakazam line, treat Team Rocket's Articuno as a
sacrifice regardless of turn number. Do not search for it, Bench it, or invest
Energy in it. Retreat is allowed only when a ready evolved attacker is already
on the Bench; otherwise accept the Active Articuno being knocked out.

### GR-022 — Honchkrow/Porygon strategic resource gate

The dedicated Honchkrow/Porygon policy uses declared Pokémon counts and a fixed
twenty-card Team Rocket Supporter model. Proton values remaining Murkrow first,
then the Porygon line, and values Articuno only when Dragapult (Dreepy 119,
Drakloak 120, or Dragapult ex 121) or the visible Alakazam line justifies the
tech. Proton is blocked on a full Bench and is preferred through Rocket
Transceiver during turns one and two when it is not already in hand.

Hacking is forbidden. Deceit is retained only for damage, Knock Out, or an
explicitly decisive interruption. Ignition Energy is allowed only on the Active
when it completes a damaging attack line; Team Rocket Energy is not attached to
Porygon2. Unsupported Articuno is sacrificial and is preferred over discarding
Energy. Poké Pad may fetch Honchkrow when it enables an attack or reduces a large
hand for Ariana, while Porygon2 is not benched before the opening line.
Transceiver fetches Proton during early setup even when Ariana is already in
hand, provided a positive target remains. When Dragapult evidence is public
(Dreepy, Drakloak, or Dragapult ex), Articuno is a required defensive setup
target: place it before nonessential evolution, keep it on the Bench, and do
not promote it unless the simulator forces the switch. The protection applies
to Basic Team Rocket Pokémon, so eager evolution can remove the relevant
protection window.

Ultra Ball must be held when its discard would consume a productive recovery
card or another scarce resource without creating a concrete search/evolution
line. Factory is not played merely because it is available; before a
Supporter has been played, it requires a playable Supporter or an explicit
same-turn conversion.

### GR-023 — Productive terminal and promotion ordering

`END` is filtered whenever visible Energy, a valid attacker, and enough
Supporters expose a lethal Rocket Feathers/R Command line. A voluntary switch
must bind one Bench Pokémon serial, its planned attack, projected damage, and
whether Ignition Energy is required. The switch is illegal without a positive
same-turn attack; after promotion, the policy must attach the committed
Ignition when needed and execute the committed attack. Giovanni has precedence
over paid retreat when the opponent has no Bench, using post-Giovanni hand and
discard counts for Rocket Feathers and R Command damage.

Miracle Headset normally remains reserved for exactly two recoverable Team
Rocket Supporters completing an immediate Honchkrow Knock Out. After hand
disruption, an emergency exception allows it with at most two cards, no
playable Supporter, and Ariana in the discard, so Ariana can restore the hand
and enable Factory. Its nested selection must take exactly two Supporters and
avoid another Ariana when Ariana is already in hand. Guaranteed Knock Outs and
KO-enabling discards precede development,
search, Energy, retreat, and `END`. Stadium plays are an explicit phase before
Supporters. Roto Stick is reserved until fetching a Supporter can close a Knock
Out line. Ariana remains protected unless the discard is marked as required by
the current KO line.

### GR-024 — Deck-out monitoring is the next release gate

The dedicated agent must record terminal reason, turn, remaining deck, field,
and prizes for every loss. A loss with the own deck at zero is a deck-out
regression signal even when the agent completed every SDK action legally.
Deck-out prevention, shuffle-refill timing, and preservation of a winning line
take precedence over the current win-rate result until the P0 gate is closed.

### GR-025 — Persistent turn objective and proven tactical lines

The dedicated Honchkrow/Porygon policy records absolute turn, own turn,
turn-action count, and one persistent objective in this order: win now;
prevent a no-Pokémon loss; take the highest-value Knock Out; build an attacker
and the Bench; improve resources; then attack for damage or control. Lower
actions cannot displace a reachable higher objective during nested prompts.

On the first own turn, Proton precedes Ariana when a useful Basic remains in
the deck, the Bench has space, and the board needs development. Rocket
Transceiver selects Proton only for that demonstrated setup gain; otherwise it
selects Ariana, Petrel, or Giovanni according to the stored objective. When
Ariana would draw at most one card and Factory is not active, legal
`Petrel → Factory → draw two` takes precedence.

Poké Pad commits to Honchkrow only when a visible Murkrow is legally evolvable,
Honchkrow remains accessible, attached Energy pays Rocket Feathers, and the
visible Supporter count proves the target Knock Out. The commitment persists
through search, evolution of the exact Murkrow serial, and attack. Torment is
not legal policy output while that superior committed line exists.

## Required evaluation metrics

- productive actions and unexplained `END`;
- required development skipped before terminal actions;
- Bench width, Evolution conversion, and backup readiness;
- attacks, Knock Outs, Prize cards, donks, and termination reason;
- prevented or ineffective attacks;
- confirmed unavailable tutor targets;
- fallback, parser, catalog, belief, and operational failures;
- decision latency by context.

The task registry owns implementation work for missing metrics.
