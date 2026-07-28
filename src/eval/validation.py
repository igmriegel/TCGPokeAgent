from __future__ import annotations

import importlib
import io
import os
from collections.abc import Mapping
from contextlib import redirect_stderr, redirect_stdout
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from src.core.exceptions import PreflightError

DEFAULT_SDK_VERSION = "1.32.2"
REQUIRED_PACKAGE_PATHS = ("main.py", "src", "src/artifacts/deck.csv")

__all__ = [
    "DEFAULT_SDK_VERSION",
    "PreflightError",
    "check_agent_output",
    "check_cabt_import",
    "check_deck",
    "check_observation",
    "check_package_layout",
    "check_sdk_version",
    "check_writable",
]


def check_sdk_version(expected: str = DEFAULT_SDK_VERSION) -> str:
    """Validate that the installed SDK matches the pinned harness version.

    Args:
        expected: Exact ``kaggle-environments`` version required by the harness.

    Raises:
        PreflightError: If the distribution is absent or has a different version.

    Returns:
        The installed distribution version.
    """
    try:
        installed = version("kaggle-environments")
    except PackageNotFoundError as error:
        raise PreflightError("kaggle-environments not installed") from error

    if installed != expected:
        raise PreflightError(
            f"kaggle-environments version {installed} installed, expected {expected}"
        )
    return installed


def check_cabt_import() -> None:
    """Verify that the pinned SDK exposes the competition adapter.

    Raises:
        PreflightError: If the adapter cannot be imported or lacks ``first_agent``.
    """
    stdout_fd = os.dup(1)
    stderr_fd = os.dup(2)
    try:
        with open(os.devnull, "w", encoding="utf-8") as sink:
            os.dup2(sink.fileno(), 1)
            os.dup2(sink.fileno(), 2)
            with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                cabt = importlib.import_module("kaggle_environments.envs.cabt.cabt")
    except Exception as error:
        raise PreflightError(f"cabt adapter is not importable: {error}") from error
    finally:
        os.dup2(stdout_fd, 1)
        os.dup2(stderr_fd, 2)
        os.close(stdout_fd)
        os.close(stderr_fd)

    if not callable(getattr(cabt, "first_agent", None)):
        raise PreflightError("cabt adapter does not expose callable first_agent")


def check_package_layout(root: str | Path = ".") -> None:
    """Validate files required by the runnable package are present.

    Args:
        root: Repository or extracted package root to inspect.

    Raises:
        PreflightError: If a required package path is missing.
    """
    package_root = Path(root)
    missing = [path for path in REQUIRED_PACKAGE_PATHS if not (package_root / path).exists()]
    if missing:
        raise PreflightError(f"package layout missing: {', '.join(missing)}")


def check_deck(deck_path: str | Path) -> list[list[str]]:
    """Validate and load a 60-card deck file.

    Args:
        deck_path: Path to a newline-delimited CSV deck.

    Returns:
        The non-empty CSV rows in deterministic file order.

    Raises:
        PreflightError: If the file is missing, malformed, or not 60 cards long.
    """
    import csv

    path = Path(deck_path)
    if not path.exists():
        raise PreflightError(f"deck not found: {path}")

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        cards = list(reader)

    if len(cards) != 60:
        raise PreflightError(f"deck has {len(cards)} cards, expected 60")
    if any(len(row) != 1 or not row[0].strip() for row in cards):
        raise PreflightError("deck must contain one non-empty card identifier per row")
    try:
        if any(int(row[0]) <= 0 for row in cards):
            raise PreflightError("deck card identifiers must be positive integers")
    except ValueError as error:
        raise PreflightError("deck card identifiers must be integers") from error

    return cards


def check_agent_output(output: Any) -> None:
    """Validate the public agent output shape.

    Args:
        output: Value returned by an agent policy.

    Raises:
        PreflightError: If the value is not a list of integers.
    """
    if not isinstance(output, list):
        raise PreflightError(f"agent output is {type(output).__name__}, expected list[int]")
    for item in output:
        if isinstance(item, bool) or not isinstance(item, int):
            raise PreflightError(f"agent output contains {type(item).__name__}, expected int")


def check_writable(directory: str | Path) -> None:
    """Verify that an existing directory accepts a temporary file.

    Args:
        directory: Existing directory to probe.

    Raises:
        PreflightError: If the path is absent, not a directory, or not writable.
    """
    path = Path(directory)
    if not path.is_dir():
        raise PreflightError(f"writable directory not found: {path}")
    probe = path / ".write_test"
    try:
        probe.touch()
        probe.unlink()
    except OSError as e:
        raise PreflightError(f"directory not writable: {path}") from e


def check_observation(observation: Any) -> None:
    """Validate the outer shape of an SDK observation.

    Args:
        observation: Raw observation supplied to the agent.

    Raises:
        PreflightError: If observation sections have invalid container types.
    """
    if not isinstance(observation, Mapping):
        raise PreflightError("observation must be a mapping")

    for field in ("current", "select", "search_begin_input"):
        value = observation.get(field)
        if value is not None and not isinstance(value, Mapping):
            raise PreflightError(f"observation field {field!r} must be a mapping or null")

    select = observation.get("select")
    if select is None:
        return
    options = select.get("option")
    if not isinstance(options, list) or any(not isinstance(option, Mapping) for option in options):
        raise PreflightError("observation select.option must be a list of mappings")


def check_legal_selection(observation: Any, output: Any) -> None:
    """Validate selection indices against the active SDK decision.

    Args:
        observation: Raw SDK observation containing the current selection.
        output: Candidate option indices returned by the agent.

    Raises:
        PreflightError: If the output violates the decision bounds.
    """
    check_agent_output(output)
    if not isinstance(observation, Mapping):
        raise PreflightError("observation must be a mapping")
    select = observation.get("select")
    if select is None:
        return
    if not isinstance(select, Mapping):
        raise PreflightError("observation field 'select' must be a mapping or null")
    options = select.get("option")
    if not isinstance(options, list):
        raise PreflightError("observation select.option must be a list")
    if len(output) != len(set(output)):
        raise PreflightError("agent output contains duplicate option indices")
    if any(index < 0 or index >= len(options) for index in output):
        raise PreflightError("agent output contains an out-of-range option index")

    min_count = int(select.get("minCount", 0) or 0)
    max_count = int(select.get("maxCount", 0) or 0)
    if not min_count <= len(output) <= max_count:
        raise PreflightError(
            f"agent output has {len(output)} indices, expected between {min_count} and {max_count}"
        )

    energy_required = int(select.get("remainEnergyCost", 0) or 0)
    damage_required = int(select.get("remainDamageCounter", 0) or 0)
    selected_options = [options[index] for index in output]
    for required, field, label in (
        (energy_required, "count", "energy"),
        (damage_required, "count", "damage"),
    ):
        if required <= 0:
            continue
        counts = [option.get(field, 1) for option in selected_options]
        if any(isinstance(count, bool) or not isinstance(count, int) for count in counts):
            raise PreflightError(f"selected option {field} values must be integers")
        total = sum(counts)
        if total < required:
            raise PreflightError(
                f"agent output provides {total} {label} count, expected at least {required}"
            )
