#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

OUTPUT="${1:-submission.tar.gz}"

echo "=== Building package: ${OUTPUT} ==="

TMPDIR=$(mktemp -d)
trap 'rm -rf "${TMPDIR}"' EXIT

cp main.py "${TMPDIR}/"
cp src/artifacts/deck.csv "${TMPDIR}/deck.csv"
mkdir -p "${TMPDIR}/src/agents" "${TMPDIR}/src/core"
cp src/__init__.py "${TMPDIR}/src/"
cp src/agents/__init__.py "${TMPDIR}/src/agents/"
cp src/agents/baseline.py "${TMPDIR}/src/agents/"
cp src/agents/heuristic.py "${TMPDIR}/src/agents/"
cp src/agents/search.py "${TMPDIR}/src/agents/"
cp src/core/*.py "${TMPDIR}/src/core/"

find "${TMPDIR}" -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find "${TMPDIR}" -name '*.pyc' -delete

tar czf "${OUTPUT}" -C "${TMPDIR}" main.py deck.csv src

echo "Package size: $(du -h "${OUTPUT}" | cut -f1)"
echo "=== Package built: ${OUTPUT} ==="
