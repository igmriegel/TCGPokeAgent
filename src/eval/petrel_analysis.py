"""State-based audit of Petrel choices against Supporters already in hand."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from src.eval.archer_analysis import CARD_NAMES

PETREL = 1219
ARIANA = 1216
PROTON = 1220
SUPPORTERS = {1216, 1217, 1218, 1219, 1220}


def _card_id(value: Any) -> int:
    """Return a card ID from a public card mapping."""
    if isinstance(value, Mapping):
        value = value.get("id", value.get("cardId", 0))
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _hand(state: Mapping[str, Any]) -> list[int]:
    """Return public hand IDs for the acting player."""
    players = state.get("players", [])
    index = state.get("yourIndex", 0)
    if not isinstance(players, list) or not isinstance(index, int) or index >= len(players):
        return []
    player = players[index]
    cards = player.get("hand", []) if isinstance(player, Mapping) else []
    return [_card_id(card) for card in cards if isinstance(card, Mapping)]


def _reasons(event: Mapping[str, Any]) -> list[str]:
    """Return final policy reasons from a decision trace."""
    ranked = (event.get("decision_trace") or {}).get("ranked_scores", [])
    if isinstance(ranked, list) and ranked and isinstance(ranked[0], list):
        reasons = ranked[0][-1]
        return [str(reason) for reason in reasons] if isinstance(reasons, list) else []
    return []


def analyze_petrel_decision(
    match: Mapping[str, Any], event: Mapping[str, Any]
) -> dict[str, Any] | None:
    """Analyze one selected Petrel decision and its visible alternatives."""
    selected = event.get("selected_card_ids", [])
    if not isinstance(selected, list) or PETREL not in selected:
        return None
    before = event.get("state_before", {})
    if not isinstance(before, Mapping):
        return None
    hand = _hand(before)
    reasons = _reasons(event)
    supporters = [card_id for card_id in hand if card_id in SUPPORTERS and card_id != PETREL]
    ariana_refresh_signal = (
        ARIANA in hand
        and "petrel_target_Team Rocket's Ariana" in reasons
        and "ariana_hand_refresh_and_energy_access" in reasons
    )
    proton_deferred_signal = PROTON in hand and "petrel_only_target_is_deferred_proton" in reasons
    return {
        "match_id": match.get("match_id"),
        "result": match.get("result"),
        "agent_side": match.get("agent_side"),
        "turn": event.get("turn"),
        "hand_card_ids": hand,
        "hand_count": len(hand),
        "supporters_in_hand": [
            {"card_id": card_id, "name": CARD_NAMES.get(card_id, str(card_id))}
            for card_id in supporters
        ],
        "ariana_in_hand": ARIANA in hand,
        "proton_in_hand": PROTON in hand,
        "energy_cards_in_hand": event.get("energy_cards_in_hand", 0),
        "active_card_id": event.get("active_card_id", 0),
        "active_energy_count": event.get("active_energy_count", 0),
        "bench_count": event.get("bench_count", 0),
        "opponent_hand_count": _opponent_hand_count(before),
        "selection_reasons": reasons,
        "ariana_refresh_signal": ariana_refresh_signal,
        "proton_deferred_signal": proton_deferred_signal,
        "other_supporter_in_hand": bool(supporters),
        "flags": {
            "loss": match.get("result") == "loss",
            "potential_ariana_substitution": ariana_refresh_signal,
            "potential_proton_setup_substitution": proton_deferred_signal,
        },
    }


def _opponent_hand_count(state: Mapping[str, Any]) -> int:
    """Return public opponent hand size."""
    players = state.get("players", [])
    index = state.get("yourIndex", 0)
    if not isinstance(players, list) or not isinstance(index, int) or len(players) < 2:
        return 0
    opponent = players[1 - index]
    if not isinstance(opponent, Mapping):
        return 0
    hand = opponent.get("hand")
    return len(hand) if isinstance(hand, list) else int(opponent.get("handCount", 0) or 0)


def _outcomes(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Count outcomes in a sample."""
    counts = Counter(row.get("result", "unknown") for row in rows)
    return {key: counts.get(key, 0) for key in ("win", "loss", "draw")}


def analyze_matches(matches: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate Petrel substitutions and outcome correlations."""
    rows = [
        row
        for match in matches
        for event in match.get("events", [])
        if isinstance(event, Mapping)
        for row in [analyze_petrel_decision(match, event)]
        if row is not None
    ]
    ariana = [row for row in rows if row["ariana_refresh_signal"]]
    proton = [row for row in rows if row["proton_deferred_signal"]]
    with_other = [row for row in rows if row["other_supporter_in_hand"]]
    reason_counts = Counter(reason for row in rows for reason in row["selection_reasons"])
    return {
        "report_type": "petrel_decision_audit_v1",
        "petrel_plays": len(rows),
        "outcomes": _outcomes(rows),
        "petrel_with_other_supporter_in_hand": len(with_other),
        "ariana_already_in_hand_refresh_signal": {
            "count": len(ariana),
            "outcomes": _outcomes(ariana),
        },
        "proton_already_in_hand_deferred_setup_signal": {
            "count": len(proton),
            "outcomes": _outcomes(proton),
        },
        "selection_reasons": dict(reason_counts),
        "rows": rows,
    }


def load_matches(report_path: Path) -> list[dict[str, Any]]:
    """Load full match events from a JSON report or its compressed trace."""
    import gzip

    report = json.loads(report_path.read_text(encoding="utf-8"))
    trace_path = Path(report["trace_jsonl"])
    if not trace_path.is_absolute():
        trace_path = report_path.parent / trace_path
    with gzip.open(trace_path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]
