# Operational scripts

The implemented scripts cover preflight, smoke/full evaluation, agent
comparison, gameplay checks, local replay generation, data download, package
construction, documentation drift, and guarded Kaggle submission.

Canonical command inventory:
[`docs/23_scripts_spec.md`](../docs/23_scripts_spec.md).

## End-to-end simulation submission

Run every local gate, build and validate `submission.tar.gz`, then answer the
interactive confirmation prompt:

```bash
scripts/submit_simulation.sh
```

Nothing is uploaded unless the prompt receives `y` or `yes`. To exercise the
complete local pipeline without an upload:

```bash
scripts/submit_simulation.sh --dry-run
```

The flow requires an authenticated Kaggle CLI and submits to
`pokemon-tcg-ai-battle`. Successful uploads create a credential-free receipt
under `reports/submissions/`.

## Gameplay smoke

Run a balanced matrix and reject an agent that completes games without
observable gameplay:

```bash
PYTHONPATH=. .venv/bin/python scripts/gameplay_smoke.py \
  --matches 10 --agent-mode heuristic --opponent random
```

The summary reports productive main actions, attacks, matches with attacks,
end-turn rate, wins, and operational failures. The high-level behavior is
defined in [`docs/27_gameplay_rules.md`](../docs/27_gameplay_rules.md).

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
