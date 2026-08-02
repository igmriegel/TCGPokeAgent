#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
exec .venv/bin/python scripts/generate_investigation_report.py "$@"
