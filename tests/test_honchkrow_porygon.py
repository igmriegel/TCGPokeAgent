from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.agents.honchkrow_porygon import (
    ARIANA,
    ARTICUNO,
    GIOVANNI,
    HONCHKROW,
    IGNITION_ENERGY,
    NIGHT_STRETCHER,
    POKE_PAD,
    R_COMMAND,
    ROCKET_FEATHERS,
    ROTO_STICK,
    HonchkrowPorygonAgent,
    HonchkrowPorygonScorer,
)
from src.core import Candidate, GameState, OptionType, PlayerState, PokemonState, SelectContext

ROOT = Path(__file__).parents[1]


def _candidate(
    index: int,
    option_type: OptionType,
    *,
    card_id: int | None = None,
    attack_id: int | None = None,
    card: dict[str, object] | None = None,
) -> Candidate:
    option: dict[str, object] = {"type": option_type.value}
    if card_id is not None:
        option["cardId"] = card_id
    if attack_id is not None:
        option["attackId"] = attack_id
    return Candidate(
        index,
        option,
        option_type,
        card=card,
        attack={"attackId": attack_id} if attack_id else None,
        features={"card_id": card_id or 0},
    )


def _profile():
    data = json.loads((ROOT / "src/artifacts/deck_profile_honchkrow_porygon.json").read_text())
    from src.core import DeckProfile

    return DeckProfile.from_dict(data)


def test_dedicated_deck_and_profile_are_bound() -> None:
    import main_honchkrow_porygon as entrypoint

    deck = entrypoint._load_deck()
    profile = entrypoint._load_profile()
    assert len(deck) == 60
    assert deck[:4] == [463] * 4
    assert profile.deck_id == "honchkrow_porygon"


def test_ariana_is_prioritized_as_the_hand_and_energy_engine() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    candidate = _candidate(
        0,
        OptionType.PLAY,
        card_id=ARIANA,
        card={"cardType": 3, "name": "Team Rocket's Ariana"},
    )
    score, reasons = scorer._play_score(GameState(), candidate)
    assert score > 800
    assert "ariana_hand_refresh_and_energy_access" in reasons


def test_honchkrow_and_porygon2_damage_scale_with_rocket_supporters() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    hand = [{"id": card_id} for card_id in (ARIANA, 1217, 1218)]
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130),
                hand=hand,
                discard=[{"id": card_id} for card_id in (ARIANA, 1217, 1218)],
            ),
            PlayerState(),
        ]
    )
    honchkrow = _candidate(0, OptionType.ATTACK, attack_id=ROCKET_FEATHERS)
    score, reasons = scorer._attack_score(state, honchkrow)
    assert score >= 1180
    assert "rocket_hand_damage" in reasons

    porygon = _candidate(1, OptionType.ATTACK, attack_id=R_COMMAND)
    porygon_score, _ = scorer._attack_score(state, porygon)
    assert porygon_score >= 310


def test_articuno_is_not_selected_without_an_effect_threat() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    candidate = _candidate(
        0,
        OptionType.PLAY,
        card_id=ARTICUNO,
        card={"cardType": 0, "name": "Team Rocket's Articuno"},
    )
    score, reasons = scorer._play_score(
        GameState(players=[PlayerState(), PlayerState()]), candidate
    )
    assert score < 0
    assert "preserve_articuno_until_needed" in reasons


def test_rocket_feathers_requires_supporter_in_hand() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        players=[
            PlayerState(active=PokemonState(HONCHKROW, 130, 130)),
            PlayerState(),
        ]
    )
    candidate = _candidate(0, OptionType.ATTACK, attack_id=ROCKET_FEATHERS)
    assert agent._candidate_is_forbidden(state, candidate, SelectContext.MAIN)
    assert scorer._supporters_in_hand(state) == 0


