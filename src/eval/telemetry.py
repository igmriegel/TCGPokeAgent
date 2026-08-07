"""Public CABT state snapshots, transitions, and terminal classification."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

ROCKET_SUPPORTERS = {1216, 1217, 1218, 1219, 1220}


def _card_id(card: Any) -> int | None:
    if not isinstance(card, Mapping):
        return None
    value = card.get("id", card.get("cardId"))
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


def _cards(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [card for card in value if isinstance(card, Mapping)]


def _pokemon(value: Any) -> list[Mapping[str, Any]]:
    return _cards(value)


def _player_snapshot(player: Mapping[str, Any]) -> dict[str, Any]:
    active = _pokemon(player.get("active"))
    bench = _pokemon(player.get("bench"))
    hand = _cards(player.get("hand"))
    discard = _cards(player.get("discard"))
    pokemon = active + bench
    supporter_hand = sum(_card_id(card) in ROCKET_SUPPORTERS for card in hand)
    supporter_discard = sum(_card_id(card) in ROCKET_SUPPORTERS for card in discard)

    def card_snapshot(card: Mapping[str, Any]) -> dict[str, Any]:
        energies = card.get("energies", [])
        return {
            "card_id": _card_id(card),
            "hp": int(card.get("hp", 0) or 0),
            "max_hp": int(card.get("maxHp", 0) or 0),
            "energy_count": len(energies) if isinstance(energies, list) else 0,
            "energy_ids": list(energies) if isinstance(energies, list) else [],
            "tool_count": len(card.get("tools", []))
            if isinstance(card.get("tools", []), list)
            else 0,
        }

    return {
        "deck_count": int(player.get("deckCount", 0) or 0),
        "prize_count": len(player.get("prize", [])) if isinstance(player.get("prize"), list) else 0,
        "hand_count": int(player.get("handCount", len(hand)) or 0),
        "discard_count": len(discard),
        "hand_supporters": supporter_hand,
        "discard_supporters": supporter_discard,
        "active": card_snapshot(active[0]) if active else None,
        "bench": [card_snapshot(card) for card in bench],
        "bench_count": len(bench),
        "pokemon_in_play": len(pokemon),
        "total_hp": sum(int(card.get("hp", 0) or 0) for card in pokemon),
        "total_max_hp": sum(int(card.get("maxHp", 0) or 0) for card in pokemon),
    }


def public_snapshot(observation: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize the public state visible at one CABT decision.

    Hidden card identities are intentionally omitted. Counts and revealed
    board cards remain factual and are suitable for decision-level analysis.
    """
    current = observation.get("current", observation)
    if not isinstance(current, Mapping):
        return {}
    players = current.get("players", [])
    if not isinstance(players, list):
        return {}
    if not players:
        return {
            "turn": int(current.get("turn", 0) or 0),
            "your_index": 0,
            "own": {},
            "opponent": {},
        }
    your_index = int(current.get("yourIndex", 0) or 0)
    your_index = your_index if 0 <= your_index < len(players) else 0
    opponent_index = 1 - your_index
    own = players[your_index] if isinstance(players[your_index], Mapping) else {}
    opponent = players[opponent_index] if 0 <= opponent_index < len(players) else {}
    return {
        "turn": int(current.get("turn", 0) or 0),
        "turn_action_count": int(current.get("turnActionCount", 0) or 0),
        "your_index": your_index,
        "first_player": int(current.get("firstPlayer", 0) or 0),
        "result": current.get("result"),
        "supporter_played": bool(current.get("supporterPlayed", False)),
        "energy_attached": bool(current.get("energyAttached", False)),
        "retreated": bool(current.get("retreated", False)),
        "own": _player_snapshot(own),
        "opponent": _player_snapshot(opponent),
    }


