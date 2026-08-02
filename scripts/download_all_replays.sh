#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
exec .venv/bin/python scripts/download_all_replays.py "$@"
