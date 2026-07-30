# Execution profiles

The current YAML files are executable under the flat schema documented in
[`22_config_spec.md`](22_config_spec.md).

## Profiles

| Profile | Games | Search | Trace | Usage |
|---:|---|---|---|
| `eval_small` | 10 seeds | disabled | full runner records | quick iteration only |
| `full` | >= 200 | per candidate | full | experimental decision |
| `heuristic` | defined by eval | no | configurable | stable baseline |
| `search` | defined by eval | yes, 100 ms | search metrics | ablation |
| `submission` | isolated smoke | per freeze | minimal | final package |

## Search budget

- `max_decision_ms: 100`;
- `disable_below_overage_s: 30`;
- `top_k: 3`;
- `max_depth: 4`;
- `manual_coin: false`.

These values are MVP invariants. Changes require an experiment and a new version.

## Precedence

Included YAML is deep-merged with the including file. Current run scripts may
override `config.agent` in memory. The manifest stores the resolved
configuration, but it does not yet record field-level origin.

## Seeds

`run_experiment` defaults to `range(config.runs)` unless explicit seeds are
passed. A promotion run must freeze and record its actual seed list; the YAML
files do not currently contain versioned seed lists.
