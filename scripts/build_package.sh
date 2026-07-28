#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

OUTPUT="${1:-submission.tar.gz}"

echo "=== Building package: ${OUTPUT} ==="

TMPDIR=$(mktemp -d)
trap 'rm -rf "${TMPDIR}"' EXIT

cp main.py "${TMPDIR}/"
cp src/artifacts/deck.csv "${TMPDIR}/"
cp -r src/ "${TMPDIR}/src/"
mkdir -p "${TMPDIR}/configs"
cp -r configs/decks "${TMPDIR}/configs/decks"

find "${TMPDIR}" -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find "${TMPDIR}" -name '*.pyc' -delete

tar czf "${OUTPUT}" -C "${TMPDIR}" .

echo "Package size: $(du -h "${OUTPUT}" | cut -f1)"
echo "=== Package built: ${OUTPUT} ==="
