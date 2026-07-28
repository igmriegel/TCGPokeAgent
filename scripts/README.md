# Operational scripts

Implement thin wrappers for preflight, smoke/full, comparison, freeze, package, isolated validation, Strategy, and Kaggle inventory.

Commands and exit codes: [`docs/23_scripts_spec.md`](../docs/23_scripts_spec.md).
## Local replay visualization

Generate a replay with the `cg.game` API bundled by the pinned
`kaggle-environments` package:

```bash
PYTHONPATH=. .venv/bin/python scripts/run_replay.py \
  --agent-one heuristic --agent-two random --matches 1
```

The JSON is written under `replays/YYYYMMDD/`. Open `visualizer.html`, select
the JSON file, and allow the page to submit it to the competition visualizer.
The visualizer is an external service; do not upload private observations or
credentials.
