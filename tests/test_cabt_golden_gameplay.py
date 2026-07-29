from __future__ import annotations

import json
from pathlib import Path

from src.agents.heuristic import HeuristicAgent
from src.core import DefaultParser, OptionType, SelectContext
from src.core.catalog import CardCatalog

_FIXTURE = Path(__file__).parent / "fixtures" / "cabt_main_turn.json"


def _real_main_observation() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


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
