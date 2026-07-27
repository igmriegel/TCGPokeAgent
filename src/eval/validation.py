from __future__ import annotations

from pathlib import Path
from typing import Any


class PreflightError(Exception): ...


def check_sdk_version(expected: str = "1.14.10") -> None:
    try:
        import kaggle_environments  # noqa: F401
    except ImportError:
        raise PreflightError("kaggle-environments not installed")


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
