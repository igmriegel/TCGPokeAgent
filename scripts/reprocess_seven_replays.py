"""Reprocess the seven state-based review replays with the current policy."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import audit_submission_55333874 as audit  # noqa: E402

EPISODES = (92410349, 92351382, 92344156, 92301028, 92280407, 92269436, 92201785)
SUBMISSION_REPLAY_DIR = Path("data/raw/kaggle/replays/remote/55422182")
OWNER_NAME = "mudkip_mini_chicken"


def _resolve_owner(replay: Mapping[str, Any], deck: list[int]) -> int:
    """Resolve the reviewed policy side by public replay agent name."""
    del deck
    agents = replay.get("info", {}).get("Agents", [])
    matches = [
        index
        for index, agent in enumerate(agents)
        if isinstance(agent, Mapping) and agent.get("Name") == OWNER_NAME
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one {OWNER_NAME!r} side, found {matches}")
    return matches[0]


def reprocess(source_dir: Path, output: Path) -> None:
    """Run the current policy over all seven replay decision streams."""
    with tempfile.TemporaryDirectory(prefix="seven-replay-reprocess-") as temporary:
        replay_dir = Path(temporary)
        for episode in EPISODES:
            source = source_dir / f"episode-{episode}-replay.json"
            if not source.is_file():
                raise FileNotFoundError(source)
            shutil.copy2(source, replay_dir / source.name)
        original_resolver = audit._resolve_owner
        audit._resolve_owner = _resolve_owner
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
            audit._run_worker(replay_dir, output, "expert_turn_loop", None)
        finally:
            audit._resolve_owner = original_resolver


def main() -> int:
    """Parse paths and execute the seven-replay reprocessing."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=SUBMISSION_REPLAY_DIR)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/replay_audits/seven_state_based_20260813/reprocessed.json"),
    )
    args = parser.parse_args()
    reprocess(args.source_dir, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
