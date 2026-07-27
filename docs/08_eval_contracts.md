# Evaluation contracts

## Runner

The runner receives immutable versions of two agents, decks, seed, and profile. It executes the SDK without knowing scoring, records every call, and returns a `MatchRecord`.

Minimum fields of `MatchRecord`:

- `run_id`, `match_id`, seed, and side;
- agent, deck, and SDK versions;
- start, end, and duration;
- result, reason, and turns;
- final status of both agents;
- list of `DecisionRecord`;
- replay and error paths.

`DecisionRecord` records turn, context, cardinality, chosen indices, scores/reasons, duration, overage balance, and search data.

## Gate matrix

The candidate runs as player 0 and 1 against:

- SDK agent `random`;
- SDK agent `first`;
- heuristic without search;
- itself.

Smoke totals 20 matches; full totals at least 200. The exact distribution per matchup/side appears in the manifest before execution.

## Validation

Before counting a decision:

- output is `list[int]`;
- cardinality respects `SelectData`;
- indices belong to the option list;
- aggregate constraints were satisfied;
- duration and overage balance were recorded.

Any `INVALID`, `ERROR`, or `TIMEOUT` fails the candidate, even if the win rate is high.

## Statistics

Calculate metrics per [`03_metrics.md`](03_metrics.md). Wilson uses 95%, with number of wins as successes and total valid matches as `n`. Paired comparisons keep results by seed and side, not just aggregates.

## Search gate

Compare the same heuristic with search off and on:

- same matrix, decks, and seeds;
- `win_rate_search >= win_rate_heuristic`;
- zero operational failures;
- max search up to 100 ms;
- coverage report and each fallback.

If the difference is within noise, the version without search remains stable because it is cheaper.
