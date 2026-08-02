# Metrics and report pipeline

This is the canonical reference for the evaluation metrics used by
`src/eval`, the gameplay smoke gate, and the replay investigation report.
It describes where each value comes from, which output formats are stable, and
how the numeric summaries are computed.

## End-to-end flow

```text
Observation
  -> MatchRunner
       - records DecisionRecord for each policy call
       - records MatchRecord for each seeded SDK match
  -> aggregate(matches) -> AggregateMetrics
  -> serialize_report(report, metrics)
       -> JSON artifact
       -> write_markdown(report)

RunReport
  -> GameplayMetrics.from_report(report)
       -> gameplay_smoke gate

Replay JSON files
  -> scripts/generate_investigation_report.py
       -> standalone HTML investigation report
```

The runner captures observable runtime facts only. Belief state, search
internals, and score explanations are serialized only when the policy exposes
them through `PolicyDecision`.

## Metric Sources

| Layer | Source | What it captures |
|---|---|---|
| Decision trace | `DecisionRecord` | One policy call, its legal options, selected indices, timing, and optional scoring/search metadata |
| Match trace | `MatchRecord` | One seeded CABT match, its result, runtime, final SDK statuses, and all recorded decisions |
| Batch trace | `RunReport` | One batch execution with timestamps and ordered match records |
| Aggregate summary | `AggregateMetrics` | Outcome counts, win rate, Wilson interval, duration percentiles, and failure counts |
| Gameplay observability | `GameplayMetrics` | Visible main-turn action counts derived from decision traces |

## Stable Dataclasses

### `AggregateMetrics`

| Field | Meaning |
|---|---|
| `total` | Number of `MatchRecord` objects in the batch |
| `wins` | Matches with `result == "win"` |
| `draws` | Matches with `result == "draw"` |
| `losses` | Matches with `result == "loss"` |
| `errors` | Matches whose `status` is not `OK` |
| `win_rate` | `wins / total` |
| `wilson_lower` | Lower bound of the 95% Wilson interval for win rate |
| `wilson_upper` | Upper bound of the 95% Wilson interval for win rate |
| `avg_duration_ms` | Mean match runtime in milliseconds |
| `p50_duration_ms` | Median match runtime |
| `p95_duration_ms` | 95th percentile of match runtime |
| `p99_duration_ms` | 99th percentile of match runtime |
| `p50_decision_ms` | Median decision runtime across all recorded decisions |
| `p95_decision_ms` | 95th percentile of decision runtime |
| `p99_decision_ms` | 99th percentile of decision runtime |
| `invalid` | Matches whose `status` is `INVALID` |
| `timeouts` | Matches whose `status` is `TIMEOUT` |

Notes:

- `aggregate()` uses all recorded matches as the denominator for `win_rate`.
- `errors` includes any non-`OK` status, including `INVALID` and `TIMEOUT`.
- Percentiles use linear interpolation over sorted samples.

### `RunReport`

| Field | Meaning |
|---|---|
| `config_name` | Batch configuration label |
| `agent_mode` | Agent mode passed to the runner |
| `matches` | Ordered list of `MatchRecord` objects |
| `started_at` | Batch start timestamp in Unix seconds |
| `finished_at` | Batch end timestamp in Unix seconds |
| `total_matches` | Convenience property equal to `len(matches)` |

### `MatchRecord`

| Field | Meaning |
|---|---|
| `match_id` | Stable match identifier derived from seed and side |
| `seed` | SDK seed used for the match |
| `agent_side` | Side controlled by the candidate agent |
| `status` | Final `ExecutionStatus` for the SDK run |
| `result` | Candidate result from the controlled side, or `None` when unavailable |
| `duration_ms` | Whole-match runtime in milliseconds |
| `decision_count` | Number of recorded decisions |
| `decisions` | Ordered list of `DecisionRecord` objects |
| `turns` | Number of environment steps when available |
| `final_statuses` | Final status string of each SDK player |
| `agent_mode` | Agent mode used for this match |
| `opponent` | Opponent label configured for the batch |
| `sdk_version` | Installed `kaggle-environments` version, or `unknown` |
| `deck_sha256` | SHA-256 of the active deck file, or `unknown` |
| `started_at` | Match start timestamp in Unix seconds |
| `finished_at` | Match end timestamp in Unix seconds |
| `termination_reason` | Runner termination classification |
| `error_category` | Runner error category string |
| `error_message` | Runner error message, if any |

