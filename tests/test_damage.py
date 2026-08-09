from __future__ import annotations

from src.core.damage import (
    ATTACK_DAMAGE_REDUCTION_EFFECTS,
    CARD_DAMAGE_REDUCTION_EFFECTS,
    DamageReductionEffect,
    calculate_damage,
)


def test_frost_barrier_reduces_damage_after_weakness_and_resistance() -> None:
    state = {
        "turn": 2,
        "logs": [{"type": 15, "attackId": 1047, "serial": 9}],
    }
    defender = {"weakness": 1, "resistance": 2}

    assert calculate_damage(
        100,
        1,
        defender,
        state_raw=state,
        defender_serial=9,
    ) == 170


def test_damage_reduction_is_not_applied_without_matching_source_event() -> None:
    state = {"turn": 2, "logs": [{"type": 15, "attackId": 1047, "serial": 8}]}

    assert calculate_damage(100, 1, {}, state_raw=state, defender_serial=9) == 100


def test_damage_reduction_rules_are_extensible_without_changing_calculator() -> None:
    ATTACK_DAMAGE_REDUCTION_EFFECTS[9999] = DamageReductionEffect(amount=25)
    try:
        state = {"turn": 2, "logs": [{"type": 15, "attackId": 9999, "serial": 9}]}
        assert calculate_damage(100, 1, {}, state_raw=state, defender_serial=9) == 75
    finally:
        del ATTACK_DAMAGE_REDUCTION_EFFECTS[9999]


def test_card_reduction_registry_supports_tools_and_items() -> None:
    CARD_DAMAGE_REDUCTION_EFFECTS[7777] = DamageReductionEffect(amount=20)
    try:
        state = {"turn": 2, "logs": [{"cardId": 7777, "serial": 9, "type": 10}]}
        assert calculate_damage(100, 1, {}, state_raw=state, defender_serial=9) == 80
    finally:
        del CARD_DAMAGE_REDUCTION_EFFECTS[7777]
