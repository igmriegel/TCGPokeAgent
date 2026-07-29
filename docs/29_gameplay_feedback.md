# Gameplay feedback register

**Status:** `ACTIVE`

This document is the canonical register for gameplay feedback obtained from
Kaggle episodes, local matches, replay reviews, and monitored human play. It
preserves the original observation, separates deck-specific conclusions from
general principles, and turns accepted feedback into traceable development
work.

Feedback is evidence, not an automatic rule. A proposed behavior becomes part
of the agent only after its scope, exceptions, tests, metrics, and promotion
gate are defined.

## Feedback lifecycle

Each item moves through these states:

1. `CAPTURED` — the original observation is recorded without reinterpretation;
2. `TRIAGED` — affected decisions, impact, and available evidence are known;
3. `GENERALIZED` — deck-specific and reusable conclusions are separated;
4. `IN_PROGRESS` — implementation and regression work has started;
5. `IMPLEMENTED` — code and focused tests exist;
6. `VALIDATED` — the frozen evaluation gate supports promotion;
7. `REJECTED` — evidence disproved the hypothesis or showed unacceptable
   regression.

`IMPLEMENTED` is not equivalent to `VALIDATED`. A Kaggle submission should use
the change only after the applicable operational and gameplay gates pass.

## Rule levels

Every accepted feedback item should identify one or more rule levels.

### Observation

What happened in a specific match or group of matches. This level must retain
the source, deck, opponent when known, and whether the evidence came from live
play or post-hoc review.

### Deck rule

A concrete response for the deck that produced the feedback. It may reference
specific cards, evolution lines, target counts, attacks, and sequencing.

### General principle

A reusable behavior that applies to other decks when explicit applicability
conditions are satisfied. Generalization must not erase deck-specific
exceptions.

### Deck profile

The configuration needed to instantiate the general principle for one deck.
For board development, a profile should eventually declare:

- primary and backup attacker lines;
- support Pokémon and whether their effects stack;
- desired minimum and target counts in play;
- evolution chains and preferred timing;
- Bench slots that should normally remain reserved;
- liabilities that should not be played automatically;
- actions that may override development, such as an immediate game win.

## Feedback record template

```text
Feedback ID:
Date:
Status:
Priority:
Source:
Evidence type:
Deck:
Opponent or matchup:

Original feedback:
Observed behavior:
Impact:
Confidence and limitations:

Deck-specific rule:
General principle:
Applicability conditions:
Exceptions:

Diagnosed implementation gap:
Development actions:
Reason codes:
Metrics:
Golden scenarios:
Evaluation gate:
Related sprint:
Related commits and reports:
```

Raw feedback should remain recognizable in `Original feedback`. Clarifications
and technical interpretation belong in later fields.

---

## FB-2026-001 — Continuous board development

**Date:** 2026-07-29

**Status:** `IN_PROGRESS`

**Priority:** `P0`

**Source:** human post-submission review of Kaggle submissions `55088176` and
`55093119`.

**Evidence type:** post-hoc gameplay review plus static inspection of the
current heuristic scorer.

**Deck:** frozen Mega Abomasnow ex deck.

### Original feedback

The agent lost matches because it stopped placing Pokémon on the Bench. With
the Abomasnow deck, Snover in hand should be put into play and eligible Snover
should be evolved. The agent must not stop developing its Pokémon and board.

### Observed behavior and impact

The agent could make attacks while leaving Snover in hand or leaving an
available evolution undeveloped. This produced a fragile board without enough
future attackers and could cause a loss after the Active Pokémon was Knocked
Out.

The static scorer contains a matching failure mode: playing Snover receives
approximately 330 points, while Hammer Lanche can receive approximately 500
points. Because attacking ends the turn, a non-winning attack can prevent all
remaining development for that turn.

The replay review establishes the gameplay symptom. The score comparison
establishes a credible code path, but decision-level traces are still required
to quantify every occurrence.

The failure recurred in submission `55093119`: the agent lost after leaving no
additional Pokémon in play. This confirms that the deck-profile and Prize
foundation did not complete the pre-terminal board-safety policy. Until the
exact episode trace is linked, the report is evidence of recurrence rather
than a decision-level root-cause proof.

### Deck-specific rule

For the frozen Mega Abomasnow ex deck:

- play every legally playable Snover while a Bench slot is available before a
  non-winning attack or `END`;
- evolve each eligible Snover into Mega Abomasnow ex before a non-winning
  attack or `END`;
