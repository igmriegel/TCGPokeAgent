# Gameplay feedback register

> Canonical record of human gameplay feedback. This file owns feedback meaning
> and lifecycle; [`03_tasks/TASK_INDEX.md`](03_tasks/TASK_INDEX.md) owns work
> status; [`27_gameplay_rules.md`](27_gameplay_rules.md) owns active policy.

**Last reviewed:** 2026-08-03

## Summary

| State | Count |
|---|---:|
| Recorded | 12 |
| Implemented | 11 |
| Validated | 0 |
| Rejected | 0 |
| Open implementation/validation actions | 11 |

`IMPLEMENTED` means code and focused tests exist. `VALIDATED` additionally
requires the frozen gameplay gate. No feedback item below is eligible for a
promotion claim yet.

## Lifecycle

`CAPTURED` → `TRIAGED` → `GENERALIZED` → `IN_PROGRESS` → `IMPLEMENTED` →
`VALIDATED` or `REJECTED`

Raw feedback remains immutable. A correction appends a new review with a
`supersedes` link.

## Register

| ID | Finding | Implementation | Validation | Open tasks |
|---|---|---|---|---|
| FB-2026-001 | Develop the Bench before a terminal attack | MAIN-phase sequencer with board-development priority implemented | Pending | T-001–T-004 |
| FB-2026-002 | Respect Rule Box damage and Prize value | Catalog traits and `PrizeMap` implemented | Pending | T-005 |
| FB-2026-003 | Distinguish prized from searchable cards | Probabilistic/exact `PrizeCheck` implemented | Pending | T-006 |
| FB-2026-004 | Snover must reach the Bench and never be discarded | `development_priority` scoring implemented | Pending | T-015 |
| FB-2026-005 | Evolve before deciding Energy placement | `EVOLVE` now wins the earliest MAIN phase | Pending | T-016 |
| FB-2026-006 | Search before generic Bench; never tutor Petrel | Search-role scoring and `trainer_search` penalty implemented | Pending | T-017 |
| FB-2026-007 | Kyogre must shuffle-refill near deck-out | `deck_refill` attack bonus implemented | Pending | T-018 |
| FB-2026-008 | Play every legal Item before any Supporter; Supporters are a last-resort search | Item-before-Supporter phase ordering implemented | Pending | T-020 |
| FB-2026-009 | Prefer the attack with guaranteed Knock Out over probabilistic or non-KO attacks | Guaranteed-KO attack scoring remains active inside the ATTACK phase | Pending | T-021 |
| FB-2026-010 | Legal attacks should not be blocked by attacker-target development | Attacker-target gate retired; legal attacks now score directly | Reinterpreted | None |
| FB-2026-011 | Retreat only under public Knock Out risk, and pivot to Articuno on visible Alakazam-line evidence | Retreat gating and conditional Articuno tech branch implemented | Pending | T-023 |
| FB-2026-012 | Articuno without matchup evidence should be sacrificial and discard-favored over Energy | Conditional-sacrifice Articuno scoring implemented | Pending | T-024 |

## FB-2026-001 — Continuous board development

**Priority:** P0

**Status:** `IMPLEMENTED`, not validated

**Source:** post-submission human review of automated Kaggle matches

### Original feedback

The agent lost because it did not place Kyogre on the Bench. More generally,
the Abomasnow deck must continue placing Pokémon and evolving Snover before a
non-winning terminal action.

### Accepted rule

With open Bench capacity, select a legal Pokémon `PLAY` during the Bench
development phase before `ATTACK` or `END`, then parse the next `MAIN`
observation and re-evaluate. Attack is terminal and only happens after required
development is exhausted or blocked.

The implemented foundation covers generic Pokémon plays and full-Bench
legality. Evolution ordering, backup readiness, target counts, reserved slots,
liabilities, and immediate-win overrides remain part of T-001–T-004.

### Evidence

