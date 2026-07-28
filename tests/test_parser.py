from dataclasses import dataclass

import pytest

from src.core import DefaultParser, OptionType, SelectContext, SelectType
from src.core.catalog import CardCatalog
from src.core.exceptions import ParseError


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


def test_parse_preserves_raw_observation_and_auxiliary_fields(sample_observation):
    sample_observation["logs"] = [{"event": "draw"}]
    sample_observation["search_begin_input"] = "opaque-input"

    parsed = DefaultParser().parse(sample_observation)

    assert parsed.raw_observation is sample_observation
    assert parsed.logs == [{"event": "draw"}]
    assert parsed.search_begin_input == "opaque-input"
    assert parsed.normalized_observation["select"] == sample_observation["select"]


def test_parse_preserves_hidden_active_and_prize_cards(sample_observation):
    sample_observation["current"]["opponent"]["active"] = None
    sample_observation["current"]["you"]["prize"] = [None, "visible-card"]

    parsed = DefaultParser().parse(sample_observation)

    assert parsed.state.players[1].active is None
    assert parsed.state.players[0].prize == [None, "visible-card"]
    assert parsed.state.players[1].hand is None


@dataclass
class DataclassObservation:
    current: dict
    select: dict
    logs: list
    search_begin_input: str | None


def test_parse_dataclass_matches_dictionary(sample_observation):
    observation = DataclassObservation(**sample_observation)

    from_dict = DefaultParser().parse(sample_observation)
    from_dataclass = DefaultParser().parse(observation)

    assert from_dataclass.raw_observation is observation
    assert from_dataclass.state.snapshot() == from_dict.state.snapshot()
    assert [candidate.option for candidate in from_dataclass.candidates] == [
        candidate.option for candidate in from_dict.candidates
    ]
    assert [candidate.option_index for candidate in from_dataclass.candidates] == [0, 1, 2]


def test_parse_resolves_catalog_metadata(sample_observation):
    catalog = CardCatalog()
    catalog.load_cards([{"id": "base1-4", "name": "Active"}])
    catalog.load_attacks([{"id": "attack-1", "name": "Punch"}])

    parsed = DefaultParser(catalog).parse(sample_observation)

    assert parsed.candidates[0].card == {"id": "base1-4", "name": "Active"}
    assert parsed.candidates[0].attack == {"id": "attack-1", "name": "Punch"}
    assert parsed.candidates[1].attack is None


def test_parse_rejects_malformed_observation():
    with pytest.raises(ParseError, match="observation must be"):
        DefaultParser().parse([])


def test_parse_rejects_malformed_option(sample_observation):
    sample_observation["select"]["option"] = ["not-a-mapping"]

    with pytest.raises(ParseError, match="options must be mappings"):
        DefaultParser().parse(sample_observation)
