from __future__ import annotations

from pathlib import Path

from src.agents.factory import load_deck_profile
from src.core import DeckDefinition

_ROOT = Path(__file__).resolve().parents[1]


def test_profile_sha_matches_active_deck() -> None:
    deck = DeckDefinition.from_path(
        _ROOT / "src" / "artifacts" / "deck.csv", "mega_abomasnow_kyogre"
    )
    profile = load_deck_profile(_ROOT)

    assert profile is not None
    assert profile.deck_sha256 == deck.sha256


def test_pokepad_has_pokemon_search_role() -> None:
    profile = load_deck_profile(_ROOT)

    assert profile is not None
    assert profile.has_role(1152, "pokemon_search")
    assert 1152 in profile.resource_values
