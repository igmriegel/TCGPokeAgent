# Operational scripts

The implemented scripts cover preflight, smoke/full evaluation, agent
comparison, gameplay checks, local replay generation, data download, package
construction, grouped ranker training, documentation drift, and guarded Kaggle
submission.

Canonical command inventory:
[`docs/23_scripts_spec.md`](../docs/23_scripts_spec.md).

## End-to-end simulation submission

Run every local gate, build and validate `submissions/submission.tar.gz`, then answer the
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
`pokemon-tcg-ai-battle`. OAuth credentials created by the current CLI are
stored in `~/.kaggle/credentials.json`. See
[`docs/36_kaggle_submission_debug.md`](../docs/36_kaggle_submission_debug.md)
for authentication diagnostics and the stdout-debug experiment.
Successful uploads create a credential-free receipt under
`reports/submissions/`.

For the dedicated Honchkrow/Porygon package, select its builder explicitly so
the submission flow does not replace it with the standard package:

```bash
scripts/submit_simulation.sh \
  --package-kind honchkrow_porygon \
  --archive submissions/honchkrow_porygon_submission.tar.gz \
  --skip-smoke --yes
```

Run the dedicated CABT smoke before this command. The OAuth credential remains
outside the repository and is never printed, stored, or included in an
archive/report.

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

## Local replay inspection

Use the replay inspector when you need a readable step-by-step trace instead
of ad-hoc `jq` filters:

```bash
PYTHONPATH=. .venv/bin/python scripts/inspect_replay.py \
  replays/remote/55392121/episode-91484013-replay.json \
  --turn 11 --player-index 0 \
  --card-id 1216 --card-id 1257 --card-id 15
```

The helper prints each matching frame with:

- the stable replay coordinates (`step`, `entry`, `turn`, `player`);
- the recorded `action`;
- the legal `options` with any resolved hand card or attack ID;
- the visible `logs`, including drawn or played cards.

Use `--format json` when you want machine-readable output for a follow-up
filter or a note in a report.

## Download Kaggle replays

Download replay files from all completed Kaggle submissions:

```bash
scripts/download_all_replays.sh
```

This downloads replays to `replays/remote/{submission_id}/` and copies them to
`data/raw/kaggle/kaggle_gameplay_runs/`. It also creates/updates
`data/raw/kaggle/episode_to_submission.json` mapping episodes to submissions.

## Generate investigation report

Generate the HTML investigation report from downloaded replays:

```bash
scripts/generate_investigation_report.sh
```

This reads replays from `data/raw/kaggle/kaggle_gameplay_runs/`, analyzes
them using the CG SDK for card metadata, and generates
The legacy aggregate output `perf_reports/INVESTIGATION_REPORT_ABOMASNOW.html`
is disabled. Use a submission-specific output path or `--deck-filter` for an
active report.

The report includes:
- Executive summary (W/L, win rate, avg turns)
- Submission history comparison
- First vs second player analysis
- Attack usage and damage distribution
- Matchup analysis with threat bars (52+ archetypes)
- Worst and best matchups with confidence labels
