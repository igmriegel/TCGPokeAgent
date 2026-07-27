# Core implementation

## Target files

| File | Responsibility |
|---|---|
| `src/core/types.py` | aliases, result/failure enums, and re-exports of `cabt` enums |
| `src/core/action.py` | `Candidate`, `Selection`, and validation |
| `src/core/state.py` | `GameState`, player/Pokémon views, and `BeliefState` |
| `src/core/parser.py` | observation → normalized decision |
| `src/core/interfaces.py` | small independent protocols |
| `src/core/catalog.py` | cache of `all_card_data()` and `all_attack()` |

The legacy name `action.py` may remain for layout compatibility, but it does not define a singular action; its public type is `Selection`.

## Parser

### Input

Accept the `Observation` dataclass or payload convertible by `to_observation_class`. Store the converted input without mutation.

### Factual state

Copy official fields from `State` and `PlayerState`. Keep `None` for hidden cards. Derive only mathematical values, such as current damage `maxHp - hp`; do not infer card identity.

### Candidates

Enumerate `select.option` with `enumerate`. Resolve metadata by `cardId`, `attackId`, area/index, and visible cards. Missing field generates `None`, not an invented value.

## Selection generation

1. Produce combinations of sizes `minCount..maxCount`.
2. For energy, sum `Option.count` and satisfy `remainEnergyCost`.
3. For damage, respect `remainDamageCounter` and the offered granularity.
4. Apply specific constraints documented by the context.
5. Validate again before returning.
6. Sort by index tuple.

Do not prune by quality at this layer.

## `BeliefBuilder`

Subtract public cards and unambiguous events from logs from the known deck. Fill hidden zones in stable order from the remaining multiset. For the opponent, use the versioned reference deck and remove public cards. Validate that each list delivered to `search_begin` has exactly the required length.

If a subtraction results in a negative value, a Basic is missing in opponent setup, or a cardinality does not close, mark `consistent=False` and do not search.

## Required tests

- golden tests of real observations;
- index preservation;
- `minCount=0`;
- multiple selection;
- energy cost with `count`;
- damage distribution;
- opponent with `hand=None`;
- `None` cards in prize/active;
- consistent and inconsistent belief;
- snapshot serialization without transforming belief into fact.
