from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from typing import Any

from src.agents.baseline import BaselineAgent
from src.agents.heuristic import HeuristicAgent
from src.core import AgentMode, AgentPolicy
from src.logging_setup import get_logger, setup_logging

logger = get_logger(__name__)

_agent: AgentPolicy | None = None
_deck: list[int] | None = None


def _load_deck() -> list[int]:
    deck_path = Path(__file__).parent / "src" / "artifacts" / "deck.csv"
    if not deck_path.exists():
        deck_path = Path(__file__).parent / "deck.csv"

    if deck_path.exists():
        with open(deck_path) as f:
            reader = csv.reader(f)
            cards = []
            for row in reader:
                if row:
                    try:
                        cards.append(int(row[0]))
                    except ValueError:
                        cards.append(hash(row[0]))
        return cards

    return list(range(1, 61))


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
        return _deck

    return _agent.select(observation)


def main() -> None:
    setup_logging(os.environ.get("LOG_LEVEL", "INFO"))
    logger.info("agent_started", mode=os.environ.get("AGENT_MODE", "baseline"))

    observation = _read_observation()
    result = agent_policy(observation)
    _write_result(result)


def _read_observation() -> dict[str, Any]:
    import json
    raw = sys.stdin.read()
    if raw:
        return dict(json.loads(raw))
    return {}


def _write_result(result: list[int]) -> None:
    import json
    json.dump(result, sys.stdout, indent=None)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
