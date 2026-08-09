#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

AGENT_MODE="${1:-expert_turn_loop}"
CONFIG="${2:-configs/eval_full.yaml}"

echo "=== Full evaluation: ${AGENT_MODE} (${CONFIG}) ==="

export AGENT_MODE
export LOG_LEVEL=INFO

uv run --frozen python -c "
import os
from src.experiments.orchestrator import run_experiment
from src.config.loader import load_config

config = load_config('${CONFIG}')
config.agent = os.environ.get('AGENT_MODE', config.agent)
exp = run_experiment(
    name='full_${AGENT_MODE}',
    config=config,
    output_dir='reports',
)
print(f'Done: {exp.report.total_matches} matches')
"

echo "=== Full evaluation complete ==="
