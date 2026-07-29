from src.core.belief import DefaultBeliefBuilder
from src.core.state import GameState, PlayerState


def test_belief_is_deterministic_and_separate_from_snapshot() -> None:
    state = GameState(players=[PlayerState(deck_count=2, prize=[None] * 2), PlayerState()])
    observation = {"logs": [{"event": "draw"}]}
    builder = DefaultBeliefBuilder(["1", "2", "3", "4"])

    first = builder.build(observation, state)
    second = builder.build(observation, state)

    assert first == second
    assert first.incorporated_log_events == 1
    assert "hand_hypotheses" not in state.snapshot()


def test_belief_marks_impossible_public_card() -> None:
    state = GameState(players=[PlayerState(discard=["9"]), PlayerState()])
    belief = DefaultBeliefBuilder(["1"]).build({}, state)

    assert not belief.consistent
    assert "card_count:9" in belief.violations