- Active annotation: `KGR-88879568-002`
- Superseded annotation: `KGR-88879568-001`
- Episode: `88879568`
- First corrected decision: `88879568:72:0`, play Kyogre at index `1`
- Implementation: `e268c96`
- Raw records: `data/annotations/gameplay_reviews/v1/annotations.jsonl`

### Gate

Zero skipped required development actions in focused fixtures; zero
operational failures; no regression in the frozen both-side opponent matrix.

## FB-2026-002 — Rule Box-aware combat and Prize valuation

**Priority:** P0

**Status:** `IMPLEMENTED`, not validated

### Original feedback

Rule Box status changes damage prevention and the Prize race. Normal Pokémon,
Pokémon ex, and Mega Evolution Pokémon ex must not be valued as equivalent.

### Accepted rule

Derive Rule Box and base Prize value from the canonical catalog. Apply known
public damage prevention and contextual Prize modifiers before valuing an
attack. Trace a prevented attack explicitly.

### Implemented foundation

- catalog `has_rule_box` and `base_prize_value`;
- Mega ex classification;
- contextual `PrizeMap`;
- `attack_damage_prevented` reason;
- focused normal/ex/Mega ex tests.

### Gate

T-005: tactical fixtures and frozen paired comparison with zero operational
failures.

## FB-2026-003 — Prize checking and searchable availability

**Priority:** P0

**Status:** `IMPLEMENTED`, not validated

### Original feedback

The agent must know when a required card is confirmed prized and must not plan
a tutor sequence around an unavailable card.

### Accepted rule

Treat own-card availability as probabilistic until a complete deck search
reveals the remaining deck. Then preserve exact searchable and prized counts
through known zone transitions. Belief never becomes factual `GameState`.

### Implemented foundation

- `PROBABILISTIC`, `EXACT`, and `INCONSISTENT` modes;
- searchable/prized ranges and expectations;
- exact search results;
- `confirmed_prized_unsearchable` reason;
- safe disablement on cardinality failure.

### Gate

T-006: golden search, draw, discard, attachment, Evolution, and Prize-taking
transitions.

## FB-2026-004 — Snover goes to the Bench and is never discarded

**Priority:** P0

**Status:** `IMPLEMENTED`, not validated

**Source:** post-submission human review of automated Kaggle matches

### Original feedback

"Confirmo sim, se Snover tiver na mão ele tem que ir no banco, não pode ser
descartado ou só ficar na mão." Snover is the `development_priority` Pokémon;
a hand Snover must be played and must survive discard selection.

### Accepted rule

A `development_priority` Pokémon still scores above generic Bench development
and is heavily penalized in `DISCARD` selection (`preserve_development_pokemon`),
legal only when it is the sole discardable option.

### Implemented foundation

- `_main_phase_selections` keeps Pokémon plays in the Bench-development phase;
- `_play_score` still gives the role a 400-point Bench score (GR-011) inside
  that phase;
- `_card_selection_score` applies `-1000` in discard contexts;
- `tests/test_heuristic_strategy.py::test_bench_development_prefers_snover`
  and `test_snover_not_discarded`.

### Gate

T-015: focused fixtures over the real deck and no regression in the frozen
paired comparison.

## FB-2026-005 — Evolution before Energy placement

**Priority:** P0

**Status:** `IMPLEMENTED`, not validated

### Original feedback

After Snover evolved into Abomasnow ex, the Energy attachment used the
pre-evolution target and underfed the Active attacker. Evolution must resolve
before the Energy decision.

### Accepted rule

A legal `EVOLVE` precedes Energy attachment and Bench development, and the
attachment that completes the Active attacker's required post-evolution attack
cost wins inside the ATTACH phase over later development (GR-003, GR-014).

### Implemented foundation

- `_main_phase_selections` puts `EVOLVE` in the earliest `MAIN` phase;
- `_attachment_score` still adds a completion bonus for the Active attacker;
- `tests/test_heuristic_strategy.py::test_evolve_precedes_energy_attachment`
  and `test_post_evolution_energy_completes_active_attack`.

