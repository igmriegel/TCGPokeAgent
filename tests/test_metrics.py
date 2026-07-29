from src.eval.comparison import CompositeMetrics, paired_bootstrap_lower_bound
from src.eval.metrics import _wilson, aggregate
from src.eval.runner import ExecutionStatus, MatchRecord


def test_wilson_extremes():
    lo, hi = _wilson(0, 100)
    assert 0.0 <= lo <= hi <= 1.0
    lo, hi = _wilson(100, 100)
    assert 0.0 <= lo <= hi <= 1.0


def test_wilson_fifty():
    lo, hi = _wilson(50, 100)
    assert lo <= 0.5 <= hi


def test_aggregate_no_matches():
    m = aggregate([])
    assert m.total == 0


def test_aggregate_all_wins():
    matches = [
        MatchRecord(match_id=f"m{i}", seed=i, agent_side=0, status=ExecutionStatus.OK, result="win")
        for i in range(10)
    ]
    m = aggregate(matches)
    assert m.total == 10
    assert m.wins == 10
    assert m.win_rate == 1.0


def test_composite_score_uses_prize_latency_and_stability_components():
    metrics = CompositeMetrics(
        match_score_rate=0.6,
        worst_matchup_score=0.4,
        prizes_taken=4,
        prizes_conceded=2,
        p95_decision_ms=20.0,
        fallback_or_invalid_model_decisions=1,
        decisions=10,
    )

    assert metrics.prize_efficiency == 4 / 6
    assert 0.0 < metrics.promotion_score < 1.0


def test_paired_bootstrap_detects_uniform_improvement():
    baseline = [
        MatchRecord(
            match_id=f"b-{seed}",
            seed=seed,
            agent_side=0,
            status=ExecutionStatus.OK,
            result="loss",
        )
        for seed in range(10)
    ]
    candidate = [
        MatchRecord(
            match_id=f"c-{seed}",
            seed=seed,
            agent_side=0,
            status=ExecutionStatus.OK,
            result="win",
        )
        for seed in range(10)
    ]

    assert paired_bootstrap_lower_bound(baseline, candidate) == 1.0
