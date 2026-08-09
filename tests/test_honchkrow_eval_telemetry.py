"""Tests for terminal and Mega Abomasnow evaluation telemetry."""

from __future__ import annotations

from scripts.run_honchkrow_porygon_eval import _is_partial_mega_abomasnow_attack
from src.agents.honchkrow_porygon import MEGA_ABOMASNOW_EX, R_COMMAND, ROCKET_FEATHERS


def test_damaged_mega_exact_lethal_is_not_counted_as_partial() -> None:
    """Rocket Feathers must use current target HP rather than printed HP."""
    target = {"id": MEGA_ABOMASNOW_EX, "hp": 110}

    assert not _is_partial_mega_abomasnow_attack(target, [ROCKET_FEATHERS], 2, 0)


def test_underfunded_mega_attack_remains_partial() -> None:
    """An attack below the visible target HP remains an actionable regression."""
    target = {"id": MEGA_ABOMASNOW_EX, "hp": 350}

    assert _is_partial_mega_abomasnow_attack(target, [ROCKET_FEATHERS], 4, 0)
    assert _is_partial_mega_abomasnow_attack(target, [R_COMMAND], 0, 17)
