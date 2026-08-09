"""Shared public attack-damage rules used by tactical planning."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DamageReductionEffect:
    """Describe a temporary reduction applied after weakness and resistance."""

    amount: int
    duration_turns: int = 1
    after_weakness_resistance: bool = True


ATTACK_DAMAGE_REDUCTION_EFFECTS: dict[int, DamageReductionEffect] = {
    # Mega Abomasnow ex — Frost Barrier.
    1047: DamageReductionEffect(amount=30),
}
CARD_DAMAGE_REDUCTION_EFFECTS: dict[int, DamageReductionEffect] = {}


def calculate_damage(
    base_damage: int,
    attacker_energy_type: Any,
    defender_card: Mapping[str, Any] | None,
    *,
    prevented: bool = False,
    state_raw: Mapping[str, Any] | None = None,
    defender_serial: int | None = None,
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
    if state_raw is not None and defender_serial is not None:
        damage = max(
            0,
            damage - active_damage_reduction(state_raw, defender_serial),
        )
    return damage


def active_damage_reduction(state_raw: Mapping[str, Any], defender_serial: int) -> int:
    """Return reductions active for a defender during the current turn.

    Attack effects are registered in ``ATTACK_DAMAGE_REDUCTION_EFFECTS`` and
    card effects in ``CARD_DAMAGE_REDUCTION_EFFECTS`` so future attacks,
    tools, or items can add rules without changing damage calculation.  CABT
    logs do not attach a turn number to every attack;
    therefore an effect is active only when its source attack is the latest
    attack event and the current turn is the immediately following turn.
    """
    logs = state_raw.get("_logs", state_raw.get("logs", ()))
    if not isinstance(logs, list):
        return 0
    current_turn = _int(state_raw.get("turn"))
    if current_turn <= 0:
        return 0
    total = 0
    for event in reversed(logs):
        if not isinstance(event, Mapping):
            continue
        attack_id = _int(event.get("attackId"))
        card_id = _int(event.get("cardId"))
        event_serial = _int(event.get("serial", event.get("pokemonSerial")))
        if event_serial != defender_serial:
            continue
        if attack_id > 0:
            effect = ATTACK_DAMAGE_REDUCTION_EFFECTS.get(attack_id)
            if effect is None:
                # A later attack on this Pokémon supersedes an older effect.
                return 0
        elif card_id > 0:
            effect = CARD_DAMAGE_REDUCTION_EFFECTS.get(card_id)
            if effect is None:
                continue
        else:
            continue
        if effect.duration_turns >= 1:
            total += effect.amount
        return total
    return 0


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