def transition(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    """Calculate observable resource, board, damage, and prize changes."""
    own_before = before.get("own", {})
    own_after = after.get("own", {})
    opponent_before = before.get("opponent", {})
    opponent_after = after.get("opponent", {})

    def delta(player_before: Mapping[str, Any], player_after: Mapping[str, Any], key: str) -> int:
        return int(player_after.get(key, 0) or 0) - int(player_before.get(key, 0) or 0)

    active_before = own_before.get("active") or {}
    active_after = own_after.get("active") or {}
    target_before = opponent_before.get("active") or {}
    target_after = opponent_after.get("active") or {}
    target_hp_before = int(target_before.get("hp", 0) or 0)
    target_hp_after = int(target_after.get("hp", 0) or 0)
    own_hp_before = int(active_before.get("hp", 0) or 0)
    own_hp_after = int(active_after.get("hp", 0) or 0)
    return {
        "turn_delta": int(after.get("turn", 0) or 0) - int(before.get("turn", 0) or 0),
        "target_damage": max(0, target_hp_before - target_hp_after),
        "own_active_damage": max(0, own_hp_before - own_hp_after),
        "target_hp_before": target_hp_before,
        "target_hp_after": target_hp_after,
        "target_ko": bool(target_before) and not bool(target_after),
        "own_active_ko": bool(active_before) and not bool(active_after),
        "own_deck_delta": delta(own_before, own_after, "deck_count"),
        "opponent_deck_delta": delta(opponent_before, opponent_after, "deck_count"),
        "own_prize_delta": delta(own_before, own_after, "prize_count"),
        "opponent_prize_delta": delta(opponent_before, opponent_after, "prize_count"),
        "own_discard_delta": delta(own_before, own_after, "discard_count"),
        "own_hand_delta": delta(own_before, own_after, "hand_count"),
        "own_supporter_discard_delta": delta(own_before, own_after, "discard_supporters"),
        "own_pokemon_delta": delta(own_before, own_after, "pokemon_in_play"),
        "opponent_pokemon_delta": delta(opponent_before, opponent_after, "pokemon_in_play"),
        "active_changed": active_before.get("card_id") != active_after.get("card_id"),
        "opponent_active_changed": target_before.get("card_id") != target_after.get("card_id"),
    }


def classify_terminal(
    snapshot: Mapping[str, Any],
    result: str | None,
    agent_side: int,
) -> tuple[str, bool]:
    """Classify terminal outcome from public loser counts.

    Returns the reason and whether it was directly exposed by CABT. Live CABT
    observations generally omit the explicit reason, so count-based results
    are marked inferred.
    """
    own = snapshot.get("own", {})
    opponent = snapshot.get("opponent", {})
    loser = opponent if result == "win" else own if result == "loss" else {}
    if not isinstance(loser, Mapping):
        return "UNRESOLVED_TERMINAL_STATE", False
    if int(loser.get("prize_count", -1)) == 0:
        return "ALL_PRIZES_TAKEN", False
    if int(loser.get("deck_count", -1)) == 0:
        return "DECK_OUT", False
    if int(loser.get("pokemon_in_play", -1)) == 0:
        return "NO_POKEMON_IN_PLAY", False
    return "UNRESOLVED_TERMINAL_STATE", False


def failure_flags(
    *,
    selected_indices: Sequence[int],
    options: Sequence[Mapping[str, Any]],
    before: Mapping[str, Any],
    effects: Mapping[str, Any],
) -> list[str]:
    """Identify decision-level risk patterns without inventing hidden state."""
    selected = [options[index] for index in selected_indices if 0 <= index < len(options)]
    selected_types = {option.get("type") for option in selected}
    selected_attacks = [option for option in selected if option.get("attackId") is not None]
    flags: list[str] = []
    target = before.get("opponent", {}).get("active") or {}
    target_hp = int(target.get("hp", 0) or 0)
    attacks = [option for option in options if option.get("attackId") is not None]
    if 14 in selected_types and attacks and int(before.get("own", {}).get("deck_count", 0)) <= 2:
        flags.append("END_WITH_CRITICAL_DECK")
    if 12 in selected_types and attacks and effects.get("target_damage", 0) == 0:
        flags.append("RETREAT_WITHOUT_OBSERVED_DAMAGE")
    if target_hp > 0 and selected_attacks and effects.get("target_damage", 0) == 0:
        flags.append("ATTACK_WITHOUT_OBSERVED_DAMAGE")
    if int(before.get("own", {}).get("deck_count", 0)) <= 2:
        flags.append("DECK_CRITICAL")
    return flags


def aggregate_decisions(matches: Sequence[Any]) -> dict[str, Any]:
    """Aggregate full decision traces into actionable failure counters."""
    flags: Counter[str] = Counter()
    actions: Counter[str] = Counter()
    transitions: Counter[str] = Counter()
    for match in matches:
        for decision in match.decisions:
            flags.update(decision.failure_flags)
            selected = decision.selected_indices
            options = decision.options
            for index in selected:
                if 0 <= index < len(options):
                    option_type = options[index].get("type")
                    actions[str(option_type)] += 1
            effects = decision.transition
            transitions.update(
                {
                    "target_kos": int(bool(effects.get("target_ko"))),
                    "observed_target_damage": int(effects.get("target_damage", 0) or 0),
                    "active_ko_taken": int(bool(effects.get("own_active_ko"))),
                }
            )
    return {
        "decision_failure_flags": dict(flags),
        "selected_option_types": dict(actions),
        "transition_totals": dict(transitions),
    }
