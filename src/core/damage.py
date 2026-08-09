"""Shared public attack-damage rules used by tactical planning."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def calculate_damage(
    base_damage: int,
    attacker_energy_type: Any,
    defender_card: Mapping[str, Any] | None,
    *,
    prevented: bool = False,
) -> int:
    """Calculate damage after weakness, resistance, and prevention.

    ``attacker_energy_type`` is the Pokémon's elemental type.  Attack costs
    are deliberately not accepted here: a Colorless cost must not change the
    attacker's type.
    """
    if prevented or base_damage <= 0:
        return 0
    card = defender_card or {}
    damage = int(base_damage)
    if types_equal(card.get("weakness") or card.get("weaknesses"), attacker_energy_type):
        damage *= 2
    if types_equal(card.get("resistance") or card.get("resistances"), attacker_energy_type):
        damage = max(0, damage - 30)
    return damage


def types_equal(value: Any, expected: Any) -> bool:
    """Return whether a weakness/resistance value equals an elemental type."""
    if isinstance(value, Mapping):
        return types_equal(value.get("type", value.get("name")), expected)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(types_equal(item, expected) for item in value)
    if value is None or expected is None:
        return False
    try:
        return int(value) == int(expected)
    except (TypeError, ValueError):
        return str(value).casefold() == str(expected).casefold()


def has_splashing_dodge_protection(state_raw: Mapping[str, Any], serial: int | None) -> bool:
    """Detect Phantump's heads-based protection for the immediately next turn."""
    if serial is None:
        return False
    current_turn = _int(state_raw.get("turn"))
    logs = state_raw.get("_logs", state_raw.get("logs", ()))
    if not isinstance(logs, list):
        return False
    for event in logs:
        if not isinstance(event, Mapping):
            continue
        event_serial = event.get("serial", event.get("targetSerial", event.get("pokemonSerial")))
        if _int(event.get("attackId")) != 1266 or _int(event_serial) != serial:
            continue
        coin = str(
            event.get(
                "coin",
                event.get(
                    "coinFlip", event.get("coinResult", event.get("result", event.get("flip", "")))
                ),
            )
        ).casefold()
        if coin not in {"head", "heads", "true", "1"} and not any(
            event.get(key) is True for key in ("heads", "isHeads", "coinHead")
        ):
            continue
        event_turn = event.get("turn")
        if event_turn is None or _int(event_turn) == current_turn - 1:
            return True
    return False


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
