# Catálogo de métricas

## Resultado

Para cada matchup e agregado:

- `wins`, `draws`, `losses`;
- `win_rate`, `draw_rate`, `loss_rate`;
- intervalo de Wilson de 95% para `win_rate`;
- partidas como jogador 0 e jogador 1;
- turnos por partida e motivo de término.

O denominador de `win_rate` inclui todas as partidas válidas; empates não são removidos. Falhas operacionais são reportadas separadamente e impedem promoção.

## Operação

- duração de decisão p50, p95 e máxima;
- duração de partida p50, p95 e máxima;
- contagens `INVALID`, `ERROR` e `TIMEOUT`;
- memória/tamanho do pacote no gate final.

## Busca

- decisões elegíveis;
- decisões realmente pesquisadas;
- `search_coverage = pesquisadas / elegíveis`;
- falhas por `belief_inconsistent`, `api_error`, `budget_exhausted` e `unexpected`;
- duração p50/p95/máxima;
- alteração da escolha top-1;
- delta pareado de vitória contra heurística pura.

## Estabilidade

- taxa por lado, seed e matchup;
- diferença jogador 0 versus jogador 1;
- dispersão entre lotes;
- pior matchup do pool congelado.

## Gate

O relatório é inválido se omitir denominadores, lados, versão do deck, SDK, seeds ou falhas. Média de duração não substitui p95 e máximo.