- repeat this check after every action because one play or evolution does not
  complete development for the whole turn;
- preserve SDK legality and `benchMax`;
- allow an immediate game-winning action to override development.

### General principle

**Continuous development before terminal actions:** before selecting an action
that ends the actionable part of the turn, re-evaluate whether the current
deck plan has any required legal board-development action. Execute required
development first, then recompute the board and repeat.

In this context, a terminal action is normally an attack or `END`. Other decks
or card effects may introduce additional actions that irreversibly close the
development window and should be classified the same way.

The general algorithm is:

1. derive the current board-development targets from the deck profile;
2. inspect legal Basic Pokémon plays, evolutions, and required support setup;
3. classify each opportunity as required, optional, blocked, or harmful;
4. choose required development before a non-winning terminal action;
5. parse the next observation and recompute instead of retaining a permanent
   "development complete" flag;
6. permit the terminal action when no required development remains or a
   declared override applies.

### Applicability conditions

This principle applies when at least one of these conditions is true:

- the deck requires multiple attackers to complete its Prize plan;
- an evolution line must be established before its evolved card can be used;
- the current Active Pokémon may be Knocked Out without a viable replacement;
- a support Pokémon must enter play to enable draw, search, acceleration, or
  another core engine;
- the deck profile declares a minimum board width or target count.

Examples include evolution decks, decks that rotate attackers, decks with
Bench-based engines, and decks that need multiple setup pieces in play.

### Exceptions

The principle does not mean that every deck should blindly fill every Bench
slot. Development may be skipped when:

- another legal action wins the game immediately;
- the Bench is full or the play is otherwise illegal;
- the deck profile has already reached its target count;
- the Pokémon is a known Prize liability with no useful role in the matchup;
- a Bench slot is explicitly reserved for a higher-priority attacker or
  support Pokémon;
- evolution would remove an immediately required attack, Ability, or effect;
- a card effect, lock, or resource constraint makes delayed development more
  valuable and the exception is represented by an explicit reason code.

The Abomasnow deck rule intentionally overrides the generic target-count
exception for legally playable Snover until the available Bench capacity or
another explicit override blocks the play.

### Active development actions

| ID | Action | Status |
|---|---|---|
| FB001-A1 | Add board counts, open slots, legal development options, and backup-attacker readiness | `PLANNED` |
| FB001-A2 | Add a pre-terminal-action ordering layer instead of relying only on independent fixed scores | `PLANNED` |
| FB001-A3 | Implement the Snover/Mega Abomasnow ex deck profile and required-action policy | `PLANNED` |
| FB001-A4 | Add real and synthetic golden scenarios for repeated play, evolution, full Bench, and immediate win | `PLANNED` |
| FB001-A5 | Add skipped-development, conversion, board-width, and replacement-attacker metrics | `PLANNED` |
| FB001-A6 | Run smoke and frozen matchup evaluation before packaging another submission | `PLANNED` |

The parent feedback remains `IN_PROGRESS` because its rule, diagnosis, and
acceptance work are active even though the code actions remain planned.

---

## FB-2026-002 — Rule Box-aware combat and Prize valuation

**Date:** 2026-07-29

**Status:** `IMPLEMENTED`

**Priority:** `P0`

**Source:** gameplay planning review plus verified CABT `CardData` metadata.

**Evidence type:** SDK contract and replay matchup inspection.

### Original feedback

Rule Box status changes both combat and the Prize race. Pokémon ex and Mega
Evolution Pokémon ex concede different numbers of Prize cards, and some
Pokémon or Stadium effects prevent damage based on the attacker or defender
having a Rule Box.

### General principle

Derive Rule Box status and base Prize value from the canonical catalog. Before
scoring an attack or target, apply known public damage-prevention and Prize
modifier effects. Trace an ineffective legal attack explicitly instead of
valuing its printed damage.

### Implemented foundation

- catalog traits expose `has_rule_box` and `base_prize_value`;
- Mega Evolution Pokémon ex remain Rule Box Pokémon even when only `megaEx` is
  set by the SDK;
- `PrizeMap` records contextual Prize value and known damage prevention;
- the heuristic emits `attack_damage_prevented`;
- focused tests cover normal, ex, Mega ex, and ex-based damage prevention.

### Evaluation gate

Promotion still requires the paired local matrix, zero operational failures,
and the Rule Box tactical fixtures. This record remains below `VALIDATED`
until that matrix exists.