### Gate

T-016: post-evolution fixtures and no regression in the frozen paired
comparison.

## FB-2026-006 — Search before generic Bench; never tutor Petrel

**Priority:** P0

**Status:** `IMPLEMENTED`, not validated

### Original feedback

Poké Pad fetched Kyogre instead of Snover, and Petrel fetched Petrel. Search
must prefer the declared resource order and must not re-fetch a redundant
Supporter.

### Accepted rule

Search, draw, and hand-refresh Items are played before Supporters in the MAIN
phase order (GR-012), and `trainer_search` targets are penalized in `TO_HAND`
selection (GR-013).

### Implemented foundation

- `_main_phase_selections` keeps search and draw Items ahead of Supporters;
- `_play_score` adds a search bonus for the five search roles inside that
  phase;
- `_card_selection_score` applies a `-200` penalty to `trainer_search` targets;
- `tests/test_heuristic_strategy.py::test_pokepad_search_prefers_snover` and
  `test_petrel_search_prefers_item_or_lillie`.

### Gate

T-017: search-order fixtures and no regression in the frozen paired comparison.

## FB-2026-007 — Kyogre shuffle-refill near deck-out

**Priority:** P0

**Status:** `IMPLEMENTED`, not validated

### Original feedback

With the deck about to empty and 18 Basic {W} Energy in the discard, the agent
benched Snover instead of using Riptide, which would have confirmed a Knock Out
and shuffled the Energy back.

### Accepted rule

Attacks with guaranteed Knock Out remain preferred inside the ATTACK phase, and
near deck-out a shuffle-refill attack gains a bonus proportional to the
discarded Energy count (GR-015).

### Implemented foundation

- `_guaranteed_attack_damage` computes deterministic discard-pile damage;
- the conditional filter exempts guaranteed-KO attacks;
- `_attack_score` emits `deck_refill`;
- `tests/test_heuristic_strategy.py::test_heuristic_deck_out`.

### Gate

T-018: deck-out fixtures and no regression in the frozen paired comparison.

## FB-2026-008 — Every legal Item before any Supporter

**Priority:** P0

**Status:** `IMPLEMENTED`, not validated

### Original feedback

The agent played a Supporter (Lillie) while legal Items were still in hand.
All Items must be played before any Supporter; a Supporter is used only when no
Item is playable, to search for more Items.

### Accepted rule

Play all legal Items before any Supporter; Supporters are a last-resort search
(GR-016).

### Implemented foundation

- `_play_score` scores Item search (340), Item (240), Supporter search (230),
  and Supporter (210), removing the Supporter hand-size draw bonus;
- `tests/test_heuristic_strategy.py::test_all_items_played_before_supporter` and
  `test_supporter_played_when_no_items_available`.

### Gate

T-020: item/supporter ordering fixtures and no regression in the frozen paired
comparison.

## FB-2026-009 — Prefer the attack with guaranteed Knock Out

**Priority:** P0

**Status:** `IMPLEMENTED`, not validated

### Original feedback

With enough Energy for the second attack (Swirling Waves, 130 guaranteed) whose
damage reached the opponent Active's HP, the agent used the first attack
(Riptide) or Hammer-lanche instead. Guaranteed Knock Outs must be preferred
over probabilistic or non-KO attacks.

### Accepted rule

Prefer an attack whose deterministic damage reaches the opponent Active's HP;
apply the guaranteed-KO bonus and never treat probabilistic top-of-deck damage
as guaranteed (GR-017).

### Implemented foundation

- `_main_phase_selections` still leaves `ATTACK` as the offensive phase;
- `_guaranteed_attack_damage` resolves the `deck_profile` `attack_plans`
  guaranteed damage (and public discard-pile damage) instead of only option
  metadata;
- `_attack_score` adds `GUARANTEED_KO_BONUS` when guaranteed damage reaches the
  opponent Active HP, emitting `guaranteed_ko`;