def test_ignition_energy_is_restricted_to_active_or_promotion_target() -> None:
    agent = HonchkrowPorygonAgent(_profile())
    candidate = _candidate(
        0,
        OptionType.ATTACH,
        card_id=IGNITION_ENERGY,
        card={"cardType": 6},
    )
    candidate = Candidate(
        candidate.option_index,
        candidate.option,
        candidate.option_type,
        candidate.card,
        candidate.attack,
        {"card_id": IGNITION_ENERGY, "target_card_id": HONCHKROW, "target_energy_count": 0},
    )
    state = GameState(players=[PlayerState(), PlayerState()])
    assert agent._candidate_is_forbidden(state, candidate, SelectContext.ATTACH_ENERGY)


def test_pokepad_does_not_search_honchkrow_before_murkrow_is_ready() -> None:
    agent = HonchkrowPorygonAgent(_profile())
    candidate = _candidate(
        0,
        OptionType.CARD,
        card_id=HONCHKROW,
        card={"cardType": 0},
    )
    state = GameState(players=[PlayerState(hand=[{"id": POKE_PAD}]), PlayerState()])
    assert agent._candidate_is_forbidden(state, candidate, SelectContext.TO_HAND)


def test_roto_stick_requires_ready_honchkrow() -> None:
    agent = HonchkrowPorygonAgent(_profile())
    candidate = _candidate(
        0,
        OptionType.PLAY,
        card_id=ROTO_STICK,
        card={"cardType": 1},
    )
    state = GameState(players=[PlayerState(), PlayerState()])
    assert agent._candidate_is_forbidden(state, candidate, SelectContext.MAIN)


def test_giovanni_is_low_priority_when_it_would_break_the_ko_line() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    candidate = _candidate(
        0,
        OptionType.PLAY,
        card_id=GIOVANNI,
        card={"cardType": 3},
    )
    state = GameState(
        players=[
            PlayerState(hand=[{"id": GIOVANNI}, {"id": ARIANA}], hand_count=2),
            PlayerState(active=PokemonState(9999, 180, 180)),
        ]
    )
    score, reasons = scorer._play_score(state, candidate)
    assert score < 200
    assert "giovanni_preserves_supporters_until_ko" in reasons


def test_night_stretcher_payload_cannot_be_energy_or_tool() -> None:
    agent = HonchkrowPorygonAgent(_profile())
    candidate = _candidate(
        0,
        OptionType.CARD,
        card_id=IGNITION_ENERGY,
        card={"cardType": 6},
    )
    candidate = Candidate(
        candidate.option_index,
        {"type": OptionType.CARD.value, "sourceCardId": NIGHT_STRETCHER},
        candidate.option_type,
        candidate.card,
        candidate.attack,
        {"card_id": IGNITION_ENERGY},
    )
    state = GameState(players=[PlayerState(), PlayerState()])
    assert agent._candidate_is_forbidden(state, candidate, SelectContext.TO_HAND)


def test_is_first_prefers_yes() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    yes = _candidate(0, OptionType.YES)
    no = _candidate(1, OptionType.NO)
    assert scorer._sdk_score(GameState(), yes, SelectContext.IS_FIRST)[0] > 0
    assert scorer._sdk_score(GameState(), no, SelectContext.IS_FIRST)[0] < 0


def test_dedicated_entrypoint_returns_dedicated_deck() -> None:
    completed = subprocess.run(
        [sys.executable, "main_honchkrow_porygon.py"],
        cwd=ROOT,
        input='{"select": null}',
        text=True,
        capture_output=True,
        check=True,
    )
    assert json.loads(completed.stdout)[:4] == [463] * 4


def test_make_exposes_separate_deck_packaging_commands() -> None:
    completed = subprocess.run(
        ["make", "-n", "build-abomasnow-package", "build-honchkrow-porygon-package"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "scripts/build_package.sh" in completed.stdout
    assert "scripts/build_honchkrow_porygon_package.sh" in completed.stdout


assert HonchkrowPorygonAgent
