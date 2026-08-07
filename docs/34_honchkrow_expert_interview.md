# Honchkrow/Porygon expert interview and policy audit

> Interview checkpoint: Rounds 1–3 were completed and ratified on 2026-08-07.
> Rounds 4–12 below are frozen as the resume agenda. Runtime experiments may
> implement only explicitly ratified rules and must remain separate from the
> promoted `supporter_resource_v2` baseline until their evaluation gate passes.

> Status: `INTERVIEW_REQUIRED`. This document audits the current dedicated
> policy and defines the protocol for converting expert answers into an
> implementation plan. It does not change gameplay behavior by itself.

**Last reviewed:** 2026-08-07

**Current code baseline:** `d5f42c5`

**CABT comparison baseline:** 300 matches, 249W/51L, 83.0% win rate, zero
execution failures, 12 audited deck-out losses

## Objective

Ratify the real game plan of the fixed Honchkrow/Porygon deck with an expert
player, distinguish universal rules from matchup exceptions, and leave a
decision-complete implementation plan that another agent can resume without
inventing strategy.

The interview must produce rules with explicit conditions, priorities,
exceptions, counterexamples, observability requirements, tests, telemetry, and
promotion gates. Expert statements are requirements evidence, not automatic
authorization to modify the runtime.

## Evidence and authority

Use evidence in this order during the interview:

1. CABT legal options and simulator behavior;
2. exact card text and fixed 60-card list;
3. expert decisions and counterexamples captured in this interview;
4. synchronized Kaggle replays and CABT traces;
5. current implementation and tests;
6. historical strategy notes.

When card text and CABT behavior differ, record both. The implementation must
follow CABT while the document preserves the divergence.

## Deck facts

| Role | Cards | Count | Current implementation assumption |
|---|---|---:|---|
| Primary line | Team Rocket's Murkrow / Honchkrow | 4 / 3 | Honchkrow is the default attacker; Murkrow attacks are conditional |
| Secondary line | Team Rocket's Porygon / Porygon2 | 2 / 1 | Porygon2 is a late R Command attacker; Hacking is always forbidden |
| Matchup tech | Team Rocket's Articuno | 2 | Used only against visible Dragapult-family threats and never attacks |
| Supporters | Ariana, Archer, Giovanni, Petrel, Proton | 4 each | All twenty feed Rocket Feathers in hand and R Command in discard |
| Pokémon search | Poké Pad / Ultra Ball | 4 / 1 | Search is allowed only with a proven immediate development target |
| Supporter search | Team Rocket's Transceiver | 4 | Target follows the persistent turn objective |
| Top-deck selection | Roto-Stick | 4 | Used for a nonlethal ready-Honchkrow line; every revealed Supporter is taken |
| Recovery | Night Stretcher / Miracle Headset | 3 / 1 | Stretcher requires an immediately playable Pokémon; Headset prefers exactly two Supporters |
| Stadium | Team Rocket's Factory | 3 | Play before Ariana; activate after a Rocket Supporter and productive Roto-Stick |
| Energy | Team Rocket's Energy / Ignition Energy | 4 / 4 | Rocket supplies two Darkness/Psychic units; Ignition supplies three Colorless on Evolutions and expires |

## Current decision model

The dedicated agent currently:

1. chooses one persistent objective when the first decision of a turn is seen;
2. filters hard-forbidden candidates;
3. honors exact switch, Ignition, evolution-KO, and discard commitments;
4. takes immediate wins and committed attacks;
5. plays Factory before the draw sequence;
6. performs required Proton setup;
7. prefers Petrel-to-Factory over a marginal Ariana;
8. reduces the hand through selected recovery, Pokémon, and evolution plays;
9. plays Ariana, productive Roto-Stick, and the Factory draw effect;
10. evolves productive attackers, attacks, or ends the turn.

The scorer separately ranks targets, discard choices, attacks, promotions, and
nested selections. Generic fallback remains available for every legal prompt.

