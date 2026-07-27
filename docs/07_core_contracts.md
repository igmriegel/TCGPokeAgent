# Contratos do core

## Vocabulário único

### `Selection`

Decisão completa enviada ao simulador:

```text
Selection.indices: tuple[int, ...]
Selection.option_types: tuple[OptionType, ...]
Selection.context: SelectContext
Selection.score: float | None
Selection.reasons: tuple[str, ...]
```

`indices` preserva ordem e posições originais. Uma `Selection` é válida quando:

- `minCount <= len(indices) <= maxCount`;
- não repete índice, salvo se a API documentar repetição para o contexto;
- todos os índices existem;
- soma exigida por `remainEnergyCost` ou `remainDamageCounter` é satisfeita sem exceder regra do contexto;
- combinações incompatíveis são rejeitadas antes do scoring.

Se `minCount == 0`, `()` é candidata legal. O agente nunca representa a decisão como `Action` singular.

### `Candidate`

Visão tipada de uma `Option`:

```text
Candidate.option_index: int
Candidate.option: Option
Candidate.option_type: OptionType
Candidate.card: CardView | None
Candidate.features: Mapping[str, float | int | bool]
```

Criar um candidato por opção, na mesma ordem, sem filtrar antes de guardar `option_index`.

### `GameState`

Visão factual derivada de `State`:

- `turn`, `turnActionCount`, `yourIndex`, `firstPlayer`, `result`;
- `supporterPlayed`, `stadiumPlayed`, `energyAttached`, `retreated`;
- `stadium` e `looking`;
- dois jogadores com `active`, `bench`, `benchMax`, `deckCount`, `discard`, `prize`, `handCount`, `hand`;
- condições `poisoned`, `burned`, `asleep`, `paralyzed`, `confused`;
- para cada Pokémon visível: HP, HP máximo, energias, cartas de energia, tools, pré-evoluções e `appearThisTurn`.

`hand=None` do oponente e cartas `None` viradas para baixo permanecem desconhecidas. O parser não preenche esses campos.

### `BeliefState`

Hipótese separada, nunca serializada como fato:

- multiconjunto provável do deck próprio restante;
- multiconjunto do deck adversário de referência restante;
- hipóteses ordenadas para mão e prêmios;
- hipótese do ativo adversário virado para baixo;
- eventos dos logs já incorporados;
- `consistent: bool` e lista de violações.

Uma crença inconsistente impede busca, mas não impede heurística.

## Interfaces

```text
AgentPolicy.select(observation: Observation) -> list[int]
ObservationParser.parse(observation: Observation) -> ParsedDecision
SelectionGenerator.generate(select: SelectData, candidates) -> list[Selection]
HeuristicScorer.score(state: GameState, selection: Selection) -> Score
BeliefBuilder.build(observation, state, history) -> BeliefState
StateEvaluator.evaluate(state: GameState, belief: BeliefState) -> float
ShortSearch.choose(observation, belief, ranked, budget) -> SearchOutcome
```

`ParsedDecision` mantém `raw_observation`, `state`, `select`, `candidates` e `selections`.

## Falhas

Falhas core têm categorias estáveis: `PARSE_ERROR`, `NO_VALID_SELECTION`, `BELIEF_INCONSISTENT`, `SEARCH_API_ERROR`, `SEARCH_BUDGET`, `INVALID_OUTPUT`. Toda exceção chega ao wrapper como evento estruturado; o fallback legal permanece disponível.
