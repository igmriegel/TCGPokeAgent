# Human gameplay capture

**Status:** `IDEA`

This document defines a future workflow for observing a human playing CABT,
capturing the decisions and optional reasoning, and deriving auditable
heuristics or learning data from those demonstrations.

The goal is not merely to replay a completed match. The system must pause at
each live decision, expose the legal options without renumbering them, collect
the human choice, send it to the simulator, and preserve enough context to
understand why that choice was made.

## Objectives

- let a human play the frozen deck against SDK agents or another policy;
- record every observation, legal option, selected simulator index, and
  resulting transition;
- optionally collect a structured explanation before or after the choice;
- compare human and agent rankings on the exact same decision;
- derive candidate gameplay rules, feature priorities, preference pairs, and
  supervised examples;
- preserve the original demonstration separately from derived labels.

A human action is evidence of a preference, not automatically a correct or
optimal label.

## Proposed interaction

At every decision:

1. render the visible board, hand, discard, Prize count, turn flags, and
   remaining deck counts;
2. render every legal option with its original option position and resolved
   card, Pokémon, attack, target, or count;
3. show the current high-level turn plan when one exists;
4. let the human select one or more legal indices within the current
   cardinality;
5. optionally ask for reasoning tags, free text, confidence, and intended
   follow-up;
6. validate the selection locally and send it to CABT;
7. record the resulting observation and continue until the match ends.

The interface must support nested selections such as tutor targets, discard
costs, Energy costs, switching, damage placement, and yes/no effects. These
choices remain linked to the parent action that opened the sequence.

## Interface options

### Phase 1 — Terminal human agent

Build the smallest reliable capture surface first:

- run a local `cg.game` or `kaggle-environments` match;
- print a readable board and numbered legal options;
- read the human selection from stdin;
- reject malformed or illegal input without advancing the game;
- save an immutable JSONL trace and a normal visualizer replay.

This phase validates the simulator bridge and trace schema without requiring a
browser application.

### Phase 2 — Local browser player

Add a local web interface that:

- renders the same live information as the terminal agent;
- communicates with a local match process;
- provides card names, action descriptions, and target previews;
- captures optional reasoning without delaying the simulator indefinitely;
- lets the user review the completed replay and annotations.

The current `visualizer.html` is a post-match replay bridge and cannot by
itself capture live decisions. It may become the entry point for an addon, but
live play requires a local backend that owns the CABT battle state.

### Phase 3 — Visualizer annotation addon

For existing replays, add a separate review mode where a human can:

- pause at each decision;
- inspect the action that was taken;
- choose the action they would have preferred;
- label the original decision as acceptable, mistake, forced, or uncertain;
- explain the tactical or strategic reason;
- mark the first decision where the turn plan or match plan went wrong.

Post-hoc annotations must be marked separately from live demonstrations because
the reviewer can see information or outcomes unavailable at decision time.

## Human decision trace

Each record should contain at least:

```text
schema_version
session_id
match_id
decision_index
parent_decision_index
participant_id
participant_experience
deck_id and deck_sha256
sdk_version
agent/opponent identity
side and turn
observation_before
visible_state_snapshot
select_type and select_context
legal_options
original_option_indices
human_selected_indices
agent_ranked_indices
agent_selected_indices
selection_legal
decision_duration_ms
reason_tags
free_text_reason
confidence
intended_follow_up
observation_after
match_result
termination_reason
replay_path
```

Suggested reason tags include:

- `DRAW_NEED`
- `BOARD_PRESENCE`
- `SECOND_ATTACKER`
- `SUPPORT_POKEMON`
- `EVOLUTION_SETUP`
- `ENERGY_ENABLE_ATTACK`
- `ENERGY_PREPARE_BENCH`
- `SUPPORTER_DRAW`
- `SUPPORTER_TUTOR`
- `ITEM_SEQUENCE`
- `STADIUM_NEED`
- `SWITCH_OR_RETREAT`
- `KO_NOW`
- `PRIZE_TRADE`
- `DONK`
- `RESOURCE_PRESERVATION`
- `DECKOUT_RISK`
- `STRATEGIC_PASS`
- `FORCED_SELECTION`
- `OTHER`

The trace stores the raw human reason and the normalized tags. Automated
pipelines must never overwrite the raw record.

## Deriving knowledge

Human traces can support several different outputs:

### Heuristic discovery

- aggregate actions and reasons by `SelectContext`, board shape, and turn;
- find repeated conditional patterns;
- convert a pattern into a proposed rule using the template in
  [`27_gameplay_rules.md`](27_gameplay_rules.md);
- require golden scenarios and an evaluation gate before implementation.

### Disagreement analysis

- replay the exact observation through the current agent;
- compare the human choice with the agent's ranking and score margin;
- group disagreements by missing feature, bad weight, unresolved card,
  sequencing error, or strategic horizon;
- prioritize rules that explain many high-confidence disagreements.

### Preference and imitation data

- create chosen-versus-rejected option pairs from high-confidence decisions;
- keep all options grouped by decision;
- split train, validation, and holdout by match or capture session, never by
  individual decision;
- retain participant identity only as a pseudonymous grouping field;
- do not use post-hoc knowledge as if it were available during live play.

### Turn-plan extraction

Use intended follow-ups and linked nested decisions to learn sequences such as:

```text
tutor Pokémon -> bench attacker -> attach Energy -> evolve -> attack
```

The derived plan remains a hypothesis until it is validated against simulator
outcomes.

## Quality, privacy, and bias

- capture only visible information available to the human at decision time;
- never store Kaggle credentials, API tokens, browser cookies, or unrelated
  local data;
- obtain explicit consent before retaining participant identifiers or free
  text;
- allow deletion of a participant's raw sessions;
- record experience level, deck familiarity, and whether assistance was used;
- distinguish live choice, replay review, corrected choice, and guessed
  rationale;
- preserve mistakes instead of silently relabeling them as optimal;
- require multiple examples or simulator evidence before promoting a human
  pattern into a universal rule.

## Proposed delivery stages

| Stage | Outcome | Gate |
|---|---|---|
| HD0 | Trace schema and privacy contract | schema round-trip and no hidden-data leakage |
| HD1 | Terminal human agent | one complete legal match and replay |
| HD2 | Local browser player | complete match with reconnect-safe decision capture |
| HD3 | Replay annotation addon | live and post-hoc labels remain distinguishable |
| HD4 | Insight report | disagreement clusters and proposed rule candidates |
| HD5 | Learning export | leakage-safe preference dataset with immutable provenance |

## Definition of useful completion

The first useful milestone is not a trained model. It is one complete human
match for which we can answer:

- what the human saw;
- which legal alternatives existed;
- what they selected;
- why they selected it;
- what the current agent would have selected;
- what happened next;
- whether the difference suggests a reusable gameplay rule.

