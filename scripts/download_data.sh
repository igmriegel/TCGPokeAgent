#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ "${1:-}" = "--check" ]; then
    echo "=== Checking data integrity ==="
    exec uv run --frozen python -m src.data.downloader --check
fi

echo "=== Downloading Kaggle datasets ==="
echo "Make sure ~/.kaggle/kaggle.json is configured."
echo ""

COMPETITION="all"
if [ "${1:-}" = "--competition" ] && [ -n "${2:-}" ]; then
    COMPETITION="$2"
    shift 2
fi

exec uv run --frozen python -m src.data.downloader --competition "$COMPETITION"
