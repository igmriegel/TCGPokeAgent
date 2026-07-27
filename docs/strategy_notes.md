# Registro de evidências Strategy

Este arquivo é append-only para decisões aceitas. Rascunhos podem ser editados; registros com `status: accepted` só recebem correções explícitas.

## Estados

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
sdk_version: "1.14.10"
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

## Registro inicial

```yaml
experiment_id: DOC-20260727-001
status: accepted
hypothesis: "Contratos alinhados à API oficial reduzem decisões arquiteturais pendentes."
agent_version: null
baseline_version: null
deck_version: null
sdk_version: "1.14.10"
finished_at: "2026-07-27"
decision: "Adotar Selection list[int], GameState factual e BeliefState separado."
limitations:
  - "Nenhuma política foi implementada ou avaliada nesta revisão."
evidence:
  manifest: "docs/20_master_index.md"
  report: "docs/07_core_contracts.md"
  traces: []
writeup_claim: null
```
