"""Copy downloaded replays to the dashboard directory and create submission map."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


REPLAY_SOURCE = Path("replays/remote")
REPLAY_DEST = Path("data/raw/kaggle/kaggle_gameplay_runs")
SUBMISSION_MAP_PATH = Path("data/raw/kaggle/episode_to_submission.json")


def main() -> int:
    REPLAY_DEST.mkdir(parents=True, exist_ok=True)

    submission_map = {}
    if SUBMISSION_MAP_PATH.exists():
        submission_map = json.loads(SUBMISSION_MAP_PATH.read_text())

    copied = 0
    for submission_dir in sorted(REPLAY_SOURCE.iterdir()):
        if not submission_dir.is_dir():
            continue
        submission_id = submission_dir.name

        for replay_file in sorted(submission_dir.glob("*.json")):
            # Extract episode ID from filename (episode-89030986-replay.json -> 89030986)
            stem = replay_file.stem
            if stem.startswith("episode-"):
                episode_id = stem.replace("episode-", "").replace("-replay", "")
            else:
                episode_id = stem

            dest_file = REPLAY_DEST / f"{episode_id}.json"
            if not dest_file.exists():
                shutil.copy2(replay_file, dest_file)
                copied += 1

            submission_map[episode_id] = submission_id

    SUBMISSION_MAP_PATH.write_text(json.dumps(submission_map, indent=2) + "\n")
    print(f"Copied {copied} new replays")
    print(f"Submission map: {len(submission_map)} entries")
    print(f"Total replays in destination: {len(list(REPLAY_DEST.glob('*.json')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
