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
dependencies, while `dev` adds the `dev` group.

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
- for the official Honchkrow/Porygon archive, require the active
  `decision-ledger-v1` manifest contract, its bundled key dictionary, and an
  extracted-package smoke that preserves action stdout while emitting a
  checksum-verifiable stderr ledger.

### Decision-ledger dictionary

The interpretation source for every official Honchkrow/Porygon audit event is
`src/artifacts/decision_ledger_dictionary.json`, both in the repository and at
the same relative path in the extracted archive. The package manifest points to
this exact path through `parameters.decision_ledger.dictionary`.

The dictionary's `keys` map reversibly maps each compact ledger alias to its
full field name. `field_descriptions` defines the decision, trace, candidate,
ranking, feature, and raw-CABT-map fields. `turn_ledger_fields` and
`match_ledger_fields` define every tactical counter and calculated value by its
uncompressed field name. The decoder verifies the payload SHA-256, expands
aliases using this file, and only then produces audit JSONL. Do not interpret
an encoded payload with a dictionary from a different schema version.

The package harness rejects an archive that declares the ledger but omits the
dictionary or active emitter. The smoke gate must additionally prove that a
captured stderr event decodes into the required `selection`, `trace`, `ranked`,
`features`, `turn_ledger`, and `match_ledger` fields.

Remote logs are intentionally compact, not encrypted. The required
interpretation entrypoint is `scripts/download_kaggle_decision_logs.py`: it
downloads both agent-index logs for completed submission episodes, verifies each
compact payload checksum, expands aliases, and writes plain plus
description-annotated JSONL with the exact dictionary and provenance manifest.
Raw Base64 log strings are not a valid harness input for strategic review.

SDK upgrades require an explicit compatibility experiment, a regenerated
lockfile, and a harness contract update; the dependency is never updated
silently.
