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
