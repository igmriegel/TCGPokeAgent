# Configuration contract

## Canonical schema

```yaml
project:
  name: pokemon_tcg_engine_kaggle
  sdk_version: "1.32.2"
  seed: 0
agent:
  kind: heuristic
  version: dev
  deck: deck.csv
  fallback: deterministic
heuristic:
  weights: {}
  rules: {}
search:
  enabled: false
  top_k: 3
  max_depth: 4
  max_decision_ms: 100
  disable_below_overage_s: 30
  manual_coin: false
  opponent_deck_version: null
evaluation:
  profile: smoke
  games: 20
  seeds: []
  opponents: [random, first, heuristic, self]
  both_sides: true
outputs:
  root: runs
  decisions: true
  replays: true
```

## Validation

- unknown fields: error;
- missing required field: error;
- `games < 20` in smoke or `< 200` in full: error;
- `both_sides != true`: error at gates;
- search with limits different from MVP: requires `experiment_id`;
- `manual_coin != false`: forbidden in competitive runtime;
- deck/opponent without version/hash at freeze: error.

## Layers

1. `default.yaml`;
2. agent profile;
3. evaluation profile;
4. CLI overrides.

Merge of mappings is deep; lists are fully replaced. No value comes from hidden global state. The manifest records resolved configuration and list of overrides.

## Migration of current files

- `agent_baseline.yaml`: conceptually rename to fallback/first only in implementation.
- `agent_heuristic.yaml`: M1 weights and flags.
- `agent_hybrid.yaml`: reserve for M2+ models; short search does not make the agent "hybrid".
- `eval_small.yaml`: exactly 20 matches.
- `eval_full.yaml`: at least 200.

The existing YAML files remain unchanged in this documentation revision and should not be treated as executable until they pass the schema.
