# Configurations

The YAML files are executable profiles loaded by `ConfigLoader`. Top-level
fields map to `Config`; additional mappings such as `search`, `evaluation`,
`weights`, and `feature_flags` are preserved in `Config.extra`. Includes use a
deep merge.

Contract, precedence, and validation: [`docs/22_config_spec.md`](../docs/22_config_spec.md).
