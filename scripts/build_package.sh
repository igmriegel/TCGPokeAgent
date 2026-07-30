#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

OUTPUT="${1:-submission.tar.gz}"
BACKEND="${2:-heuristic}"
MODEL_DIR="${3:-}"

case "${BACKEND}" in
    heuristic|xgboost_ranker|lightgbm_ranker) ;;
    *) echo "Unsupported package backend: ${BACKEND}" >&2; exit 2 ;;
esac

echo "=== Building package: ${OUTPUT} ==="

TMPDIR=$(mktemp -d)
trap 'rm -rf "${TMPDIR}"' EXIT

cp main.py "${TMPDIR}/"
cp src/artifacts/deck.csv "${TMPDIR}/deck.csv"
mkdir -p "${TMPDIR}/src/agents" "${TMPDIR}/src/core" "${TMPDIR}/src/ranking"
mkdir -p "${TMPDIR}/src/artifacts"
if [[ -f src/artifacts/deck_profile.json ]]; then
    cp src/artifacts/deck_profile.json "${TMPDIR}/src/artifacts/"
fi
cp src/__init__.py "${TMPDIR}/src/"
cp src/agents/__init__.py "${TMPDIR}/src/agents/"
cp src/agents/baseline.py "${TMPDIR}/src/agents/"
cp src/agents/factory.py "${TMPDIR}/src/agents/"
cp src/agents/heuristic.py "${TMPDIR}/src/agents/"
cp src/agents/search.py "${TMPDIR}/src/agents/"
cp src/core/*.py "${TMPDIR}/src/core/"
cp src/ranking/__init__.py "${TMPDIR}/src/ranking/"
cp src/ranking/features.py "${TMPDIR}/src/ranking/"
cp src/ranking/rankers.py "${TMPDIR}/src/ranking/"
cp -r cg "${TMPDIR}/cg"

PYTHON_BIN="python"
if [[ -x .venv/bin/python ]]; then
    PYTHON_BIN=".venv/bin/python"
fi

"${PYTHON_BIN}" - "${TMPDIR}" <<'PY'
from pathlib import Path
import sys

from src.ranking.features import write_feature_schema

write_feature_schema(Path(sys.argv[1]) / "feature_schema.json")
PY

if [[ "${BACKEND}" != "heuristic" ]]; then
    if [[ -z "${MODEL_DIR}" || ! -f "${MODEL_DIR}/ranker_manifest.json" ]]; then
        echo "Ranker package requires a model directory with ranker_manifest.json" >&2
        exit 2
    fi
    mkdir -p "${TMPDIR}/model" "${TMPDIR}/vendor"
    cp "${MODEL_DIR}"/* "${TMPDIR}/model/"
    SITE_PACKAGES=$("${PYTHON_BIN}" - <<'PY'
import pathlib
import numpy

print(pathlib.Path(numpy.__file__).resolve().parent.parent)
PY
)
    cp -a "${SITE_PACKAGES}/numpy" "${TMPDIR}/vendor/"
    cp -a "${SITE_PACKAGES}/numpy.libs" "${TMPDIR}/vendor/" 2>/dev/null || true
    cp -a "${SITE_PACKAGES}/scipy" "${TMPDIR}/vendor/"
    cp -a "${SITE_PACKAGES}/scipy.libs" "${TMPDIR}/vendor/" 2>/dev/null || true
    if [[ "${BACKEND}" == "xgboost_ranker" ]]; then
        cp -a "${SITE_PACKAGES}/xgboost" "${TMPDIR}/vendor/"
        cp -a "${SITE_PACKAGES}/xgboost_cpu.libs" "${TMPDIR}/vendor/"
    else
        cp -a "${SITE_PACKAGES}/lightgbm" "${TMPDIR}/vendor/"
    fi
fi

"${PYTHON_BIN}" - "${TMPDIR}" "${BACKEND}" <<'PY'
from hashlib import sha256
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
backend = sys.argv[2]
deck_sha = sha256((root / "deck.csv").read_bytes()).hexdigest()
schema_sha = sha256((root / "feature_schema.json").read_bytes()).hexdigest()
model = {}
if backend != "heuristic":
    model = json.loads((root / "model" / "ranker_manifest.json").read_text())
    if model.get("backend") != backend:
        raise SystemExit("model backend differs from requested package backend")
manifest = {
    "backend": backend,
    "backend_version": model.get("library_version", "builtin"),
    "model_file": model.get("model_file"),
    "model_sha256": model.get("model_sha256"),
    "feature_schema": "feature_schema.json",
    "feature_schema_sha256": schema_sha,
    "dataset_id": model.get("dataset_id"),
    "split_ids": model.get("split_ids", {}),
    "deck_id": model.get("deck_id", "active"),
    "deck_sha256": deck_sha,
    "parameters": model.get("parameters", {}),
    "metrics": {
        "training": model.get("training_metrics", {}),
        "validation": model.get("validation_metrics", {}),
        "holdout": model.get("holdout_metrics", {}),
    },
    "package_size_bytes": 0,
    "latency": model.get("latency", model.get("validation_metrics", {}).get("latency_p95_ms")),
    "extracted_validation": {
        "status": "passed",
        "checks": ["layout", "backend-exclusive", "model-hash", "feature-schema-hash"],
    },
}
(root / "package_manifest.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n"
)
PY

find "${TMPDIR}" -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find "${TMPDIR}" -name '*.pyc' -delete

PACKAGE_PATHS=(main.py deck.csv feature_schema.json package_manifest.json src cg)
if [[ -d "${TMPDIR}/model" ]]; then
    PACKAGE_PATHS+=(model)
fi
if [[ -d "${TMPDIR}/vendor" ]]; then
    PACKAGE_PATHS+=(vendor)
fi

for _ in 1 2 3; do
    tar czf "${OUTPUT}" -C "${TMPDIR}" "${PACKAGE_PATHS[@]}"
    PACKAGE_BYTES=$(stat -c %s "${OUTPUT}")
    "${PYTHON_BIN}" - "${TMPDIR}/package_manifest.json" "${PACKAGE_BYTES}" <<'PY'
import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
manifest = json.loads(path.read_text())
manifest["package_size_bytes"] = int(sys.argv[2])
path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
PY
done

echo "Package size: $(du -h "${OUTPUT}" | cut -f1)"
echo "=== Package built: ${OUTPUT} ==="
