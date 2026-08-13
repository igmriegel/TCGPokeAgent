from __future__ import annotations

import json
from pathlib import Path

from src.agents.honchkrow_porygon import (
    ARCHER,
    FACTORY,
    GIOVANNI,
    HONCHKROW,
    MURKROW,
    PORYGON,
    PROTON,
    ROTO_STICK,
    TRANSCEIVER,
    HonchkrowPorygonAgent,
    HonchkrowPorygonScorer,
)
from src.core import (
    Candidate,
    GameState,
    OptionType,
    PlayerState,
    PokemonState,
    SelectContext,
    Selection,
)

ROOT = Path(__file__).parents[1]


def _profile():
    from src.core import DeckProfile

    return DeckProfile.from_dict(
        json.loads((ROOT / "src/artifacts/deck_profile_honchkrow_porygon.json").read_text())
    )


def _play(card_id: int) -> Candidate:
    return Candidate(
        0,
        {"type": OptionType.PLAY.value, "cardId": card_id},
        OptionType.PLAY,
        card={"cardType": 3},
        features={"card_id": card_id},
    )


def test_factory_adds_two_cards_to_ariana_draw_target() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(
        stadium=str(FACTORY),
        players=[PlayerState(active=PokemonState(HONCHKROW, 130, 130), deck_count=20)],
    )

    assert scorer._ariana_draw_count(state) == 10


def test_proton_redundancy_requires_new_public_setup_gain() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(players=[PlayerState(active=PokemonState(HONCHKROW, 130, 130))])

    scorer.record_proton_search(0, converted=False)
    score, reasons = scorer._play_score(state, _play(PROTON))

    assert score < 0
    assert "proton_redundant_without_new_setup_gain" in reasons


def test_giovanni_is_hard_vetoed_without_immediate_public_conversion() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(
        players=[
            PlayerState(hand=[{"id": GIOVANNI}], hand_count=1),
            PlayerState(active=PokemonState(999, 180, 180)),
        ]
    )

    score, reasons = scorer._play_score(state, _play(GIOVANNI))

    assert score < -1000
    assert "giovanni_without_immediate_ko_or_control" in reasons


def test_archer_is_productive_only_when_projected_hand_is_smaller() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    scorer.set_own_ko_observed(True)
    candidate = _play(ARCHER)
    state = GameState(
        players=[
            PlayerState(hand=[{"id": ARCHER}] * 7, hand_count=7, deck_count=0),
            PlayerState(active=PokemonState(999, 100, 100), deck_count=20),
        ]
    )

    assert scorer._archer_is_safe_and_useful(state, candidate)
    assert scorer._archer_reason(state) == "fetch_archer_after_ko_hand_reset"


def test_archer_is_rejected_when_draw_five_would_increase_hand() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    scorer.set_own_ko_observed(True)
    state = GameState(
        players=[
            PlayerState(hand=[{"id": ARCHER}], hand_count=2, deck_count=20),
            PlayerState(active=PokemonState(999, 100, 100)),
        ]
    )

    assert not scorer._archer_is_safe_and_useful(state, _play(ARCHER))


def test_roto_expected_value_is_nonnegative_only_for_a_measurable_line() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{}, {}]),
                bench=[PokemonState(PORYGON, 90, 90)],
                hand=[{"id": ROTO_STICK}],
                hand_count=1,
                deck_count=2,
            ),
            PlayerState(active=PokemonState(999, 30, 100)),
        ]
    )

    value, _ = scorer._roto_expected_value(state, 1)

    assert isinstance(value, float)


def test_critical_deck_transceiver_allows_only_immediate_survival_supporter() -> None:
    agent = HonchkrowPorygonAgent(_profile(), "expert_turn_loop")
    state = GameState(
        players=[
            PlayerState(active=PokemonState(HONCHKROW, 130, 130), deck_count=2),
            PlayerState(active=PokemonState(999, 100, 100)),
        ]
    )
    selections = [Selection((0,), (OptionType.CARD,))]
    candidates = [
        Candidate(
            0,
            {"type": OptionType.CARD.value, "sourceCardId": TRANSCEIVER, "cardId": PROTON},
            OptionType.CARD,
            features={"card_id": PROTON},
        )
    ]

    selected = agent._transceiver_selections(state, selections, candidates)

    assert selected == selections
    assert agent.turn_ledger.transceiver_critical_survival_line


