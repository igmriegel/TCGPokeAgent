"""Tests for Giovanni replay sequencing analysis."""

from __future__ import annotations

import json

from src.eval.giovanni_analysis import analyze_submission, combined_to_dict


def test_giovanni_audit_detects_basic_without_energy_and_missing_follow_up(tmp_path) -> None:
    """Detect a Giovanni promotion that had Energy but no same-turn development."""
    replay_dir = tmp_path / "remote" / "123"
    replay_dir.mkdir(parents=True)
    replay = {
        "info": {
            "EpisodeId": 9,
            "Agents": [{"Name": "mudkip_mini_chicken"}, {"Name": "opponent"}],
        },
        "rewards": [1, -1],
        "steps": [
            [
                {
                    "visualize": [
                        {
                            "current": {
                                "turn": 2,
                                "players": [
                                    {
                                        "active": [
                                            {
                                                "id": 463,
                                                "serial": 3,
                                                "preEvolution": [],
                                                "energyCards": [],
                                            }
                                        ],
                                        "hand": [{"id": 15, "name": "Team Rocket's Energy"}],
                                    },
                                    {"active": [], "bench": []},
                                ],
                            },
                            "logs": [
                                {
                                    "cardId": 1218,
                                    "playerIndex": 0,
                                    "serial": 1,
                                    "type": "MoveCard",
                                    "fromArea": 2,
                                    "toArea": 3,
                                }
                            ],
                        },
                        {"current": {"turn": 3}, "logs": []},
                    ],
                }
            ]
        ],
    }
    (replay_dir / "episode-9-replay.json").write_text(json.dumps(replay))

    audit = analyze_submission("123", tmp_path)

    assert len(audit.zero_energy_unevolved) == 1
    event = audit.zero_energy_unevolved[0]
    assert event.energy_in_hand == 1
    assert not event.evolution_in_hand
    assert combined_to_dict([audit])["zero_energy_unevolved_followed_by_same_turn_attach"] == 0
