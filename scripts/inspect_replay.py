"""Inspect Kaggle CABT replay frames without ad-hoc ``jq`` filters."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# noqa: E402 keeps the helper import after sys.path setup.
from src.data.replay_inspector import (  # noqa: E402
    filter_replay_frames,
    frame_as_text,
    frames_as_json,
    load_replay_frames,
    parse_int_list,
)


def main() -> None:
    """Parse CLI options and print matching replay frames."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path, help="Path to a Kaggle replay JSON file.")
    parser.add_argument(
        "--step",
        action="append",
        default=[],
        help="Filter to one or more replay step indices.",
    )
    parser.add_argument("--turn", type=int, help="Filter to one replay turn.")
    parser.add_argument(
        "--player-index",
        type=int,
        help="Filter to one player index from the replay observation.",
    )
    parser.add_argument(
        "--card-id",
        action="append",
        default=[],
        help="Keep frames whose logs include one of these card IDs.",
    )
    parser.add_argument(
        "--attack-id",
        action="append",
        default=[],
        help="Keep frames whose logs include one of these attack IDs.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Render matching frames as text or JSON.",
    )
    args = parser.parse_args()

    frames = load_replay_frames(args.replay)
    filtered = filter_replay_frames(
        frames,
        step_indices=parse_int_list(args.step) if args.step else None,
        turn=args.turn,
        your_index=args.player_index,
        card_ids=parse_int_list(args.card_id) if args.card_id else None,
        attack_ids=parse_int_list(args.attack_id) if args.attack_id else None,
    )

    if args.format == "json":
        print(json.dumps(frames_as_json(filtered), indent=2, ensure_ascii=False))
        return

    for index, frame in enumerate(filtered):
        if index > 0:
            print()
        print(frame_as_text(frame))


if __name__ == "__main__":
    main()
