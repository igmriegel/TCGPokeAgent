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


def test_active_submissions_includes_55389788() -> None:
    """Allow submission 55389788 to be downloaded after its exclusion is lifted."""
    submissions = [
        {
            "ref": "55389788",
            "date": "2026-08-06 00:00:00",
            "status": "SubmissionStatus.COMPLETE",
        },
        {
            "ref": "55389999",
            "date": "2026-08-05 00:00:00",
            "status": "SubmissionStatus.COMPLETE",
        },
    ]

    assert [row["ref"] for row in downloader._active_submissions(submissions)] == [
        "55389788",
        "55389999",
    ]


def test_latest_downloaded_submission_ids_ignores_older_reports(tmp_path: Path) -> None:
    """Select only the latest completed submissions with local replay files."""
    replay_dir = tmp_path / "replays" / "remote"
    (replay_dir / "new").mkdir(parents=True)
    (replay_dir / "old").mkdir()
    (replay_dir / "new" / "episode-100-replay.json").touch()
    (replay_dir / "old" / "episode-200-replay.json").touch()
    metadata = [
        {"ref": "old", "date": "2026-08-01 00:00:00", "status": "SubmissionStatus.COMPLETE"},
        {"ref": "new", "date": "2026-08-05 00:00:00", "status": "SubmissionStatus.COMPLETE"},
        {"ref": "missing", "date": "2026-08-06 00:00:00", "status": "SubmissionStatus.COMPLETE"},
    ]
    submission_map = {"100": "new", "200": "old"}

    assert report_updater.latest_downloaded_submission_ids(
        metadata, submission_map, replay_dir
    ) == ["new", "old"]


def test_latest_downloaded_submission_ids_includes_55389788(
    tmp_path: Path,
) -> None:
    """Allow submission 55389788 to receive a generated replay report."""
    replay_dir = tmp_path / "replays" / "remote"
    (replay_dir / "55389788").mkdir(parents=True)
    (replay_dir / "55389999").mkdir()
    (replay_dir / "55389788" / "episode-100-replay.json").touch()
    (replay_dir / "55389999" / "episode-200-replay.json").touch()
    metadata = [
        {
            "ref": "55389788",
            "date": "2026-08-06 00:00:00",
            "status": "SubmissionStatus.COMPLETE",
        },
        {
            "ref": "55389999",
            "date": "2026-08-05 00:00:00",
            "status": "SubmissionStatus.COMPLETE",
        },
    ]
    submission_map = {
        "100": "55389788",
        "200": "55389999",
    }

    assert report_updater.latest_downloaded_submission_ids(
        metadata, submission_map, replay_dir
    ) == ["55389788", "55389999"]


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


def test_filter_replay_paths_handles_kaggle_replay_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Accept Kaggle replay filenames ending in '-replay.json'."""
    mapping_path = tmp_path / "episode_to_submission.json"
    mapping_path.write_text(json.dumps({"91667826": "55392121"}))
    monkeypatch.setattr(report, "SUBMISSION_MAP_PATH", mapping_path)
    replay_paths = [tmp_path / "episode-91667826-replay.json"]

    selected = report._filter_replay_paths(replay_paths, "55392121")

    assert selected == [tmp_path / "episode-91667826-replay.json"]


def test_submission_history_links_to_submission_report() -> None:
    """Link each submission-history ID to its standalone report."""
    assert (
        report._submission_report_link("55392121")
        == '<a class="submission-link" href="INVESTIGATION_REPORT_55392121.html">'
        "55392121</a>"
    )


def test_generate_report_recurses_into_submission_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Collect replays from a nested Kaggle submission directory."""
    mapping_path = tmp_path / "episode_to_submission.json"
    mapping_path.write_text(json.dumps({"91667826": "55392121"}))
    monkeypatch.setattr(report, "SUBMISSION_MAP_PATH", mapping_path)
    monkeypatch.setattr(
        report,
        "_list_completed_submissions",
        lambda: [
            {
                "ref": "55392121",
                "date": "2026-08-10T00:07:25.943000",
                "description": "nested test submission",
                "publicScore": "123.4",
            }
        ],
    )

    replay_dir = tmp_path / "replays" / "remote" / "55392121"
    replay_dir.mkdir(parents=True)
    replay_path = replay_dir / "episode-91667826-replay.json"
    replay_path.touch()

    def fake_parse_replay(path: Path, owner_name: str) -> dict[str, object]:
        del owner_name
        assert path == replay_path
        return {
            "episode_id": "91667826",
            "outcome": "win",
            "first_player": 0,
            "max_turn": 1,
            "opp_archetype": "test opponent",
            "owner_deck": "test deck",
            "attack_usage": {},
            "damage_dealt": [],
            "damage_taken": [],
            "evolution_turns": [],
        }

    monkeypatch.setattr(report, "parse_replay", fake_parse_replay)
    output_path = tmp_path / "report.html"

    report.generate_report(
        replay_dir,
        "mudkip_mini_chicken",
        output_path,
        submission_id="55392121",
    )

    content = output_path.read_text()
    assert "Total Replays</div>" in content
    assert "1</div>" in content
    assert "Report generated" not in content


