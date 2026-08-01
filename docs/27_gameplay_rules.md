# Gameplay rule registry

> Canonical policy-level rules. Feedback explains why a rule exists; this file
> states what the agent should do.

**Last reviewed:** 2026-08-01

## Status vocabulary

- `ACTIVE`: implemented and allowed in the current heuristic.
- `ACTIVE / UNVALIDATED`: implemented but not promotion-proven.
- `PROPOSED`: accepted direction without complete implementation.
- `REJECTED`: retained for history but not used.

## Rule summary

| ID | Rule | Status | Evidence or task |
|---|---|---|---|
| GR-001 | Prefer productive legal actions over unexplained `END` | `ACTIVE` | Gameplay recovery smoke |
| GR-002 | Prioritize Bench development only when no priority action exists | `ACTIVE / UNVALIDATED` | FB-2026-001, T-001–T-004, T-015–T-021 |
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

## Turn order

For a normal `MAIN` decision:

1. take forced or nested selections legally;
2. evaluate an immediate game-winning action;
3. use required draw/search when its need is known;
4. Evolve; Evolution precedes Energy and Bench decisions;
5. attach Energy that completes the Active attacker's required attack;
6. place the declared `development_priority` Pokémon (Snover) on the Bench;
7. develop the secondary/backup attacker;
8. play Items, Tools, Stadiums, and Abilities, search roles first; every Item precedes any Supporter;
9. play a Supporter only when no Item is playable, preferring search Supporters;
10. attack, preferring guaranteed Knock Outs and, near deck-out, shuffle-refill attacks;
11. choose `END` only when no higher-value legal action remains.

Steps not represented by an active rule remain heuristic preferences, not
guaranteed behavior.

## Active rules

### GR-001 — Productive action before unexplained end

When legal productive actions exist, `END` must not win solely from a fixed
positive score. Any pass must carry a reason that can be audited.

### GR-002 — Bench development when no priority action exists

In `MAIN`, with open Bench capacity, a legal Pokémon `PLAY` is preferred over
`ATTACK` or `END`, but only when no priority action is legal. Priority actions
are Evolution, Ability, search/Trainer `PLAY`, an attach that completes the
Active attack, and an attack with a guaranteed Knock Out. Parse the resulting
observation and repeat. Full Bench and illegal plays are safe exits.

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

### GR-017 — Guaranteed Knock Out attacks

When an attack's deterministic damage (the `deck_profile` `attack_plans`
guaranteed damage, or public discard-pile based damage) reaches the opponent
Active's HP, that attack gains a bonus and is preferred over probabilistic
attacks such as Hammer-lanche and over non-KO attacks.

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
