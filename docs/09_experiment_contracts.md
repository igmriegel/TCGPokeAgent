# Contratos de experimento

## `ExperimentSpec`

Um experimento é totalmente descrito antes de rodar:

```yaml
experiment_id: EXP-YYYYMMDD-NNN
hypothesis: texto falsificável
candidate: versão imutável
baseline: versão imutável
deck_version: versão imutável
sdk_version: "1.14.10"
matchups: []
seeds: []
games: 200
metrics: []
acceptance: expressão explícita
```

O arquivo não contém lógica de jogo. A configuração efetiva resulta das camadas documentadas em [`22_config_spec.md`](22_config_spec.md) e é salva integralmente no manifesto.

## `ExperimentRun`

Estados: `PLANNED`, `RUNNING`, `COMPLETED`, `FAILED`, `REJECTED`. Um run cria diretório próprio e nunca sobrescreve outro.

Saídas obrigatórias:

- `manifest.json`;
- `matches.jsonl`;
- `decisions.jsonl`;
- `metrics.json` e `metrics.csv`;
- `summary.md`;
- referências aos replays e erros;
- decisão final e vínculo com `strategy_notes.md`.

## Sweeps

Um grid expande combinações em ordem determinística, atribui um `run_id` por combinação e aplica o mesmo conjunto de seeds. Seleção posterior no mesmo conjunto de avaliação é declarada; o candidato escolhido passa por um holdout separado.

## Promoção e rollback

`promote` atualiza a referência estável somente após todos os gates. A referência anterior e seus artefatos permanecem disponíveis. Configurações sem relatório, runs parciais e comparações com seeds diferentes não podem promover.
