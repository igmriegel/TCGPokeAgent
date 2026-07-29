"""Tests for deterministic replay ingestion and leakage controls."""

from __future__ import annotations

import json
from pathlib import Path

from src.data.replay_ingestor import ingest_replays


def _player(deck_count: int = 54) -> dict:
    return {
        "active": [],
        "bench": [],
        "benchMax": 5,
        "deckCount": deck_count,
        "discard": [],
        "hand": [],
        "handCount": 0,
        "prize": [None] * 6,
    }


def _observation(select: dict | None) -> dict:
    return {
        "current": {
            "yourIndex": 0,
            "turn": 1,
            "turnActionCount": 0,
            "players": [_player(), _player()],
        },
        "logs": [],
        "select": select,
        "search_begin_input": "must-not-leak",
    }


def test_ingestor_aligns_next_action_and_writes_model_safe_dataset(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    deck_a = [1] * 60
    deck_b = [2] * 60
    replay = {
        "name": "cabt",
        "module_version": "1.32.2",
        "info": {
            "EpisodeId": 123,
            "Agents": [{"Name": "Owner"}, {"Name": "Opponent"}],
        },
        "rewards": [1, -1],
        "statuses": ["DONE", "DONE"],
        "steps": [
            [
                {
                    "action": [],
                    "status": "ACTIVE",
                    "observation": _observation(None),
                    "visualize": [{"action": [deck_a, deck_b]}],
                },
                {
                    "action": [],
                    "status": "INACTIVE",
                    "observation": _observation(None),
                },
            ],
            [
                {
                    "action": deck_a,
                    "status": "ACTIVE",
                    "observation": _observation(
                        {
                            "type": 9,
                            "context": 41,
                            "minCount": 1,
                            "maxCount": 1,
                            "option": [{"type": 1}, {"type": 2}],
                        }
                    ),
                },
                {
                    "action": deck_b,
                    "status": "INACTIVE",
                    "observation": _observation(None),
                },
            ],
            [
                {
                    "action": [1],
                    "status": "DONE",
                    "observation": _observation(None),
                },
                {
                    "action": [],
                    "status": "DONE",
                    "observation": _observation(None),
                },
            ],
        ],
    }
    (raw / "123.json").write_text(json.dumps(replay), encoding="utf-8")
    output = tmp_path / "derived" / "v1"

    summary = ingest_replays(raw, output, owner_name="Owner")

    records = [
        json.loads(line)
        for path in (output / "decisions" / "regression").glob("*.jsonl")
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert summary.matches == 1
    assert summary.decisions == 1
    assert records[0]["selected_indices"] == [1]
    assert "search_begin_input" not in records[0]["observation"]
    assert json.loads((output / "leakage_report.json").read_text())["status"] == "passed"
