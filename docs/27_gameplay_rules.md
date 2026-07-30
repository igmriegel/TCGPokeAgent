# Gameplay rule registry

> Canonical policy-level rules. Feedback explains why a rule exists; this file
> states what the agent should do.

**Last reviewed:** 2026-07-29

## Status vocabulary

- `ACTIVE`: implemented and allowed in the current heuristic.
- `ACTIVE / UNVALIDATED`: implemented but not promotion-proven.
- `PROPOSED`: accepted direction without complete implementation.
- `REJECTED`: retained for history but not used.

## Rule summary

| ID | Rule | Status | Evidence or task |
|---|---|---|---|
| GR-001 | Prefer productive legal actions over unexplained `END` | `ACTIVE` | Gameplay recovery smoke |
| GR-002 | Play available Pokémon before non-winning terminal actions | `ACTIVE / UNVALIDATED` | FB-2026-001, T-001–T-004 |
| GR-003 | Continue required Evolution before terminal actions | `PROPOSED` | T-001–T-002 |
| GR-004 | Apply Rule Box damage prevention and Prize value | `ACTIVE / UNVALIDATED` | FB-2026-002, T-005 |
| GR-005 | Respect exact and probabilistic searchable-card availability | `ACTIVE / UNVALIDATED` | FB-2026-003, T-006 |
| GR-006 | Complete nested costs without renumbering options | `ACTIVE` | Selection/fallback tests |
| GR-007 | Choose Supporters from a factual need vector | `PROPOSED` | Future H2 work |
| GR-008 | Preserve a turn plan across nested selections | `PROPOSED` | Future H2 work |
| GR-009 | Pass only with an explicit strategic reason | `PROPOSED` | Future H2 work |
| GR-010 | Estimate all relevant attack effects reliably | `PROPOSED` | Future H3 work |

## Turn order

For a normal `MAIN` decision:

1. take forced or nested selections legally;
2. evaluate an immediate game-winning action;
3. use required draw/search when its need is known;
4. develop required Pokémon and Evolutions;
5. sequence non-terminal Items, Tools, Stadiums, and Abilities;
6. attach Energy according to attack and backup needs;
7. attack;
8. choose `END` only when no higher-value legal action remains.

Steps not represented by an active rule remain heuristic preferences, not
guaranteed behavior.

## Active rules

### GR-001 — Productive action before unexplained end

When legal productive actions exist, `END` must not win solely from a fixed
positive score. Any pass must carry a reason that can be audited.

### GR-002 — Play available Pokémon before attacking

In `MAIN`, with open Bench capacity, any legal Pokémon `PLAY` is required
before `ATTACK` or `END`. Parse the resulting observation and repeat. Full
Bench and illegal plays are safe exits.

Current limitations: the generic rule does not yet model target count, reserved
slots, liability, complete Evolution ordering, or every immediate-win
exception.

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
