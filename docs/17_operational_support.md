# Daily operation

## Cycle

1. `preflight`: versions, deck, data and imports.
2. `smoke`: 20 matches on both sides.
3. `full`: at least 200 matches.
4. `compare`: candidate versus reference/ablation.
5. `freeze`: code, deck, configuration and hashes.
6. `package`: `.tar.gz`.
7. `validate-package`: extraction and isolated smoke.
8. `strategy-export`: evidence block.

Target commands are in [`23_scripts_spec.md`](23_scripts_spec.md).

## Runtime profiles

- `heuristic-only`: stable path and fallback for every version.
- `search-enabled`: same heuristic with search subject to gates.
- `trace`: detailed logging, local only.
- `submission`: limited logging, relative paths and packaged dependencies.

## Diagnostics

Inspection order:

1. environment status and error;
2. original observation/select;
3. generated valid selections;
4. choice/fallback and reasons;
5. duration and overage;
6. belief and Search API cycle;
7. version/hash of all components.

## Incidents

- one `INVALID`, `ERROR` or `TIMEOUT`: block promotion;
- search failure: keep match via heuristic and open issue;
- unknown schema: legal fallback, save sanitized fixture and add test;
- SDK regression: freeze 1.14.10 and open compatibility experiment;
- package fails in isolation: do not submit, even if local code passes.
