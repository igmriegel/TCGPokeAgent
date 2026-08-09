"""Restore and hash-verify the immutable replay corpus used by T-034."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SUBMISSION_ID = "55333874"
HASHES_PATH = ROOT / "reports" / "replay_audits" / SUBMISSION_ID / "replay_hashes.json"
DEFAULT_OUTPUT = ROOT / "replays" / "remote" / SUBMISSION_ID


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest for one replay file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _expected_hashes(path: Path) -> dict[str, str]:
    """Load the frozen replay filename-to-hash mapping."""
    value: Any = json.loads(path.read_text(encoding="utf-8"))
    hashes = value.get("replay_sha256") if isinstance(value, dict) else None
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError(f"missing replay_sha256 mapping: {path}")
    if not all(
        isinstance(name, str) and isinstance(digest, str) for name, digest in hashes.items()
    ):
        raise ValueError("invalid replay hash mapping")
    return dict(hashes)


def _episode_id(filename: str) -> str:
    """Return the episode identifier encoded in one frozen replay name."""
    prefix = "episode-"
    suffix = "-replay.json"
    if not filename.startswith(prefix) or not filename.endswith(suffix):
        raise ValueError(f"unexpected replay filename: {filename}")
    return filename[len(prefix) : -len(suffix)]


def restore(output: Path, hashes: dict[str, str]) -> None:
    """Download every expected replay, verify it, and atomically publish the corpus."""
    with tempfile.TemporaryDirectory(prefix="t034-replay-restore-") as temporary:
        staging = Path(temporary)
        for filename in sorted(hashes):
            subprocess.run(
                [
                    "kaggle",
                    "competitions",
                    "replay",
                    _episode_id(filename),
                    "-p",
                    str(staging),
                    "-q",
                ],
                check=True,
            )
            downloaded = staging / filename
            if not downloaded.is_file():
                raise FileNotFoundError(f"Kaggle did not return expected replay: {filename}")
            actual = _sha256(downloaded)
            if actual != hashes[filename]:
                raise ValueError(f"hash mismatch for {filename}: {actual}")
        output.mkdir(parents=True, exist_ok=True)
        for filename in sorted(hashes):
            shutil.copy2(staging / filename, output / filename)


def main() -> int:
    """Restore the T-034 corpus after checking all frozen hashes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hashes", type=Path, default=HASHES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    hashes = _expected_hashes(args.hashes)
    restore(args.output, hashes)
    print(
        json.dumps(
            {"submission_id": SUBMISSION_ID, "replays": len(hashes), "output": str(args.output)}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