## Audit findings requiring ratification

### A. Correctness and measurement risks

| ID | Severity | Finding | Consequence | Interview or implementation decision |
|---|---|---|---|---|
| HA-001 | P0 | Porygon terminal telemetry counts any visible winning R Command damage as an opportunity, even when Porygon2, promotion, or Energy is unavailable | The baseline reports 29 opportunities and zero conversions, but that ratio is not a valid policy conversion metric | Define a feasible terminal opportunity and correct attacker/target attribution |
| HA-002 | P0 | Conversion telemetry compares the committed own attacker card ID with the attack candidate's target card ID | A real Porygon2 conversion can remain recorded as zero | Bind telemetry to attacker serial, attack ID, target serial, and resulting Prizes |
| HA-003 | P0 | Typed energy exists in the attack solver and scorer, but several hard guards and horizon checks still use raw attached-card counts | Rocket Energy can be treated as one card in one branch and two units in another | Establish one authoritative typed energy evaluator for all policy branches |
| HA-004 | P1 | Entry-point exception fallback returns the first cardinality-valid indices without strategic telemetry | A legal but strategically catastrophic fallback can be invisible in evaluation | Decide whether fallback must emit a reason and use context-aware least harm |
| HA-005 | P1 | Terminal classification has 39 unknown losses in the promoted 300-match baseline | Strategy changes cannot be attributed confidently | Define exact terminal reason extraction before the next promotion claim |

### B. Strategic assumptions currently encoded as hard rules

| ID | Current rule | Ratification question |
|---|---|---|
| HS-001 | Always choose to go first | Is first always correct, or does the preferred side depend on matchup, opening hand, or Proton access? |
| HS-002 | Hacking is never used | Are there hand sizes, deck-out positions, lock states, or zero-damage turns where Hacking is correct? |
| HS-003 | Articuno never attacks | Can Dark Frost ever be the cheapest KO, a Prize-race bridge, or the only legal productive attack? |
| HS-004 | Deceit needs immediate decisive metadata | When is searching any Supporter better than Torment, setup, or passing? Which Supporter should it fetch? |
| HS-005 | Torment is mostly damage/control and loses to a proven Honchkrow KO | Which opposing attacks are worth disabling, and when does Torment create a two-turn win? |
| HS-006 | One natural draw is reserved globally; two are reserved against incomplete Mega Abomasnow | What reserve is correct by Prize count, board state, attacker durability, and known remaining Energy? |
| HS-007 | The first chosen objective persists for the full turn | Which draws or revealed cards should permit replanning from setup into KO, control, or conservation? |
| HS-008 | Factory is playable whenever the Stadium slot is open and the deck reserve permits it | Should Factory require a Rocket Supporter line, protect an existing Stadium, or consider the opponent's Stadium value? |
| HS-009 | Petrel primarily searches Factory, emergency Ariana, or Giovanni | What is the complete Trainer target priority by phase and matchup? |
| HS-010 | Ultra Ball requires two non-Energy, non-Supporter disposable cards | When should Supporters be discarded deliberately to power R Command, and when may Energy or Pokémon be spent? |
| HS-011 | Night Stretcher requires an immediately playable Pokémon | Is recovery for next turn, hand-count shaping, Prize denial, or future evolution ever worth the card now? |
| HS-012 | Miracle Headset normally requires two missing KO Supporters | When is one recovered Supporter, Ariana, Giovanni, or disruption worth the ACE SPEC? |
| HS-013 | Roto-Stick is used only with a ready Honchkrow and takes every revealed Supporter | Should it be used to find Ariana/setup cards, and are there deck-out or hand-size reasons to leave Supporters? |
| HS-014 | Rocket Energy is forbidden on Porygon2; Ignition is restricted to an immediate active attack | Confirm the exact attachment map for Murkrow, Honchkrow, Porygon, Porygon2, and Articuno across current and next-turn plans |
| HS-015 | Retreat requires a specific same-turn attack improvement | Are survival, Prize denial, status removal, pivoting, or protecting accumulated Energy independently valid reasons? |
| HS-016 | Articuno is activated only by a fixed Dragapult-family ID set | Which archetypes, attacks, or board effects actually justify Articuno? |

