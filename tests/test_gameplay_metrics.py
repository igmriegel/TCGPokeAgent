from __future__ import annotations

import pytest

from src.core import ExecutionStatus
from src.eval.gameplay import GameplayMetrics
from src.eval.runner import DecisionRecord, MatchRecord, RunReport


def _decision(option_type: int) -> DecisionRecord:
    return DecisionRecord(
        decision_index=0,
        turn=1,
        context="0",
        select_type="0",
        options=[{"type": option_type}],
        option_count=1,
        min_count=1,
        max_count=1,
        selected_indices=[0],
        legal=True,
        duration_ms=1.0,
        overage_balance_ms=99.0,
    )


def test_gameplay_metrics_detect_productive_actions_and_attacks() -> None:
    report = RunReport(
        config_name="test",
        agent_mode="heuristic",
        matches=[
            MatchRecord(
                match_id="one",
                seed=1,
                agent_side=0,
                status=ExecutionStatus.OK,
                result="win",
                decisions=[_decision(8), _decision(13), _decision(14)],
            )
        ],
    )

    metrics = GameplayMetrics.from_report(report)

    assert metrics.productive_main_actions == 2
    assert metrics.attacks == 1
    assert metrics.attack_match_rate == 1.0
    assert metrics.end_turn_rate == pytest.approx(1 / 3)
    metrics.assert_minimum_gameplay()


def test_gameplay_gate_rejects_end_turn_only_agent() -> None:
    report = RunReport(
        config_name="test",
        agent_mode="heuristic",
        matches=[
            MatchRecord(
                match_id="one",
                seed=1,
                agent_side=0,
                status=ExecutionStatus.OK,
                decisions=[_decision(14)],
            )
        ],
    )

    with pytest.raises(ValueError, match="no productive main actions"):
        GameplayMetrics.from_report(report).assert_minimum_gameplay()
