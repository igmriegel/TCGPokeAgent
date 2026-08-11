"""Download missing replays from the active Kaggle submissions."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

COMPETITION = "pokemon-tcg-ai-battle"
REPLAY_DIR = Path("data/raw/kaggle/replays/remote")
SUBMISSION_MAP_PATH = Path("data/raw/kaggle/episode_to_submission.json")
SUBMISSION_METADATA_PATH = Path("data/raw/kaggle/submission_metadata.json")
KAGGLE_COMMAND_TIMEOUT = int(os.environ.get("KAGGLE_COMMAND_TIMEOUT", "60"))
ACTIVE_SUBMISSION_LIMIT = 2
EXCLUDED_SUBMISSION_IDS = {"55389788"}


def _list_submissions() -> list[dict[str, str]]:
    result = subprocess.run(
        ["kaggle", "competitions", "submissions", COMPETITION, "-v"],
        capture_output=True,
        text=True,
        check=True,
        timeout=KAGGLE_COMMAND_TIMEOUT,
    )
    return list(csv.DictReader(io.StringIO(result.stdout)))


def _parse_submission_date(value: str) -> datetime:
    """Parse a Kaggle submission date, using the minimum on malformed input."""
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min


def _active_submissions(submissions: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return the most recent completed submissions with replay availability."""
    completed = [
        submission
        for submission in submissions
        if submission.get("status") == "SubmissionStatus.COMPLETE"
        and submission.get("ref") not in EXCLUDED_SUBMISSION_IDS
    ]
    return sorted(
        completed,
        key=lambda submission: _parse_submission_date(submission.get("date", "")),
        reverse=True,
    )[:ACTIVE_SUBMISSION_LIMIT]


def _list_episodes(submission_id: str) -> list[dict[str, str]] | None:
    try:
        result = subprocess.run(
            ["kaggle", "competitions", "episodes", submission_id, "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
            timeout=KAGGLE_COMMAND_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        print(f"  SKIPPED: episode listing timed out after {KAGGLE_COMMAND_TIMEOUT}s")
        return None
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() if error.stderr else "unknown Kaggle CLI error"
        print(f"  SKIPPED: could not list episodes: {detail}")
        return None

    output = result.stdout
    bracket_end = output.rfind("]")
    if bracket_end == -1:
        return []
    return json.loads(output[: bracket_end + 1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--submission-id",
        action="append",
        default=[],
        help="Download only the specified completed submission ID; repeatable.",
    )
    args = parser.parse_args()

    submission_map: dict[str, str] = {}
    if SUBMISSION_MAP_PATH.exists():
        submission_map = json.loads(SUBMISSION_MAP_PATH.read_text())

    submissions = _list_submissions()
    completed_submissions = [
        submission
        for submission in submissions
        if submission.get("status") == "SubmissionStatus.COMPLETE"
    ]
    SUBMISSION_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUBMISSION_METADATA_PATH.write_text(
        json.dumps(completed_submissions, indent=2) + "\n",
        encoding="utf-8",
    )
    requested_ids = set(args.submission_id)
    active = (
        [
            submission
            for submission in submissions
            if submission.get("ref") in requested_ids
            and submission.get("ref") not in EXCLUDED_SUBMISSION_IDS
        ]
        if requested_ids
        else _active_submissions(submissions)
    )
    if requested_ids:
        blocked_ids = sorted(requested_ids & EXCLUDED_SUBMISSION_IDS)
        if blocked_ids:
            message = "submission IDs are excluded from replay download: " + ", ".join(blocked_ids)
            raise ValueError(message)
        found_ids = {submission.get("ref") for submission in active}
        missing_ids = sorted(requested_ids - found_ids)
        if missing_ids:
            raise ValueError(f"unknown submission IDs: {', '.join(missing_ids)}")
        incomplete_ids = [
            submission.get("ref", "unknown")
            for submission in active
            if submission.get("status") != "SubmissionStatus.COMPLETE"
        ]
        if incomplete_ids:
            raise ValueError(f"submission IDs are not complete: {', '.join(incomplete_ids)}")
    print(
        "Active replay window: "
        + ", ".join(submission.get("ref", "unknown") for submission in active)
    )

    total_downloaded = 0
    total_skipped = 0

    for sub in active:
        sub_id = sub["ref"]
        score = sub.get("publicScore", "N/A")
        print(f"\n=== Sub {sub_id} (score: {score}) ===")

        episodes = _list_episodes(sub_id)
        if episodes is None:
            continue
        completed_eps = [e for e in episodes if e.get("state") == "EpisodeState.COMPLETED"]
        print(f"  Episodes: {len(completed_eps)}")

        sub_dir = REPLAY_DIR / sub_id
        sub_dir.mkdir(parents=True, exist_ok=True)

        downloaded = 0
        skipped = 0
        for ep in completed_eps:
            ep_id = str(ep["id"])
            replay_file = sub_dir / f"episode-{ep_id}-replay.json"
            if replay_file.exists():
                submission_map[ep_id] = sub_id
                skipped += 1
                continue

            try:
                subprocess.run(
                    ["kaggle", "competitions", "replay", ep_id, "-p", str(sub_dir), "-q"],
                    check=True,
                    capture_output=True,
                    timeout=KAGGLE_COMMAND_TIMEOUT,
                )
            except subprocess.TimeoutExpired:
                print(f"    FAILED: {ep_id} (download timed out)")
                continue
            except subprocess.CalledProcessError:
                print(f"    FAILED: {ep_id}")
                continue
            if replay_file.exists():
                submission_map[ep_id] = sub_id
                downloaded += 1

        total_downloaded += downloaded
        total_skipped += skipped
        print(f"  New: {downloaded}, Cached: {skipped}")

    SUBMISSION_MAP_PATH.write_text(json.dumps(submission_map, indent=2) + "\n")
    print("\n=== Summary ===")
    print(f"Downloaded: {total_downloaded}")
    print(f"Cached: {total_skipped}")
    print(f"Mapping: {len(submission_map)} episodes")
    print(f"Replay files: {len(list(REPLAY_DIR.glob('*/*.json')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
