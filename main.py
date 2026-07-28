from __future__ import annotations

import json
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
from src.logging_setup import get_logger, setup_logging

logger = get_logger(__name__)

_agent: AgentPolicy | None = None
_deck: list[int] | None = None


def _load_deck() -> list[int]:
    deck_path = Path(__file__).parent / "src" / "artifacts" / "deck.csv"
    if not deck_path.exists():
        deck_path = Path(__file__).parent / "deck.csv"
    rows = check_deck(deck_path)
    return [int(row[0]) for row in rows]


def _build_agent() -> AgentPolicy:
    mode = os.environ.get("AGENT_MODE", "baseline").lower()
    if mode == "heuristic":
        return HeuristicAgent()
    return BaselineAgent()


def agent_policy(observation: dict[str, Any]) -> list[int]:
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
    setup_logging(os.environ.get("LOG_LEVEL", "INFO"))
    logger.info("agent_started", mode=os.environ.get("AGENT_MODE", "baseline"))

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


if __name__ == "__main__":
    main()
