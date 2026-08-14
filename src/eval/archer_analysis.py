"""State-based audit helpers for observed Archer decisions."""

from __future__ import annotations

import gzip
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

ARCHER = 1217
ENERGY_IDS = {15, 17}
ITEM_IDS = {1077, 1097, 1109, 1121, 1134, 1137, 1152, 1257}
ROCKET_SUPPORTER_IDS = {1216, 1217, 1218, 1219, 1220}
LARGE_HAND_THRESHOLD = 8
SUPPORTER_TOTALS = {1216: 4, 1217: 4, 1218: 4, 1219: 4, 1220: 4}
ENERGY_TOTALS = {15: 4, 17: 4}
CARD_NAMES = {
    414: "Articuno",
    463: "Murkrow",
    473: "Porygon",
    474: "Porygon2",
    891: "Honchkrow",
    15: "Rocket Energy",
    17: "Ignition Energy",
    1077: "Roto-Stick",
    1097: "Night Stretcher",
    1109: "Miracle Headset",
    1121: "Ultra Ball",
    1134: "Team Rocket's Transceiver",
    1137: "Tool Scrapper",
    1152: "Poké Pad",
    1216: "Team Rocket's Ariana",
    1217: "Team Rocket's Archer",
    1218: "Team Rocket's Giovanni",
    1219: "Team Rocket's Petrel",
    1220: "Team Rocket's Proton",
    1257: "Team Rocket's Factory",
}


def _card_id(value: Any) -> int:
    """Return a numeric card ID from a public card mapping."""
    if isinstance(value, Mapping):
        raw = value.get("id", value.get("cardId", 0))
        try:
            return int(raw)
        except (TypeError, ValueError):
            return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _mean(values: list[int]) -> float | None:
    """Return a rounded mean, or ``None`` for an empty sample."""
    return round(sum(values) / len(values), 3) if values else None


def _percentile(values: list[int], fraction: float) -> float | None:
    """Return a nearest-rank percentile for a non-empty integer sample."""
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))
    return float(ordered[index])


