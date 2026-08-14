"""Tests for Petrel substitution analysis."""

from __future__ import annotations

from src.eval.petrel_analysis import analyze_matches


def _event() -> dict:
    """Build a Petrel decision with Ariana and Proton already in hand."""
    return {
        "turn": 10,
        "selected_card_ids": [1219],
        "energy_cards_in_hand": 0,
        "active_card_id": 891,
        "active_energy_count": 0,
        "bench_count": 2,
        "state_before": {
            "yourIndex": 0,
            "players": [
                {"hand": [{"id": 1219}, {"id": 1216}, {"id": 1220}]},
                {"hand": [{"id": 1}] * 8},
            ],
        },
        "decision_trace": {
            "ranked_scores": [
                [
                    [0],
                    1000.0,
                    [
                        "petrel_target_Team Rocket's Ariana",
                        "ariana_hand_refresh_and_energy_access",
                    ],
                ]
            ]
        },
    }


def test_petrel_flags_existing_ariana_and_deferred_proton() -> None:
    """Petrel alternatives are counted only with matching trace signals."""
    report = analyze_matches([{"match_id": "m1", "result": "loss", "events": [_event()]}])

    assert report["petrel_plays"] == 1
    assert report["ariana_already_in_hand_refresh_signal"]["count"] == 1
    assert report["proton_already_in_hand_deferred_setup_signal"]["count"] == 0
