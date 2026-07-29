"""Kaggle and command-line entry points for the Pokemon TCG agent."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from src.agents.baseline import BaselineAgent
from src.agents.heuristic import HeuristicAgent
from src.core import AgentPolicy
from src.eval.validation import (
    check_deck,
    check_legal_selection,
)

logger = logging.getLogger(__name__)

_agent: AgentPolicy | None = None
_deck: list[int] | None = None


def _project_root() -> Path:
    source_path = globals().get("__file__")
    if isinstance(source_path, str):
        return Path(source_path).resolve().parent
    return Path.cwd()


def _load_deck() -> list[int]:
    deck_path = _project_root() / "src" / "artifacts" / "deck.csv"
    if not deck_path.exists():
        deck_path = _project_root() / "deck.csv"
    rows = check_deck(deck_path)
    return [int(row[0]) for row in rows]


def _build_agent() -> AgentPolicy:
    mode = os.environ.get("AGENT_MODE", "heuristic").lower()
    if mode == "rfl":
        try:
            from src.rfl.profiles import agent_from_profile

            root = _project_root()
            profile = os.environ.get(
                "AGENT_PROFILE",
                str(
                    root / "configs" / "decks" / "mega_abomasnow_kyogre" / "heuristic_rfl_0001.yaml"
                ),
            )
            deck_path = root / "src" / "artifacts" / "deck.csv"
            return agent_from_profile(
                profile,
                active_deck_id="mega_abomasnow_kyogre",
                active_deck_path=deck_path,
            )
        except (ImportError, OSError, ValueError, TypeError):
            return HeuristicAgent()
    if mode == "heuristic":
        return HeuristicAgent()
    if mode == "hybrid":
        try:
            from src.agents.search import HybridAgent

            return HybridAgent(HeuristicAgent())
        except (ImportError, ValueError):
            return HeuristicAgent()
    return BaselineAgent()


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
        return list(_deck)

    try:
        result = _agent.select(observation)
        check_legal_selection(observation, result)
        return result
    except Exception:
        return _fallback_selection(observation)


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
        check_legal_selection(observation, fallback)
    except Exception:
        return []
    return fallback


def main() -> None:
    """Read one observation from stdin and write the selected action as JSON."""
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    logger.info("agent_started mode=%s", os.environ.get("AGENT_MODE", "heuristic"))

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
