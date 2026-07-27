from src.core import DefaultParser, OptionType, SelectContext, SelectType


def test_parse_sample(sample_observation):
    parser = DefaultParser()
    parsed = parser.parse(sample_observation)

    assert parsed.state.turn == 1
    assert parsed.state.turn_action_count == 0
    assert parsed.state.your_index == 0
    assert parsed.state.first_player == 0
    assert len(parsed.state.players) == 2
    assert parsed.state.players[0].hand_count == 6
    assert parsed.state.players[0].hand is not None
    assert parsed.state.players[1].hand is None

    assert parsed.select_type == SelectType.MAIN
    assert parsed.select_context == SelectContext.ATTACK
    assert parsed.min_count == 1
    assert parsed.max_count == 1
    assert len(parsed.candidates) == 3

    assert parsed.candidates[0].option_index == 0
    assert parsed.candidates[0].option_type == OptionType.ATTACK
    assert parsed.candidates[2].option_type == OptionType.END


def test_parse_empty(empty_observation):
    parser = DefaultParser()
    parsed = parser.parse(empty_observation)

    assert parsed.state.turn == 0
    assert parsed.candidates == []


def test_parse_preserves_indices(sample_observation):
    parser = DefaultParser()
    parsed = parser.parse(sample_observation)

    for i, c in enumerate(parsed.candidates):
        assert c.option_index == i


def test_parse_min_count_zero(min_count_zero_observation):
    parser = DefaultParser()
    parsed = parser.parse(min_count_zero_observation)

    assert parsed.min_count == 0
    assert parsed.max_count == 1
    assert parsed.select_type == SelectType.YES_NO
