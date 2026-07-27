# Contratos de avaliação

## Runner

O runner recebe versões imutáveis de dois agentes, decks, seed e perfil. Ele executa o SDK sem conhecer scoring, registra cada chamada e devolve um `MatchRecord`.

Campos mínimos de `MatchRecord`:

- `run_id`, `match_id`, seed e lado;
- versões de agente, deck e SDK;
- início, fim e duração;
- resultado, motivo e turnos;
- status final de ambos os agentes;
- lista de `DecisionRecord`;
- caminhos de replay e erro.

`DecisionRecord` registra turno, contexto, cardinalidade, índices escolhidos, scores/razões, duração, saldo de overage e dados de busca.

## Matriz do gate

O candidato roda como jogador 0 e 1 contra:

- agente SDK `random`;
- agente SDK `first`;
- heurística sem busca;
- a si próprio.

Smoke soma 20 partidas; full soma pelo menos 200. A distribuição exata por matchup/lado aparece no manifesto antes da execução.

## Validação

Antes de contabilizar uma decisão:

- saída é `list[int]`;
- cardinalidade respeita `SelectData`;
- índices pertencem à lista de opções;
- restrições agregadas foram atendidas;
- duração e saldo de overage foram registrados.

Qualquer `INVALID`, `ERROR` ou `TIMEOUT` reprova o candidato, mesmo que a taxa de vitória seja alta.

## Estatística

Calcular métricas conforme [`03_metrics.md`](03_metrics.md). Wilson usa 95%, com número de vitórias como sucessos e total de partidas válidas como `n`. Comparações pareadas mantêm resultados por seed e lado, não apenas agregados.

## Gate da busca

Compare a mesma heurística com busca desligada e ligada:

- mesma matriz, decks e seeds;
- `win_rate_search >= win_rate_heuristic`;
- zero falhas operacionais;
- busca máxima até 100 ms;
- relatório de cobertura e cada fallback.

Se a diferença estiver dentro do ruído, a versão sem busca permanece estável por ser mais barata.
