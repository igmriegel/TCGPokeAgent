"""Tests for the replay inspection helper."""

from __future__ import annotations

import json
from pathlib import Path

from src.data.replay_inspector import (
    filter_replay_frames,
    frame_as_text,
    frames_as_json,
    load_replay_frames,
)


def _replay_payload() -> dict[str, object]:
    """Build a minimal replay with a turn that includes Ariana, Factory, and Rocket Energy."""

    return {
        "steps": [
            [
                {
                    "action": [1],
                    "observation": {
                        "current": {
                            "turn": 11,
                            "yourIndex": 0,
                            "players": [
                                {
                                    "hand": [
                                        {"id": 1216, "serial": 17},
                                        {"id": 1257, "serial": 53},
                                        {"id": 15, "serial": 58},
                                    ]
                                }
                            ],
                        },
                        "logs": [
                            {"type": 10, "playerIndex": 0, "cardId": 1216},
                            {"type": 10, "playerIndex": 0, "cardId": 1257},
                            {"type": 4, "playerIndex": 0, "cardId": 15},
                            {"type": 15, "playerIndex": 0, "attackId": 1277},
                        ],
                        "select": {
                            "type": 0,
                            "context": 0,
                            "option": [
                                {"type": 7, "index": 0},
                                {"type": 7, "index": 1},
                                {"type": 14},
                                {"attackId": 1277, "type": 13},
                            ],
                        },
                    },
                }
            ]
        ]
    }


def test_replay_inspector_finds_card_sequence(tmp_path: Path) -> None:
    """The helper should find and render a frame containing the requested cards."""

    replay_path = tmp_path / "episode-91484013-replay.json"
    replay_path.write_text(json.dumps(_replay_payload()), encoding="utf-8")

    frames = load_replay_frames(replay_path)
    filtered = filter_replay_frames(
        frames,
        turn=11,
        your_index=0,
        card_ids={1216, 1257, 15},
        attack_ids={1277},
    )

    assert len(filtered) == 1
    text = frame_as_text(filtered[0])
    assert "turn=11" in text
    assert "cardId=1216" in text
    assert "cardId=1257" in text
    assert "cardId=15" in text
    assert "attackId=1277" in text
    assert "action=[1]" in text


def test_replay_inspector_json_round_trips(tmp_path: Path) -> None:
    """The JSON formatter should keep the stable replay coordinates."""

    replay_path = tmp_path / "episode-91484013-replay.json"
    replay_path.write_text(json.dumps(_replay_payload()), encoding="utf-8")

    frames = load_replay_frames(replay_path)
    payload = frames_as_json(frames)

    assert payload == [
        {
            "step_index": 0,
            "entry_index": 0,
            "turn": 11,
            "your_index": 0,
            "select_type": 0,
            "select_context": 0,
            "action": [1],
            "card_ids": [1216, 1257, 15],
            "attack_ids": [1277],
            "options": [
                "type=7 index=0 cardId=1216",
                "type=7 index=1 cardId=1257",
                "type=14",
                "type=13 attackId=1277",
            ],
            "logs": [
                "type=10 player=0 cardId=1216",
                "type=10 player=0 cardId=1257",
                "type=4 player=0 cardId=15",
                "type=15 player=0 attackId=1277",
            ],
        }
    ]