def _hand(state: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Return the policy player's public hand from a state snapshot."""
    players = state.get("players", [])
    index = state.get("yourIndex", 0)
    if not isinstance(players, list) or not isinstance(index, int) or index >= len(players):
        return []
    player = players[index]
    cards = player.get("hand", []) if isinstance(player, Mapping) else []
    return [card for card in cards if isinstance(card, Mapping)] if isinstance(cards, list) else []


def _opponent_hand_count(state: Mapping[str, Any]) -> int:
    """Return the public opponent hand count, preferring cards over metadata."""
    players = state.get("players", [])
    index = state.get("yourIndex", 0)
    if not isinstance(players, list) or not isinstance(index, int) or len(players) < 2:
        return 0
    opponent = players[1 - index]
    if not isinstance(opponent, Mapping):
        return 0
    cards = opponent.get("hand")
    if isinstance(cards, list):
        return len(cards)
    return int(opponent.get("handCount", 0) or 0)


def _candidate_cards(event: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return non-Archer playable cards surviving the final decision ranking."""
    trace = event.get("decision_trace")
    if not isinstance(trace, Mapping):
        return []
    ranked = trace.get("ranked_scores", [])
    ranked_indices = {
        int(row[0][0]): row[1]
        for row in ranked
        if isinstance(row, list)
        and len(row) >= 1
        and isinstance(row[0], list)
        and row[0]
        and isinstance(row[0][0], int)
    }
    result: list[dict[str, Any]] = []
    for candidate in trace.get("candidates", []):
        if not isinstance(candidate, Mapping):
            continue
        option_index = candidate.get("option_index")
        card_id = _card_id(candidate.get("card", {}))
        if (
            isinstance(option_index, int)
            and card_id
            and card_id != ARCHER
            and candidate.get("option_type") == "PLAY"
        ):
            result.append(
                {
                    "card_id": card_id,
                    "name": CARD_NAMES.get(card_id, str(card_id)),
                    "score": ranked_indices.get(option_index),
                }
            )
    return result


def _candidate_cards_with_id(event: Mapping[str, Any], card_id: int) -> list[dict[str, Any]]:
    """Return generated PLAY candidates for one card ID, including filtered candidates."""
    trace = event.get("decision_trace")
    if not isinstance(trace, Mapping):
        return []
    return [
        {
            "card_id": card_id,
            "name": CARD_NAMES.get(card_id, str(card_id)),
            "option_index": candidate.get("option_index"),
        }
        for candidate in trace.get("candidates", [])
        if isinstance(candidate, Mapping)
        and candidate.get("option_type") == "PLAY"
        and _card_id(candidate.get("card", {})) == card_id
    ]


def _selected_supporters(event: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return Supporter cards selected in a main/supporter decision."""
    return [
        {"card_id": card_id, "name": CARD_NAMES.get(card_id, str(card_id))}
        for card_id in event.get("selected_card_ids", [])
        if isinstance(card_id, int) and card_id in ROCKET_SUPPORTER_IDS and card_id != ARCHER
    ]


def _hand_composition(hand_ids: list[int]) -> dict[str, Any]:
    """Summarize Supporters, Energy, Items, and individual known cards in hand."""
    counts = Counter(hand_ids)
    supporters = [card_id for card_id in hand_ids if card_id in ROCKET_SUPPORTER_IDS]
    energy = [card_id for card_id in hand_ids if card_id in ENERGY_IDS]
    items = [card_id for card_id in hand_ids if card_id in ITEM_IDS]
    return {
        "hand_count": len(hand_ids),
        "supporter_count": len(supporters),
        "energy_count": len(energy),
        "item_count": len(items),
        "supporters_in_hand": dict(Counter(supporters)),
        "energy_in_hand": dict(Counter(energy)),
        "items_in_hand": dict(Counter(items)),
        "cards_in_hand": {
            str(card_id): {
                "card_id": card_id,
                "name": CARD_NAMES.get(card_id, str(card_id)),
                "copies": count,
            }
            for card_id, count in sorted(counts.items())
        },
    }


def _pokemon_snapshot(pokemon: Any) -> dict[str, Any]:
    """Return the public strategic fields for one Pokémon in play."""
    if isinstance(pokemon, list):
        pokemon = pokemon[0] if pokemon else None
    if not isinstance(pokemon, Mapping):
        return {"card_id": 0, "hp": 0, "energy_count": 0, "energy_ids": []}
    energies = pokemon.get("energyCards", pokemon.get("energies", []))
    energy_list = energies if isinstance(energies, list) else []
    return {
        "card_id": _card_id(pokemon),
        "hp": int(pokemon.get("hp", 0) or 0),
        "max_hp": int(pokemon.get("maxHp", pokemon.get("maxHP", 0)) or 0),
        "energy_count": len(energy_list),
        "energy_ids": [_card_id(energy) for energy in energy_list],
    }


def _board_snapshot(state: Mapping[str, Any]) -> dict[str, Any]:
    """Return a factual snapshot of both boards before an Archer decision."""
    players = state.get("players", [])
    index = state.get("yourIndex", 0)
    if not isinstance(players, list) or not isinstance(index, int) or len(players) < 2:
        return {"own": {}, "opponent": {}}

    def player_board(player: Any) -> dict[str, Any]:
        if not isinstance(player, Mapping):
            return {}
        bench = player.get("bench", [])
        bench_cards = bench if isinstance(bench, list) else []
        active = _pokemon_snapshot(player.get("active"))
        bench_snapshots = [
            _pokemon_snapshot(pokemon) for pokemon in bench_cards if isinstance(pokemon, Mapping)
        ]
        return {
            "active": active,
            "bench": bench_snapshots,
            "bench_count": len(bench_snapshots),
            "pokemon_in_play": len(bench_snapshots) + int(active["card_id"] != 0),
            "total_energy_in_play": active["energy_count"]
            + sum(item["energy_count"] for item in bench_snapshots),
        }

    return {"own": player_board(players[index]), "opponent": player_board(players[1 - index])}


def _resource_zones(state: Mapping[str, Any]) -> dict[str, Any]:
    """Return observed hand/discard and inferred deck ranges for resources."""
    players = state.get("players", [])
    index = state.get("yourIndex", 0)
    if not isinstance(players, list) or not isinstance(index, int) or index >= len(players):
        return {}
    player = players[index]
    if not isinstance(player, Mapping):
        return {}
    hand = [_card_id(card) for card in player.get("hand", []) if isinstance(card, Mapping)]
    discard = [_card_id(card) for card in player.get("discard", []) if isinstance(card, Mapping)]
    prizes = player.get("prize", [])
    prize_cards = prizes if isinstance(prizes, list) else []
    known_prizes = [_card_id(card) for card in prize_cards if card is not None]
    hidden_prizes = sum(card is None for card in prize_cards)
    board = _board_snapshot(state).get("own", {})
    attached_energy_ids = [
        energy_id
        for pokemon in [board.get("active", {}), *board.get("bench", [])]
        if isinstance(pokemon, Mapping)
        for energy_id in pokemon.get("energy_ids", [])
    ]
    result: dict[str, Any] = {
        "hidden_prize_slots": hidden_prizes,
        "supporters": {},
        "energy": {},
    }
    for label, totals in (("supporters", SUPPORTER_TOTALS), ("energy", ENERGY_TOTALS)):
        for card_id, total in totals.items():
            hand_count = hand.count(card_id)
            discard_count = discard.count(card_id)
            prize_count = known_prizes.count(card_id)
            attached_count = attached_energy_ids.count(card_id) if label == "energy" else 0
            deck_upper = max(0, total - hand_count - discard_count - prize_count - attached_count)
            result[label][str(card_id)] = {
                "card_id": card_id,
                "name": CARD_NAMES.get(card_id, str(card_id)),
                "hand": hand_count,
                "discard": discard_count,
                "deck_inferred_min": max(0, deck_upper - hidden_prizes),
                "deck_inferred_max": deck_upper,
                "known_prize": prize_count,
            }
    return result


def _resource_zone_summary(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate means and totals for resource zones across decisions."""
    materialized_rows = [row for row in rows if row.get("resource_zones")]
    summary: dict[str, Any] = {"observations": len(materialized_rows)}
    for label in ("supporters", "energy"):
        entries = [
            item for row in materialized_rows for item in row["resource_zones"][label].values()
        ]
        summary[label] = {
            "hand_total": sum(item["hand"] for item in entries),
            "discard_total": sum(item["discard"] for item in entries),
            "mean_hand": _mean([item["hand"] for item in entries]),
            "mean_discard": _mean([item["discard"] for item in entries]),
            "mean_deck_inferred_min": _mean([item["deck_inferred_min"] for item in entries]),
            "mean_deck_inferred_max": _mean([item["deck_inferred_max"] for item in entries]),
            "cards": {
                card_key: {
                    "card_id": card_rows[0]["card_id"],
                    "name": card_rows[0]["name"],
                    "hand_total": sum(item["hand"] for item in card_rows),
                    "discard_total": sum(item["discard"] for item in card_rows),
                    "mean_hand": _mean([item["hand"] for item in card_rows]),
                    "mean_discard": _mean([item["discard"] for item in card_rows]),
                    "mean_deck_inferred_min": _mean(
                        [item["deck_inferred_min"] for item in card_rows]
                    ),
                    "mean_deck_inferred_max": _mean(
                        [item["deck_inferred_max"] for item in card_rows]
                    ),
                }
                for card_key in {item["card_id"] for item in entries}
                for card_rows in [[item for item in entries if item["card_id"] == card_key]]
            },
        }
    return summary


def _board_summary(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate board states observed at Archer decisions."""
    materialized_rows = list(rows)
    if not materialized_rows:
        return {
            "observations": 0,
            "active_cards": {},
            "bench_counts": {},
            "mean_energy_in_play": None,
        }
    active_cards = Counter(
        str(row["board_state"]["own"]["active"]["card_id"])
        for row in materialized_rows
        if row["board_state"].get("own")
    )
    active_card_names = Counter(
        CARD_NAMES.get(row["board_state"]["own"]["active"]["card_id"], "Empty")
        for row in materialized_rows
        if row["board_state"].get("own")
    )
    bench_counts = Counter(
        row["board_state"]["own"].get("bench_count", 0)
        for row in materialized_rows
        if row["board_state"].get("own")
    )
    energy_counts = [
        row["board_state"]["own"].get("total_energy_in_play", 0)
        for row in materialized_rows
        if row["board_state"].get("own")
    ]
    return {
        "observations": len(materialized_rows),
        "active_cards": dict(active_cards),
        "active_card_names": dict(active_card_names),
        "bench_counts": dict(bench_counts),
        "mean_energy_in_play": _mean(energy_counts),
    }


def _composition_summary(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate hand composition observations for a decision sample."""
    materialized_rows = list(rows)
    if not materialized_rows:
        return {
            "observations": 0,
            "mean_hand_count": None,
            "mean_supporter_count": None,
            "mean_energy_count": None,
            "mean_item_count": None,
            "cards": {},
        }
    compositions = [row["hand_composition"] for row in materialized_rows]
    card_stats: dict[str, dict[str, Any]] = {}
    for composition in compositions:
        for card_key, card in composition["cards_in_hand"].items():
            stat = card_stats.setdefault(
                card_key,
                {"card_id": card["card_id"], "name": card["name"], "times_present": 0, "copies": 0},
            )
            stat["times_present"] += 1
            stat["copies"] += card["copies"]
    for stat in card_stats.values():
        stat["mean_copies_when_observed"] = round(stat["copies"] / len(materialized_rows), 3)
    return {
        "observations": len(materialized_rows),
        "mean_hand_count": _mean([item["hand_count"] for item in compositions]),
        "mean_supporter_count": _mean([item["supporter_count"] for item in compositions]),
        "mean_energy_count": _mean([item["energy_count"] for item in compositions]),
        "mean_item_count": _mean([item["item_count"] for item in compositions]),
        "cards": dict(sorted(card_stats.items(), key=lambda item: item[1]["name"])),
    }


def _card_breakdown(rows: Iterable[Mapping[str, Any]], card_ids: set[int]) -> dict[str, Any]:
    """Count named cards in hand with outcome and copy breakdowns."""
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        hand_ids = row["hand_card_ids"]
        counts = Counter(card_id for card_id in hand_ids if card_id in card_ids)
        for card_id, copies in counts.items():
            key = str(card_id)
            stat = result.setdefault(
                key,
                {
                    "card_id": card_id,
                    "name": CARD_NAMES.get(card_id, str(card_id)),
                    "times_present": 0,
                    "total_copies": 0,
                    "wins": 0,
                    "losses": 0,
                    "win_copies": 0,
                    "loss_copies": 0,
                },
            )
            stat["times_present"] += 1
            stat["total_copies"] += copies
            if row["result"] == "win":
                stat["wins"] += 1
                stat["win_copies"] += copies
            elif row["result"] == "loss":
                stat["losses"] += 1
                stat["loss_copies"] += copies
    return dict(sorted(result.items(), key=lambda item: str(item[1]["name"])))


def _outcome_counts(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Count wins, losses, and draws in a decision sample."""
    counts = Counter(str(row.get("result", "unknown")) for row in rows)
    return {key: counts.get(key, 0) for key in ("win", "loss", "draw")}


def analyze_archer_decision(
    match: Mapping[str, Any], event: Mapping[str, Any]
) -> dict[str, Any] | None:
    """Analyze one observed Archer selection from a CABT event trace.

    Args:
        match: Match record containing the event's result.
        event: Decision event with public state and decision trace.

    Returns:
        A JSON-serializable audit row, or ``None`` when Archer was not selected.
    """
    selected_ids = event.get("selected_card_ids", [])
    if not isinstance(selected_ids, list) or ARCHER not in selected_ids:
        return None
    before = event.get("state_before", {})
    after = event.get("state_after", {})
    if not isinstance(before, Mapping):
        before = {}
    if not isinstance(after, Mapping):
        after = {}
    hand_ids = [_card_id(card) for card in _hand(before)]
    energy_ids = [card_id for card_id in hand_ids if card_id in ENERGY_IDS]
    item_ids = [card_id for card_id in hand_ids if card_id in ITEM_IDS]
    composition = _hand_composition(hand_ids)
    board_state = _board_snapshot(before)
    resource_zones = _resource_zones(before)
    alternatives = _candidate_cards(event)
    trace = event.get("decision_trace", {}) or {}
    selected_indices = trace.get("selected_indices", []) if isinstance(trace, Mapping) else []
    archer_rank = next(
        (
            row
            for row in trace.get("ranked_scores", [])
            if isinstance(row, list) and row and row[0] == selected_indices
        ),
        None,
    )
    archer_score = (
        archer_rank[1] if isinstance(archer_rank, list) and len(archer_rank) > 1 else None
    )
    legal_alternatives = alternatives
    better_options = [
        option
        for option in alternatives
        if archer_score is not None
        and isinstance(option["score"], (int, float))
        and option["score"] > archer_score
    ]
    opponent_before = _opponent_hand_count(before)
    opponent_after = _opponent_hand_count(after) if after else None
    playable_items = [item for item in legal_alternatives if item["card_id"] in ITEM_IDS]
    energy_attachable = bool(event.get("energy_attachable")) and bool(energy_ids)
    option_classes = sorted(
        {"item" if item["card_id"] in ITEM_IDS else "supporter" for item in better_options}
    )
    return {
        "match_id": match.get("match_id"),
        "result": match.get("result"),
        "agent_side": match.get("agent_side"),
        "turn": event.get("turn"),
        "decision_phase": event.get("decision_phase"),
        "opponent_hand_count_before": opponent_before,
        "opponent_hand_count_after": opponent_after,
        "opponent_hand_reduction": (
            opponent_before - opponent_after if isinstance(opponent_after, int) else None
        ),
        "hand_card_ids": hand_ids,
        "hand_composition": composition,
        "board_state": board_state,
        "resource_zones": resource_zones,
        "energy_ids_in_hand": energy_ids,
        "energy_attachable": energy_attachable,
        "items_in_hand": [
            {"card_id": card_id, "name": CARD_NAMES.get(card_id, str(card_id))}
            for card_id in item_ids
        ],
        "playable_items": playable_items,
        "legal_alternatives": legal_alternatives,
        "better_options": better_options,
        "better_option_classes": option_classes,
        "archer_score": archer_score,
        "selection_reasons": (
            ((event.get("decision_trace", {}) or {}).get("ranked_scores", [[]])[0][-1])
            if (event.get("decision_trace", {}) or {}).get("ranked_scores")
            else []
        ),
        "flags": {
            "loss": match.get("result") == "loss",
            "energy_opportunity": energy_attachable,
            "opponent_hand_small": opponent_before <= 3,
            "item_opportunity": bool(playable_items),
        },
    }


def analyze_archer_omission(
    match: Mapping[str, Any], event: Mapping[str, Any]
) -> dict[str, Any] | None:
    """Analyze a legal Archer opportunity that was declined.

    A declined opportunity is generated only for a PLAY_SUPPORTER decision in
    which Archer was in the public hand and CABT generated Archer as a legal
    option. This is evidence of an available line, not proof that it would
    have won the game.
    """
    if event.get("decision_phase") != "PLAY_SUPPORTER":
        return None
    selected_ids = event.get("selected_card_ids", [])
    if not isinstance(selected_ids, list) or ARCHER in selected_ids:
        return None
    before = event.get("state_before", {})
    if not isinstance(before, Mapping):
        return None
    hand_ids = [_card_id(card) for card in _hand(before)]
    archer_in_hand = hand_ids.count(ARCHER)
    archer_candidates = _candidate_cards_with_id(event, ARCHER)
    if not archer_in_hand or not archer_candidates:
        return None
    energy_ids = [card_id for card_id in hand_ids if card_id in ENERGY_IDS]
    hand_count = len(hand_ids)
    selected_supporters = _selected_supporters(event)
    composition = _hand_composition(hand_ids)
    board_state = _board_snapshot(before)
    resource_zones = _resource_zones(before)
    no_energy = not energy_ids
    large_hand_no_energy = hand_count >= LARGE_HAND_THRESHOLD and no_energy
    return {
        "match_id": match.get("match_id"),
        "result": match.get("result"),
        "agent_side": match.get("agent_side"),
        "turn": event.get("turn"),
        "hand_count": hand_count,
        "hand_card_ids": hand_ids,
        "hand_composition": composition,
        "board_state": board_state,
        "resource_zones": resource_zones,
        "archer_count_in_hand": archer_in_hand,
        "archer_candidates": archer_candidates,
        "energy_ids_in_hand": energy_ids,
        "energy_count": len(energy_ids),
        "no_energy_in_hand": no_energy,
        "large_hand": hand_count >= LARGE_HAND_THRESHOLD,
        "large_hand_no_energy": large_hand_no_energy,
        "selected_supporters": selected_supporters,
        "selected_card_ids": selected_ids,
        "opponent_hand_count": _opponent_hand_count(before),
        "selection_reasons": (
            ((event.get("decision_trace", {}) or {}).get("ranked_scores", [[]])[0][-1])
            if (event.get("decision_trace", {}) or {}).get("ranked_scores")
            else []
        ),
        "flags": {
            "loss": match.get("result") == "loss",
            "post_ko_eligible": True,
            "post_ko_large_hand_no_energy": large_hand_no_energy,
            "other_supporter_played": bool(selected_supporters),
        },
    }


def analyze_matches(matches: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate Archer decisions, resource misses, and opponent hand size."""
    materialized_matches = list(matches)
    rows = [
        row
        for match in materialized_matches
        for event in match.get("events", [])
        if isinstance(event, Mapping)
        for row in [analyze_archer_decision(match, event)]
        if row is not None
    ]
    omissions = [
        row
        for match in materialized_matches
        for event in match.get("events", [])
        if isinstance(event, Mapping)
        for row in [analyze_archer_omission(match, event)]
        if row is not None
    ]
    opponent_hands = [row["opponent_hand_count_before"] for row in rows]
    energy_rows = [row for row in rows if row["energy_attachable"]]
    item_rows = [row for row in rows if row["playable_items"]]
    better_rows = [row for row in rows if row["better_options"]]
    played_losses = [row for row in rows if row["result"] == "loss"]
    played_loss_energy = [row for row in played_losses if row["energy_attachable"]]
    played_loss_better = [row for row in played_losses if row["better_options"]]
    played_loss_small_opponent = [
        row for row in played_losses if row["opponent_hand_count_before"] <= 3
    ]
    omission_focus = [row for row in omissions if row["large_hand_no_energy"]]
    omission_focus_losses = [row for row in omission_focus if row["result"] == "loss"]
    omission_focus_wins = [row for row in omission_focus if row["result"] == "win"]
    matches_with_played_loss = {row["match_id"] for row in played_losses}
    matches_with_omission_focus = {row["match_id"] for row in omission_focus}
    omission_by_supporter: dict[str, dict[str, int]] = {}
    for row in omissions:
        names = [item["name"] for item in row["selected_supporters"]] or ["Non-supporter"]
        for name in names:
            bucket = omission_by_supporter.setdefault(
                name, {"all": 0, "wins": 0, "losses": 0, "large_hand_no_energy_losses": 0}
            )
            bucket["all"] += 1
            bucket["wins"] += row["result"] == "win"
            bucket["losses"] += row["result"] == "loss"
            bucket["large_hand_no_energy_losses"] += (
                row["large_hand_no_energy"] and row["result"] == "loss"
            )
    played_loss_reasons = Counter(
        reason for row in played_losses for reason in row["selection_reasons"]
    )
    item_counts = Counter(item["name"] for row in rows for item in row["items_in_hand"])
    hand_distribution = Counter(
        "0-2" if count <= 2 else "3-5" if count <= 5 else "6-8" if count <= 8 else "9+"
        for count in opponent_hands
    )
    return {
        "report_type": "archer_decision_audit_v2",
        "archer_plays": len(rows),
        "archer_with_better_option": len(better_rows),
        "archer_with_attachable_energy": len(energy_rows),
        "archer_with_playable_item": len(item_rows),
        "hand_composition": {
            "archer_played": _composition_summary(rows),
            "archer_omitted": _composition_summary(omissions),
            "archer_omitted_large_hand_no_energy": _composition_summary(omission_focus),
        },
        "item_breakdown": {
            "archer_played": _card_breakdown(rows, ITEM_IDS),
            "archer_omitted": _card_breakdown(omissions, ITEM_IDS),
            "archer_omitted_large_hand_no_energy": _card_breakdown(omission_focus, ITEM_IDS),
        },
        "board_state": {
            "archer_played": _board_summary(rows),
            "archer_omitted": _board_summary(omissions),
            "archer_omitted_large_hand_no_energy": _board_summary(omission_focus),
        },
        "resource_zones": {
            "archer_played": _resource_zone_summary(rows),
            "archer_omitted": _resource_zone_summary(omissions),
            "archer_omitted_large_hand_no_energy": _resource_zone_summary(omission_focus),
        },
        "played_outcomes": {
            "all": _outcome_counts(rows),
            "losses_with_attachable_energy": len(played_loss_energy),
            "losses_with_better_option": len(played_loss_better),
            "losses_with_opponent_hand_3_or_less": len(played_loss_small_opponent),
            "potentially_negative_loss_rows": sum(
                row["energy_attachable"] or bool(row["better_options"]) for row in played_losses
            ),
        },
        "omitted_archer": {
            "all_opportunities": len(omissions),
            "outcomes": _outcome_counts(omissions),
            "with_large_hand_no_energy": len(omission_focus),
            "large_hand_no_energy_outcomes": {
                "win": len(omission_focus_wins),
                "loss": len(omission_focus_losses),
                "draw": sum(row["result"] == "draw" for row in omission_focus),
            },
            "large_hand_no_energy_and_other_supporter": sum(
                bool(row["selected_supporters"]) for row in omission_focus
            ),
            "matches_with_opportunity": len(matches_with_omission_focus),
            "by_selected_supporter": omission_by_supporter,
        },
        "cross_correlation": {
            "matches_with_archer_play_in_loss": len(matches_with_played_loss),
            "matches_with_omitted_large_hand_no_energy": len(matches_with_omission_focus),
            "matches_with_both": len(matches_with_played_loss & matches_with_omission_focus),
            "played_loss_selection_reasons": dict(played_loss_reasons),
        },
        "opponent_hand": {
            "mean_before": _mean(opponent_hands),
            "median_before": _percentile(opponent_hands, 0.5),
            "minimum_before": min(opponent_hands) if opponent_hands else None,
            "maximum_before": max(opponent_hands) if opponent_hands else None,
            "p25_before": _percentile(opponent_hands, 0.25),
            "p75_before": _percentile(opponent_hands, 0.75),
            "distribution": dict(hand_distribution),
            "mean_reduction": _mean(
                [
                    row["opponent_hand_reduction"]
                    for row in rows
                    if isinstance(row["opponent_hand_reduction"], int)
                ]
            ),
        },
        "item_counts_in_hand": dict(item_counts),
        "rows": rows,
        "omission_rows": omissions,
    }


def load_matches(report_path: Path) -> list[dict[str, Any]]:
    """Load match records from an evaluation report or compressed trace."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if isinstance(report.get("matches"), list) and any(
        isinstance(match, Mapping) and isinstance(match.get("events"), list)
        for match in report["matches"]
    ):
        return [match for match in report["matches"] if isinstance(match, dict)]
    trace_path = Path(report["trace_jsonl"])
    if not trace_path.is_absolute():
        trace_path = report_path.parent / trace_path
    opener = gzip.open if trace_path.suffix == ".gz" else open
    with opener(trace_path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]