---

## FB-2026-003 — Prize checking and searchable-card availability

**Date:** 2026-07-29

**Status:** `IMPLEMENTED`

**Priority:** `P0`

**Source:** gameplay planning review and CABT replay inspection.

**Evidence type:** 31 Kaggle replays in which `select.deck` cardinality matches
the actor's `deckCount`.

### Original feedback

The agent must know which of its cards are prized and which copies remain
available to search. It must not plan a tutor sequence around a card confirmed
to be unavailable.

### General principle

Maintain probabilistic own-card availability until a complete deck search
exposes the remaining deck. After that observation, derive exact current
prized and searchable counts from the immutable submitted deck and known
zones. Never expose the estimate as a factual public state.

### Implemented foundation

- `PrizeCheckResult` distinguishes `PROBABILISTIC`, `EXACT`, and
  `INCONSISTENT`;
- each card exposes searchable/prized ranges, expectations, and probability;
- exact deck searches produce exact counts;
- confirmed unavailable tutor targets emit
  `confirmed_prized_unsearchable`;
- cardinality failure disables the signal safely.

### Evaluation gate

Golden replay cases must confirm exact counts across search, draw, discard,
attachment, Evolution, and Prize-taking transitions before this record can
move to `VALIDATED`.

### Reason codes

- `develop_required_basic_before_terminal`;
- `develop_snover_before_attack`;
- `evolve_required_line_before_terminal`;
- `evolve_abomasnow_before_attack`;
- `maintain_backup_attacker`;
- `development_target_reached`;
- `immediate_win_overrides_development`;
- `bench_full_blocks_development`;
- `reserved_bench_slot`;
- `development_liability_avoided`.

### Metrics

- required legal Basic Pokémon plays skipped before attack or `END`;
- required legal evolutions skipped before attack or `END`;
- Bench occupancy by turn;
- turns to first viable backup attacker;
- fraction of turns ending with no viable replacement attacker;
- Basic-to-final-stage conversion rate and conversion time;
- losses after an Active Knock Out with no replacement Pokémon;
- operational failures and decision latency after adding the ordering layer.

Metrics must be reported both generically and by deck profile. The Abomasnow
profile must additionally report Snover plays and Snover-to-Mega-Abomasnow
conversion.

### Golden scenarios

- Snover in hand, open Bench slot, and legal non-winning attack;
- two consecutive legal Snover plays across successive `MAIN` observations;
- eligible Active and Benched Snover evolution targets;
- immediate winning attack with development still available;
- full Bench with Snover in hand;
- target count reached for a generic deck profile;
- reserved Bench slot and low-value Basic Pokémon;
- Active attacker at Knock Out risk without a prepared replacement.

### Evaluation gate

- zero required development actions skipped before a non-winning terminal
  action in focused fixtures;
- zero invalid choices in full-Bench and blocked states;
- immediate wins remain dominant;
- zero `INVALID`, `ERROR`, and `TIMEOUT` in evaluation;
- no regression against the frozen accepted gameplay baseline;
- decision traces demonstrate repeated re-evaluation after every `MAIN`
  action.

### Traceability

- Gameplay rule:
  [`27_gameplay_rules.md`](27_gameplay_rules.md#confirmed-deck-rule-continuous-snoverabomasnow-development)
- Active remediation:
  [`02_sprints/heuristic_only_improvement_sprints.md`](02_sprints/heuristic_only_improvement_sprints.md#h2a--continuous-snoverabomasnow-board-development)
- MVP policy work:
  [`02_sprints/mvp_implementation_sprints.md`](02_sprints/mvp_implementation_sprints.md#s4--explainable-heuristic-policy)
- Future human evidence capture:
  [`28_human_gameplay_capture.md`](28_human_gameplay_capture.md)

## Adding future feedback

Add one immutable feedback record for each distinct gameplay finding. If
several observations expose the same underlying principle, link them to the
existing item instead of silently rewriting its source.

When evidence contradicts an active item:

- preserve both observations;
- record the relevant deck, matchup, and board conditions;
- narrow the applicability conditions or add an explicit exception;
- rerun the affected golden scenarios and evaluation gate;
- mark the old rule `REJECTED` only when its original scope is disproved.

Human demonstrations defined in
[`28_human_gameplay_capture.md`](28_human_gameplay_capture.md) may create new
feedback items automatically in `CAPTURED` state, but promotion to
`IN_PROGRESS` remains a reviewed decision.
