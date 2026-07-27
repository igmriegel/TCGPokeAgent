# Perfis de execução

Os YAML atuais são placeholders e não são alterados nesta revisão. A implementação deve migrá-los ao schema canônico de [`22_config_spec.md`](22_config_spec.md).

## Perfis

| Perfil | Jogos | Busca | Trace | Uso |
|---|---:|---|---|---|
| `smoke` | 20 | conforme candidato | reduzido | integração e falha rápida |
| `full` | >= 200 | conforme candidato | completo | decisão experimental |
| `heuristic` | definido pelo eval | não | configurável | baseline estável |
| `search` | definido pelo eval | sim, 100 ms | métricas de busca | ablação |
| `submission` | smoke isolado | conforme freeze | mínimo | pacote final |

## Orçamento da busca

- `max_decision_ms: 100`;
- `disable_below_overage_s: 30`;
- `top_k: 3`;
- `max_depth: 4`;
- `manual_coin: false`.

Esses valores são invariantes do MVP. Alteração exige experimento e nova versão.

## Precedência

`default` < perfil de agente < perfil de avaliação < override CLI. O manifesto armazena valor final e origem de cada override.

## Seeds

Perfis não usam seed implícita. Smoke e full carregam listas fixas versionadas; trocá-las cria nova revisão do protocolo.
