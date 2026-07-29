import pytest

from src.core import (
    Candidate,
    DefaultSelectionGenerator,
    LegalityViolationError,
    OptionType,
    Selection,
    SelectionValidator,
)


def _make_candidate(index: int, opt_type: str, card_id: str = "") -> Candidate:
    return Candidate(
        option_index=index,
        option={"type": opt_type, "cardId": card_id or f"c{index}"},
        option_type=OptionType(opt_type)
        if opt_type in OptionType._value2member_map_
        else OptionType.CARD,
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
    candidates = [
        _make_candidate(0, "ENERGY"),
        _make_candidate(1, "ENERGY"),
        _make_candidate(2, "ENERGY"),
    ]
    selections = gen.generate(candidates, min_count=1, max_count=2)

    assert len(selections) == 6
    for sel in selections:
        assert 1 <= len(sel.indices) <= 2
        assert len(sel.indices) == len(set(sel.indices))


def test_no_candidates():
    gen = DefaultSelectionGenerator()
    selections = gen.generate([], min_count=1, max_count=1)
    assert selections == []


def test_empty_selection_is_generated_without_candidates_when_optional():
    gen = DefaultSelectionGenerator()
    selections = gen.generate([], min_count=0, max_count=1)
    assert [selection.indices for selection in selections] == [()]


def test_invalid_bounds_have_no_legal_selections():
    gen = DefaultSelectionGenerator()
    assert gen.generate([], min_count=-1, max_count=1) == []
    assert gen.generate([], min_count=2, max_count=1) == []


def test_remaining_energy_cost_is_fulfilled_across_repeated_sdk_prompts():
    gen = DefaultSelectionGenerator()
    candidates = [_make_candidate(0, "ENERGY"), _make_candidate(1, "ENERGY")]
    selections = gen.generate(candidates, 1, 1, remain_energy_cost=2)
    assert [selection.indices for selection in selections] == [(0,), (1,)]


def test_validator_rejects_duplicate_and_unknown_indices():
    validator = SelectionValidator()
    candidates = [_make_candidate(3, "YES")]
    with pytest.raises(LegalityViolationError):
        validator.validate(Selection((3, 3), (OptionType.YES, OptionType.YES)), candidates, 2, 2)
    with pytest.raises(LegalityViolationError):
        validator.validate(Selection((0,), (OptionType.YES,)), candidates, 1, 1)


def test_no_duplicate_indices():
    gen = DefaultSelectionGenerator()
    candidates = [
        _make_candidate(0, "ENERGY"),
        _make_candidate(0, "ENERGY"),
    ]
    selections = gen.generate(candidates, min_count=1, max_count=1)
    for sel in selections:
        assert len(sel.indices) == len(set(sel.indices))
