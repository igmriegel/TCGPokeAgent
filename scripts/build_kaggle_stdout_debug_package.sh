#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

OUTPUT="${1:-submissions/honchkrow_porygon_stdout_debug.tar.gz}"
BASE_PACKAGE="$(mktemp --suffix=.tar.gz)"
TMPDIR="$(mktemp -d)"
trap 'rm -f "${BASE_PACKAGE}"; rm -rf "${TMPDIR}"' EXIT

scripts/build_honchkrow_porygon_package.sh "${BASE_PACKAGE}" expert_turn_loop
mkdir -p "$(dirname "${OUTPUT}")" "${TMPDIR}/package"
tar xzf "${BASE_PACKAGE}" -C "${TMPDIR}/package"

python3 - "${TMPDIR}/package/main.py" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
source = source.replace(
    "import logging\nimport sys\n",
    "import logging\nimport sys\nfrom dataclasses import asdict, is_dataclass\n",
    1,
)
source = source.replace(
    "_deck: list[int] | None = None\n",
    """_deck: list[int] | None = None


def _emit_stdout_debug() -> None:
    decision = getattr(_agent, "last_decision", None)
    if decision is None:
        return
    payload = {
        "event": "debug_decision",
        "decision_phase": decision.decision_phase,
        "decision_phase_reason": decision.decision_phase_reason,
        "fallback_used": decision.fallback_used,
        "model_backend": decision.model_backend,
        "duration_ms": decision.duration_ms,
        "trace": asdict(decision.trace) if is_dataclass(decision.trace) else None,
    }
    print(json.dumps(payload, separators=(",", ":")), flush=True)
""",
    1,
)
source = source.replace(
    "        result = _agent.select(observation)\n        _validate_selection(observation, result)\n",
    "        result = _agent.select(observation)\n        _emit_stdout_debug()\n        _validate_selection(observation, result)\n",
    1,
)
path.write_text(source, encoding="utf-8")
PY

python3 - "${TMPDIR}/package" <<'PY'
from hashlib import sha256
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
digest = sha256()
for path in sorted(item for item in root.rglob("*") if item.is_file()):
    if path.name == "package_manifest.json" or "__pycache__" in path.parts:
        continue
    digest.update(path.relative_to(root).as_posix().encode())
    digest.update(b"\0")
    digest.update(path.read_bytes())
manifest_path = root / "package_manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["package_payload_sha256"] = digest.hexdigest()
manifest["parameters"]["stdout_debug"] = True
manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
PY

tar czf "${OUTPUT}" -C "${TMPDIR}/package" \
    main.py deck.csv feature_schema.json package_manifest.json src cg
python3 - "${TMPDIR}/package/package_manifest.json" "${OUTPUT}" <<'PY'
import json
from pathlib import Path
import sys

manifest_path = Path(sys.argv[1])
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["package_size_bytes"] = Path(sys.argv[2]).stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
PY
tar czf "${OUTPUT}" -C "${TMPDIR}/package" \
    main.py deck.csv feature_schema.json package_manifest.json src cg
sha256sum "${OUTPUT}" > "${OUTPUT}.sha256"
echo "=== Kaggle stdout-debug package built: ${OUTPUT} ==="
echo "Package size: $(du -h "${OUTPUT}" | cut -f1)"
echo "Package SHA-256: $(cut -d' ' -f1 "${OUTPUT}.sha256")"
