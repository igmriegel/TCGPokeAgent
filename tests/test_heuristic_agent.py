from __future__ import annotations

import pytest

from src.agents.heuristic import HeuristicAgent, SimpleHeuristicScorer
from src.core import Candidate, GameState, OptionType, Selection


def _candidate(index: int, option_type: OptionType, **option: object) -> Candidate:
    return Candidate(index, {"type": option_type.value, **option}, option_type)


def test_win_now_dominates_attack_score():
    scorer = SimpleHeuristicScorer()
    candidates = [
        _candidate(0, OptionType.ATTACK, damage=10, win=True),
        _candidate(1, OptionType.ATTACK, damage=100),
    ]
    winning_score, winning_reasons = scorer.score(
        GameState(), Selection((0,), (OptionType.ATTACK,)), candidates
    )
    other_score, _ = scorer.score(GameState(), Selection((1,), (OptionType.ATTACK,)), candidates)
    assert winning_score > other_score
    assert "win_now" in winning_reasons


def test_attack_enabling_energy_is_explained():
    scorer = SimpleHeuristicScorer()
    candidate = _candidate(2, OptionType.ENERGY, enablesAttack=True, count=1)
    score, reasons = scorer.score(GameState(), Selection((2,), (OptionType.ENERGY,)), [candidate])
    assert score == scorer.weights["attack_enabling_energy"]
    assert reasons == ["attack_enabling_energy"]


def test_end_turn_is_penalized_before_actions():
    scorer = SimpleHeuristicScorer()
    candidate = _candidate(0, OptionType.END)
    score, reasons = scorer.score(
        GameState(turn_action_count=0), Selection((0,), (OptionType.END,)), [candidate]
    )
    assert score == scorer.weights["premature_end"]
    assert reasons == ["premature_end"]


def test_no_signal_is_explicit():
    score, reasons = SimpleHeuristicScorer().score(GameState(), Selection((), ()), [])
    assert score == 0.0
    assert reasons == ["no_signal"]


def test_profile_validation_rejects_unknown_or_non_numeric_values():
    with pytest.raises(ValueError, match="unknown heuristic weight"):
        SimpleHeuristicScorer({"unknown": 1})
    with pytest.raises(ValueError, match="must be numeric"):
        SimpleHeuristicScorer({"win_now": "high"})
    with pytest.raises(ValueError, match="must be boolean"):
        SimpleHeuristicScorer(feature_flags={"use_attack_signals": 1})


def test_agent_prefers_immediate_win_and_ties_by_index(sample_observation):
    observation = dict(sample_observation)
    observation["select"] = {
        **sample_observation["select"],
        "option": [
            {"type": "ATTACK", "win": True},
            {"type": "ATTACK", "damage": 100},
        ],
    }
    assert HeuristicAgent().select(observation) == [0]

    observation["select"]["option"] = [
        {"type": "ATTACK", "damage": 10},
        {"type": "ATTACK", "damage": 10},
    ]
    assert HeuristicAgent().select(observation) == [0]
