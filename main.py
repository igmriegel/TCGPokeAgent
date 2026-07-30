"""Kaggle and command-line entry points for the Pokemon TCG agent."""

from __future__ import annotations

import json
import logging
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_SOURCE_PATH = globals().get("__file__")
_BOOTSTRAP_ROOT = (
    Path(_SOURCE_PATH).resolve().parent if isinstance(_SOURCE_PATH, str) else Path.cwd()
)
if not (_BOOTSTRAP_ROOT / "vendor").is_dir():
    _BOOTSTRAP_ROOT = next(
        (
            Path(entry).resolve()
            for entry in reversed(sys.path)
            if entry and (Path(entry).resolve() / "vendor").is_dir()
        ),
        _BOOTSTRAP_ROOT,
    )
_VENDOR_PATH = _BOOTSTRAP_ROOT / "vendor"
if _VENDOR_PATH.is_dir():
    sys.path.insert(0, str(_VENDOR_PATH))

from src.agents.factory import build_agent, load_deck, load_deck_profile  # noqa: E402
from src.core import AgentPolicy, DeckDefinition  # noqa: E402

logger = logging.getLogger(__name__)

_agent: AgentPolicy | None = None
_deck: list[int] | None = None


def _discover_project_root() -> Path:
    source_path = globals().get("__file__")
    if isinstance(source_path, str):
        return Path(source_path).resolve().parent
    kaggle_root = Path("/kaggle_simulations/agent")
    if (kaggle_root / "deck.csv").is_file():
        return kaggle_root
    for entry in reversed(sys.path):
        if not entry:
            continue
        candidate = Path(entry).resolve()
        if (candidate / "main.py").is_file() and (
            (candidate / "deck.csv").is_file()
            or (candidate / "src" / "artifacts" / "deck.csv").is_file()
        ):
            return candidate
    return Path.cwd()


_PROJECT_ROOT = _discover_project_root()


def _project_root() -> Path:
    return _PROJECT_ROOT


def _load_deck() -> list[int]:
    return load_deck(_project_root())


def _build_agent() -> AgentPolicy:
    return build_agent(_configured_agent_mode(), root=_project_root())


def _configured_agent_mode() -> str:
    configured = os.environ.get("AGENT_MODE")
    if configured:
        return configured
    manifest = _project_root() / "package_manifest.json"
    if manifest.is_file():
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            backend = payload.get("backend")
            if isinstance(backend, str):
                return backend
        except (OSError, json.JSONDecodeError):
            pass
    return "heuristic"


def _load_deck_profile() -> Any:
    """Load the optional declarative strategy bundled with the active deck."""
    return load_deck_profile(_project_root())


def agent_policy(observation: dict[str, Any]) -> list[int]:
    """Return a legal action for one CABT observation.

    Args:
        observation: Raw observation supplied by the CABT environment.

    Returns:
        Simulator option indices, or the canonical deck for the initial request.
    """
    global _agent, _deck

    if _agent is None:
        _agent = _build_agent()
    if _deck is None:
        _deck = _load_deck()

    select = observation.get("select")
    if select is None:
        _agent.start_match(DeckDefinition.from_cards(_deck, "active"))
        return list(_deck)

    try:
        result = _agent.select(observation)
        _validate_selection(observation, result)
        return result
    except Exception:
        return _fallback_selection(observation)


def _validate_selection(observation: Mapping[str, Any], output: list[int]) -> None:
    if any(isinstance(index, bool) or not isinstance(index, int) for index in output):
        raise ValueError("agent output must contain only integer indices")
    select = observation.get("select")
    if select is None:
        return
    if not isinstance(select, Mapping):
        raise ValueError("select must be a mapping")
    options = select.get("option")
    if not isinstance(options, list):
        raise ValueError("select.option must be a list")
    if len(output) != len(set(output)):
        raise ValueError("agent output contains duplicate indices")
    if any(index < 0 or index >= len(options) for index in output):
        raise ValueError("agent output contains an out-of-range index")

    min_count = int(select.get("minCount", 0) or 0)
    max_count = int(select.get("maxCount", 0) or 0)
    if not min_count <= len(output) <= max_count:
        raise ValueError("agent output violates selection cardinality")

    selected_options = [options[index] for index in output]
    counts = [
        option.get("count", 1) if isinstance(option, Mapping) else 1 for option in selected_options
    ]
    if any(isinstance(count, bool) or not isinstance(count, int) or count < 0 for count in counts):
        raise ValueError("selected option count values must be non-negative integers")


def _fallback_selection(observation: dict[str, Any]) -> list[int]:
    """Return the first deterministic selection satisfying SDK cardinality."""
    select = observation.get("select")
    if not isinstance(select, dict):
        return []
    options = select.get("option")
    if not isinstance(options, list):
        return []
    try:
        min_count = max(0, int(select.get("minCount", 0) or 0))
    except (TypeError, ValueError):
        return []
    count = min(min_count, len(options))
    fallback = list(range(count))
    try:
        _validate_selection(observation, fallback)
    except Exception:
        return []
    return fallback


def main() -> None:
    """Read one observation from stdin and write the selected action as JSON."""
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    logger.info("agent_started mode=%s", _configured_agent_mode())

    observation = _read_observation()
    result = agent_policy(observation)
    _write_result(result)


def _read_observation() -> dict[str, Any]:
    raw = sys.stdin.read()
    if raw:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def _write_result(result: list[int]) -> None:
    json.dump(result, sys.stdout, indent=None)
    sys.stdout.flush()


def agent(obs_dict: dict[str, Any]) -> list[int]:
    """Run the callable entry point discovered by ``kaggle-environments``.

    Args:
        obs_dict: Raw observation supplied by the simulation runtime.

    Returns:
        Simulator option indices, or the canonical deck for the initial request.
    """
    return agent_policy(obs_dict)


if __name__ == "__main__":
    main()
