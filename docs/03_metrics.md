# Metrics catalog

## Outcome

For each matchup and aggregate:

- `wins`, `draws`, `losses`;
- `win_rate`, `draw_rate`, `loss_rate`;
- 95% Wilson interval for `win_rate`;
- matches as player 0 and player 1;
- turns per match and termination reason.

The denominator of `win_rate` includes all valid matches; draws are not removed. Operational failures are reported separately and prevent promotion.

## Operation

- decision duration p50, p95 and maximum;
- match duration p50, p95 and maximum;
- `INVALID`, `ERROR` and `TIMEOUT` counts;
- memory/package size at the final gate.

## Search

- eligible decisions;
- actually searched decisions;
- `search_coverage = searched / eligible`;
- failures by `belief_inconsistent`, `api_error`, `budget_exhausted` and `unexpected`;
- p50/p95/maximum duration;
- top-1 choice change;
- paired win delta against pure heuristics.

## Stability

- rate by side, seed and matchup;
- player 0 versus player 1 difference;
- dispersion between batches;
- worst matchup in the frozen pool.

## Gate

The report is invalid if it omits denominators, sides, deck version, SDK, seeds or failures. Average duration does not replace p95 and maximum.
