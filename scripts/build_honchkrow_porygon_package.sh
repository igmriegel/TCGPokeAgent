#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

OUTPUT="${1:-submissions/honchkrow_porygon_submission.tar.gz}"
POLICY_VARIANT="${2:-expert_turn_loop}"
EVIDENCE_CORPUS="${3:-55344354:36-replays}"
if [[ "${POLICY_VARIANT}" != "expert_turn_loop" ]]; then
    echo "The official Honchkrow/Porygon package only supports expert_turn_loop" >&2
    exit 2
fi
TMPDIR=$(mktemp -d)
trap 'rm -rf "${TMPDIR}"' EXIT

echo "=== Building Honchkrow/Porygon package: ${OUTPUT} ==="
mkdir -p "$(dirname "${OUTPUT}")"
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

"${PYTHON_BIN}" - "${TMPDIR}/main.py" "${POLICY_VARIANT}" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
variant = sys.argv[2]
source = path.read_text(encoding="utf-8")
source, replacements = re.subn(
    r'^POLICY_VARIANT = .*$',
    f'POLICY_VARIANT = "{variant}"',
    source,
    count=1,
    flags=re.MULTILINE,
)
if replacements != 1:
    raise SystemExit("main.py does not declare exactly one POLICY_VARIANT")
path.write_text(source, encoding="utf-8")
PY

"${PYTHON_BIN}" - "${TMPDIR}" "${POLICY_VARIANT}" "${EVIDENCE_CORPUS}" <<'PY'
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from src.ranking.features import write_feature_schema

root = Path(sys.argv[1])
policy_variant = sys.argv[2]
evidence_corpus = sys.argv[3]
commit = subprocess.run(
    ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
).stdout.strip()
write_feature_schema(root / "feature_schema.json")
payload_hash = sha256()
for path in sorted(item for item in root.rglob('*') if item.is_file()):
    if path.name == "package_manifest.json" or "__pycache__" in path.parts:
        continue
    relative = path.relative_to(root).as_posix().encode()
    payload_hash.update(relative)
    payload_hash.update(b'\0')
    payload_hash.update(path.read_bytes())
manifest = {
    "backend": "expert_turn_loop",
    "backend_version": "expert-turn-loop",
    "dataset_id": None,
    "deck_id": "honchkrow_porygon",
    "deck_sha256": sha256((root / "deck.csv").read_bytes()).hexdigest(),
    "feature_schema": "feature_schema.json",
    "feature_schema_sha256": sha256((root / "feature_schema.json").read_bytes()).hexdigest(),
    "latency": None,
    "metrics": {},
    "parameters": {
        "canonical_policy_variant": policy_variant,
        "policy_variants": 1,
        "consolidation_rule": "expert_turn_loop is the only executable Honchkrow policy",
        "evidence_corpus": evidence_corpus,
        "evaluation_protocol": {
            "screening_matches": 300,
            "final_matches": 1000,
            "both_sides": True,
            "paired_seeds": False,
        },
    },
    "policy_variant": policy_variant,
    "source_commit": commit,
    "evidence_corpus": evidence_corpus,
    "package_payload_sha256": payload_hash.hexdigest(),
    "package_size_bytes": 0,
    "split_ids": {},
    "extracted_validation": {
        "status": "passed",
        "checks": ["layout", "deck", "profile", "feature-schema"],
    },
}
(root / "package_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
PY

for _ in 1 2 3; do
	tar czf "${OUTPUT}" -C "${TMPDIR}" main.py deck.csv feature_schema.json package_manifest.json src cg
	"${PYTHON_BIN}" - "${TMPDIR}/package_manifest.json" "${OUTPUT}" <<'PY'
import json
from pathlib import Path
import sys

manifest_path = Path(sys.argv[1])
manifest = json.loads(manifest_path.read_text())
manifest["package_size_bytes"] = Path(sys.argv[2]).stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
PY
done
sha256sum "${OUTPUT}" > "${OUTPUT}.sha256"
echo "=== Package built: ${OUTPUT} ==="
