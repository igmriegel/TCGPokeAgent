"""Copy active-submission replays to the dashboard directory."""

from __future__ import annotations

import csv
import io
import json
import subprocess
from datetime import datetime
from pathlib import Path

REPLAY_SOURCE = Path("data/raw/kaggle/replays/remote")
SUBMISSION_MAP_PATH = Path("data/raw/kaggle/episode_to_submission.json")
COMPETITION = "pokemon-tcg-ai-battle"
ACTIVE_SUBMISSION_LIMIT = 2


def _parse_submission_date(value: str) -> datetime:
    """Parse a Kaggle submission date, using the minimum on malformed input."""
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min


def _active_submission_ids() -> set[str]:
    """Return IDs of the latest completed submissions known to Kaggle."""
    result = subprocess.run(
        ["kaggle", "competitions", "submissions", COMPETITION, "-v"],
        capture_output=True,
        text=True,
        check=True,
    )
    rows = list(csv.DictReader(io.StringIO(result.stdout)))
    completed = [row for row in rows if row.get("status") == "SubmissionStatus.COMPLETE"]
    completed.sort(key=lambda row: _parse_submission_date(row.get("date", "")), reverse=True)
    return {row["ref"] for row in completed[:ACTIVE_SUBMISSION_LIMIT] if row.get("ref")}


def main() -> int:
    submission_map = {}
    if SUBMISSION_MAP_PATH.exists():
        submission_map = json.loads(SUBMISSION_MAP_PATH.read_text())

    active_submission_ids = _active_submission_ids()
    print(f"Active replay window: {', '.join(sorted(active_submission_ids))}")
    discovered = 0
    for submission_dir in sorted(REPLAY_SOURCE.iterdir()):
        if not submission_dir.is_dir():
            continue
        submission_id = submission_dir.name
        if submission_id not in active_submission_ids:
            continue

        for replay_file in sorted(submission_dir.glob("*.json")):
            # Extract episode ID from filename (episode-89030986-replay.json -> 89030986)
            stem = replay_file.stem
            if stem.startswith("episode-"):
                episode_id = stem.replace("episode-", "").replace("-replay", "")
            else:
                episode_id = stem

            submission_map[episode_id] = submission_id
            discovered += 1

    SUBMISSION_MAP_PATH.write_text(json.dumps(submission_map, indent=2) + "\n")
    print(f"Indexed {discovered} canonical replays")
    print(f"Submission map: {len(submission_map)} entries")
    print(f"Total replays in source: {len(list(REPLAY_SOURCE.glob('*/*.json')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