### `DecisionRecord`

| Field | Meaning |
|---|---|
| `decision_index` | Zero-based order of the policy call within the match |
| `turn` | Visible turn number when available |
| `context` | SDK selection context string |
| `select_type` | SDK selection type string |
| `options` | Raw legal option payloads provided by the SDK |
| `option_count` | Count of available options |
| `min_count` | Minimum number of indices required |
| `max_count` | Maximum number of indices allowed |
| `selected_indices` | Indices returned by the agent |
| `legal` | Whether the returned indices passed legal-selection validation |
| `duration_ms` | Policy latency in milliseconds |
| `overage_balance_ms` | Remaining budget after the call |
| `score` | Top ranked score when the policy exposes one |
| `reasons` | Explanation strings for the top ranked selection |
| `search` | Optional search payload when a policy populates it |
| `error_category` | Selection error category string |
| `error_message` | Selection error message, if any |
| `state_before` | JSON-safe snapshot of visible state before the decision |
| `state_after` | Optional post-decision state snapshot |
| `action_sequence` | Optional sequence of executed SDK actions |
| `teacher_decision` | Optional teacher indices for supervised traces |
| `ranked` | Serialized ranking list from the policy |
| `features` | Serialized feature vectors from the policy |
| `fallback_used` | Whether the policy fell back to a deterministic baseline |
| `model_backend` | Model backend label, if any |
| `model_version` | Model version label, if any |

### `GameplayMetrics`

| Field | Meaning |
|---|---|
| `matches` | Number of matches in the batch |
| `operational_failures` | Matches whose `status` was not `OK` |
| `wins` | Matches with result `win` |
| `main_decisions` | Decisions with `select_type` equal to `"0"` or `"MAIN"` |
| `productive_main_actions` | Main decisions whose selected option types include a productive action |
| `attacks` | Total selected `ATTACK` options across main decisions |
| `matches_with_attack` | Matches that contained at least one selected `ATTACK` option |
| `end_turns` | Main decisions that selected `END` |
| `action_counts` | Histogram of selected visible action types |

Derived properties:

- `end_turn_rate = end_turns / main_decisions`
- `attack_match_rate = matches_with_attack / matches`

`GameplayMetrics.from_report()` only inspects visible main-turn decisions and
only counts option types present in `select.option`.

## Output Formats

### JSON

`serialize_report()` produces the canonical machine-readable report structure.
`write_json()` writes it atomically with sorted keys and a trailing newline.

Stable top-level keys:

- `config`
- `agent_mode`
- `total_matches`
- `started_at`
- `finished_at`
- `matches`
- `metrics`

Rounding rules:

- `win_rate` and the `wilson_ci` bounds are rounded to 4 decimal places.
- duration metrics are rounded to 2 decimal places.
- list and dataclass fields are preserved recursively through JSON-safe
  conversion.

### Markdown

`write_markdown()` emits a human-readable summary of the same JSON payload.
It does not recompute metrics. The document highlights:

- agent mode and total matches;
- W/D/L counts and win rate;
- Wilson 95% interval;
- errors;
- duration percentiles for match and decision latency.

Percentages are rendered with fixed formatting for readability, not for
recomputation.

### HTML

`scripts/generate_investigation_report.py` generates a standalone HTML report
from replay JSON files. It is an investigation artifact, not an evaluation
gate.

The report:

- filters out replay files that do not contain the expected `visualize`
  structure;
- ignores episodes that do not mention the requested owner name;
- derives a deck label from the opening visualization;
- aggregates attack usage, damage dealt and taken, evolution turns, first vs
  second player performance, and matchup summaries;
- writes a single self-contained HTML file.

## Calculation Notes

- Wilson confidence intervals use `z = 1.96` for a 95% interval.
- Percentiles are computed on sorted samples with linear interpolation.
- `GameplayMetrics.assert_minimum_gameplay()` fails when the agent produces no
  productive main actions, no attacks, too many `END` selections, or any
  operational failures.
- The replay investigation report groups matchups by the derived opponent
  archetype and only treats groups with at least five samples as reliable when
  highlighting best and worst matchups.

## Canonical References

- `src/eval/runner.py`
- `src/eval/metrics.py`
- `src/eval/reporting.py`
- `src/eval/gameplay.py`
- `scripts/gameplay_smoke.py`
- `scripts/generate_investigation_report.py`
