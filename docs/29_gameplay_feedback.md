# Gameplay feedback register

> Canonical record of human gameplay feedback. This file owns feedback meaning
> and lifecycle; [`03_tasks/TASK_INDEX.md`](03_tasks/TASK_INDEX.md) owns work
> status; [`27_gameplay_rules.md`](27_gameplay_rules.md) owns active policy.

**Last reviewed:** 2026-07-29

## Summary

| State | Count |
|---|---:|
| Recorded | 3 |
| Implemented | 3 |
| Validated | 0 |
| Rejected | 0 |
| Open implementation/validation actions | 6 |

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
| FB-2026-001 | Develop the Bench before a terminal attack | Core generic play ordering implemented | Pending | T-001–T-004 |
| FB-2026-002 | Respect Rule Box damage and Prize value | Catalog traits and `PrizeMap` implemented | Pending | T-005 |
| FB-2026-003 | Distinguish prized from searchable cards | Probabilistic/exact `PrizeCheck` implemented | Pending | T-006 |

## FB-2026-001 — Continuous board development

**Priority:** P0

**Status:** `IMPLEMENTED`, not validated

**Source:** post-submission human review of automated Kaggle matches

### Original feedback

The agent lost because it did not place Kyogre on the Bench. More generally,
the Abomasnow deck must continue placing Pokémon and evolving Snover before a
non-winning terminal action.

### Accepted rule

With open Bench capacity, select a legal Pokémon `PLAY` before `ATTACK` or
`END`, then parse the next `MAIN` observation and re-evaluate. Attack after
required development is exhausted or blocked.

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

## Adding feedback

Create one record per distinct finding. Include the original words, evidence
source, affected decision, accepted scope, exceptions, rule link, task IDs, and
gate. Post-hoc agent replay review and live human demonstration must remain
different evidence types.
