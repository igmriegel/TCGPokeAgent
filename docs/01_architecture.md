# Arquitetura vertical

## Fluxo de decisão

`main.py` recebe a observação. Se `select is None`, devolve o deck. Caso contrário:

1. `ObservationParser` preserva a entrada bruta e cria `GameState` factual.
2. `CandidateBuilder` transforma cada `Option` em candidato sem mudar seu índice.
3. `SelectionGenerator` produz combinações válidas segundo cardinalidade, energia e dano.
4. `HeuristicScorer` ordena as combinações.
5. `ShortSearch` reavalia no máximo as três melhores quando o gate de busca abre.
6. `AgentPolicy` devolve os índices da melhor `Selection`.
7. Qualquer falha após a etapa 3 retorna imediatamente o primeiro fallback legal.

## Componentes e dependências

| Componente | Entrada | Saída | Dependência permitida |
|---|---|---|---|
| `ObservationParser` | `Observation` | `GameState`, candidatos | API `cabt`, catálogo de cartas |
| `SelectionGenerator` | `SelectData`, candidatos | `list[Selection]` | contratos core |
| `BeliefBuilder` | fatos, logs, decks de referência | `BeliefState` consistente | core |
| `HeuristicScorer` | estado, seleção | score + razões | core |
| `StateEvaluator` | estado de busca | valor escalar | core |
| `ShortSearch` | observação bruta, crença, top candidatos | seleção ou falha tipada | Search API |
| `AgentPolicy` | `Observation` | `list[int]` | componentes anteriores |
| runner | agentes, seeds, matchup | traces e resultados | SDK |

## Fronteiras obrigatórias

- `GameState` contém somente fatos observados.
- `BeliefState` contém hipóteses sobre mão, deck, prêmios e ativo oculto.
- A observação bruta é passada sem reconstrução a `search_begin`.
- Índices de opções pertencem ao simulador; normalização nunca os renumera.
- Scoring não executa I/O nem altera estado.
- Runner mede políticas sem conhecer sua lógica.
- `main.py` é um adaptador fino, não um segundo agente.

## Determinismo

Mesma versão, deck, configuração, seed e observação produzem a mesma seleção. Empates são resolvidos pela tupla lexicográfica de índices. Sorte só existe no simulador ou em experimentos que registrem explicitamente a seed.
