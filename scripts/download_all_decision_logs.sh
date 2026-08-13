#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

replay_root="data/raw/kaggle/replays/remote"
if [[ -n "${SUBMISSION_ID:-}" ]]; then
	readarray -t submission_ids <<< "${SUBMISSION_ID}"
else
	# Match download_all_replays.py: ignore historical replay directories and
	# process only the current two-submission window. The replay mirror is
	# intentionally cumulative, so scanning directories alone would retry old
	# submissions whose Kaggle display name may no longer be the current owner.
	mapfile -t submission_ids < <(.venv/bin/python - <<'PY'
import json
from datetime import datetime
from pathlib import Path

metadata_path = Path("data/raw/kaggle/submission_metadata.json")
replay_root = Path("data/raw/kaggle/replays/remote")
if not metadata_path.is_file():
    raise SystemExit("Missing submission metadata; run download_all_replays.sh first.")

metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
completed = [
    row
    for row in metadata
    if row.get("status") == "SubmissionStatus.COMPLETE"
    and (replay_root / str(row.get("ref", ""))).is_dir()
]
def submission_date(row: dict[str, str]) -> datetime:
    try:
        return datetime.fromisoformat(row.get("date", ""))
    except ValueError:
        return datetime.min

completed.sort(
    key=submission_date,
    reverse=True,
)
for row in completed[:2]:
    print(row["ref"])
PY
)
fi

if [[ "${#submission_ids[@]}" -eq 0 ]]; then
	echo "No downloaded submission replay directories found under ${replay_root}."
	exit 0
fi

for submission_id in "${submission_ids[@]}"; do
	if [[ -z "$submission_id" ]]; then
		continue
	fi
	echo "=== Decision logs for submission ${submission_id} ==="
	.venv/bin/python scripts/download_kaggle_decision_logs.py "$submission_id"
done
