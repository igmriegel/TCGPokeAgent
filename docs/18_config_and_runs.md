# Execution profiles

The current YAML files are placeholders and are not changed in this revision. The implementation must migrate them to the canonical schema of [`22_config_spec.md`](22_config_spec.md).

## Profiles

| Profile | Games | Search | Trace | Usage |
|---:|---|---|---|
| `smoke` | 20 | per candidate | reduced | integration and fast failure |
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

`default` < agent profile < evaluation profile < CLI override. The manifest stores the final value and origin of each override.

## Seeds

Profiles do not use implicit seeds. Smoke and full load fixed versioned lists; changing them creates a new protocol revision.
