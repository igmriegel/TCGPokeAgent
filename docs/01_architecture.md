# Vertical architecture

## Decision flow

`main.py` receives the observation. If `select is None`, it initializes the
policy with the active deck and returns that deck. Otherwise:

1. `DefaultParser` preserves the raw input, creates factual `GameState`, and
   creates one `Candidate` per option without changing its index.
2. `DefaultSelectionGenerator` produces combinations according to cardinality,
   energy, and damage constraints.
3. `HeuristicAgent` sequences `MAIN` by fixed phases, then ranks only the
   legal selections inside the earliest available phase. `ATTACK` is terminal
   for the turn, so no later action is considered after it.
4. `SelectionFeatureExtractor` creates the immutable
   `selection-ranking-v1` vector for every remaining legal selection.
5. `HeuristicSelectionRanker`, `XGBoostSelectionRanker`, or
   `LightGBMSelectionRanker` orders the same rows. Learned inference failures
   reuse the exact heuristic ranking and are counted.
6. `PolicyDecision` records alternatives, scores, ranks, margins, features,
   backend/version, fallback state, and latency.
7. `HybridAgent` is currently a heuristic pass-through. `BoundedShortSearch`
   is unit-tested separately but is not connected to policy decisions.
8. `main.py` validates the selected indices and returns them.
9. Any policy or validation failure returns the minimal deterministic
   cardinality fallback.

## Components and dependencies

| Component | Input | Output | Allowed dependency |
|---|---|---|---|
| `DefaultParser` | `Observation` | `ParsedDecision` with state and candidates | card catalog |
| `SelectionGenerator` | `SelectData`, candidates | `list[Selection]` | core contracts |
| `BeliefBuilder` | facts, logs, reference decks | consistent `BeliefState` | core |
| `HeuristicScorer` | state, selection | score + reasons | core |
| `SelectionFeatureExtractor` | parsed decision, legal selections | shared ordered rows | factual core and deck profile |
| `SelectionRanker` | parsed decision, selections, shared rows | `list[RankedSelection]` | selected native backend or heuristic |
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
