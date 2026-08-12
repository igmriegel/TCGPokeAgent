"""Refresh general replay reports and reports for the latest downloaded submissions."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

REPLAY_DIR = Path("data/raw/kaggle/replays/remote")
SUBMISSION_MAP_PATH = Path("data/raw/kaggle/episode_to_submission.json")
SUBMISSION_METADATA_PATH = Path("data/raw/kaggle/submission_metadata.json")
REPORT_DIR = Path("perf_reports")
OWNER_NAME = "mudkip_mini_chicken"
LATEST_REPORT_LIMIT = 2


def _parse_submission_date(value: str) -> datetime:
    """Parse a cached submission date, returning the minimum on malformed input."""
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min


def latest_downloaded_submission_ids(
    metadata: list[dict[str, str]],
    submission_map: dict[str, str],
    replay_dir: Path,
    limit: int = LATEST_REPORT_LIMIT,
) -> list[str]:
    """Return the latest completed submissions with at least one local replay.

    Args:
        metadata: Cached Kaggle submission rows.
        submission_map: Episode-to-submission mapping.
        replay_dir: Directory containing downloaded replay JSON files.
        limit: Maximum number of submission IDs to return.

    Returns:
        Submission IDs ordered from newest to oldest.
    """
    downloaded_episode_ids = {
        path.stem.removeprefix("episode-").removesuffix("-replay")
        for path in replay_dir.rglob("episode-*-replay.json")
    }
    downloaded_ids = {
        submission_map[episode_id]
        for episode_id in downloaded_episode_ids
        if episode_id in submission_map
    }
    completed = [
        row
        for row in metadata
        if row.get("status") == "SubmissionStatus.COMPLETE" and row.get("ref") in downloaded_ids
    ]
    completed.sort(key=lambda row: _parse_submission_date(row.get("date", "")), reverse=True)
    return [str(row["ref"]) for row in completed[:limit] if row.get("ref")]


def _load_json(path: Path) -> object:
    """Load JSON from a repository data file."""
    return json.loads(path.read_text(encoding="utf-8"))


def _run_report(*args: str) -> None:
    """Run the report generator with repository-relative arguments."""
    subprocess.run(["scripts/generate_investigation_report.sh", *args], check=True)


def main() -> int:
    """Refresh general reports and the latest downloaded individual reports."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    replay_dir = str(REPLAY_DIR)
    _run_report(replay_dir, str(REPORT_DIR / "INVESTIGATION_REPORT_ABOMASNOW.html"), OWNER_NAME)
    _run_report(
        replay_dir,
        str(REPORT_DIR / "INVESTIGATION_REPORT_HONCHKROW.html"),
        OWNER_NAME,
        "--deck-filter",
        "Honchkrow",
    )

    # The general report refreshes the metadata cache from Kaggle when the API
    # is available. Read it only after that refresh so the individual reports
    # follow the same moving two-submission window as the downloader.
    metadata = _load_json(SUBMISSION_METADATA_PATH)
    submission_map = _load_json(SUBMISSION_MAP_PATH)
    if not isinstance(metadata, list) or not isinstance(submission_map, dict):
        raise ValueError("submission metadata or episode map has an invalid format")

    submission_ids = latest_downloaded_submission_ids(
        metadata,
        {str(key): str(value) for key, value in submission_map.items()},
        REPLAY_DIR,
    )
    for submission_id in submission_ids:
        _run_report(
            replay_dir,
            str(REPORT_DIR / f"INVESTIGATION_REPORT_{submission_id}.html"),
            OWNER_NAME,
            "--submission-id",
            submission_id,
        )
    print(f"Updated individual reports: {', '.join(submission_ids) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
