# Evaluation contracts

## Runner

The runner executes seeded CABT matches, records every policy call, and returns
`MatchRecord` objects without scoring decisions or aggregating statistics.

The stable field-level contract for `MatchRecord`, `DecisionRecord`, and
`RunReport` lives in [`03_metrics.md`](03_metrics.md) and the dataclasses in
[`src/eval/runner.py`](../src/eval/runner.py).

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

Calculate metrics per [`03_metrics.md`](03_metrics.md). Wilson uses 95%, with
the number of wins as successes and the full batch size as `n`. Paired
comparisons keep results by evaluation case identifier and side, not just
aggregates. For `cabt`, the identifier is metadata rather than a promise that
native RNG outcomes repeat.

## Search gate

Compare the same heuristic with search off and on:

- same matrix, decks, and seeds;
- `win_rate_search >= win_rate_heuristic`;
- zero operational failures;
- max search up to 100 ms;
- coverage report and each fallback.

If the difference is within noise, the version without search remains stable because it is cheaper.
