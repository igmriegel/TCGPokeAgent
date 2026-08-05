"""Standalone Kaggle entrypoint for the Honchkrow/Porygon heuristic deck."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Mapping

from src.agents.honchkrow_porygon import HonchkrowPorygonAgent
from src.core import AgentPolicy, DeckDefinition, DeckProfile

logger = logging.getLogger(__name__)
_ROOT = Path(__file__).resolve().parent
_DECK_PATH = _ROOT / "src" / "artifacts" / "deck_team_rocket_murkrow.csv"
if not _DECK_PATH.is_file():
    _DECK_PATH = _ROOT / "deck.csv"
_PROFILE_PATH = _ROOT / "src" / "artifacts" / "deck_profile_honchkrow_porygon.json"
_agent: AgentPolicy | None = None
_deck: list[int] | None = None


def _load_deck() -> list[int]:
    """Load the dedicated 60-card Honchkrow/Porygon deck."""
    deck = DeckDefinition.from_path(_DECK_PATH, "honchkrow_porygon")
    return list(deck.card_ids)


def _load_profile() -> DeckProfile:
    """Load and validate the dedicated declarative deck profile."""
    data = json.loads(_PROFILE_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("Honchkrow/Porygon profile must be a mapping")
    profile = DeckProfile.from_dict(data)
    deck = DeckDefinition.from_path(_DECK_PATH, "honchkrow_porygon")
    if profile.deck_sha256 != deck.sha256:
        raise ValueError("Honchkrow/Porygon profile does not match its deck")
    return profile


def _build_agent() -> HonchkrowPorygonAgent:
    """Build the isolated Honchkrow/Porygon policy."""
    return HonchkrowPorygonAgent(_load_profile())


def agent_policy(observation: dict[str, Any]) -> list[int]:
    """Return one legal CABT action for the dedicated deck."""
    global _agent, _deck
    if _agent is None:
        _agent = _build_agent()
    if _deck is None:
        _deck = _load_deck()
    if observation.get("select") is None:
        _agent.start_match(DeckDefinition.from_cards(_deck, "honchkrow_porygon"))
        return list(_deck)
    try:
        result = _agent.select(observation)
        _validate_selection(observation, result)
        return result
    except Exception:
        return _fallback_selection(observation)


def _validate_selection(observation: Mapping[str, Any], output: list[int]) -> None:
    """Validate indices against the current CABT selection contract."""
    select = observation.get("select")
    if not isinstance(select, Mapping):
        raise ValueError("select must be a mapping")
    options = select.get("option")
    if not isinstance(options, list):
        raise ValueError("select.option must be a list")
    if len(output) != len(set(output)) or any(
        isinstance(index, bool) or not isinstance(index, int) or index < 0 or index >= len(options)
        for index in output
    ):
        raise ValueError("selection contains invalid indices")
    minimum = int(select.get("minCount", 0) or 0)
    maximum = int(select.get("maxCount", 0) or 0)
    if not minimum <= len(output) <= maximum:
        raise ValueError("selection violates cardinality")


def _fallback_selection(observation: Mapping[str, Any]) -> list[int]:
    """Return the first deterministic selection satisfying cardinality."""
    select = observation.get("select")
    if not isinstance(select, Mapping) or not isinstance(select.get("option"), list):
        return []
    options = select["option"]
    minimum = max(0, int(select.get("minCount", 0) or 0))
    result = list(range(minimum))
    return result if len(result) <= len(options) else []


def agent(observation: dict[str, Any]) -> list[int]:
    """Expose the Kaggle callable entrypoint."""
    return agent_policy(observation)


def main() -> None:
    """Read one JSON observation and write one JSON selection."""
    logging.basicConfig(level="INFO")
    raw = sys.stdin.read()
    try:
        observation = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        observation = {}
    result = agent_policy(observation if isinstance(observation, dict) else {})
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
