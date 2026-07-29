"""Tests for deck-agnostic Rule Box and Prize strategy."""

from __future__ import annotations

from src.core import (
    CardCatalog,
    DeckDefinition,
    GameState,
    GenericDeckProfileBuilder,
    PlayerState,
    PokemonState,
    PrizeChecker,
    PrizeCheckMode,
    PrizeMapBuilder,
)


def test_rule_box_traits_and_prize_values_follow_catalog_metadata() -> None:
    catalog = CardCatalog()
    catalog.load_cards(
        [
            {"id": 1, "cardType": 0, "ex": False, "megaEx": False, "skills": []},
            {"id": 2, "cardType": 0, "ex": True, "megaEx": False, "skills": []},
            {"id": 3, "cardType": 0, "ex": False, "megaEx": True, "skills": []},
        ]
    )

    assert catalog.get_traits("1").base_prize_value == 1
    assert catalog.get_traits("2").base_prize_value == 2
    assert catalog.get_traits("2").has_rule_box
    assert catalog.get_traits("3").base_prize_value == 3
    assert catalog.get_traits("3").has_rule_box


def test_prize_check_is_probabilistic_then_exact_after_deck_search() -> None:
    deck = DeckDefinition.from_cards([1] * 54 + [2] * 6, "fixture")
    checker = PrizeChecker(deck)
    player = {
        "deckCount": 54,
        "prize": [None] * 6,
        "hand": [],
        "discard": [],
        "active": [],
        "bench": [],
    }
    observation = {
        "current": {"yourIndex": 0, "players": [player, {}]},
        "select": {"deck": None},
    }

    probabilistic = checker.check(observation)

    assert probabilistic.mode is PrizeCheckMode.PROBABILISTIC
    assert probabilistic.availability(2) is not None
    assert probabilistic.availability(2).prized_exact is None

    observation["select"] = {"deck": [{"id": 1}] * 54}
    exact = checker.check(observation)

    assert exact.mode is PrizeCheckMode.EXACT
    assert exact.availability(2).prized_exact == 6
    assert exact.availability(2).searchable_exact == 0

    player["deckCount"] = 53
    player["hand"] = [{"id": 1}]
    observation["select"] = {"deck": None}
    preserved = checker.check(observation)

    assert preserved.mode is PrizeCheckMode.EXACT
    assert preserved.availability(2).prized_exact == 6
    assert preserved.availability(1).searchable_exact == 53


def test_prize_map_avoids_damage_prevented_by_rule_box_attacker() -> None:
    catalog = CardCatalog()
    catalog.load_cards(
        [
            {
                "id": 10,
                "cardType": 0,
                "ex": True,
                "megaEx": False,
                "attacks": [100],
                "skills": [],
            },
            {
                "id": 20,
                "cardType": 0,
                "ex": False,
                "megaEx": False,
                "attacks": [],
                "skills": [
                    {
                        "text": (
                            "Prevent all damage done to this Pokémon by attacks "
                            "from your opponent’s Pokémon {ex}."
                        )
                    }
                ],
            },
        ]
    )
    catalog.load_attacks([{"id": 100, "damage": 200, "energies": [1]}])
    state = GameState(
        your_index=0,
        players=[
            PlayerState(
                active=PokemonState(10, 200, 200),
                prize=[None] * 6,
            ),
            PlayerState(active=PokemonState(20, 100, 100), prize=[None] * 6),
        ],
    )

    target = PrizeMapBuilder(catalog).build(state).targets[0]

    assert target.damage_prevented
    assert not target.reachable_now
    assert target.expected_damage == 0


def test_generic_profile_changes_with_deck_without_policy_code() -> None:
    catalog = CardCatalog()
    catalog.load_cards(
        [
            {
                "id": 1,
                "name": "Basic",
                "cardType": 0,
                "attacks": [1],
                "skills": [],
                "ex": False,
                "megaEx": False,
            },
            {
                "id": 2,
                "name": "Other",
                "cardType": 0,
                "attacks": [2],
                "skills": [],
                "ex": True,
                "megaEx": False,
            },
        ]
    )
    catalog.load_attacks(
        [
            {"id": 1, "damage": 10, "energies": [1]},
            {"id": 2, "damage": 20, "energies": [1, 1]},
        ]
    )

    first = GenericDeckProfileBuilder(catalog).build(DeckDefinition.from_cards([1] * 60, "first"))
    second = GenericDeckProfileBuilder(catalog).build(DeckDefinition.from_cards([2] * 60, "second"))

    assert first.cards_for_role("attacker") == (1,)
    assert second.cards_for_role("attacker") == (2,)
    assert first.deck_sha256 != second.deck_sha256
