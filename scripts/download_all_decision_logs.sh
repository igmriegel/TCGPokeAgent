#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

replay_root="data/raw/kaggle/replays/remote"
if [[ -n "${SUBMISSION_ID:-}" ]]; then
	readarray -t submission_ids <<< "${SUBMISSION_ID}"
else
	mapfile -t submission_ids < <(
		find "$replay_root" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort -u
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