### C. Documentation and policy ownership gaps

| ID | Finding | Required resolution |
|---|---|---|
| HD-001 | `27_gameplay_rules.md` mixes generic Abomasnow/Kyogre rules with dedicated Honchkrow rules | Create a deck-specific rule section and state precedence explicitly |
| HD-002 | The runtime variant named `baseline` is not the newly promoted CABT comparison baseline; the default remains `supporter_resource_v2` | Rename or document runtime variants so baseline identity is unambiguous |
| HD-003 | The deck profile calls all five Pokémon attackers while the policy forbids Articuno and Porygon attacks | Ratify roles and make the profile match executable policy |
| HD-004 | Profile promotion priorities include `lowest_prize_value`, but all own Pokémon are declared as one Prize and the dedicated selection code does not implement a general tie-breaker | Replace the placeholder with the real sacrifice and promotion order |
| HD-005 | Historical notes and current report contents contain incompatible results for the Ignition 200-match run | Preserve history but add a correction record with the authoritative artifact hash and metrics |
| HD-006 | Task T-026 still cites 56/400 deck-outs, while the current baseline records 12/300 | Update the next action without erasing the historical gate |
| HD-007 | No single document states the complete fixed-deck playbook | Make the ratified interview output the canonical Honchkrow strategy specification |

## Interview answer contract

Each accepted answer must be recorded with this schema:

```yaml
question_id: "HI-..."
expert_rule: "One imperative sentence"
strength: "MUST | SHOULD | MAY | NEVER"
when:
  - "Observable precondition"
priority_above:
  - "Competing line"
priority_below:
  - "Superior line"
exceptions:
  - "Explicit exception"
counterexample: "A position where the naive rule is wrong"
hidden_information_policy: "How uncertainty changes the choice"
required_state: ["Facts the parser must expose"]
telemetry: ["Counters or decision reasons"]
golden_tests: ["Minimum reproducible positions"]
status: "PROPOSED | RATIFIED | REJECTED | NEEDS_REPLAY"
```

If a response is matchup-dependent, capture a decision table. If the answer is
"it depends," the next question must identify the observable variables and
their ordering. Examples are evidence only when the relevant board, hand,
discard, deck, Prize, turn, and legal-option facts are preserved.

## Interview sequence

### Round 1 — Deck identity and default win condition

Goal: define what the deck is trying to accomplish before discussing cards.

1. `HI-001`: What is the primary win condition in an average game: repeated
   Rocket Feathers, one large Rocket Feathers, late R Command, or a flexible
   combination?
2. `HI-002`: What observable facts make the plan switch from Honchkrow to
   Porygon2?
3. `HI-003`: How many attackers should normally be developed, and which Bench
   slots must remain free?
4. `HI-004`: Which resources are genuinely scarce: Energy, Murkrow, Honchkrow,
   Porygon2, Ariana, Miracle Headset, Stadium, or turns?
5. `HI-005`: Describe the ideal board, hand, discard, and deck state at the end
   of turns 1, 2, 3, and the first Prize-taking turn.

Exit criterion: one default plan, named alternative plans, and observable plan
switches.

### Round 2 — Opening, turn order, and setup

1. `HI-010`: Is going first unconditional? List every exception.
2. `HI-011`: Rank opening Active choices for every legal opening combination.
3. `HI-012`: Rank Bench placement when Murkrow, Porygon, and Articuno compete
   for space.
4. `HI-013`: When should first-turn Proton be played, and what exact three-card
   selection should it make for each existing board?
5. `HI-014`: When is Ariana better than Proton on the first two own turns?
6. `HI-015`: When should Transceiver fetch Proton versus Ariana, Petrel,
   Giovanni, or Archer?

