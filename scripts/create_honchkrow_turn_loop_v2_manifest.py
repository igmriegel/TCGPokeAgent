"""Create a reproducible foundation manifest for the expert turn-loop track."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DECK_PATH = ROOT / "src/artifacts/deck_team_rocket_murkrow.csv"
PROFILE_PATH = ROOT / "src/artifacts/deck_profile_honchkrow_porygon.json"
LOCK_PATH = ROOT / "uv.lock"
REPLAY_HASHES_PATH = ROOT / "reports/replay_audits/55333874/replay_hashes.json"


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest of one file.

    Args:
        path: File to hash.

    Returns:
        Lowercase hexadecimal SHA-256 digest.
    """
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(*args: str) -> str:
    """Run a read-only Git query.

    Args:
        *args: Arguments passed after ``git``.

    Returns:
        Stripped standard output, or ``unknown`` when Git is unavailable.
    """
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def build_manifest() -> dict[str, Any]:
    """Build the HLV2 immutable-input manifest.

    Returns:
        JSON-serializable manifest containing policy and evidence identities.
    """
    replay_manifest = json.loads(REPLAY_HASHES_PATH.read_text(encoding="utf-8"))
    status_lines = _git("status", "--porcelain=v1").splitlines()
    dirty_paths = [
        line[3:] if len(line) > 3 and line[2] == " " else line.split(maxsplit=1)[-1]
        for line in status_lines
        if line
    ]
    implementation_paths = (
        ROOT / "src/agents/honchkrow_porygon.py",
        ROOT / "scripts/run_honchkrow_porygon_eval.py",
        ROOT / "scripts/compare_honchkrow_reports.py",
        ROOT / "scripts/build_honchkrow_turn_loop_v2_report.py",
        ROOT / "scripts/create_honchkrow_turn_loop_v2_manifest.py",
        ROOT / "scripts/summarize_honchkrow_turn_loop_v2_replays.py",
        ROOT / "scripts/audit_submission_55333874.py",
    )
    return {
        "schema": "honchkrow_turn_loop_v2_foundation_manifest_v1",
        "baseline_variant": "supporter_resource_v2",
        "candidate_variant": "expert_turn_loop",
        "source": {
            "commit": _git("rev-parse", "HEAD"),
            "worktree_dirty": bool(dirty_paths),
            "dirty_paths": sorted(dirty_paths),
            "uv_lock_sha256": _sha256(LOCK_PATH),
            "implementation_sha256": {
                str(path.relative_to(ROOT)): _sha256(path) for path in implementation_paths
            },
        },
        "runtime": {
            "python": sys.version.split()[0],
            "kaggle_environments": importlib.metadata.version("kaggle-environments"),
            "cabt_sdk_pin": "kaggle-environments==1.32.2",
        },
        "immutable_inputs": {
            "deck_path": str(DECK_PATH.relative_to(ROOT)),
            "deck_sha256": _sha256(DECK_PATH),
            "profile_path": str(PROFILE_PATH.relative_to(ROOT)),
            "profile_sha256": _sha256(PROFILE_PATH),
            "deck_or_profile_changes_allowed": False,
        },
        "historical_corpus": {
            "submission_id": 55333874,
            "episode_count": len(replay_manifest["episode_ids"]),
            "episode_ids": replay_manifest["episode_ids"],
            "corpus_sha256": replay_manifest["corpus_sha256"],
            "replay_hashes_path": str(REPLAY_HASHES_PATH.relative_to(ROOT)),
        },
        "evaluation_protocol": {
            "screening_matches_per_policy": 300,
            "final_matches_per_policy": 1000,
            "both_sides": True,
            "final_seed_pairing": False,
            "remote_kaggle_is_promotion_gate": False,
        },
    }


def write_manifest(output: Path) -> Path:
    """Write the deterministic manifest.

    Args:
        output: Destination JSON path.

    Returns:
        The destination path.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(build_manifest(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def main() -> int:
    """Parse CLI arguments and write the manifest.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports/honchkrow_turn_loop_v2/foundation/manifest.json",
    )
    args = parser.parse_args()
    print(write_manifest(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
