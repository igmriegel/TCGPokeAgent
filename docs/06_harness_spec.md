# Environment and submission contract

Verified on 2026-07-27 against the [`cabt` API](https://matsuoinstitute.github.io/cabt/api.html), the [`cabt.json`](https://raw.githubusercontent.com/Kaggle/kaggle-environments/master/kaggle_environments/envs/cabt/cabt.json) and the [competition](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/overview/description).

## Reproducible environment

The harness standardizes local development and containers on Python 3.12.
`.python-version` selects the local interpreter, while `uv sync` creates and
synchronizes the ignored `.venv` automatically. `pyproject.toml` declares
dependencies and `uv.lock` is the only resolved dependency source; no
parallel dependency manifest is maintained.

Local acceptance commands use `uv run --frozen ...` and do not require
activation. `source .venv/bin/activate` remains optional for an interactive
shell. Docker stages use the same frozen lock: `agent` installs runtime
dependencies, `dev` adds the `dev` group, and `marimo` adds the `notebooks`
group.

## Agent input

`Observation` contains:

| Field | Type | Contract |
|---|---|---|
| `current` | `State | None` | `None` only in the initial deck selection |
| `logs` | `list[Log]` | events since the previous selection |
| `select` | `SelectData | None` | `None` only in the initial deck selection |
| `search_begin_input` | `str | None` | opaque input associated with `search_begin` |

The wrapper converts the payload with `to_observation_class` when the runtime does not deliver the dataclass. It preserves the raw received instance for the Search API.

## Agent output

In-game, `AgentPolicy.select(observation) -> list[int]`. Each integer is the original position in `observation.select.option`. The list may contain zero, one or multiple indices according to `minCount` and `maxCount`.

On the initial call, `select is None` and `current is None`; `main.py` returns the deck in the format required by the SDK. This branch does not execute parser, heuristic or search.

## `SelectData`

Canonical fields:

- `type: SelectType`;
- `context: SelectContext`;
- `minCount`, `maxCount`;
- `remainDamageCounter`, `remainEnergyCost`;
- `option: list[Option]`;
- `deck`, present when selecting from the deck;
- `contextCard`, used in the activation context;
- `effect`, card whose effect is being processed.

`SelectType` defines the family of the selection; `SelectContext` defines its purpose. The strategy dispatches by the pair, with priority for `SelectContext`.

## `SelectType` and `OptionType`

| `SelectType` | Expected `OptionType` |
|---|---|
| `MAIN` | `PLAY`, `ATTACH`, `EVOLVE`, `ABILITY`, `DISCARD`, `RETREAT`, `ATTACK`, `END` |
| `CARD` | `CARD` |
| `ATTACHED_CARD` | `TOOL_CARD`, `ENERGY_CARD` |
| `CARD_OR_ATTACHED_CARD` | `CARD`, `TOOL_CARD`, `ENERGY_CARD` |
| `ENERGY` | `ENERGY` |
| `SKILL` | `SKILL` |
| `ATTACK` | `ATTACK` |
| `EVOLVE` | `EVOLVE` |
| `COUNT` | `NUMBER` |
| `YES_NO` | `YES`, `NO` |
| `SPECIAL_CONDITION` | `SPECIAL_CONDITION` |

`Option` fields are optional and interpreted by `type`: `number`, `area`, `index`, `playerIndex`, `toolIndex`, `energyIndex`, `count`, `inPlayArea`, `inPlayIndex`, `attackId`, `cardId`, `serial` and `specialConditionType`.

## Budget

The environment publishes `actTimeout=0`, `runTimeout=2000`, `remainingOverageTime=600` and action as array. The agent does not interpret `actTimeout=0` as infinite time: it applies 100 ms as internal search limit and preserves margin for parsing/fallback. Search is disabled below 30 seconds of `remainingOverageTime`.

## Package

- pin `kaggle-environments==1.32.2` during the MVP and verify the installed
  distribution version during preflight;
- validate the 60-card deck from `cabt.first_agent` on the installed SDK;
- keep `main.py` and `deck.csv` at the root of the `.tar.gz`;
- make imports from `/kaggle_simulations/agent/`;
- keep the file under 197.7 MiB;
- extract into a temporary directory and test using only the extracted content.

SDK upgrades require an explicit compatibility experiment, a regenerated
lockfile, and a harness contract update; the dependency is never updated
silently.