- `tests/test_heuristic_strategy.py`:
  `test_second_attack_preferred_over_first_when_guaranteed_ko`,
  `test_guaranteed_ko_attack_preferred_over_hammerlanche`,
  `test_swirling_waves_ko_preferred_over_hammerlanche`, and
  `test_guaranteed_attack_damage_uses_profile_plans`.

### Gate

T-021: guaranteed-KO fixtures and no regression in the frozen paired comparison.

## FB-2026-010 — Legal attacks are not blocked by attacker target

**Priority:** P0

**Status:** `REINTERPRETED`, not validated

### Original feedback

With a near-empty Bench and a Snover or Ultra Ball in hand, the agent attacked
with a guaranteed Knock Out (or Hammer-lanche) instead of developing the board.
The attacker-target gate was too restrictive; legal attacks should remain
available and be scored directly rather than blocked until the board target is
met.

### Accepted rule

Legal attacks are no longer blocked by `board_targets.minimum_attackers`.
Development, evolution, and attachment priorities remain in their own rules,
and guaranteed-KO or refill attacks keep their own bonuses.

### Implemented foundation

- legal attacks remain available even when development actions exist;
- guaranteed-KO attacks still outrank weaker attacks via scoring;
- `tests/test_heuristic_strategy.py`: fixtures covering Ultra Ball and Snover
  before guaranteed KO, weak-attack preservation, and Evolution/attachment
  ordering.

### Gate

Policy revision only; no active validation task remains for this gate.

## FB-2026-011 — Public-risk retreat and visible Alakazam-line tech branch

**Priority:** P0

**Status:** `IMPLEMENTED`, not validated

### Original feedback

Only retreat when the public board shows real Knock Out risk and a ready
replacement improves the position. When Abra, Kadabra, or Alakazam is visible,
pivot into Team Rocket's Articuno and attach Energy there instead of continuing
the default Snover/Kyogre line.

### Accepted rule

Retreat now scores only when the public board is under Knock Out risk and the
Bench replacement is ready, except that an un-supported Active Articuno may
retreat only to a ready evolved attacker. The visible Alakazam-line branch
raises Team Rocket's Articuno above the default development line and also
prefers Energy on that branch.

### Implemented foundation

- retreat scoring uses public risk and replacement readiness;
- non-strategic retreat falls behind `END`;
- visible Abra, Kadabra, or Alakazam raises Articuno in `PLAY`, `CARD`, and
  `ATTACH` contexts;
- focused tests cover retreat gating and the Articuno branch.

### Gate

T-023: retreat/mobility and tech-branch fixtures, plus the frozen paired
comparison.

## FB-2026-012 — Articuno without evidence is sacrificial

**Priority:** P0

**Status:** `IMPLEMENTED`, not validated

### Original feedback

When Team Rocket's Articuno is Active or in hand without public Alakazam-line
evidence, the plan should not invest resources into it. When Articuno is in hand
during discard selection, it should be discarded before Energy cards.

### Accepted rule

Treat unsupported Articuno as a sacrificial line regardless of turn. Block its
search, Bench placement, and Energy attachment, keep the visible Alakazam-line
tech branch separate, and score Articuno above Energy in discard contexts.

### Implemented foundation

- `_opponent_visible_alakazam_line` gates the conditional tech branch;
- `_attachment_score` avoids spending Energy on unsupported Articuno and above
  the declared attack cost;
- `_play_score` and selection filtering block unsupported Articuno plays;
- `_card_selection_score` prefers discarding unsupported Articuno before Energy;
- focused fixtures cover both attachment and discard ordering.

### Gate

T-024: conditional-Articuno attachment and discard fixtures, plus the frozen
paired comparison.

## Adding feedback

Create one record per distinct finding. Include the original words, evidence
source, affected decision, accepted scope, exceptions, rule link, task IDs, and
gate. Post-hoc agent replay review and live human demonstration must remain
different evidence types.
