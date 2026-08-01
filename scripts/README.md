# Operational scripts

The implemented scripts cover preflight, smoke/full evaluation, agent
comparison, gameplay checks, local replay generation, data download, package
construction, grouped ranker training, documentation drift, and guarded Kaggle
submission.

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

## Download Kaggle replays

Download replay files from all completed Kaggle submissions:

```bash
uv run --frozen python -m scripts.download_all_replays
```

This downloads replays to `replays/remote/{submission_id}/` and copies them to
`data/raw/kaggle/kaggle_gameplay_runs/`. It also creates/updates
`data/raw/kaggle/episode_to_submission.json` mapping episodes to submissions.

## Generate investigation report

Generate the HTML investigation report from downloaded replays:

```bash
uv run --frozen python -m scripts.generate_investigation_report
```

This reads replays from `data/raw/kaggle/kaggle_gameplay_runs/`, analyzes
them using the CG SDK for card metadata, and generates
`perf_reports/INVESTIGATION_REPORT_ABOMASNOW.html`.

The report includes:
- Executive summary (W/L, win rate, avg turns)
- Submission history comparison
- First vs second player analysis
- Attack usage and damage distribution
- Matchup analysis with threat bars (52+ archetypes)
- Worst and best matchups with confidence labels
