#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

OUTPUT="${1:-submissions/honchkrow_porygon_stdout_debug.tar.gz}"

scripts/build_honchkrow_porygon_package.sh "${OUTPUT}" expert_turn_loop
echo "=== Auditable Kaggle package built: ${OUTPUT} ==="
echo "Decision ledger: audit_decision_ledger (stderr logger, decision-ledger-v1)"
