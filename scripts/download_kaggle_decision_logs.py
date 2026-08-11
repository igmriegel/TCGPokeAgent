"""Download, decode, and annotate all available decision logs for a Kaggle submission."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

from decode_kaggle_decision_ledger import (
    DICTIONARY_PATH,
    annotate_record,
    decode_events,
    load_dictionary,
)

COMPETITION = "pokemon-tcg-ai-battle"
DEFAULT_OWNER_NAME = "mudkip_mini_chicken"
DEFAULT_REPLAY_DIR = Path("data/raw/kaggle/replays/remote")
DEFAULT_OUTPUT_DIR = Path("data/raw/kaggle/decision_logs")


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


def _download_log(episode_id: str, agent_index: int, destination: Path) -> Path | None:
    """Download an accessible agent log, returning ``None`` for Kaggle-forbidden logs."""
    destination.mkdir(parents=True, exist_ok=True)
    expected_paths = (
        destination / f"{episode_id}-{agent_index}",
        destination / f"episode-{episode_id}-agent-{agent_index}-logs.json",
    )
    for path in expected_paths:
        if path.is_file():
            return path
    try:
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
    except subprocess.CalledProcessError as error:
        if error.returncode == 1:
            return None
        raise
    for path in expected_paths:
        if path.is_file():
            return path
    expected = ", ".join(str(path) for path in expected_paths)
    raise FileNotFoundError(f"Kaggle did not return an expected agent log: {expected}")


def _load_replay(episode_id: str, replay_dir: Path, destination: Path) -> dict[str, Any]:
    """Load a replay, downloading it once when it is absent from the local mirror."""
    candidates = (
        replay_dir / f"{episode_id}.json",
        destination / f"episode-{episode_id}-replay.json",
    )
    for path in candidates:
        if path.is_file():
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
            raise ValueError(f"replay must be a mapping: {path}")

    destination.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["kaggle", "competitions", "replay", episode_id, "-p", str(destination), "-q"],
        check=True,
    )
    path = destination / f"episode-{episode_id}-replay.json"
    if not path.is_file():
        raise FileNotFoundError(f"Kaggle did not return expected replay: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"replay must be a mapping: {path}")
    return payload


def _owner_agent_indices(replay: Mapping[str, Any], owner_name: str) -> list[int]:
    """Return every replay seat belonging to the submitted agent name."""
    info = replay.get("info")
    if not isinstance(info, Mapping):
        raise ValueError("replay info must be a mapping")
    agents = info.get("Agents")
    if not isinstance(agents, list):
        raise ValueError("replay info Agents must be a list")
    indices = [
        index
        for index, agent in enumerate(agents)
        if isinstance(agent, Mapping) and agent.get("Name") == owner_name
    ]
    if not indices:
        episode_id = info.get("EpisodeId", "unknown")
        raise ValueError(f"owner {owner_name!r} is absent from replay {episode_id}")
    return indices


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
    """Download and annotate submitted-agent logs for completed submission episodes."""
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
        help="Explicit agent index to process; bypasses replay-based owner resolution.",
    )
    parser.add_argument(
        "--owner-name",
        default=DEFAULT_OWNER_NAME,
        help="Kaggle display name of the submission owner used to resolve replay seats.",
    )
    parser.add_argument(
        "--replay-dir",
        type=Path,
        default=DEFAULT_REPLAY_DIR,
        help=(
            "Local Kaggle replay mirror; missing replays are downloaded into the output directory."
        ),
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
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
    output_root = args.output_dir / args.submission_id
    output_root.mkdir(parents=True, exist_ok=True)
    dictionary_target = output_root / DICTIONARY_PATH.name
    dictionary_target.write_text(DICTIONARY_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    decoded_total = 0
    downloaded: list[dict[str, Any]] = []
    for episode in episodes:
        episode_id = str(episode["id"])
        agent_indices = args.agent_index
        if not agent_indices:
            replay_directory = args.replay_dir / args.submission_id
            replay = _load_replay(
                episode_id,
                replay_directory,
                replay_directory,
            )
            agent_indices = _owner_agent_indices(replay, args.owner_name)
        for agent_index in agent_indices:
            log_path = _download_log(episode_id, agent_index, output_root / "raw")
            if log_path is None:
                continue
            count = _write_decoded_log(log_path, output_root)
            decoded_total += count
            downloaded.append(
                {
                    "episode_id": episode_id,
                    "agent_index": agent_index,
                    "owner_name": args.owner_name,
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
