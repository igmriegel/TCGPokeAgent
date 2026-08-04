"""Download all missing replays from all submissions."""

from __future__ import annotations

import csv
import io
import json
import os
import shutil
import subprocess
from pathlib import Path

COMPETITION = "pokemon-tcg-ai-battle"
REPLAY_DIR = Path("replays/remote")
DATA_DIR = Path("data/raw/kaggle/kaggle_gameplay_runs")
SUBMISSION_MAP_PATH = Path("data/raw/kaggle/episode_to_submission.json")
KAGGLE_COMMAND_TIMEOUT = int(os.environ.get("KAGGLE_COMMAND_TIMEOUT", "60"))


def _list_submissions() -> list[dict[str, str]]:
    result = subprocess.run(
        ["kaggle", "competitions", "submissions", COMPETITION, "-v"],
        capture_output=True,
        text=True,
        check=True,
        timeout=KAGGLE_COMMAND_TIMEOUT,
    )
    return list(csv.DictReader(io.StringIO(result.stdout)))


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
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    submission_map: dict[str, str] = {}
    if SUBMISSION_MAP_PATH.exists():
        submission_map = json.loads(SUBMISSION_MAP_PATH.read_text())

    submissions = _list_submissions()
    completed = [s for s in submissions if s.get("status") == "SubmissionStatus.COMPLETE"]
    print(f"Found {len(completed)} completed submissions")

    total_downloaded = 0
    total_skipped = 0

    for sub in completed:
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
            dest = DATA_DIR / f"{ep_id}.json"

            if dest.exists():
                submission_map[ep_id] = sub_id
                skipped += 1
                continue

            replay_file = sub_dir / f"episode-{ep_id}-replay.json"
            if not replay_file.exists():
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
                shutil.copy2(replay_file, dest)
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
    print(f"Data dir: {len(list(DATA_DIR.glob('*.json')))} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
