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
mkdir -p "${TMPDIR}/src/artifacts"
if [[ -f src/artifacts/deck_profile.json ]]; then
    cp src/artifacts/deck_profile.json "${TMPDIR}/src/artifacts/"
fi
cp src/__init__.py "${TMPDIR}/src/"
cp src/agents/__init__.py "${TMPDIR}/src/agents/"
cp src/agents/baseline.py "${TMPDIR}/src/agents/"
cp src/agents/heuristic.py "${TMPDIR}/src/agents/"
cp src/agents/search.py "${TMPDIR}/src/agents/"
cp src/core/*.py "${TMPDIR}/src/core/"
cp -r cg "${TMPDIR}/cg"

find "${TMPDIR}" -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find "${TMPDIR}" -name '*.pyc' -delete

tar czf "${OUTPUT}" -C "${TMPDIR}" main.py deck.csv src cg

echo "Package size: $(du -h "${OUTPUT}" | cut -f1)"
echo "=== Package built: ${OUTPUT} ==="
