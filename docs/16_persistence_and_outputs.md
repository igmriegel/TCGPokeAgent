# Persistence and outputs

## Run layout

```text
runs/<experiment_id>/<run_id>/
  manifest.json
  matches.jsonl
  decisions.jsonl
  metrics.json
  metrics.csv
  summary.md
  replays/
  errors/
```

`runs/` is generated output, outside the submission package.

## Contracts

- `manifest.json`: resolved input, versions, hashes, seeds and matrix.
- `matches.jsonl`: one `MatchRecord` per line.
- `decisions.jsonl`: one `DecisionRecord` per line.
- `metrics.json`: full values for machines.
- `metrics.csv`: flattened table for analysis.
- `summary.md`: interpretation and decision, without recomputing metrics.
- `replays/`: sufficient payload for replay/audit.
- `errors/`: stack trace and sanitized context.

## Immutability

Files from a completed run are not overwritten. A fix creates a new `run_id` and references the previous one. A promoted artifact receives a SHA-256 and a copy of the manifest.

## Retention

- raw logs: keep for candidates and failures; exploratory runs may follow documented policy;
- reports: keep all;
- derived datasets: version schema, sources and transformation;
- models/packages: keep promoted versions and previous reference.

## Privacy and security

Do not persist Kaggle token, secret variables or credential paths. Catalog samples remove personal identifiers; official card data does not contain expected personal data, but still goes through column inspection.

## Atomicity

Write temporary outputs and rename only after validation. Manifest starts as `RUNNING`; completion changes to `COMPLETED` after all required files exist.
