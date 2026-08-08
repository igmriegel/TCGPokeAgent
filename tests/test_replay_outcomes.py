from __future__ import annotations

import json

from src.data.replay_outcomes import extract_replay_outcome, load_replay_outcomes


def _replay(reason: int, *, winner: int = 0) -> dict:
    players = [
        {
            "active": [{"id": 1}],
            "bench": [{"id": 2}],
            "deck": [{"id": 3}],
            "deckCount": 1,
            "prize": [{"id": 4}],
        },
        {
            "active": [{"id": 5}],
            "bench": [],
            "deck": [{"id": 6}],
            "deckCount": 1,
            "prize": [{"id": 7}],
        },
    ]
    loser = 1 - winner
    if reason == 1:
        players[winner]["prize"] = []
    elif reason == 2:
        players[loser]["deck"] = []
        players[loser]["deckCount"] = 0
    elif reason == 3:
        players[loser]["active"] = []
        players[loser]["bench"] = []
    terminal = {
        "current": {"result": winner, "turn": 8, "players": players},
        "logs": [{"type": "Result", "result": winner, "reason": reason}],
    }
    return {
        "name": "cabt",
        "info": {
            "EpisodeId": 123,
            "Agents": [{"Name": "Owner"}, {"Name": "Opponent"}],
        },
        "steps": [[{"visualize": [{"current": {"result": -1}}, terminal]}, {}]],
    }


def test_extracts_explicit_prize_victory(tmp_path) -> None:
    replay_path = tmp_path / "123.json"
    replay_path.write_text(json.dumps(_replay(1)), encoding="utf-8")

    outcome = extract_replay_outcome(replay_path, owner_name="Owner")

    assert outcome.termination_reason == "all_prizes_taken"
    assert outcome.owner_outcome == "win"
    assert outcome.winner_prizes_remaining == 0
    assert outcome.reason_explicit
    assert outcome.reason_consistent


def test_extracts_deck_out_and_empty_board(tmp_path) -> None:
    for reason, expected in ((2, "deck_out"), (3, "no_pokemon_in_play")):
        replay_path = tmp_path / f"{reason}.json"
        replay_path.write_text(json.dumps(_replay(reason, winner=1)), encoding="utf-8")

        outcome = extract_replay_outcome(replay_path, owner_name="Owner")

        assert outcome.termination_reason == expected
        assert outcome.owner_outcome == "loss"
        assert outcome.reason_consistent


def test_unknown_reason_is_retained_and_reported_inconsistent(tmp_path) -> None:
    replay_path = tmp_path / "unknown.json"
    replay_path.write_text(json.dumps(_replay(99)), encoding="utf-8")

    outcome = extract_replay_outcome(replay_path)

    assert outcome.termination_reason == "unknown"
    assert outcome.reason_code == 99
    assert not outcome.reason_consistent


def test_bulk_load_keeps_file_errors_visible(tmp_path) -> None:
    (tmp_path / "valid.json").write_text(json.dumps(_replay(1)), encoding="utf-8")
    (tmp_path / "invalid.json").write_text("{}", encoding="utf-8")

    outcomes, errors = load_replay_outcomes(tmp_path, owner_name="Owner")

    assert len(outcomes) == 1
    assert len(errors) == 1
    assert errors[0]["path"].endswith("invalid.json")


def test_explicit_owner_index_resolves_duplicate_names(tmp_path) -> None:
    replay = _replay(1, winner=1)
    replay["info"]["Agents"] = [{"Name": "Owner"}, {"Name": "Owner"}]
    replay_path = tmp_path / "self-play.json"
    replay_path.write_text(json.dumps(replay), encoding="utf-8")

    outcome = extract_replay_outcome(replay_path, owner_name="Owner", owner_index=1)

    assert outcome.owner_index == 1
    assert outcome.owner_outcome == "win"