def test_generate_report_infers_owner_name_when_initial_pass_is_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Retry parsing with an inferred owner name when the default misses all replays."""
    mapping_path = tmp_path / "episode_to_submission.json"
    mapping_path.write_text(json.dumps({"91667826": "55392121"}))
    monkeypatch.setattr(report, "SUBMISSION_MAP_PATH", mapping_path)
    monkeypatch.setattr(
        report,
        "_list_completed_submissions",
        lambda: [
            {
                "ref": "55392121",
                "date": "2026-08-10T00:07:25.943000",
                "description": "nested test submission",
                "publicScore": "123.4",
            }
        ],
    )

    replay_dir = tmp_path / "replays"
    replay_dir.mkdir()
    replay_path = replay_dir / "episode-91667826-replay.json"
    replay_path.touch()

    calls: list[str] = []

    def fake_parse_replay(path: Path, owner_name: str) -> dict[str, object] | None:
        del path
        calls.append(owner_name)
        if owner_name == "Correct Owner":
            return {
                "episode_id": "91667826",
                "outcome": "win",
                "first_player": 0,
                "max_turn": 1,
                "opp_archetype": "test opponent",
                "owner_deck": "test deck",
                "attack_usage": {},
                "damage_dealt": [],
                "damage_taken": [],
                "evolution_turns": [],
            }
        return None

    monkeypatch.setattr(report, "parse_replay", fake_parse_replay)
    monkeypatch.setattr(report, "_infer_owner_name", lambda replay_paths: "Correct Owner")
    output_path = tmp_path / "report.html"

    report.generate_report(
        replay_dir,
        "mudkip_mini_chicken",
        output_path,
        submission_id="55392121",
    )

    assert calls == ["mudkip_mini_chicken", "Correct Owner"]
    assert "1</div>" in output_path.read_text()


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

    report.generate_report(
        tmp_path,
        "mudkip_mini_chicken",
        output_path,
        submission_id="55222565",
    )

    content = output_path.read_text()
    assert "Selected Submission Summary" in content
    assert "Submission History" not in content
    assert "Matchup Analysis &mdash; Submission 55222565" in content
    assert "4 &mdash; Elo Trajectory" in content
    assert "test opponent" in content
    assert "Final Kaggle Public Score" in content
    assert "614.4" in content
    assert "8.1 &mdash; Worst Matchups (Top 5)" in content
    assert "minimum 5 games" not in content.split("8.1", 1)[1].split("8.2", 1)[0]
    assert "8.2 &mdash; Best Matchups (Top 5, minimum 5 games)" in content
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

    report.generate_report(
        tmp_path,
        "mudkip_mini_chicken",
        output_path,
        deck_filter="Abomasnow",
    )

    content = output_path.read_text()
    assert "Total Replays</div>" in content
    assert "1</div>" in content
    assert "Filter: Abomasnow" in content
    assert "Elo Trajectory" not in content


def test_elo_trajectory_starts_at_600_and_names_each_opponent() -> None:
    """Build an ordered Elo-style trend from replay outcomes."""
    trajectory = report._elo_trajectory(
        [
            {
                "episode_id": "20",
                "outcome": "loss",
                "opp_archetype": "Deck B",
                "lost_to_deck_out": True,
            },
            {"episode_id": "10", "outcome": "win", "opp_archetype": "Deck A"},
        ],
        final_rating=584.0,
    )

    assert [point["episode_id"] for point in trajectory] == ["10", "20"]
    assert [point["opponent"] for point in trajectory] == ["Deck A", "Deck B"]
    assert [point["marker"] for point in trajectory] == [None, "deckout"]
    assert float(trajectory[0]["rating"]) > 600
    assert float(trajectory[1]["rating"]) < float(trajectory[0]["rating"])
    assert float(trajectory[-1]["rating"]) == 584.0

    chart = report._elo_chart_html(
        [
            {
                "episode_id": "10",
                "outcome": "win",
                "opp_archetype": "Deck A",
                "lost_to_no_pokemon_by_turn_3": True,
            },
        ],
        final_rating=616.0,
    )
    assert "Starts at 600" in chart
    assert "| Elo" not in chart
    assert ">600</text>" in chart
    assert ">616.0</text>" in chart
    assert "event-donk" in chart
    assert ">donk</text>" in chart
    assert "Deck A" in chart
