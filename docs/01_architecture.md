# Vertical architecture

## Decision flow

`main.py` receives the observation. If `select is None`, it returns the deck. Otherwise:

1. `ObservationParser` preserves the raw input and creates a factual `GameState`.
2. `CandidateBuilder` transforms each `Option` into a candidate without changing its index.
3. `SelectionGenerator` produces valid combinations according to cardinality, energy and damage.
4. `HeuristicScorer` ranks the combinations.
5. `ShortSearch` re-evaluates at most the top three when the search gate opens.
6. `AgentPolicy` returns the indices of the best `Selection`.
7. Any failure after step 3 immediately returns the first legal fallback.

## Components and dependencies

| Component | Input | Output | Allowed dependency |
|---|---|---|---|
| `ObservationParser` | `Observation` | `GameState`, candidates | `cabt` API, card catalog |
| `SelectionGenerator` | `SelectData`, candidates | `list[Selection]` | core contracts |
| `BeliefBuilder` | facts, logs, reference decks | consistent `BeliefState` | core |
| `HeuristicScorer` | state, selection | score + reasons | core |
| `StateEvaluator` | search state | scalar value | core |
| `ShortSearch` | raw observation, belief, top candidates | selection or typed failure | Search API |
| `AgentPolicy` | `Observation` | `list[int]` | preceding components |
| runner | agents, seeds, matchup | traces and results | SDK |

## Mandatory boundaries

- `GameState` contains only observed facts.
- `BeliefState` contains hypotheses about hand, deck, prizes and hidden active.
- The raw observation is passed without reconstruction to `search_begin`.
- Option indices belong to the simulator; normalization never renumbers them.
- Scoring does not perform I/O or alter state.
- Runner measures policies without knowing their logic.
- `main.py` is a thin adapter, not a second agent.

## Determinism

Same version, deck, configuration, seed and observation produce the same selection. Ties are resolved by the lexicographic tuple of indices. Randomness exists only in the simulator or in experiments that explicitly record the seed.
