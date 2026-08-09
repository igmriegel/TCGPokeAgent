#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -z "${KAGGLE_API_TOKEN:-}" ]] && command -v kaggle >/dev/null 2>&1; then
	_cached_kaggle_token="$(kaggle auth print-access-token 2>/dev/null || true)"
	if [[ -n "${_cached_kaggle_token}" ]]; then
		export KAGGLE_API_TOKEN="${_cached_kaggle_token}"
	fi
fi

exec .venv/bin/python scripts/download_all_replays.py "$@"
