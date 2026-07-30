# Human gameplay capture

> Specification for future live human demonstrations. This is not a feedback
> register and does not describe post-hoc reviews of automated matches.

**Track status:** `DEFERRED`

**Captured live sessions:** 0

**Canonical tasks:** HD-00–HD-05 in
[`03_tasks/TASK_INDEX.md`](03_tasks/TASK_INDEX.md)

## Boundary

A live demonstration records only information visible when the human decides.
The human selects original simulator indices, the selection is validated, CABT
advances, and the transition is stored.

Post-hoc review can use later knowledge and therefore has a different schema.
The existing `competitive-gameplay-review-v1` records are post-hoc reviews of
agent matches; they are not human demonstrations.

## Delivery stages

| Stage | Outcome | Gate |
|---|---|---|
| HD0 | Trace schema and privacy contract | Round-trip, consent, deletion, and no hidden-data leakage |
| HD1 | Terminal human player | One complete legal match and replay |
| HD2 | Browser player | Complete reconnect-safe match |
| HD3 | Replay annotation UI | Live and post-hoc labels remain distinguishable |
| HD4 | Insight report | Human/agent disagreement clusters and rule candidates |
| HD5 | Learning export | Leakage-safe grouped preferences with immutable provenance |

No stage is complete. The post-hoc annotation CLI provides reusable foundation
for HD3 but does not satisfy its UI or evidence gate.

## Minimum live decision record

- schema, session, match, participant pseudonym, and experience;
- deck, SDK, opponent, side, turn, and parent decision;
- observation before and visible factual snapshot;
- selection type/context and legal options with original indices;
- human choice, agent ranking/choice, legality, and duration;
- optional tags, raw reasoning, confidence, and intended follow-up;
- observation after, result, termination reason, and replay path.

Raw records are immutable. Derived labels, preferences, and proposed rules are
separate versioned outputs.

## Interaction requirements

1. render the visible board and every legal option;
2. accept zero, one, or multiple indices within CABT cardinality;
3. reject malformed input without advancing;
4. support nested tutor, cost, switch, damage, and yes/no selections;
5. optionally collect reasoning without changing the action;
6. persist the transition and continue to termination.

## Privacy and evidence rules

- obtain explicit consent before retaining identifiers or free text;
- never store credentials, tokens, cookies, or unrelated local data;
- allow participant-session deletion;
- preserve human mistakes rather than silently relabeling them;
- split learned data by session or match, never individual decisions;
- treat one human action as preference evidence, not optimal ground truth;
- promote a derived rule only through the normal feedback and evaluation gates.

## First useful milestone

HD1 is useful when one complete match can answer what the human saw, which
alternatives existed, what they selected, why, what the agent preferred, what
happened next, and whether the disagreement suggests a reusable rule.
