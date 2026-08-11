"""Audit the owner-provided Honchkrow replay set and emit stable evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.replay_deep_analysis import load_all_deep_analyses  # noqa: E402
from src.data.replay_diagnostics import diagnose_replay  # noqa: E402

EXPECTED_EPISODES = {
    91758635,
    91759604,
    91759546,
    91760528,
    91762444,
    91763370,
    91765226,
    91767096,
    91768028,
    91769879,
    91764307,
    91770820,
    91771748,
    91775439,
}


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest of a replay file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    """Validate the evidence set and write replay-level diagnostics."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay_dir", type=Path)
    parser.add_argument("--owner-name", default="mudkip_mini_chicken")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    analyses = load_all_deep_analyses(args.replay_dir, owner_name=args.owner_name)
    actual = {analysis.episode_id for analysis in analyses}
    missing = sorted(EXPECTED_EPISODES - actual)
    unexpected = sorted(actual - EXPECTED_EPISODES)
    if missing or unexpected:
        raise SystemExit(f"replay set mismatch: missing={missing}, unexpected={unexpected}")

    diagnostics = [diagnose_replay(analysis) for analysis in analyses]
    files = sorted(args.replay_dir.glob("*.json"))
    report = {
        "report_type": "owner_honchkrow_replay_audit_v1",
        "owner_name": args.owner_name,
        "episodes": sorted(actual),
        "files": [{"path": str(path), "sha256": _sha256(path)} for path in files],
        "diagnostics": [asdict(item) for item in diagnostics],
        "reconciled": all(
            item.reason_consistent and item.result_consistent for item in diagnostics
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"episodes": len(actual), "reconciled": report["reconciled"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
