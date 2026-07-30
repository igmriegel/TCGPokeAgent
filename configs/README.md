# Configurations

The YAML files are executable profiles loaded by `ConfigLoader`. Top-level
fields map to `Config`; additional mappings such as `search`, `evaluation`,
`weights`, and `feature_flags` are preserved in `Config.extra`. Includes use a
deep merge.

`agent_xgboost_ranker.yaml` and `agent_lightgbm_ranker.yaml` inherit the
heuristic fallback settings and select a backend-exclusive model directory.
They do not imply that either learned candidate is promoted.

Contract, precedence, and validation: [`docs/22_config_spec.md`](../docs/22_config_spec.md).
