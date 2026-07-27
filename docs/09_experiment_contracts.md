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
