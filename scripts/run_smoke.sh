#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

AGENT_MODE="${1:-baseline}"
SEED="${2:-42}"

echo "=== Smoke test: ${AGENT_MODE} (seed ${SEED}) ==="

export AGENT_MODE
export LOG_LEVEL=INFO

uv run --frozen pytest tests/ -v --tb=short 2>&1

uv run --frozen python scripts/cabt_smoke.py --matches 20 --agent-mode "${AGENT_MODE}"

echo "=== Smoke complete ==="
