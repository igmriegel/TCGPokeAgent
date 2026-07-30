# Vertical architecture

## Decision flow

`main.py` receives the observation. If `select is None`, it initializes the
policy with the active deck and returns that deck. Otherwise:

1. `DefaultParser` preserves the raw input, creates factual `GameState`, and
   creates one `Candidate` per option without changing its index.
2. `DefaultSelectionGenerator` produces combinations according to cardinality,
   energy, and damage constraints.
3. `HeuristicAgent` may require a legal board-development play before a
   terminal attack or end-turn choice.
4. `SimpleHeuristicScorer` ranks the remaining selections with traceable
   reasons.
5. `HybridAgent` is currently a heuristic pass-through. `BoundedShortSearch`
   is unit-tested separately but is not connected to policy decisions.
6. `main.py` validates the selected indices and returns them.
7. Any policy or validation failure returns the minimal deterministic
   cardinality fallback.

## Components and dependencies

| Component | Input | Output | Allowed dependency |
|---|---|---|---|
| `DefaultParser` | `Observation` | `ParsedDecision` with state and candidates | card catalog |
| `SelectionGenerator` | `SelectData`, candidates | `list[Selection]` | core contracts |
| `BeliefBuilder` | facts, logs, reference decks | consistent `BeliefState` | core |
| `HeuristicScorer` | state, selection | score + reasons | core |
| `StateEvaluator` | search state | scalar value | core |
| `BoundedShortSearch` | opaque search input, belief, ranked candidates | selection or heuristic fallback | injected adapter; not integrated |
| `AgentPolicy` | `Observation` | `list[int]` | preceding components |
| runner | agents, seeds, matchup | traces and results | SDK |

## Mandatory boundaries

- `GameState` contains only observed facts.
- `BeliefState` contains hypotheses about hand, deck, prizes and hidden active.
- The opaque `search_begin_input` is passed to the vendored adapter without
  reconstruction; model-safe persisted data excludes it.
- Option indices belong to the simulator; normalization never renumbers them.
- Scoring does not perform I/O or alter state.
- Runner measures policies without knowing their logic.
- `main.py` is a thin adapter, not a second agent.

## Determinism

Same version, deck, configuration, seed and observation produce the same selection. Ties are resolved by the lexicographic tuple of indices. Randomness exists only in the simulator or in experiments that explicitly record the seed.
