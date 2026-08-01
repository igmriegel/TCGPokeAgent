"""Focused acceptance tests for the deterministic HDI v1 policy."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from src.agents.factory import load_deck_profile
from src.agents.hdi import HdiAgent
from src.core import DeckDefinition

ROOT = Path(__file__).parents[1]


def _agent() -> HdiAgent:
    profile = load_deck_profile(ROOT)
    assert profile is not None
    agent = HdiAgent(profile)
    agent.start_match(
        DeckDefinition.from_path(
            ROOT / "src" / "artifacts" / "deck.csv",
            "mega_abomasnow_kyogre",
        )
    )
    return agent


def _pokemon(
    card_id: int,
    hp: int,
    *,
    energies: int = 0,
    serial: int = 1,
) -> dict[str, Any]:
    return {
        "id": card_id,
        "serial": serial,
        "playerIndex": 0,
        "hp": hp,
        "maxHp": hp,
        "energies": [3] * energies,
        "energyCards": [],
        "tools": [],
        "preEvolution": [],
    }


def _observation(
    options: list[dict[str, Any]],
    *,
    context: int | str = 0,
    select_type: int | str = 0,
    own_active: dict[str, Any] | None = None,
    own_bench: list[dict[str, Any]] | None = None,
    opponent_active: dict[str, Any] | None = None,
    opponent_bench: list[dict[str, Any]] | None = None,
    own_prizes: int = 6,
    discard: list[dict[str, Any]] | None = None,
    hand: list[dict[str, Any]] | None = None,
    supporter_played: bool = False,
    conditions: dict[str, bool] | None = None,
    logs: list[dict[str, Any]] | None = None,
    min_count: int = 1,
    max_count: int = 1,
) -> dict[str, Any]:
    own = {
        "active": [own_active or _pokemon(723, 350, energies=3)],
        "bench": own_bench or [],
        "benchMax": 5,
        "deckCount": 30,
        "discard": discard or [],
        "hand": hand or [],
        "handCount": len(hand or []),
        "prize": [None] * own_prizes,
        **(conditions or {}),
    }
    opponent = {
        "active": [opponent_active or _pokemon(721, 150)],
        "bench": opponent_bench or [],
        "benchMax": 5,
        "deckCount": 30,
        "discard": [],
        "hand": None,
        "handCount": 5,
        "prize": [None] * 6,
    }
    return {
        "current": {
            "turn": 7,
            "turnActionCount": 1,
            "yourIndex": 0,
            "firstPlayer": 0,
            "supporterPlayed": supporter_played,
            "stadiumPlayed": False,
            "energyAttached": False,
            "retreated": False,
            "players": [own, opponent],
        },
        "select": {
            "type": select_type,
            "context": context,
            "minCount": min_count,
            "maxCount": max_count,
            "remainEnergyCost": 0,
            "remainDamageCounter": 0,
            "option": options,
        },
        "logs": logs or [],
    }


def test_active_profile_declares_reviewed_roles_attacks_and_priorities() -> None:
    profile = load_deck_profile(ROOT)
    assert profile is not None

    assert profile.cards_for_role("primary_attacker") == (723,)
    assert profile.cards_for_role("secondary_attacker") == (721,)
    assert profile.cards_for_role("development_priority") == (722,)
    assert profile.attack_plans[1042].energy_cost == 1
    assert profile.attack_plans[1042].damage_per_basic_energy_in_discard == 20
    assert profile.attack_plans[1047].requires_guaranteed_ko
    assert profile.discard_priority[:4] == (
        "basic_energy",
        "powerglass",
        "redundant_supporter",
        "duplicate_pokemon",
    )


def test_takes_last_prize_before_a_non_ko_attack() -> None:
    observation = _observation(
        [
            {"type": 13, "guaranteedDamage": 60, "prizeValue": 1},
            {"type": 13, "guaranteedDamage": 50},
        ],
        own_prizes=1,
        opponent_active=_pokemon(722, 60),
        opponent_bench=[_pokemon(721, 150, serial=2)],
    )

    assert _agent().select(observation) == [0]


def test_takes_win_that_removes_the_opponents_last_pokemon() -> None:
    observation = _observation(
        [
            {"type": 13, "guaranteedDamage": 90},
            {"type": 8, "enablesAttack": True},
        ],
        opponent_active=_pokemon(722, 90),
    )

    assert _agent().select(observation) == [0]


def test_knockout_prefers_more_prizes_before_lower_effort() -> None:
    observation = _observation(
        [
            {
                "type": 13,
                "ko": True,
                "prizeValue": 1,
                "energyCost": 1,
                "targetIsActive": False,
            },
            {
                "type": 13,
                "ko": True,
                "prizeValue": 3,
                "energyCost": 3,
                "targetIsActive": False,
            },
        ],
        opponent_bench=[_pokemon(723, 350, serial=2)],
    )

    assert _agent().select(observation) == [1]


def test_rule_box_damage_prevention_vetoes_attack() -> None:
    observation = _observation(
        [
            {"type": 13, "guaranteedDamage": 200, "damagePrevented": True},
            {"type": 13, "guaranteedDamage": 50},
        ],
        opponent_active=_pokemon(721, 150),
        opponent_bench=[_pokemon(722, 90, serial=2)],
    )

    assert _agent().select(observation) == [1]


def test_riptide_requires_a_provable_knockout() -> None:
    observation = _observation(
        [{"type": 13, "attackId": 1042}, {"type": 14}],
        own_active=_pokemon(721, 150, energies=1),
        opponent_active=_pokemon(722, 30),
        discard=[{"id": 3, "serial": 40}],
    )
    assert _agent().select(observation) == [1]

    observation["current"]["players"][1]["active"][0]["hp"] = 20
    assert _agent().select(observation) == [0]


def test_frost_barrier_requires_a_guaranteed_knockout() -> None:
    observation = _observation(
        [
            {"type": 13, "attackId": 1047},
            {"type": 13, "attackId": 1046},
            {"type": 14},
        ],
        opponent_active=_pokemon(723, 250),
        opponent_bench=[_pokemon(722, 90, serial=2)],
    )
    assert _agent().select(observation) == [1]

    observation["current"]["players"][1]["active"][0]["hp"] = 200
    assert _agent().select(observation) == [0]


def test_swirling_waves_requires_public_previous_riptide() -> None:
    observation = _observation(
        [{"type": 13, "attackId": 1043}, {"type": 14}],
        own_active=_pokemon(721, 150, energies=3),
        opponent_active=_pokemon(722, 130),
    )
    assert _agent().select(observation) == [1]

    observation["logs"] = [{"type": 15, "playerIndex": 0, "attackId": 1042}]
    assert _agent().select(observation) == [0]


def test_guaranteed_damage_precedes_larger_potential_damage() -> None:
    observation = _observation(
        [
            {"type": 13, "guaranteedDamage": 40},
            {"type": 13, "potentialDamage": 200},
        ],
        opponent_active=_pokemon(723, 350),
        opponent_bench=[_pokemon(722, 90, serial=2)],
    )

    assert _agent().select(observation) == [0]


def test_attachment_enabling_attack_precedes_other_development() -> None:
    observation = _observation(
        [
            {
                "type": 8,
                "cardId": 3,
                "inPlayArea": 5,
                "inPlayIndex": 0,
                "enablesAttack": True,
            },
            {"type": 9, "cardId": 723},
            {"type": 14},
        ],
        own_bench=[_pokemon(723, 350, energies=1, serial=2)],
    )

    assert _agent().select(observation) == [0]


def test_discard_order_and_protected_resources_are_declarative() -> None:
    hand = [
        {"id": 723, "serial": 10},
        {"id": 1219, "serial": 11},
        {"id": 1163, "serial": 12},
        {"id": 3, "serial": 13},
    ]
    options = [
        {"type": 3, "area": 2, "index": index, "playerIndex": 0} for index in range(len(hand))
    ]
    observation = _observation(
        options,
        context=8,
        select_type=1,
        hand=hand,
        supporter_played=True,
    )
    assert _agent().select(observation) == [3]

    observation["select"]["option"] = options[:-1]
    assert _agent().select(observation) == [2]


def test_preserves_last_pokemon_and_singleton_resource() -> None:
    hand = [
        {"id": 722, "serial": 10},
        {"id": 1092, "serial": 11},
        {"id": 1121, "serial": 12},
    ]
    options = [
        {"type": 3, "area": 2, "index": index, "playerIndex": 0} for index in range(len(hand))
    ]
    observation = _observation(
        options,
        context=8,
        select_type=1,
        hand=hand,
    )

    assert _agent().select(observation) == [2]


def test_promotion_prefers_ready_attacker_then_lower_risk() -> None:
    bench = [
        _pokemon(722, 90, energies=0, serial=2),
        _pokemon(721, 150, energies=1, serial=3),
    ]
    observation = _observation(
        [
            {"type": 3, "area": 5, "index": 0, "playerIndex": 0},
            {"type": 3, "area": 5, "index": 1, "playerIndex": 0},
        ],
        context=4,
        select_type=1,
        own_bench=bench,
    )

    assert _agent().select(observation) == [1]


def test_promotion_breaks_ready_attacker_tie_by_knockout_risk() -> None:
    bench = [
        _pokemon(722, 90, energies=1, serial=2),
        _pokemon(721, 150, energies=1, serial=3),
    ]
    observation = _observation(
        [
            {"type": 3, "area": 5, "index": 0, "playerIndex": 0},
            {"type": 3, "area": 5, "index": 1, "playerIndex": 0},
        ],
        context=4,
        select_type=1,
        own_bench=bench,
        opponent_active=_pokemon(721, 150, energies=3),
    )

    assert _agent().select(observation) == [1]


def test_special_condition_recovery_precedes_other_productive_action() -> None:
    observation = _observation(
        [
            {"type": 7, "removesSpecialCondition": True},
            {"type": 8, "cardId": 3, "enablesAttack": True},
        ],
        conditions={"paralyzed": True},
    )

    assert _agent().select(observation) == [0]


def test_full_bench_with_ready_attackers_still_uses_productive_attack() -> None:
    bench = [_pokemon(721, 150, energies=1, serial=index + 2) for index in range(5)]
    observation = _observation(
        [{"type": 13, "guaranteedDamage": 30}, {"type": 14}],
        own_bench=bench,
        opponent_active=_pokemon(723, 350),
        opponent_bench=[_pokemon(722, 90, serial=9)],
    )

    assert _agent().select(observation) == [0]


def test_end_is_rejected_for_productive_action_and_accepted_for_unsafe_attack() -> None:
    productive = _observation([{"type": 14}, {"type": 8, "cardId": 3, "enablesAttack": True}])
    assert _agent().select(productive) == [1]

    no_gain = _observation(
        [{"type": 13, "damagePrevented": True}, {"type": 14}],
        opponent_bench=[_pokemon(722, 90, serial=2)],
    )
    assert _agent().select(no_gain) == [1]


def test_final_tie_uses_original_option_index_without_renumbering() -> None:
    observation = _observation(
        [
            {"type": 7, "cardId": 1121},
            {"type": 7, "cardId": 1121},
            {"type": 14},
        ]
    )

    assert _agent().select(observation) == [0]


def test_incomplete_metadata_uses_deterministic_legal_fallback() -> None:
    observation = _observation(
        [{"type": "CARD"}, {"type": "CARD"}],
        context="LOOK",
        select_type="CARD",
    )
    observation["current"] = {}

    assert _agent().select(observation) == [0]


def test_selection_does_not_mutate_observation() -> None:
    observation = _observation([{"type": 8, "cardId": 3, "enablesAttack": True}, {"type": 14}])
    original = deepcopy(observation)

    _agent().select(observation)

    assert observation == original
