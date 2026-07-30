# Configuration contract

## Executable schema

```yaml
project: Pokemon_TCG_engine_Kaggle
sdk_version: "1.32.2"
seed: 42
agent: heuristic
runs: 200
search:
  enabled: false
  top_k: 3
  max_depth: 4
  max_decision_ms: 100
  disable_below_overage_s: 30
evaluation:
  seeds: []
  opponents: [random, first, heuristic, self]
  both_sides: true
weights: {}
feature_flags: {}
```

`project`, `sdk_version`, `seed`, `agent`, and `runs` are typed `Config`
fields. Other mappings are preserved under `Config.extra`; `evaluation` and
`search` have convenience properties.

## Current validation

- YAML must resolve to a mapping;
- `search` and `evaluation` must be mappings when present;
- `both_sides != true`: error at gates;
- `manual_coin != false`: forbidden in competitive runtime;
- numeric/string conversion failures: error.

Unknown extra fields are currently accepted. Match-count minimums, fixed seed
lists, opponent coverage, hashes, and search invariants are release gates, not
fully enforced by `ConfigLoader`.

## Layers

1. included YAML;
2. including YAML;
3. explicit in-memory overrides made by an entry point.

Merge of mappings is deep; lists are fully replaced. The current shell entry
points load one profile at a time, so composing agent and evaluation profiles
requires an explicit include or code-level override.

## Current profiles

- `agent_baseline.yaml`: deterministic fallback policy.
- `agent_heuristic.yaml`: active weights and feature flags.
- `agent_hybrid.yaml`: search wrapper with search explicitly disabled.
- `eval_small.yaml`: 10 seeds for quick iteration, not a promotion gate.
- `eval_full.yaml`: at least 200.
