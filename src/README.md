# Implementation layout

Reserved namespaces, in MVP vertical order:

- `core/`: `Selection`, factual state, belief, parser, and interfaces.
- `agents/`: fallback, heuristic, short search, and wrapper.
- `eval/`: runner, validation, metrics, comparison, and reporting.
- `experiments/`: specs, execution, grids, and registry.
- `logs/`: raw traces.
- `reports/`: computed summaries.
- `data/`: derived datasets; official raw data lives in `data/raw/`.
- `artifacts/`: models and frozen packages.

Current modules are placeholders. Implement per [`docs/11_implementation_order.md`](../docs/11_implementation_order.md), without treating existing code as contract.
