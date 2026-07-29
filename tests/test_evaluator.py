from src.agents.evaluator import StateEvaluator
from src.core.belief import BeliefState
from src.core.state import GameState


def test_evaluator_prefers_more_opponent_prizes() -> None:
    state = GameState(result=None)
    state.players = []
    value = StateEvaluator().evaluate(state, BeliefState())
    assert value == -5.0


def test_inconsistent_belief_disables_evaluation() -> None:
    value = StateEvaluator().evaluate(GameState(), BeliefState(consistent=False))
    assert value == float("-inf")
