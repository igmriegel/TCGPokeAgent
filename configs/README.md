# Configurations

The YAML files are executable profiles loaded by `ConfigLoader`. Top-level
fields map to `Config`; additional mappings such as `search`, `evaluation`,
`weights`, and `feature_flags` are preserved in `Config.extra`. Includes use a
deep merge.

`agent_xgboost_ranker.yaml` and `agent_lightgbm_ranker.yaml` inherit the
heuristic fallback settings and select a backend-exclusive model directory.
They do not imply that either learned candidate is promoted.

`agent_hdi_v1.yaml` selects the independent deterministic HDI experiment. It
uses ordinal rules and the packaged declarative deck profile; it does not
replace or modify the heuristic release mode.

Contract, precedence, and validation: [`docs/22_config_spec.md`](../docs/22_config_spec.md).
