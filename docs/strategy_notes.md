# Strategy evidence log

This file is append-only for accepted decisions. Drafts may be edited; records with `status: accepted` only receive explicit corrections.

## States

`planned` → `running` → `accepted` | `rejected` | `inconclusive`

## Template

```yaml
experiment_id: EXP-YYYYMMDD-NNN
status: planned
hypothesis: "Alteração X melhora a métrica Y no matchup Z."
agent_version: null
baseline_version: null
deck_version: null
deck_sha256: null
model_sha256: null
sdk_version: "1.32.2"
config:
  files: []
  overrides: {}
seeds: []
games_planned: 0
matchups: []
started_at: null
finished_at: null
results:
  wins: null
  draws: null
  losses: null
  wilson_95: null
  decision_ms_p50: null
  decision_ms_p95: null
  decision_ms_max: null
  invalid: null
  error: null
  timeout: null
ablation: null
decision: null
limitations: []
evidence:
  manifest: null
  report: null
  traces: []
writeup_claim: null
```

## Initial record

```yaml
experiment_id: DOC-20260727-001
status: accepted
hypothesis: "Contracts aligned with the official API reduce pending architectural decisions."
agent_version: null
baseline_version: null
deck_version: null
sdk_version: "1.32.2"
finished_at: "2026-07-27"
decision: "Adopt Selection list[int], factual GameState and separate BeliefState."
limitations:
  - "No policy was implemented or evaluated in this revision."
evidence:
  manifest: "docs/20_master_index.md"
  report: "docs/07_core_contracts.md"
  traces: []
writeup_claim: null
```

## Evaluation record

```yaml
experiment_id: EXP-20260729-001
status: accepted
hypothesis: "The implemented heuristic policy can complete the full SDK gate without operational failures."
agent_version: dev
baseline_version: null
deck_version: frozen-local
deck_sha256: 1156379af39e71bc83eecb50d1e04c5cc480501d293621fcc89c2d355d99be78
sdk_version: "1.32.2"
config:
  files: [configs/eval_full.yaml, configs/agent_heuristic.yaml]
  overrides: {}
seeds: "42..241"
games_planned: 400
matchups: [random]
started_at: "2026-07-29"
finished_at: "2026-07-29"
results:
  wins: 239
  draws: 0
  losses: 161
  wilson_95: [0.5487, 0.6444]
  decision_ms_p50: null
  decision_ms_p95: null
  decision_ms_max: 0.0
  invalid: 0
  error: 0
  timeout: 0
ablation: null
decision: "Accept heuristic operational gate; do not claim search promotion."
limitations:
  - "Full run currently uses the random opponent; the four-opponent matrix is pending."
  - "Search is disabled until the documented native lifecycle is integrated through a verified Python adapter."
evidence:
  manifest: "reports/runs/full_heuristic_final/27d3df870485/manifest.json"
  report: "reports/runs/full_heuristic_final/27d3df870485/report.json"
  traces: []
writeup_claim: "The heuristic completed 400 player-side matches with zero operational failures; recorded match-duration p50/p95 were 270.75/1033.70 ms."
```

## Release decision

The current release is heuristic-only. Search is disabled explicitly because
the documented native lifecycle is not yet integrated through a verified
Python adapter. The release archive, manifest, and isolated validation are
recorded in `reports/release_heuristic_manifest.json`.
