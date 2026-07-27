# Core contracts

## Unique vocabulary

### `Selection`

Complete decision sent to the simulator:

```text
Selection.indices: tuple[int, ...]
Selection.option_types: tuple[OptionType, ...]
Selection.context: SelectContext
Selection.score: float | None
Selection.reasons: tuple[str, ...]
```

`indices` preserves original order and positions. A `Selection` is valid when:

- `minCount <= len(indices) <= maxCount`;
- no duplicate index, unless the API documents repetition for the context;
- all indices exist;
- sum required by `remainEnergyCost` or `remainDamageCounter` is satisfied without exceeding the context rule;
- incompatible combinations are rejected before scoring.

If `minCount == 0`, `()` is a legal candidate. The agent never represents the decision as a single `Action`.

### `Candidate`

Typed view of an `Option`:

```text
Candidate.option_index: int
Candidate.option: Option
Candidate.option_type: OptionType
Candidate.card: CardView | None
Candidate.features: Mapping[str, float | int | bool]
```

Create one candidate per option, in the same order, without filtering before storing `option_index`.

### `GameState`

Factual view derived from `State`:

- `turn`, `turnActionCount`, `yourIndex`, `firstPlayer`, `result`;
- `supporterPlayed`, `stadiumPlayed`, `energyAttached`, `retreated`;
- `stadium` and `looking`;
- two players with `active`, `bench`, `benchMax`, `deckCount`, `discard`, `prize`, `handCount`, `hand`;
- conditions `poisoned`, `burned`, `asleep`, `paralyzed`, `confused`;
- for each visible Pokémon: HP, max HP, energies, energy cards, tools, pre-evolutions and `appearThisTurn`.

`hand=None` from opponent and face-down `None` cards remain unknown. The parser does not fill these fields.

### `BeliefState`

Separate hypothesis, never serialized as fact:

- probable multiset of remaining own deck;
- multiset of remaining reference opponent deck;
- ordered hypotheses for hand and prizes;
- hypothesis for the face-down opponent active;
- log events already incorporated;
- `consistent: bool` and list of violations.

An inconsistent belief blocks search, but does not block heuristics.

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

`ParsedDecision` holds `raw_observation`, `state`, `select`, `candidates` and `selections`.

## Failures

Core failures have stable categories: `PARSE_ERROR`, `NO_VALID_SELECTION`, `BELIEF_INCONSISTENT`, `SEARCH_API_ERROR`, `SEARCH_BUDGET`, `INVALID_OUTPUT`. Every exception reaches the wrapper as a structured event; the legal fallback remains available.
