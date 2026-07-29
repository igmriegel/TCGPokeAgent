from src.agents.search import BoundedShortSearch
from src.core import Selection


def test_search_gate_requires_main_multiple_options_and_overage() -> None:
    search = BoundedShortSearch()
    ranked = [Selection((), ()), Selection((), ())]
    assert not search._gate(
        {"select": {"type": "ATTACK"}}, type("B", (), {"consistent": True})(), ranked
    )
    assert search._gate(
        {
            "select": {"type": "MAIN"},
            "search_begin_input": {"opaque": True},
            "remainingOverageTime": 30,
        },
        type("B", (), {"consistent": True})(),
        ranked,
    )


def test_search_without_api_returns_heuristic_fallback() -> None:
    search = BoundedShortSearch()
    ranked = [Selection((3,), ())]
    selected = search.choose({}, type("B", (), {"consistent": True})(), ranked)
    assert selected is ranked[0]
    assert search.stats.opened == 0
