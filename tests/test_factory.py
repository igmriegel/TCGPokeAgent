from __future__ import annotations

from pathlib import Path

from src.agents.factory import (
    build_agent,
    load_deck,
    load_deck_profile,
    normalize_agent_mode,
)
from src.agents.honchkrow_porygon import HonchkrowPorygonAgent

ROOT = Path(__file__).parents[1]


def test_expert_turn_loop_is_the_canonical_honchkrow_factory_mode() -> None:
    assert normalize_agent_mode("honchkrow_porygon") == "expert_turn_loop"

    deck = load_deck(ROOT, "expert_turn_loop")
    profile = load_deck_profile(ROOT, "expert_turn_loop")
    agent = build_agent("expert_turn_loop", root=ROOT)

    assert deck[:4] == [463] * 4
    assert profile is not None
    assert profile.deck_id == "honchkrow_porygon"
    assert isinstance(agent, HonchkrowPorygonAgent)
    assert agent.policy_variant == "expert_turn_loop"
