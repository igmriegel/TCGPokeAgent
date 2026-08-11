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

## Canonical replay and log layout

Kaggle evidence and locally generated visualizer replays are stored only under
`data/`, as defined in the harness contract:

```text
data/raw/kaggle/replays/remote/<submission_id>/
data/raw/kaggle/replays/owner_feedback/<capture_id>/
data/raw/kaggle/decision_logs/<submission_id>/{raw,decoded,annotated}/
data/derived/local_replays/<date>/
```

Do not create `logs/` or `replays/` at the repository root. Flat replay caches
are redundant and must not be recreated.

## Kaggle decision-ledger contract

Every official Honchkrow/Porygon package writes one complete public decision
ledger for every non-initial decision to stderr. Stdout remains exclusively for
the simulator action. The Kaggle environment captures both streams separately,
with a 10,000-character default limit per decision.

The `audit_decision_ledger` event contains every candidate, filter stage, ranked
selection, feature vector, selected indices, `DecisionTrace`, `turn_ledger`, and
`match_ledger`. Field names use stable aliases from
`src/artifacts/decision_ledger_dictionary.json`; the payload is zlib-compressed,
base64-encoded, and protected by a SHA-256 of the uncompressed compact record.
The dictionary is bundled at that same path inside the submission archive. Its
`field_descriptions`, `turn_ledger_fields`, and `match_ledger_fields` sections
are the authoritative explanation for every decoded field. The decoder expands
aliases before writing JSONL:

```bash
uv run --frozen python scripts/decode_kaggle_decision_ledger.py REPLAY_OR_LOG \
  --output decisions.jsonl
```

If a complete compressed record cannot fit in 9,000 characters, an explicit
`audit_decision_ledger_failed` event is emitted. A truncated or failed event is
not valid evidence of a complete decision audit.

## Contracts

- `manifest.json`: resolved input, versions, hashes, seeds and matrix.
- `matches.jsonl`: one `MatchRecord` per line.
- `decisions.jsonl`: one `DecisionRecord` per line.
- `metrics.json`: full values for machines, serialized from the canonical
  evaluation metrics contract.
- `metrics.csv`: flattened table for analysis.
- `summary.md`: interpretation and decision, without recomputing metrics.
- `replays/`: sufficient payload for replay/audit.
- `errors/`: stack trace and sanitized context.

The metric fields and rounding rules are defined in
[`03_metrics.md`](03_metrics.md). Reporting must not invent additional summary
keys outside that contract.

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
