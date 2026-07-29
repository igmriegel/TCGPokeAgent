# Experiment contracts

## `ExperimentSpec`

An experiment is fully described before running:

```yaml
experiment_id: EXP-YYYYMMDD-NNN
hypothesis: falsifiable text
candidate: immutable version
baseline: immutable version
deck_version: immutable version
sdk_version: "1.32.2"
matchups: []
seeds: []
games: 200
metrics: []
acceptance: explicit expression
```

The file contains no game logic. The effective configuration results from the layers documented in [`22_config_spec.md`](22_config_spec.md) and is saved in its entirety in the manifest.

## `ExperimentRun`

States: `PLANNED`, `RUNNING`, `COMPLETED`, `FAILED`, `REJECTED`. A run creates its own directory and never overwrites another.

Required outputs:

- `manifest.json`;
- `matches.jsonl`;
- `decisions.jsonl`;
- `metrics.json` and `metrics.csv`;
- `summary.md`;
- references to replays and errors;
- final decision and link to `strategy_notes.md`.

## Sweeps

A grid expands combinations in deterministic order, assigns a `run_id` per combination, and applies the same set of seeds. Subsequent selection on the same evaluation set is declared; the chosen candidate passes through a separate holdout.

## Promotion and rollback

`promote` updates the stable reference only after all gates. The previous reference and its artifacts remain available. Configurations without a report, partial runs, and comparisons with different seeds cannot promote.

## Remote Kaggle score lifecycle

The public score returned immediately after a simulation submission is an
initial value, not an evaluated result. In this competition that value is
normally `600.0` and changes as Kaggle gameplay runs are completed.

The harness records remote fields separately:

- `initial_public_score`: the value first exposed after submission;
- `evaluated_public_score`: the latest score after gameplay runs;
- `score_observed_at`: the UTC timestamp of each observation;
- `evaluation_status`: `PENDING`, `UPDATING`, or `STABLE`.

No score delta, promotion decision, engine-versus-deck conclusion, or
leaderboard claim may use the initial score. A comparison remains pending
until a later observation demonstrates that remote evaluation has progressed
and the result is explicitly frozen as evidence.
