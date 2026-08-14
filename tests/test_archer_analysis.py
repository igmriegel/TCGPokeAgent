"""Tests for state-based Archer decision analysis."""

from __future__ import annotations

from src.eval.archer_analysis import analyze_matches


def _event(*, selected: bool, opponent_hand: int, energy: bool = False) -> dict:
    """Build a minimal public Archer decision event."""
    hand = [{"id": 1217}, {"id": 17}, {"id": 1097}, {"id": 1257}]
    return {
        "turn": 4,
        "decision_phase": "PLAY_SUPPORTER",
        "selected_card_ids": [1217] if selected else [1218],
        "energy_attachable": energy,
        "state_before": {
            "yourIndex": 0,
            "players": [{"hand": hand}, {"hand": [{"id": 1}] * opponent_hand}],
        },
        "state_after": {
            "yourIndex": 0,
            "players": [{"hand": hand}, {"hand": [{"id": 1}] * 3}],
        },
        "decision_trace": {
            "selected_indices": [1],
            "candidates": [
                {"option_index": 0, "option_type": "PLAY", "card": {"id": 1097}},
                {"option_index": 1, "option_type": "PLAY", "card": {"id": 1217}},
            ],
            "ranked_scores": [
                [[0], 900.0, ["productive_item"]],
                [[1], 780.0, ["archer"]],
            ],
        },
    }


def test_archer_audit_counts_resources_and_opponent_hand() -> None:
    """The audit separates hand resources from attachable energy and records hand size."""
    report = analyze_matches(
        [
            {
                "match_id": "m1",
                "result": "loss",
                "agent_side": 0,
                "events": [_event(selected=True, opponent_hand=7, energy=True)],
            }
        ]
    )

    assert report["archer_plays"] == 1
    assert report["archer_with_better_option"] == 1
    assert report["archer_with_attachable_energy"] == 1
    assert report["archer_with_playable_item"] == 1
    assert report["opponent_hand"]["mean_before"] == 7.0
    assert report["opponent_hand"]["mean_reduction"] == 4.0
    assert report["item_counts_in_hand"]["Night Stretcher"] == 1
    assert report["hand_composition"]["archer_played"]["mean_supporter_count"] == 1.0
    assert report["board_state"]["archer_played"]["observations"] == 1
    zones = report["resource_zones"]["archer_played"]
    assert zones["supporters"]["cards"][1217]["hand_total"] == 1
    assert zones["energy"]["cards"][17]["hand_total"] == 1


def test_non_archer_decisions_are_excluded() -> None:
    """Only an actually selected Archer play becomes an audit row."""
    report = analyze_matches(
        [{"match_id": "m1", "result": "win", "events": [_event(selected=False, opponent_hand=5)]}]
    )

    assert report["archer_plays"] == 0