def test_critical_deck_transceiver_vetoes_giovanni_without_terminal_line() -> None:
    agent = HonchkrowPorygonAgent(_profile(), "expert_turn_loop")
    state = GameState(
        players=[
            PlayerState(active=PokemonState(HONCHKROW, 130, 130), deck_count=2),
            PlayerState(active=PokemonState(999, 180, 180)),
        ]
    )
    selections = [Selection((0,), (OptionType.CARD,))]
    candidates = [
        Candidate(
            0,
            {"type": OptionType.CARD.value, "sourceCardId": TRANSCEIVER, "cardId": GIOVANNI},
            OptionType.CARD,
            features={"card_id": GIOVANNI},
        )
    ]

    assert agent._transceiver_selections(state, selections, candidates) == []
    assert agent.turn_ledger.deckout_veto_reason


def test_repeated_roto_without_expected_gain_is_blocked() -> None:
    agent = HonchkrowPorygonAgent(_profile(), "expert_turn_loop")
    agent.turn_ledger.roto_attempts_this_turn = 1
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{}, {}]),
                bench=[PokemonState(PORYGON, 90, 90)],
                hand=[{"id": ROTO_STICK}],
                deck_count=20,
            ),
            PlayerState(active=PokemonState(999, 350, 350)),
        ]
    )

    assert not agent._canonical_roto_is_productive(state)
    assert agent.turn_ledger.roto_last_outcome == "repeat_blocked_without_gain"


def test_roto_attack_mode_is_explicit_for_a_ready_honchkrow_line() -> None:
    agent = HonchkrowPorygonAgent(_profile(), "expert_turn_loop")
    state = GameState(
        turn=4,
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{}, {}]),
                bench=[PokemonState(PORYGON, 90, 90)],
                hand=[{"id": ROTO_STICK}],
                deck_count=20,
            ),
            PlayerState(active=PokemonState(999, 100, 100)),
        ],
    )

    assert agent._canonical_roto_is_productive(state)
    assert agent.turn_ledger.roto_mode == "attack_mode"


def test_roto_setup_mode_is_explicit_on_first_turn_without_supporters() -> None:
    agent = HonchkrowPorygonAgent(_profile(), "expert_turn_loop")
    state = GameState(
        turn=1,
        players=[
            PlayerState(
                active=PokemonState(MURKROW, 70, 70),
                hand=[{"id": ROTO_STICK}],
                deck_count=20,
            ),
            PlayerState(active=PokemonState(999, 100, 100)),
        ],
    )

    assert agent._canonical_roto_is_productive(state)
    assert agent.turn_ledger.roto_mode == "setup_mode"


def test_promotion_damage_tiebreak_prefers_more_damaged_comparable_attacker() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, serial=1, energies=[{}, {}]),
                bench=[
                    PokemonState(HONCHKROW, 40, 130, serial=2, energies=[{}, {}]),
                    PokemonState(HONCHKROW, 130, 130, serial=3, energies=[{}, {}]),
                ],
            ),
            PlayerState(active=PokemonState(999, 350, 350)),
        ]
    )
    damaged = Candidate(
        0,
        {"type": OptionType.CARD.value, "cardId": HONCHKROW},
        OptionType.CARD,
        features={"card_id": HONCHKROW, "target_serial": 2},
    )
    healthy = Candidate(
        1,
        {"type": OptionType.CARD.value, "cardId": HONCHKROW},
        OptionType.CARD,
        features={"card_id": HONCHKROW, "target_serial": 3},
    )

    damaged_score, damaged_reasons = scorer._card_selection_score(
        state, damaged, SelectContext.SWITCH
    )
    healthy_score, _ = scorer._card_selection_score(state, healthy, SelectContext.SWITCH)

    assert damaged_score > healthy_score
    assert "promotion_ready_attacker_lower_hp_tiebreak" in damaged_reasons
