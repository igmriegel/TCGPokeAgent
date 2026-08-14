"""Tests for the recent Tool Scrapper replay audit."""

from __future__ import annotations

import json

from src.eval.tool_scrapper_analysis import analyze_submission, combined_to_dict


def test_analyze_submission_counts_effective_scrapper_and_public_tools(tmp_path) -> None:
    """Count a played Scrapper separately from a tool seen on the opposing board."""
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
                                "players": [
                                    {"active": [], "bench": []},
                                    {
                                        "active": [
                                            {"tools": [{"id": 1159, "name": "Hero’s Cape"}]}
                                        ],
                                        "bench": [],
                                    },
                                ]
                            },
                            "logs": [
                                {
                                    "cardId": 1137,
                                    "playerIndex": 0,
                                    "serial": 50,
                                    "type": "MoveCard",
                                    "fromArea": 2,
                                    "toArea": 3,
                                }
                            ],
                        }
                    ],
                }
            ]
        ],
    }
    (replay_dir / "episode-9-replay.json").write_text(json.dumps(replay))

    audit = analyze_submission("123", tmp_path)

    assert audit.tool_scrapper_uses == 1
    assert audit.matches[0].used_tool_scrapper
    assert audit.matches[0].opposing_tools["Hero’s Cape"] == 1
    assert combined_to_dict([audit])["tools"]["Hero’s Cape"]["seen_matches_with_scrapper"] == 1
