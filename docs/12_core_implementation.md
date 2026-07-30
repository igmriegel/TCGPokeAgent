# Core implementation

## Target files

| File | Responsibility |
|---|---|
| `src/core/types.py` | project enums for selection, modes, results, and errors |
| `src/core/candidate.py` | one metadata-enriched simulator option |
| `src/core/selection.py` | one legal tuple of original option indices and validation |
| `src/core/state.py` | factual `GameState` and player/Pokémon views |
| `src/core/belief.py` | separate hidden-state hypotheses |
| `src/core/parser.py` | observation → normalized decision |
| `src/core/interfaces.py` | small independent protocols |
| `src/core/catalog.py` | cache of card and attack metadata |
| `src/core/deck.py` | active deck and declarative strategy roles |
| `src/core/prize.py` | PrizeCheck and contextual PrizeMap |

## Parser

### Input

Accept a mapping, dataclass, or object carrying CABT fields. Normalize a deep
copy without mutating the caller.

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

Subtract public cards and unambiguous events from logs from the known deck.
Fill hidden zones in stable order from the remaining multiset. Validate the
result before the search gate opens.

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
