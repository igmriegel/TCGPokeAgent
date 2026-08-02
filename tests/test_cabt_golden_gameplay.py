from __future__ import annotations

import json
from pathlib import Path

from src.agents.heuristic import HeuristicAgent
from src.core import DefaultParser, OptionType, SelectContext
from src.core.catalog import CardCatalog

_FIXTURE = Path(__file__).parent / "fixtures" / "cabt_main_turn.json"


def _real_main_observation() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _board_development_observation(*, bench_count: int, pokemon_in_hand: int = 1) -> dict:
    hand = [{"id": 3, "serial": 50}]
    hand.extend({"id": 721, "serial": serial} for serial in range(1, pokemon_in_hand + 1))
    options = [
        {"type": 8, "index": 0, "inPlayArea": 4, "inPlayIndex": 0},
        *({"type": 7, "index": index} for index in range(1, pokemon_in_hand + 1)),
        {"type": 13, "attackId": 1046},
        {"type": 14},
    ]
    return {
        "current": {
            "turn": 11,
            "turnActionCount": 0,
            "yourIndex": 0,
            "firstPlayer": 0,
            "players": [
                {
                    "active": [{"id": 723, "serial": 11, "hp": 120}],
                    "bench": [
                        {"id": 721, "serial": 20 + index, "hp": 130} for index in range(bench_count)
                    ],
                    "benchMax": 5,
                    "hand": hand,
                    "deckCount": 30,
                },
                {
                    "active": [{"id": 65, "serial": 60, "hp": 60}],
                    "bench": [],
                    "benchMax": 5,
                    "hand": None,
                    "deckCount": 30,
                },
            ],
        },
        "select": {
            "type": 0,
            "context": 0,
            "minCount": 1,
            "maxCount": 1,
            "remainEnergyCost": 0,
            "remainDamageCounter": 0,
            "option": options,
        },
        "logs": [],
    }


def test_real_cabt_observation_resolves_cards_targets_and_state() -> None:
    parsed = DefaultParser(CardCatalog.from_cg()).parse(_real_main_observation())

    assert parsed.select_context is SelectContext.MAIN
    assert parsed.state.players[0].active is not None
    assert parsed.state.players[0].active.card_id == 722
    assert parsed.state.players[0].deck_count == 46
    assert parsed.state.players[0].hand_count == 7
    assert parsed.candidates[0].option_type is OptionType.ATTACH
    assert parsed.candidates[0].features["card_id"] == 3
    assert parsed.candidates[0].features["target_card_id"] == 722
    assert parsed.candidates[0].card is not None
    assert parsed.candidates[0].card["name"] == "Basic {W} Energy"


def test_real_cabt_main_turn_selects_productive_action_instead_of_end() -> None:
    observation = _real_main_observation()
    end_index = len(observation["select"]["option"]) - 1

    selected = HeuristicAgent().select(observation)

    assert selected
    assert end_index not in selected
    assert observation["select"]["option"][selected[0]]["type"] == 8


def test_repeated_energy_cost_prompt_selects_one_available_energy() -> None:
    observation = _real_main_observation()
    observation["select"] = {
        "type": 4,
        "context": 30,
        "minCount": 1,
        "maxCount": 1,
        "remainEnergyCost": 2,
        "remainDamageCounter": 0,
        "option": [
            {
                "type": 6,
                "area": 4,
                "index": 0,
                "playerIndex": 0,
                "energyIndex": energy_index,
                "count": 1,
            }
            for energy_index in range(3)
        ],
    }

    assert HeuristicAgent().select(observation) == [0]


def test_main_plays_available_pokemon_before_attacking_with_open_bench() -> None:
    observation = _board_development_observation(bench_count=0)

    assert HeuristicAgent().select(observation) == [1]


def test_main_rechecks_development_when_another_pokemon_is_available() -> None:
    observation = _board_development_observation(bench_count=1, pokemon_in_hand=2)

    assert HeuristicAgent().select(observation) in ([1], [2])


def test_main_prefers_attach_when_the_bench_is_full() -> None:
    observation = _board_development_observation(bench_count=5)

    assert HeuristicAgent().select(observation) == [0]
