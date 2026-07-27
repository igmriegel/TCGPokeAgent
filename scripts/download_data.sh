#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

CMD="python3 -m src.data.downloader"

if [ "${1:-}" = "--check" ]; then
    echo "=== Checking data integrity ==="
    exec $CMD --check
fi

echo "=== Downloading Kaggle datasets ==="
echo "Make sure ~/.kaggle/kaggle.json is configured."
echo ""

COMPETITION="all"
if [ "${1:-}" = "--competition" ] && [ -n "${2:-}" ]; then
    COMPETITION="$2"
    shift 2
fi

exec $CMD --competition "$COMPETITION"
