from src.core import Candidate, DefaultSelectionGenerator, OptionType, Selection


def _make_candidate(index: int, opt_type: str, card_id: str = "") -> Candidate:
    return Candidate(
        option_index=index,
        option={"type": opt_type, "cardId": card_id or f"c{index}"},
        option_type=OptionType(opt_type) if opt_type in OptionType._value2member_map_ else OptionType.CARD,
    )


def test_single_selection():
    gen = DefaultSelectionGenerator()
    candidates = [_make_candidate(0, "ATTACK"), _make_candidate(1, "END")]
    selections = gen.generate(candidates, min_count=1, max_count=1)

    assert len(selections) == 2
    assert selections[0].indices == (0,)
    assert selections[1].indices == (1,)


def test_empty_selection_allowed():
    gen = DefaultSelectionGenerator()
    candidates = [_make_candidate(0, "YES"), _make_candidate(1, "NO")]
    selections = gen.generate(candidates, min_count=0, max_count=1)

    assert any(s.indices == () for s in selections)


def test_multi_selection():
    gen = DefaultSelectionGenerator()
    candidates = [_make_candidate(0, "ENERGY"), _make_candidate(1, "ENERGY"), _make_candidate(2, "ENERGY")]
    selections = gen.generate(candidates, min_count=1, max_count=2)

    assert len(selections) == 6
    for sel in selections:
        assert 1 <= len(sel.indices) <= 2
        assert len(sel.indices) == len(set(sel.indices))


def test_no_candidates():
    gen = DefaultSelectionGenerator()
    selections = gen.generate([], min_count=1, max_count=1)
    assert selections == []


def test_no_duplicate_indices():
    gen = DefaultSelectionGenerator()
    candidates = [
        _make_candidate(0, "ENERGY"),
        _make_candidate(0, "ENERGY"),
    ]
    selections = gen.generate(candidates, min_count=1, max_count=1)
    for sel in selections:
        assert len(sel.indices) == len(set(sel.indices))
