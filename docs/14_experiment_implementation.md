# Experiment implementation

## Path of a run

1. Load defaults, agent profile, and evaluation profile.
2. Apply explicit overrides.
3. Resolve and validate the `ExperimentSpec`.
4. Persist `manifest.json` before the first match.
5. Execute the planned matrix.
6. Calculate metrics and comparison.
7. Evaluate the acceptance expression.
8. Persist decision and block for `strategy_notes.md`.

## Identity

`experiment_id` identifies the hypothesis; `run_id` identifies an execution. Repetition uses a new `run_id`, same `experiment_id`, and references the previous run. Names do not depend only on timestamp.

## Versions

The manifest records:

- commit or source marker;
- deck hash;
- effective configuration hash;
- SDK and Python versions;
- model hash;
- feature schema;
- seeds and opponent pool.

`null` is allowed only for a nonexistent component, never for an unmeasured component.

## Ablation

Each heuristic rule has a flag. An ablation changes one family at a time and keeps the rest frozen. For models, compare: heuristic, model without feature group, full model, and, when applicable, search on/off.

## Temporal holdout

Traces are partitioned by date/generation order. The grid uses training/validation; a single final evaluation on holdout chooses promotion. Regenerating the holdout requires a new dataset version.

## Registry

The registry is append-only and points to artifacts, does not duplicate metrics. Incomplete runs remain as `FAILED` with error; they are not deleted nor counted as valid games.

## Tests

- same spec expands the same matrix;
- override appears in the manifest;
- grids do not collide;
- comparison rejects incompatible decks/seeds;
- gate decision is reproducible from reports;
- Strategy entry contains existing paths.
