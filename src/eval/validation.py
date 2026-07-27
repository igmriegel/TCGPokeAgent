from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any


class PreflightError(Exception):
    """Report an evaluation preflight failure."""


def check_sdk_version(expected: str = "1.32.2") -> None:
    """Validate that the installed SDK matches the pinned harness version.

    Args:
        expected: Exact ``kaggle-environments`` version required by the harness.

    Raises:
        PreflightError: If the distribution is absent or has a different version.
    """
    try:
        installed = version("kaggle-environments")
    except PackageNotFoundError as error:
        raise PreflightError("kaggle-environments not installed") from error

    if installed != expected:
        raise PreflightError(
            f"kaggle-environments version {installed} installed, expected {expected}"
        )


def check_deck(deck_path: str | Path) -> list[Any]:
    import csv

    path = Path(deck_path)
    if not path.exists():
        raise PreflightError(f"deck not found: {path}")

    with open(path) as f:
        reader = csv.reader(f)
        cards = list(reader)

    if len(cards) != 60:
        raise PreflightError(f"deck has {len(cards)} cards, expected 60")

    return cards


def check_agent_output(output: Any) -> None:
    if not isinstance(output, list):
        raise PreflightError(f"agent output is {type(output).__name__}, expected list[int]")
    for item in output:
        if not isinstance(item, int):
            raise PreflightError(f"agent output contains {type(item).__name__}, expected int")


def check_writable(directory: str | Path) -> None:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    probe = path / ".write_test"
    try:
        probe.touch()
        probe.unlink()
    except OSError as e:
        raise PreflightError(f"directory not writable: {path}") from e
