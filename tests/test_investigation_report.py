from __future__ import annotations

import json
from pathlib import Path

import pytest

from cg.api import all_card_data
from scripts import download_all_replays as downloader
from scripts import generate_investigation_report as report
from scripts import update_replays_reports as report_updater
from src.core.archetype import resolve_deck_archetype, resolve_deck_archetype_lines

CARD_BY_NAME = {card.name: card for card in all_card_data()}
CARD_BY_ID = {card.cardId: card for card in all_card_data()}


def _ids(*names: str) -> list[int]:
    """Return canonical SDK IDs for card names used by archetype tests."""
    return [CARD_BY_NAME[name].cardId for name in names]


def test_archetype_keeps_evolution_lines_and_ex_cards_separate() -> None:
    """Count all copies in each exact-name evolution line."""
    label = resolve_deck_archetype(
        _ids("Abra", "Kadabra", "Alakazam", "Dunsparce", "Dudunsparce"),
        CARD_BY_ID.get,
    )

    assert label == "Alakazam / Dudunsparce"
    assert set(
        resolve_deck_archetype(_ids("Pikachu", "Pikachu ex"), CARD_BY_ID.get).split(" / ")
    ) == {
        "Pikachu",
        "Pikachu ex",
    }


def test_metal_matchup_uses_only_dominant_terminal_lines() -> None:
    """Auxiliary Genesect must not make a non-Metal archetype Metal."""
    non_metal_lines = resolve_deck_archetype_lines(
        _ids("Abra", "Kadabra", "Alakazam", "Dunsparce", "Dudunsparce", "Genesect"),
        CARD_BY_ID.get,
    )
    metal_lines = resolve_deck_archetype_lines(_ids("Duraludon", "Archaludon ex"), CARD_BY_ID.get)

    assert not report._dominant_metal_deck(
        _ids("Abra", "Kadabra", "Alakazam", "Dunsparce", "Dudunsparce", "Genesect")
    )
    assert any(energy_type == 8 for _, _, energy_type in metal_lines)
    assert any(name == "Archaludon ex" for name, _, _ in metal_lines)
    assert non_metal_lines[0][0] == "Alakazam"


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


def test_latest_downloaded_submission_ids_ignores_older_reports(tmp_path: Path) -> None:
    """Select only the latest completed submissions with local replay files."""
    replay_dir = tmp_path / "replays"
    replay_dir.mkdir()
    (replay_dir / "new-episode.json").touch()
    (replay_dir / "old-episode.json").touch()
    metadata = [
        {"ref": "old", "date": "2026-08-01 00:00:00", "status": "SubmissionStatus.COMPLETE"},
        {"ref": "new", "date": "2026-08-05 00:00:00", "status": "SubmissionStatus.COMPLETE"},
        {"ref": "missing", "date": "2026-08-06 00:00:00", "status": "SubmissionStatus.COMPLETE"},
    ]
    submission_map = {"new-episode": "new", "old-episode": "old"}

    assert report_updater.latest_downloaded_submission_ids(
        metadata, submission_map, replay_dir
    ) == ["new", "old"]


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
    assert "7.1 &mdash; Worst Matchups (Top 5)" in content
    assert "minimum 5 games" not in content.split("7.1", 1)[1].split("7.2", 1)[0]
    assert "7.2 &mdash; Best Matchups (Top 5, minimum 5 games)" in content
    assert "614.4" in content
    assert "1W/0L" in content
    assert "other submission" not in content


def test_deck_filter_excludes_other_controlled_decks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Restrict aggregate metrics and submission rows to the requested deck."""
    mapping_path = tmp_path / "episode_to_submission.json"
    mapping_path.write_text(json.dumps({"100": "55222565", "200": "55222565"}))
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
                "description": "mixed deck test",
                "publicScore": "614.4",
            }
        ],
    )

    def fake_parse_replay(path: Path, owner_name: str) -> dict[str, object]:
        del owner_name
        return {
            "episode_id": path.stem,
            "outcome": "win" if path.stem == "100" else "loss",
            "first_player": 0,
            "max_turn": 8,
            "opp_archetype": "test opponent",
            "owner_deck": "Mega Abomasnow / Kyogre" if path.stem == "100" else "Honchkrow",
            "attack_usage": {},
            "damage_dealt": [],
            "damage_taken": [],
            "evolution_turns": [],
        }

    monkeypatch.setattr(report, "parse_replay", fake_parse_replay)
    output_path = tmp_path / "report.html"

    report.generate_report(tmp_path, "Igor Riegel", output_path, deck_filter="Abomasnow")

    content = output_path.read_text()
    assert "Total Replays</div>" in content
    assert "1</div>" in content
    assert "Filter: Abomasnow" in content
