from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import download_all_replays as downloader
from scripts import generate_investigation_report as report


def test_active_submissions_returns_two_latest_completed() -> None:
    """Limit replay synchronization to the two latest completed submissions."""
    submissions = [
        {"ref": "old", "date": "2026-08-01 00:00:00", "status": "SubmissionStatus.COMPLETE"},
        {"ref": "new", "date": "2026-08-05 00:00:00", "status": "SubmissionStatus.COMPLETE"},
        {"ref": "error", "date": "2026-08-06 00:00:00", "status": "SubmissionStatus.ERROR"},
        {"ref": "mid", "date": "2026-08-04 00:00:00", "status": "SubmissionStatus.COMPLETE"},
    ]

    assert [row["ref"] for row in downloader._active_submissions(submissions)] == [
        "new",
        "mid",
    ]


def test_filter_replay_paths_uses_submission_map(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Select only replay files mapped to the requested submission."""
    mapping_path = tmp_path / "episode_to_submission.json"
    mapping_path.write_text(json.dumps({"100": "55222565", "200": "55221265"}))
    monkeypatch.setattr(report, "SUBMISSION_MAP_PATH", mapping_path)
    replay_paths = [tmp_path / "100.json", tmp_path / "200.json", tmp_path / "300.json"]

    selected = report._filter_replay_paths(replay_paths, "55222565")

    assert selected == [tmp_path / "100.json"]


def test_filter_replay_paths_rejects_unknown_submission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject a submission ID that has no mapped episodes."""
    mapping_path = tmp_path / "episode_to_submission.json"
    mapping_path.write_text(json.dumps({"100": "55222565"}))
    monkeypatch.setattr(report, "SUBMISSION_MAP_PATH", mapping_path)

    with pytest.raises(ValueError, match="No episodes found.*99999999"):
        report._filter_replay_paths([tmp_path / "100.json"], "99999999")


def test_selected_report_has_one_submission_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Render filtered report text and metrics for one submission only."""
    mapping_path = tmp_path / "episode_to_submission.json"
    mapping_path.write_text(json.dumps({"100": "55222565", "200": "55221265"}))
    monkeypatch.setattr(report, "SUBMISSION_MAP_PATH", mapping_path)
    (tmp_path / "100.json").touch()
    (tmp_path / "200.json").touch()
    monkeypatch.setattr(
        report,
        "_list_completed_submissions",
        lambda: [
            {
                "ref": "55222565",
                "date": "2026-08-03T22:25:49",
                "description": "selected test submission",
                "publicScore": "614.4",
            },
            {
                "ref": "55221265",
                "date": "2026-08-03T20:44:03",
                "description": "other submission",
                "publicScore": "552.5",
            },
        ],
    )

    def fake_parse_replay(path: Path, owner_name: str) -> dict[str, object]:
        del owner_name
        won = path.stem == "100"
        return {
            "episode_id": path.stem,
            "outcome": "win" if won else "loss",
            "first_player": 0,
            "max_turn": 8,
            "opp_archetype": "test opponent",
            "owner_deck": "test deck",
            "attack_usage": {},
            "damage_dealt": [],
            "damage_taken": [],
            "evolution_turns": [],
        }

    monkeypatch.setattr(report, "parse_replay", fake_parse_replay)
    output_path = tmp_path / "report.html"

    report.generate_report(tmp_path, "Igor Riegel", output_path, submission_id="55222565")

    content = output_path.read_text()
    assert "Selected Submission Summary" in content
    assert "Submission History" not in content
    assert "Matchup Analysis &mdash; Submission 55222565" in content
    assert "614.4" in content
    assert "1W/0L" in content
    assert "other submission" not in content