Exit criterion: deterministic opening tables for side, Active, Bench, Proton,
and Transceiver.

### Round 3 — Turn objective and replanning

1. `HI-020`: Ratify or reorder: win now, prevent no-Pokémon loss, highest-Prize
   KO, build board, improve resources, damage/control.
2. `HI-021`: Should a turn objective remain fixed after Ariana, Factory,
   Roto-Stick, Poké Pad, Ultra Ball, or a Prize card changes known information?
3. `HI-022`: Which actions are safe before checking for a KO, and which must be
   delayed until the attack line is calculated?
4. `HI-023`: Define the tie-breaker between immediate damage, next-turn KO
   probability, board durability, and deck preservation.

Exit criterion: a replanning state machine with explicit checkpoints.

### Round 4 — Energy economy

1. `HI-030`: Give the attachment priority for each Pokémon and evolution stage.
2. `HI-031`: When should Team Rocket's Energy be placed on Murkrow before it
   evolves, and can it ever belong on Porygon/Porygon2?
3. `HI-032`: Is Ignition strictly a same-turn attack resource, or may it enable
   retreat, absorb an effect, or prepare a forced promotion?
4. `HI-033`: When is an additional Energy above the cheapest attack cost
   strategically correct?
5. `HI-034`: How should the agent value the last Energy in hand and known
   Energy remaining in deck or Prizes?

Exit criterion: one typed-energy allocation table plus over-attachment and
last-Energy exceptions.

### Round 5 — Draw, search, and sequencing

For each scenario, provide the complete ordered sequence, including when to
stop drawing:

1. `HI-040`: Factory + Ariana + Roto-Stick.
2. `HI-041`: Petrel + Ariana without Factory in play.
3. `HI-042`: Transceiver plus multiple Supporter targets.
4. `HI-043`: Poké Pad and Ultra Ball with both evolution lines available.
5. `HI-044`: Night Stretcher before or after Ariana.
6. `HI-045`: Low deck with missing Energy versus low deck with a complete
   attacker.
7. `HI-046`: Which Items must precede a Supporter, which must follow it, and
   which depend on hand-size or deck composition?

Exit criterion: a sequence DAG, not one universal linear order.

### Round 6 — Supporter-specific policy

For Ariana, Archer, Giovanni, Petrel, and Proton, answer:

1. minimum value that justifies the once-per-turn Supporter slot;
2. preferred timing and target;
3. conditions that make the card expendable to Rocket Feathers or Ultra Ball;
4. conditions that make it worth recovering with Miracle Headset;
5. matchup-specific exceptions;
6. whether it should be preserved for R Command instead of played.

Exit criterion: one decision table per Supporter.

### Round 7 — Attack selection and Supporter discard

1. `HI-060`: Enumerate valid uses of Deceit, Torment, Rocket Feathers, Hammer
   In, Hacking, R Command, and Dark Frost.
2. `HI-061`: Is a nonlethal Rocket Feathers ever correct? Define the exact
   two-turn horizon and survival assumptions.
3. `HI-062`: Which Team Rocket Supporters should be discarded first to Rocket
   Feathers, and which must be preserved?
4. `HI-063`: When should Hammer In save Supporters even if Rocket Feathers also
   takes the KO?
5. `HI-064`: When should the deck intentionally load Supporters into discard
   for R Command rather than preserve hand damage?
6. `HI-065`: How should weakness, resistance, effects, Prize value, retaliation,
   and remaining attacker depth break ties?

Exit criterion: exact attack legality, value, discard, and tie-break tables.

### Round 8 — Promotion, retreat, switching, and sacrifice

1. `HI-070`: Rank forced-promotion targets by readiness, survival, retreat
   cost, future evolution, and Prize race.
2. `HI-071`: Define every valid paid-retreat reason, including defensive ones.
3. `HI-072`: Define Giovanni's own target and opposing target as one coupled
   decision.
4. `HI-073`: When should Porygon2 be promoted for R Command now, next turn with
   Ignition, or not at all?
