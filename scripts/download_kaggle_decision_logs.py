"""Download, decode, and annotate all available decision logs for a Kaggle submission."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from decode_kaggle_decision_ledger import (
    DICTIONARY_PATH,
    annotate_record,
    decode_events,
    load_dictionary,
)

COMPETITION = "pokemon-tcg-ai-battle"


def _episodes(submission_id: str) -> list[dict[str, Any]]:
    """List completed Kaggle simulation episodes for a submission."""
    result = subprocess.run(
        ["kaggle", "competitions", "episodes", submission_id, "--format", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout[: result.stdout.rfind("]") + 1])
    if not isinstance(payload, list):
        raise ValueError("Kaggle episodes response must be a list")
    return [
        episode
        for episode in payload
        if isinstance(episode, dict) and episode.get("state") == "EpisodeState.COMPLETED"
    ]


def _download_log(episode_id: str, agent_index: int, destination: Path) -> Path:
    """Download one agent's stdout/stderr log and return its expected local path."""
    destination.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "kaggle",
            "competitions",
            "logs",
            episode_id,
            str(agent_index),
            "-p",
            str(destination),
            "-q",
        ],
        check=True,
    )
    path = destination / f"{episode_id}-{agent_index}"
    if not path.is_file():
        raise FileNotFoundError(f"Kaggle did not return expected agent log: {path}")
    return path


def _write_decoded_log(log_path: Path, output_root: Path) -> int:
    """Write decoded and annotated JSONL files plus a provenance manifest."""
    raw = log_path.read_text(encoding="utf-8")
    records = decode_events(raw)
    stem = log_path.name
    decoded_path = output_root / "decoded" / f"{stem}.jsonl"
    annotated_path = output_root / "annotated" / f"{stem}.jsonl"
    decoded_path.parent.mkdir(parents=True, exist_ok=True)
    annotated_path.parent.mkdir(parents=True, exist_ok=True)
    decoded_path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8"
    )
    annotated_path.write_text(
        "".join(json.dumps(annotate_record(record), sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    return len(records)


def main() -> None:
    """Download and annotate both agent logs for completed submission episodes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission_id", help="Kaggle simulation submission ID.")
    parser.add_argument(
        "--episode-id",
        action="append",
        default=[],
        help="Completed episode ID to process; repeatable.",
    )
    parser.add_argument(
        "--agent-index",
        action="append",
        type=int,
        choices=(0, 1),
        default=[],
        help="Agent index to process; defaults to both.",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("logs/kaggle"))
    args = parser.parse_args()

    available = _episodes(args.submission_id)
    requested = set(args.episode_id)
    episodes = [
        episode for episode in available if not requested or str(episode.get("id")) in requested
    ]
    found = {str(episode.get("id")) for episode in episodes}
    missing = requested - found
    if missing:
        raise ValueError(f"completed episodes not found: {', '.join(sorted(missing))}")
    agent_indices = args.agent_index or [0, 1]
    output_root = args.output_dir / args.submission_id
    output_root.mkdir(parents=True, exist_ok=True)
    dictionary_target = output_root / DICTIONARY_PATH.name
    dictionary_target.write_text(DICTIONARY_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    decoded_total = 0
    downloaded: list[dict[str, Any]] = []
    for episode in episodes:
        episode_id = str(episode["id"])
        for agent_index in agent_indices:
            log_path = _download_log(episode_id, agent_index, output_root / "raw")
            count = _write_decoded_log(log_path, output_root)
            decoded_total += count
            downloaded.append(
                {
                    "episode_id": episode_id,
                    "agent_index": agent_index,
                    "log": str(log_path),
                    "sha256": hashlib.sha256(log_path.read_bytes()).hexdigest(),
                    "decoded_decisions": count,
                }
            )
    (output_root / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "kaggle-decision-log-download-v1",
                "competition": COMPETITION,
                "submission_id": args.submission_id,
                "dictionary": DICTIONARY_PATH.name,
                "dictionary_schema": load_dictionary()["schema_version"],
                "logs": downloaded,
                "decoded_decisions": decoded_total,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(output_root),
                "logs": len(downloaded),
                "decoded_decisions": decoded_total,
            }
        )
    )


if __name__ == "__main__":
    main()
