"""Build a replay-derived CABT damage and failure diagnostics report."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.replay_deep_analysis import load_all_deep_analyses  # noqa: E402
from src.data.replay_diagnostics import (  # noqa: E402
    aggregate_replay_diagnostics,
    diagnose_replay,
)


def main() -> None:
    """Parse replay files and write aggregate plus per-replay diagnostics."""
    parser = argparse.ArgumentParser()
    parser.add_argument("replay_dir", type=Path)
    parser.add_argument("--owner-name", default="Igor Riegel")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    analyses = load_all_deep_analyses(args.replay_dir, owner_name=args.owner_name)
    diagnostics = [diagnose_replay(analysis) for analysis in analyses]
    report = {
        "report_type": "cabt_replay_damage_diagnostics_v1",
        "owner_name": args.owner_name,
        "source_directory": str(args.replay_dir),
        "aggregate": aggregate_replay_diagnostics(diagnostics),
        "replays": [asdict(item) for item in diagnostics],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["aggregate"], sort_keys=True))


if __name__ == "__main__":
    main()
