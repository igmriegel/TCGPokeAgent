"""Build, validate, and optionally submit the simulation agent to Kaggle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

COMPETITION = "pokemon-tcg-ai-battle"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive",
        type=Path,
        default=PROJECT_ROOT / "submission.tar.gz",
        help="Output archive path.",
    )
    parser.add_argument(
        "--message",
        help="Kaggle submission message. A timestamped message is used by default.",
    )
    parser.add_argument(
        "--agent-mode",
        default="heuristic",
        choices=("baseline", "heuristic", "hdi_v1", "rfl"),
        help="Agent mode used by the smoke gate.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Submit without the interactive confirmation prompt.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run every local gate and print the submission command without uploading.",
    )
    parser.add_argument(
        "--skip-quality",
        action="store_true",
        help="Skip tests, Ruff, and mypy.",
    )
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="Skip the 20-seed, both-side SDK smoke gate.",
    )
    return parser


def _run(
    command: Sequence[str],
    *,
    cwd: Path = PROJECT_ROOT,
    env: dict[str, str] | None = None,
) -> None:
    print(f"\n$ {' '.join(command)}", flush=True)
    completed = subprocess.run(command, cwd=cwd, env=env, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed with exit code {completed.returncode}: {' '.join(command)}"
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _submission_command(kaggle: str, archive: Path, message: str) -> list[str]:
    return [
        kaggle,
        "competitions",
        "submit",
        COMPETITION,
        "-f",
        str(archive),
        "-m",
        message,
    ]


def _confirmed(answer: str) -> bool:
    return answer.strip().lower() in {"y", "yes"}


def _submission_env() -> dict[str, str]:
    """Return the environment used for the Kaggle CLI submission step.

    The submission command should use the Kaggle credentials already configured
    in the user's home directory. If a local shell session exported
    ``KAGGLE_CONFIG_DIR`` to the repository root, remove it so the CLI does not
    prefer the repo-local token file over the logged-in home credentials.

    Returns:
        A copy of the current environment suitable for the Kaggle CLI.
    """
    env = os.environ.copy()
    if not env.get("KAGGLE_API_TOKEN"):
        local_credentials = PROJECT_ROOT / "kaggle.json"
        try:
            credentials = json.loads(local_credentials.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            credentials = {}
        token = credentials.get("key") if isinstance(credentials, dict) else None
        if isinstance(token, str) and token:
            env["KAGGLE_API_TOKEN"] = token
            print("Using the ignored repository kaggle.json as KAGGLE_API_TOKEN.", flush=True)
    config_dir = env.get("KAGGLE_CONFIG_DIR")
    if config_dir is None:
        return env

    try:
        resolved = Path(config_dir).expanduser().resolve()
    except OSError:
        return env

    if resolved == PROJECT_ROOT:
        env.pop("KAGGLE_CONFIG_DIR", None)
        print(
            "\nIgnoring KAGGLE_CONFIG_DIR=repo-root for Kaggle submission; "
            "using the authenticated ~/.kaggle credentials instead.",
            flush=True,
        )
    return env


def _write_receipt(archive: Path, digest: str, message: str) -> Path:
    timestamp = datetime.now(timezone.utc)
    receipt_dir = PROJECT_ROOT / "reports" / "submissions"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt = receipt_dir / f"{timestamp:%Y%m%dT%H%M%SZ}-{digest[:12]}.json"
    receipt.write_text(
        json.dumps(
            {
                "competition": COMPETITION,
                "submitted_at": timestamp.isoformat(),
                "archive": str(archive),
                "archive_bytes": archive.stat().st_size,
                "archive_sha256": digest,
                "message": message,
                "status": "submitted",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return receipt


def main(argv: list[str] | None = None) -> int:
    """Run all local gates and submit only after explicit confirmation."""
    args = _parser().parse_args(argv)
    archive = args.archive.expanduser().resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    python = sys.executable

    commands: list[list[str]] = [
        [python, "-m", "scripts.preflight", "--root", str(PROJECT_ROOT)],
    ]
    if not args.skip_quality:
        commands.extend(
            [
                [python, "-m", "pytest", "tests", "-q"],
                [python, "-m", "ruff", "check", "src", "tests", "main.py", "scripts"],
                [python, "-m", "mypy", "--config-file=pyproject.toml", "src"],
            ]
        )
    if not args.skip_smoke:
        commands.extend(
            [
                [
                    python,
                    "-m",
                    "scripts.cabt_smoke",
                    "--matches",
                    "20",
                    "--agent-mode",
                    args.agent_mode,
                ],
                [
                    python,
                    "-m",
                    "scripts.gameplay_smoke",
                    "--matches",
                    "5",
                    "--agent-mode",
                    args.agent_mode,
                    "--opponent",
                    "random",
                ],
            ]
        )

    try:
        for command in commands:
            _run(command)
        package_backend = args.agent_mode if args.agent_mode == "hdi_v1" else "heuristic"
        _run(["scripts/build_package.sh", str(archive), package_backend])
        _run([python, "-m", "src.eval.validation", "--package", str(archive)])
    except (OSError, RuntimeError) as error:
        print(f"\nSUBMISSION PIPELINE FAILED: {error}", file=sys.stderr)
        return 3

    digest = _sha256(archive)
    message = args.message or (
        f"{args.agent_mode} {datetime.now(timezone.utc):%Y-%m-%dT%H:%MZ} sha256:{digest[:12]}"
    )
    kaggle = shutil.which("kaggle")
    if kaggle is None:
        print(
            "\nKaggle CLI was not found. Install/configure it before submitting.",
            file=sys.stderr,
        )
        return 2
    command = _submission_command(kaggle, archive, message)

    print("\nSubmission candidate ready:")
    print(f"  competition: {COMPETITION}")
    print(f"  archive:     {archive}")
    print(f"  bytes:       {archive.stat().st_size}")
    print(f"  sha256:      {digest}")
    print(f"  message:     {message}")

    if args.dry_run:
        print(f"\nDRY RUN — upload skipped.\n$ {' '.join(command)}")
        return 0

    if not args.yes:
        try:
            answer = input("\nSubmit this archive to Kaggle now? [y/N] ")
        except EOFError:
            answer = ""
        if not _confirmed(answer):
            print("Submission cancelled; the validated archive was preserved.")
            return 0

    try:
        _run(command, env=_submission_env())
    except (OSError, RuntimeError) as error:
        print(f"\nKAGGLE SUBMISSION FAILED: {error}", file=sys.stderr)
        return 4

    receipt = _write_receipt(archive, digest, message)
    print(f"\nSubmission command completed. Receipt: {receipt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
