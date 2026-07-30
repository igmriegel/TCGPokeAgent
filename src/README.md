# Implementation layout

Active namespaces:

- `core/`: `Selection`, factual state, belief, parser, and interfaces.
- `agents/`: fallback, heuristic, short search, and wrapper.
- `eval/`: runner, validation, metrics, comparison, and reporting.
- `experiments/`: specs, execution, grids, and registry.
- `logs/`: raw traces.
- `reports/`: computed summaries.
- `data/`: derived datasets; official raw data lives in `data/raw/`.
- `artifacts/`: models and frozen packages.

The current implementation and its consumers are mapped in
[`docs/CODEBASE_MAP.md`](../docs/CODEBASE_MAP.md). Contracts define intended
behavior; the map distinguishes active, manual, and deferred code.
