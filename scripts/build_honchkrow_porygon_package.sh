#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

OUTPUT="${1:-honchkrow_porygon_submission.tar.gz}"
TMPDIR=$(mktemp -d)
trap 'rm -rf "${TMPDIR}"' EXIT

echo "=== Building Honchkrow/Porygon package: ${OUTPUT} ==="
cp main_honchkrow_porygon.py "${TMPDIR}/main.py"
cp src/artifacts/deck_team_rocket_murkrow.csv "${TMPDIR}/deck.csv"
mkdir -p "${TMPDIR}/src/agents" "${TMPDIR}/src/core" "${TMPDIR}/src/ranking" "${TMPDIR}/src/artifacts"
cp src/__init__.py "${TMPDIR}/src/"
cp src/agents/__init__.py src/agents/baseline.py src/agents/factory.py src/agents/hdi.py \
    src/agents/heuristic.py src/agents/honchkrow_porygon.py src/agents/search.py "${TMPDIR}/src/agents/"
cp src/core/*.py "${TMPDIR}/src/core/"
cp src/ranking/__init__.py src/ranking/features.py src/ranking/rankers.py "${TMPDIR}/src/ranking/"
cp src/artifacts/deck_profile_honchkrow_porygon.json "${TMPDIR}/src/artifacts/"
cp -r cg "${TMPDIR}/cg"
find "${TMPDIR}" -name '__pycache__' -type d -prune -exec rm -rf {} +
find "${TMPDIR}" -name '*.pyc' -delete

PYTHON_BIN="python"
if [[ -x .venv/bin/python ]]; then PYTHON_BIN=".venv/bin/python"; fi

"${PYTHON_BIN}" - "${TMPDIR}" <<'PY'
from hashlib import sha256
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
payload_hash = sha256()
for path in sorted(item for item in root.rglob('*') if item.is_file()):
    relative = path.relative_to(root).as_posix().encode()
    payload_hash.update(relative)
    payload_hash.update(b'\0')
    payload_hash.update(path.read_bytes())
manifest = {
    "backend": "heuristic",
    "deck_id": "honchkrow_porygon",
    "deck_sha256": sha256((root / "deck.csv").read_bytes()).hexdigest(),
    "package_payload_sha256": payload_hash.hexdigest(),
    "extracted_validation": {"status": "pending", "checks": ["layout", "deck", "profile"]},
}
(root / "package_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
PY

tar czf "${OUTPUT}" -C "${TMPDIR}" main.py deck.csv package_manifest.json src cg
sha256sum "${OUTPUT}" > "${OUTPUT}.sha256"
echo "=== Package built: ${OUTPUT} ==="
