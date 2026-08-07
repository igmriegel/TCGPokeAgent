"""Decision-level audit helpers for the Honchkrow/Porygon deck."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from src.agents.honchkrow_porygon import (
    DECEIT,
    HACKING,
    R_COMMAND,
    ROCKET_FEATHERS,
    TORMENT,
)


@dataclass(frozen=True, slots=True)
class DecisionEvidence:
    """Public evidence captured for one legal decision in a replay."""

    episode_id: int
    step_index: int
    turn: int
    context: int
    selected_indices: tuple[int, ...]
    legal_option_count: int
    active_card_id: int | None
    bench_card_ids: tuple[int, ...]
    supporter_ids_in_hand: tuple[int, ...]
    deck_count: int
    own_prizes: int
    opponent_prizes: int
    attack_id: int | None
    competing_attack_ids: tuple[int, ...]
    guaranteed_ko_available: bool
    disruption_without_damage: bool
    missed_post_draw_r_command: bool = False
    missed_ko: bool = False
    resource_waste: bool = False
    preventable_deck_out: bool = False


def _int(value: Any) -> int | None:
    """Convert a JSON value to an integer when possible."""
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


def _card_id(value: Any) -> int | None:
    """Extract a card ID from a card or option mapping."""
    if not isinstance(value, Mapping):
        return None
    return _int(value.get("cardId", value.get("id")))


def _option_attack_id(option: Mapping[str, Any]) -> int | None:
    """Extract an attack ID from a legal option."""
    return _int(option.get("attackId"))


def _player(observation: Mapping[str, Any], index: int) -> Mapping[str, Any]:
    """Return a player snapshot from an actor-visible observation."""
    current = observation.get("current", {})
    players = current.get("players", []) if isinstance(current, Mapping) else []
    player = players[index] if isinstance(players, list) and index < len(players) else {}
    return player if isinstance(player, Mapping) else {}


def decision_evidence(record: Mapping[str, Any]) -> DecisionEvidence:
    """Build decision evidence from one replay-decision JSON record."""
    observation = record.get("observation", {})
    if not isinstance(observation, Mapping):
        observation = {}
    current = observation.get("current", {})
    if not isinstance(current, Mapping):
        current = {}
    your_index = _int(current.get("yourIndex")) or 0
    opponent_index = 1 - your_index
    own = _player(observation, your_index)
    opponent = _player(observation, opponent_index)
    select = observation.get("select", {})
    if not isinstance(select, Mapping):
        select = {}
    options = select.get("option", [])
    options = options if isinstance(options, list) else []
    selected = record.get("selected_indices", [])
    selected_indices = (
        tuple(_int(index) or 0 for index in selected) if isinstance(selected, list) else ()
    )
    attack_ids = tuple(
        attack_id
        for attack_id in (
            _option_attack_id(option) for option in options if isinstance(option, Mapping)
        )
        if attack_id is not None
    )
    selected_attack_ids = tuple(
        _option_attack_id(options[index])
        for index in selected_indices
        if 0 <= index < len(options)
        and isinstance(options[index], Mapping)
        and _option_attack_id(options[index]) is not None
    )
    hand = own.get("hand") or []
    supporter_ids = (
        tuple(_card_id(card) for card in hand if _card_id(card) in {1216, 1217, 1218, 1219, 1220})
        if isinstance(hand, list)
        else ()
    )
    active = own.get("active") or []
    active_card_id = _card_id(active[0]) if isinstance(active, list) and active else None
    bench = own.get("bench") or []
    bench_ids = (
        tuple(
            card_id
            for card_id in (_card_id(card) for card in bench if isinstance(card, Mapping))
            if card_id is not None
        )
        if isinstance(bench, list)
        else ()
    )
    chosen_attack = selected_attack_ids[0] if selected_attack_ids else None
    damage_options = {
        _option_attack_id(option)
        for option in options
        if isinstance(option, Mapping)
        and _option_attack_id(option) is not None
        and (
            _int(option.get("damage"))
            or _int(option.get("expectedDamage"))
            or _int(option.get("ko"))
        )
    }
    disruptive = chosen_attack in {HACKING, DECEIT, TORMENT} and not damage_options.intersection(
        attack_ids
    )
    guaranteed_ko = any(
        isinstance(option, Mapping) and bool(option.get("ko", option.get("knockout", False)))
        for option in options
    )
    r_command_available = R_COMMAND in attack_ids
    selected_type = (
        options[selected_indices[0]].get("type")
        if selected_indices
        and 0 <= selected_indices[0] < len(options)
        and isinstance(options[selected_indices[0]], Mapping)
        else None
    )
    deck_count = _int(own.get("deckCount")) or 0
    return DecisionEvidence(
        episode_id=_int(record.get("episode_id")) or 0,
        step_index=_int(record.get("step_index")) or 0,
        turn=_int(current.get("turn")) or 0,
        context=_int(select.get("context")) or 0,
        selected_indices=selected_indices,
        legal_option_count=len(options),
        active_card_id=active_card_id,
        bench_card_ids=bench_ids,
        supporter_ids_in_hand=tuple(
            supporter_id for supporter_id in supporter_ids if supporter_id is not None
        ),
        deck_count=deck_count,
        own_prizes=len(own.get("prize") or []) if isinstance(own.get("prize"), list) else 0,
        opponent_prizes=len(opponent.get("prize") or [])
        if isinstance(opponent.get("prize"), list)
        else 0,
        attack_id=chosen_attack,
        competing_attack_ids=tuple(
            attack_id for attack_id in attack_ids if attack_id != chosen_attack
        ),
        guaranteed_ko_available=guaranteed_ko,
        disruption_without_damage=disruptive,
        missed_post_draw_r_command=r_command_available and chosen_attack not in {R_COMMAND, None},
        missed_ko=guaranteed_ko and chosen_attack not in attack_ids,
        resource_waste=chosen_attack == ROCKET_FEATHERS and not guaranteed_ko,
        preventable_deck_out=(deck_count <= 2 and selected_type == 14 and bool(attack_ids)),
    )


def load_decision_ledger(path: str | Path) -> list[DecisionEvidence]:
    """Load decision evidence from a JSONL replay-decision export."""
    ledger: list[DecisionEvidence] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            if isinstance(record, Mapping):
                ledger.append(decision_evidence(record))
    return ledger


def classify_loss(
    *,
    owner_deck_count: int,
    owner_field_count: int,
    owner_prizes: int,
    opponent_prizes: int,
    ledger: Iterable[DecisionEvidence] = (),
) -> str:
    """Classify a loss using terminal state and contextual decision evidence."""
    evidence = list(ledger)
    if owner_field_count == 0:
        return "DONK / BOARD_COLLAPSE"
    if any(item.preventable_deck_out for item in evidence):
        return "PREVENTABLE_DECK_OUT"
    if owner_deck_count == 0:
        return "DECK_OUT"
    if opponent_prizes == 0 or owner_prizes > opponent_prizes:
        return "PRIZE_RACE_LOSS"
    if any(item.disruption_without_damage for item in evidence):
        return "LOW_DAMAGE_OR_DISRUPTION"
    if any(item.missed_post_draw_r_command for item in evidence):
        return "MISSED_POST_DRAW_R_COMMAND"
    if any(item.guaranteed_ko_available for item in evidence):
        return "MISSED_KO"
    return "UNDETERMINED"


def evidence_as_dict(evidence: DecisionEvidence) -> dict[str, Any]:
    """Serialize one evidence row for JSON reports."""
    return asdict(evidence)
