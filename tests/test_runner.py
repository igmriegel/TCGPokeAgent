from __future__ import annotations

from typing import Any

from src.core import ExecutionStatus
from src.eval.metrics import aggregate
from src.eval.reporting import serialize_report
from src.eval.runner import MatchRunner


class FakeEnvironment:
    def __init__(self) -> None:
        self.state = [{"status": "DONE", "reward": 1}, {"status": "DONE", "reward": -1}]
        self.steps = [{}, {}]

    def run(self, agents: list[Any]) -> None:
        observation = {
            "current": {"turn": 3},
            "select": {
                "context": "ATTACK",
                "minCount": 1,
                "maxCount": 1,
                "option": [{"type": "ATTACK"}],
            },
        }
        agents[0](observation)


def test_runner_records_legal_decision_and_side_result() -> None:
    runner = MatchRunner(environment_factory=FakeEnvironment)
    runner._agent_for_mode = lambda mode: lambda observation: [0]  # type: ignore[method-assign]

    record = runner.run_match(seed=7, agent_mode="baseline", side=0)

    assert record.status is ExecutionStatus.OK
    assert record.result == "win"
    assert record.decision_count == 1
    assert record.decisions[0].context == "ATTACK"
    assert record.decisions[0].select_type is None
    assert record.decisions[0].options == [{"type": "ATTACK"}]
    assert record.decisions[0].score is None
    assert record.decisions[0].reasons == []
    assert record.decisions[0].search is None
    assert record.decisions[0].legal
    assert record.decisions[0].overage_balance_ms <= 100
    assert record.sdk_version == "1.32.2"
    assert len(record.deck_sha256) == 64
    assert record.termination_reason == "completed"


def test_serialized_report_contains_match_and_decision_trace() -> None:
    runner = MatchRunner(environment_factory=FakeEnvironment)
    runner._agent_for_mode = lambda mode: lambda observation: [0]  # type: ignore[method-assign]

    report = runner.run_batch([7], "baseline", sides=[0])
    serialized = serialize_report(report, aggregate(report.matches))

    assert serialized["matches"][0]["match_id"] == "match_7_0"
    assert serialized["matches"][0]["decisions"][0]["selected_indices"] == [0]


def test_runner_supports_policy_and_self_play_opponents() -> None:
    runner = MatchRunner()

    for opponent in ("baseline", "heuristic", "self_play"):
        policy = runner._opponent_callable(opponent, "heuristic")
        assert callable(policy)


def test_runner_isolates_failed_match_from_batch() -> None:
    class FailingRunner(MatchRunner):
        def _make_environment(self, seed: int) -> Any:
            if seed == 2:
                raise RuntimeError("one match failed")
            return FakeEnvironment()

    runner = FailingRunner(environment_factory=FakeEnvironment)
    runner._agent_for_mode = lambda mode: lambda observation: [0]  # type: ignore[method-assign]

    report = runner.run_batch([1, 2], "baseline", sides=[0])

    assert report.total_matches == 2
    assert report.matches[0].status is ExecutionStatus.OK
    assert report.matches[1].status is ExecutionStatus.ERROR