5. `HI-074`: When is Articuno or an unevolved Pokémon the correct sacrifice?
6. `HI-075`: What is the correct action when every optional action is bad but
   END leaves a vulnerable Active?

Exit criterion: promotion and switch matrices with exact attacker serial and
target requirements.

### Round 9 — Matchups and opponent plans

Start with Mega Abomasnow, Dragapult, and Alakazam, then add every archetype the
expert considers materially different.

For each matchup record:

1. preferred side and opening Active;
2. primary and backup attacker;
3. Prize map and target order;
4. minimum KO thresholds;
5. cards to preserve, spend, or never Bench;
6. valid control attacks and retreat rules;
7. deck-out posture;
8. observable signal that changes the plan.

Exit criterion: a matchup registry keyed by public evidence, never by guessed
hidden deck identity alone.

### Round 10 — Late game, Prizes, deck-out, and uncertainty

1. `HI-090`: Define the minimum deck reserve by board state and turns needed to
   win; ratify whether one or two natural draws are sufficient.
2. `HI-091`: When is drawing to zero correct because the game ends first?
3. `HI-092`: How should known Prizes change tutor targets and plan selection?
4. `HI-093`: What probability or evidence is sufficient to assume a missing
   card is prized?
5. `HI-094`: How should the agent play when Energy access is uncertain?
6. `HI-095`: Define acceptable intentional passes, zero-damage attacks, and
   resource-preserving turns.

Exit criterion: a deck-out horizon calculator and uncertainty policy.

### Round 11 — Worked positions and adversarial review

The expert supplies or reviews at least:

- five opening hands;
- five mid-game draw-engine decisions;
- five attack/discard choices;
- five forced promotions;
- five low-deck positions;
- three positions per important matchup;
- every known disagreement from submissions `55320796` and `55322957`.

For each position, record the best action, second-best action, why the second is
worse, and the smallest fact change that reverses the decision.

Exit criterion: replay-derived golden fixtures and explicit decision
boundaries.

### Round 12 — Final ratification and implementation planning

1. resolve conflicting rules and assign precedence;
2. mark each rule `RATIFIED`, `REJECTED`, or `NEEDS_REPLAY`;
3. identify new parser/state facts before policy work;
4. group implementation into atomic, independently testable slices;
5. freeze baseline, evaluation opponents, metrics, and rollback conditions;
6. approve the final specification before runtime changes.

## Required final implementation plan

The final plan must contain:

1. **Rule registry:** stable IDs, imperative rules, precedence, exceptions.
2. **State contract changes:** new factual fields and observation provenance.
3. **Policy slices:** scorer, filters, commitments, sequencing, matchup modules.
4. **Documentation reconciliation:** profile, gameplay rules, feedback, status,
   and historical corrections.
5. **Golden tests:** one test per rule plus boundary and counterexample cases.
6. **Replay tests:** exact observations from accepted expert disagreements.
7. **Telemetry:** opportunity denominator, conversion event, failure reason,
   and terminal attribution for every promoted tactic.
8. **Evaluation:** smoke, 300-match development sample, independent 1,000-match
   confirmation, both sides, and relevant matchup slices.
9. **Acceptance gates:** zero operational failures, no forbidden-action
   regressions, deck-out and unknown-loss ceilings, non-inferiority margin, and
   tactic-specific conversion thresholds.
10. **Rollback:** preserved runtime variant, package hash, baseline report, and
    explicit revert conditions.

## Resume protocol for another agent

1. Read this document completely.
2. Read `docs/27_gameplay_rules.md`, `docs/29_gameplay_feedback.md`, and the
   current `docs/PROJECT_STATUS.md`.
3. Continue at the first interview round without an `Exit criterion` marked as
   satisfied in a future interview record.
4. Never infer an expert answer from current code.
5. Append answers using the interview answer contract and link supporting
   replays or worked positions.
6. Do not implement until Round 12 produces an explicitly approved plan.
