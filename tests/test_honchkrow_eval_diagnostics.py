"""Tests for Honchkrow/Porygon CABT terminal diagnostics."""

from __future__ import annotations

from scripts.run_honchkrow_porygon_eval import _inferred_reason


def _player(*, prizes: int, deck: int, pokemon: int) -> dict[str, object]:
    """Build one minimal terminal player snapshot."""
    return {
        "active": [{"id": 1, "hp": 10}] if pokemon else [],
        "bench": [{"id": 2, "hp": 10} for _ in range(max(0, pokemon - 1))],
        "deckCount": deck,
        "prize": [None] * prizes,
        "handCount": 0,
        "discard": [],
    }


def test_prize_victory_uses_winner_prizes() -> None:
    """The loser may retain prizes when the winner takes the final prize."""
    current = {
        "players": [
            _player(prizes=0, deck=10, pokemon=2),
            _player(prizes=4, deck=10, pokemon=2),
        ]
    }

    assert _inferred_reason(current, loser_side=1) == "all_prizes_taken"


def test_zero_deck_is_only_deck_out_for_loser() -> None:
    """A winning player with an empty deck did not lose by deck-out."""
    current = {
        "players": [
            _player(prizes=2, deck=0, pokemon=2),
            _player(prizes=3, deck=5, pokemon=0),
        ]
    }

    assert _inferred_reason(current, loser_side=1) == "no_pokemon_in_play"
