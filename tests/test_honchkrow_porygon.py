from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.agents.heuristic import DecisionPhase
from src.agents.honchkrow_porygon import (
    ARCHER,
    ARIANA,
    ARTICUNO,
    DECEIT,
    FACTORY,
    FROSLASS,
    GIOVANNI,
    GRIMMSNARL_EX,
    HACKING,
    HAMMER_IN,
    HONCHKROW,
    IGNITION_ENERGY,
    MEGA_ABOMASNOW_DECK_RESERVE,
    MEGA_ABOMASNOW_EX,
    MEGA_ABOMASNOW_R_COMMAND_SUPPORTERS,
    MEGA_ABOMASNOW_ROCKET_FEATHERS_SUPPORTERS,
    MIRACLE_HEADSET,
    MURKROW,
    NIGHT_STRETCHER,
    PETREL,
    POKE_PAD,
    PORYGON,
    PORYGON2,
    PROTON,
    R_COMMAND,
    ROCKET_ENERGY,
    ROCKET_FEATHERS,
    ROTO_STICK,
    TORMENT,
    TRANSCEIVER,
    ULTRA_BALL,
    AttackSequence,
    HonchkrowPorygonAgent,
    HonchkrowPorygonScorer,
)
from src.core import (
    Candidate,
    GameState,
    OptionType,
    PlayerState,
    PokemonState,
    PrizeMapBuilder,
    SelectContext,
    Selection,
)
from src.data.honchkrow_audit import classify_loss, decision_evidence

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
    assert entrypoint.POLICY_VARIANT == "expert_turn_loop"
    assert entrypoint._build_agent().policy_variant == entrypoint.POLICY_VARIANT


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


def test_giovanni_economic_score_prioritizes_low_hp_two_prize_fezandipiti() -> None:
    """A reachable two-Prize Fezandipiti is an economic Giovanni target."""
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130),
                hand=[{"id": ARIANA}],
                prize=[None] * 3,
            ),
            PlayerState(
                active=PokemonState(999, 120, 120),
                bench=[PokemonState(140, 50, 120, serial=44)],
            ),
        ]
    )
    candidate = Candidate(
        0,
        {"type": OptionType.CARD.value, "cardId": 140, "targetCardId": 140},
        OptionType.CARD,
        features={"card_id": 140, "target_card_id": 140, "target_serial": 44},
    )

    _, reasons = scorer._giovanni_target_score(state, candidate)

    assert "economic_two_prize_ko" in reasons
    assert "giovanni_fezandipiti_two_prize_ko" in reasons


def test_effect_target_preserves_persistent_serial() -> None:
    """A later effect prompt must keep the already selected public Pokémon."""
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    target = PokemonState(140, 50, 120, serial=44)
    state = GameState(
        players=[PlayerState(), PlayerState(active=PokemonState(999, 120, 120), bench=[target])]
    )
    scorer.set_persistent_target(target)
    candidate = Candidate(
        0,
        {"type": OptionType.CARD.value, "cardId": 140},
        OptionType.CARD,
        features={"card_id": 140, "target_card_id": 140, "target_serial": 0},
    )

    assert scorer._target_opponent_pokemon(state, candidate) is target


def test_kadabra_super_psy_bolt_does_not_trigger_articuno_protection() -> None:
    """Kadabra's fixed-damage attack is not the Alakazam hand-size threat."""
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    scorer.set_alakazam_matchup_confirmed()
    state = GameState(players=[PlayerState(), PlayerState(active=PokemonState(742, 90, 90))])

    assert not scorer._powerful_hand_threat(state)
    assert not scorer._articuno_is_needed(state)


def test_alakazam_powerful_hand_triggers_articuno_protection() -> None:
    """Alakazam's hand-dependent attack still preserves the Articuno branch."""
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    scorer.set_alakazam_matchup_confirmed()
    state = GameState(players=[PlayerState(), PlayerState(active=PokemonState(743, 120, 120))])

    assert scorer._powerful_hand_threat(state)
    assert scorer._articuno_is_needed(state)


def test_grimmsnarl_froslass_matchup_avoids_articuno() -> None:
    """The Grimmsnarl/Froslass damage-ping board must not receive Articuno."""
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(
        players=[
            PlayerState(active=PokemonState(HONCHKROW, 120, 120)),
            PlayerState(
                active=PokemonState(GRIMMSNARL_EX, 170, 170),
                bench=[PokemonState(FROSLASS, 80, 80)],
            ),
        ]
    )
    candidate = _candidate(
        0,
        OptionType.CARD,
        card_id=ARTICUNO,
        card={"cardType": 0},
    )

    score, reasons = scorer._play_score(state, candidate)

    assert score < 0
    assert reasons == ["avoid_articuno_against_grimmsnarl_froslass"]
    assert not scorer._articuno_is_needed(state)


def test_visible_enhanced_hammer_preserves_uncommitted_special_energy() -> None:
    """Rocket Energy stays in hand until it commits an attack line."""
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(
        players=[
            PlayerState(active=PokemonState(PORYGON2, 120, 120)),
            PlayerState(hand=[{"id": 1081}]),
        ]
    )
    candidate = Candidate(
        0,
        {"type": OptionType.ATTACH.value, "cardId": ROCKET_ENERGY},
        OptionType.ATTACH,
        card={"cardType": 5},
        features={"card_id": ROCKET_ENERGY, "target_card_id": PORYGON2},
    )

    _, reasons = scorer._attachment_score(state, candidate)

    assert reasons == ["preserve_energy_against_enhanced_hammer"]


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


def test_strict_rocket_feathers_requires_six_supporters_against_mega_abomasnow() -> None:
    """The strict variant accepts the exact six-supporter Mega KO only."""
    agent = HonchkrowPorygonAgent(_profile(), "ko_priority_v2_strict")
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{"id": 15}, {"id": 15}]),
                hand=[{"id": card_id} for card_id in (1216, 1217, 1218, 1219, 1220, 1216)],
            ),
            PlayerState(active=PokemonState(MEGA_ABOMASNOW_EX, 350, 350)),
        ]
    )
    candidate = _candidate(0, OptionType.ATTACK, attack_id=ROCKET_FEATHERS)
    assert not agent._candidate_is_forbidden(state, candidate, SelectContext.MAIN)

    state.players[0].hand.pop()
    assert agent._candidate_is_forbidden(state, candidate, SelectContext.MAIN)


def test_supporter_lethal_variant_discards_exact_required_count_including_last_supporter() -> None:
    """A lethal Rocket Feathers line commits exactly the needed Supporters."""
    agent = HonchkrowPorygonAgent(_profile(), "supporter_lethal_v1")
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(
                    HONCHKROW, 130, 130, energies=[{"id": ROCKET_ENERGY}, {"id": ROCKET_ENERGY}]
                ),
                hand=[{"id": ARIANA}, {"id": ARCHER}],
            ),
            PlayerState(active=PokemonState(999, 60, 60)),
        ]
    )
    agent._attack_sequence = AttackSequence(
        ROCKET_FEATHERS, 999, 60, HONCHKROW, 2, 2, 120, 60, 60, 20
    )
    candidates = [
        _candidate(index, OptionType.CARD, card_id=card_id, card={"cardType": 3})
        for index, card_id in enumerate((ARIANA, ARCHER))
    ]
    selections = [
        Selection((0,), (OptionType.CARD,)),
        Selection((0, 1), (OptionType.CARD, OptionType.CARD)),
    ]
    filtered = agent._filter_forbidden_selections(
        state, selections, candidates, SelectContext.DISCARD
    )
    assert [selection.indices for selection in filtered] == [(0,)]


def test_resource_variant_selects_all_roto_supporters_and_blocks_duplicate_proton() -> None:
    """Roto takes every revealed Supporter and Transceiver diversifies Proton targets."""
    agent = HonchkrowPorygonAgent(_profile(), "supporter_resource_v2")
    state = GameState(players=[PlayerState(hand=[{"id": PROTON}], deck_count=20), PlayerState()])
    roto_candidates = [
        Candidate(
            index,
            {"type": OptionType.CARD.value, "sourceCardId": ROTO_STICK},
            OptionType.CARD,
            card={"cardType": 3},
            features={"card_id": card_id},
        )
        for index, card_id in enumerate((ARIANA, ARCHER, GIOVANNI, PROTON))
    ]
    roto_selections = [
        Selection((0, 1), (OptionType.CARD, OptionType.CARD)),
        Selection((0, 1, 2, 3), (OptionType.CARD,) * 4),
    ]
    filtered = agent._filter_forbidden_selections(
        state, roto_selections, roto_candidates, SelectContext.TO_HAND
    )
    assert [selection.indices for selection in filtered] == [(0, 1, 2, 3)]

    transceiver_candidates = [
        Candidate(
            index,
            {"type": OptionType.CARD.value, "sourceCardId": 1134},
            OptionType.CARD,
            card={"cardType": 3},
            features={"card_id": card_id},
        )
        for index, card_id in enumerate((PROTON, ARIANA))
    ]
    transceiver_selections = [
        Selection((0,), (OptionType.CARD,)),
        Selection((1,), (OptionType.CARD,)),
    ]
    filtered = agent._filter_forbidden_selections(
        state, transceiver_selections, transceiver_candidates, SelectContext.TO_HAND
    )
    assert [selection.indices for selection in filtered] == [(1,)]


def test_first_own_turn_uses_proton_before_ariana_for_required_setup() -> None:
    """A full opening hand does not override the one-Pokémon survival line."""
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        turn=1,
        your_index=0,
        first_player=0,
        players=[
            PlayerState(
                active=PokemonState(MURKROW, 80, 80),
                hand=[{"id": PROTON}, {"id": ARIANA}, *({"id": ARCHER} for _ in range(6))],
                deck_count=40,
            ),
            PlayerState(active=PokemonState(999, 100, 100)),
        ],
    )
    candidates = [
        _candidate(0, OptionType.PLAY, card_id=ARIANA, card={"cardType": 3}),
        _candidate(1, OptionType.PLAY, card_id=PROTON, card={"cardType": 3}),
    ]
    selections = [Selection((index,), (OptionType.PLAY,)) for index in range(2)]

    phase, reason, choices = agent._main_phase_selections(state, selections, candidates)

    assert phase == DecisionPhase.PLAY_SUPPORTER.value
    assert reason == "required_proton_board_setup"
    assert [selection.indices for selection in choices] == [(1,)]


def test_one_pokemon_board_uses_transceiver_to_reach_proton_before_ariana() -> None:
    """Transceiver inherits the setup objective when Proton is not in hand."""
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        turn=2,
        your_index=1,
        first_player=0,
        players=[
            PlayerState(
                active=PokemonState(MURKROW, 80, 80),
                hand=[{"id": TRANSCEIVER}, {"id": ARIANA}],
                deck_count=40,
            ),
            PlayerState(active=PokemonState(999, 100, 100)),
        ],
    )
    candidates = [
        _candidate(0, OptionType.PLAY, card_id=ARIANA, card={"cardType": 3}),
        _candidate(1, OptionType.PLAY, card_id=TRANSCEIVER, card={"cardType": 2}),
    ]
    selections = [Selection((index,), (OptionType.PLAY,)) for index in range(2)]

    _, reason, choices = agent._main_phase_selections(state, selections, candidates)

    assert reason == "required_proton_board_setup"
    assert [selection.indices for selection in choices] == [(1,)]


def test_late_transceiver_with_developed_board_does_not_fetch_proton() -> None:
    """A developed late board resolves Transceiver to resource improvement."""
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        turn=9,
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130),
                bench=[PokemonState(PORYGON, 60, 60)],
                hand=[{"id": TRANSCEIVER}],
                deck_count=30,
            ),
            PlayerState(active=PokemonState(999, 200, 200)),
        ],
    )
    candidates = [
        Candidate(
            index,
            {"type": OptionType.CARD.value, "sourceCardId": TRANSCEIVER},
            OptionType.CARD,
            card={"cardType": 3},
            features={"card_id": card_id},
        )
        for index, card_id in enumerate((PROTON, ARIANA))
    ]
    selections = [Selection((index,), (OptionType.CARD,)) for index in range(2)]

    choices = agent._transceiver_selections(state, selections, candidates)

    assert choices is not None
    assert [selection.indices for selection in choices] == [(1,)]
    assert agent.turn_ledger.transceiver_target == ARIANA


def test_expert_variant_takes_arithmetic_terminal_ko_before_setup() -> None:
    """A last-Prize KO is immediate even without an SDK win annotation."""
    agent = HonchkrowPorygonAgent(_profile(), "expert_rounds_1_3_v1")
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{"id": ROCKET_ENERGY}]),
                hand=[{"id": ARIANA}],
                prize=[None],
                deck_count=20,
            ),
            PlayerState(active=PokemonState(999, 60, 60)),
        ]
    )
    candidates = [
        _candidate(0, OptionType.ATTACK, attack_id=ROCKET_FEATHERS),
        _candidate(1, OptionType.PLAY, card_id=FACTORY, card={"cardType": 4}),
    ]
    selections = [
        Selection((index,), (candidate.option_type,)) for index, candidate in enumerate(candidates)
    ]

    _, reason, choices = agent._main_phase_selections(state, selections, candidates)

    assert reason == "pre_draw_game_win"
    assert [selection.indices for selection in choices] == [(0,)]


def test_expert_proton_maximizes_murkrow_instead_of_diversifying_roles() -> None:
    """Three Murkrow outrank a diversified Proton selection in the opening."""
    agent = HonchkrowPorygonAgent(_profile(), "expert_rounds_1_3_v1")
    state = GameState(turn=1, players=[PlayerState(), PlayerState()])
    candidates = [
        Candidate(
            index,
            {"type": OptionType.CARD.value, "sourceCardId": PROTON},
            OptionType.CARD,
            features={"card_id": card_id},
        )
        for index, card_id in enumerate((MURKROW, MURKROW, MURKROW, PORYGON))
    ]
    selections = [
        Selection((0, 1, 2), (OptionType.CARD,) * 3),
        Selection((0, 1, 3), (OptionType.CARD,) * 3),
    ]

    choices = agent._filter_duplicate_proton_roles(
        state, selections, candidates, SelectContext.TO_HAND
    )

    assert [selection.indices for selection in choices] == [(0, 1, 2)]


def test_expert_roto_setup_takes_one_proton_and_ariana_only() -> None:
    """Opening Roto bounds setup targets instead of maximizing all Supporters."""
    agent = HonchkrowPorygonAgent(_profile(), "expert_rounds_1_3_v1")
    state = GameState(
        turn=1,
        your_index=0,
        first_player=0,
        players=[PlayerState(hand=[{"id": ARCHER}], deck_count=30), PlayerState()],
    )
    candidates = [
        Candidate(
            index,
            {"type": OptionType.CARD.value, "sourceCardId": ROTO_STICK},
            OptionType.CARD,
            card={"cardType": 3},
            features={"card_id": card_id},
        )
        for index, card_id in enumerate((PROTON, PROTON, ARIANA, ARCHER))
    ]
    selections = [
        Selection((0, 2), (OptionType.CARD,) * 2),
        Selection((0, 1, 2), (OptionType.CARD,) * 3),
        Selection((0, 2, 3), (OptionType.CARD,) * 3),
    ]

    result = agent._roto_recovery_selections(state, selections, candidates)

    assert result is not None
    count, choices = result
    assert count == 2
    assert [selection.indices for selection in choices] == [(0, 2)]


def test_expert_replan_checkpoints_exclude_proton_and_poke_pad() -> None:
    """Only the actions ratified as information-changing clear the objective."""
    agent = HonchkrowPorygonAgent(_profile(), "expert_rounds_1_3_v1")
    state = GameState(turn=3, players=[PlayerState(), PlayerState()])
    ariana = _candidate(0, OptionType.PLAY, card_id=ARIANA, card={"cardType": 3})
    proton = _candidate(1, OptionType.PLAY, card_id=PROTON, card={"cardType": 3})
    poke_pad = _candidate(2, OptionType.PLAY, card_id=POKE_PAD, card={"cardType": 2})
    evolution = _candidate(3, OptionType.EVOLVE, card_id=HONCHKROW, card={"cardType": 0})
    energy = _candidate(4, OptionType.ATTACH, card_id=ROCKET_ENERGY, card={"cardType": 5})
    candidates = {item.option_index: item for item in (ariana, proton, poke_pad, evolution, energy)}

    assert agent._replan_reason(
        state, Selection((0,), (OptionType.PLAY,)), candidates, SelectContext.MAIN
    )
    assert not agent._replan_reason(
        state, Selection((1,), (OptionType.PLAY,)), candidates, SelectContext.MAIN
    )
    assert not agent._replan_reason(
        state, Selection((2,), (OptionType.PLAY,)), candidates, SelectContext.MAIN
    )
    assert (
        agent._replan_reason(
            state, Selection((3,), (OptionType.EVOLVE,)), candidates, SelectContext.MAIN
        )
        == "evolution"
    )
    assert (
        agent._replan_reason(
            state, Selection((4,), (OptionType.ATTACH,)), candidates, SelectContext.MAIN
        )
        == "energy_attachment"
    )
    assert (
        agent._replan_reason(state, Selection((), ()), candidates, SelectContext.TO_PRIZE)
        == "prize_selection"
    )


def test_expert_turn_loop_replans_after_board_search_supporter_and_retreat() -> None:
    """The dedicated turn loop invalidates every public state-changing plan."""
    agent = HonchkrowPorygonAgent(_profile(), "expert_turn_loop")
    state = GameState(turn=3, players=[PlayerState(), PlayerState()])
    basic = _candidate(0, OptionType.PLAY, card_id=MURKROW, card={"cardType": 0})
    search = _candidate(1, OptionType.PLAY, card_id=POKE_PAD, card={"cardType": 2})
    supporter = _candidate(2, OptionType.PLAY, card_id=PROTON, card={"cardType": 3})
    retreat = _candidate(3, OptionType.RETREAT)
    candidates = {item.option_index: item for item in (basic, search, supporter, retreat)}

    assert (
        agent._replan_reason(
            state, Selection((0,), (OptionType.PLAY,)), candidates, SelectContext.MAIN
        )
        == "pokemon_placement"
    )
    assert (
        agent._replan_reason(
            state, Selection((1,), (OptionType.PLAY,)), candidates, SelectContext.MAIN
        )
        == f"search_{POKE_PAD}"
    )
    assert (
        agent._replan_reason(
            state, Selection((2,), (OptionType.PLAY,)), candidates, SelectContext.MAIN
        )
        == f"supporter_{PROTON}"
    )
    assert (
        agent._replan_reason(
            state, Selection((3,), (OptionType.RETREAT,)), candidates, SelectContext.MAIN
        )
        == "retreat"
    )


def test_expert_turn_loop_ledger_uses_only_public_turn_facts() -> None:
    """Plan arithmetic is refreshed from the current factual zones."""
    agent = HonchkrowPorygonAgent(_profile(), "expert_turn_loop")
    state = GameState(
        turn=5,
        energy_attached=False,
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{"id": ROCKET_ENERGY}]),
                bench=[PokemonState(PORYGON2, 100, 100, energies=[{"id": IGNITION_ENERGY}])],
                hand=[{"id": ARIANA}, {"id": GIOVANNI}, {"id": IGNITION_ENERGY}],
                discard=[{"id": ARCHER}, {"id": PETREL}, {"id": PROTON}],
                deck_count=17,
            ),
            PlayerState(active=PokemonState(999, 180, 180)),
        ],
    )

    agent._refresh_public_turn_facts(state)

    ledger = agent.turn_ledger
    assert ledger.supporters_in_hand == 2
    assert ledger.supporters_in_discard == 3
    assert ledger.supporters_needed_for_ko == 3
    assert ledger.rocket_feathers_damage == 120
    assert ledger.r_command_damage == 60
    assert ledger.active_attacker_card_id == HONCHKROW
    assert ledger.bench_attacker_card_id == PORYGON2
    assert ledger.active_energy_units == 2
    assert ledger.energy_cards_in_hand == 1
    assert ledger.energy_attachable
    assert ledger.deck_reserve == 17


def test_expert_deceit_is_only_a_low_hand_no_supporter_survival_line() -> None:
    """Deceit may find Ariana only when the hand cannot otherwise progress."""
    agent = HonchkrowPorygonAgent(_profile(), "expert_rounds_1_3_v1")
    candidate = _candidate(0, OptionType.ATTACK, attack_id=DECEIT)
    low_hand = GameState(
        players=[
            PlayerState(hand=[], hand_count=0),
            PlayerState(active=PokemonState(999, 100, 100)),
        ]
    )
    supporter_hand = GameState(
        players=[
            PlayerState(hand=[{"id": ARIANA}], hand_count=1),
            PlayerState(active=PokemonState(999, 100, 100)),
        ]
    )

    assert not agent._candidate_is_forbidden(low_hand, candidate, SelectContext.MAIN)
    assert agent._candidate_is_forbidden(supporter_hand, candidate, SelectContext.MAIN)


def test_opening_active_order_is_murkrow_then_porygon_then_articuno() -> None:
    """Opening Active scoring follows the expert's sacrifice and setup order."""
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(players=[PlayerState(), PlayerState()])
    scores = []
    for card_id in (MURKROW, PORYGON, ARTICUNO):
        candidate = _candidate(0, OptionType.CARD, card_id=card_id)
        score, _ = scorer._card_selection_score(
            state, candidate, SelectContext.SETUP_ACTIVE_POKEMON
        )
        scores.append(score)

    assert scores[0] > scores[1] > scores[2]


def test_petrel_factory_dominates_one_card_ariana_draw() -> None:
    """Petrel creates the two-card Factory line when Ariana adds only one card."""
    agent = HonchkrowPorygonAgent(_profile())
    hand = [{"id": PETREL}, {"id": ARIANA}, *({"id": ARCHER} for _ in range(6))]
    state = GameState(
        turn=5,
        players=[
            PlayerState(
                active=PokemonState(MURKROW, 80, 80),
                hand=hand,
                hand_count=8,
                deck_count=30,
            ),
            PlayerState(active=PokemonState(999, 200, 200)),
        ],
    )
    candidates = [
        _candidate(0, OptionType.PLAY, card_id=ARIANA, card={"cardType": 3}),
        _candidate(1, OptionType.PLAY, card_id=PETREL, card={"cardType": 3}),
    ]
    selections = [Selection((index,), (OptionType.PLAY,)) for index in range(2)]

    _, reason, choices = agent._main_phase_selections(state, selections, candidates)

    assert reason == "petrel_factory_over_low_draw_ariana"
    assert [selection.indices for selection in choices] == [(1,)]
    assert agent.turn_ledger.petrel_factory_opportunities == 1


def test_petrel_target_scoring_accepts_non_ariana_supporter() -> None:
    """Petrel target evaluation must cover Proton and the other Supporters."""
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(MURKROW, 80, 80),
                hand=[{"id": PETREL}],
                hand_count=1,
                deck_count=30,
            ),
            PlayerState(active=PokemonState(999, 200, 200)),
        ]
    )
    candidate = Candidate(
        0,
        {"type": SelectContext.TO_HAND.value, "sourceCardId": PETREL},
        OptionType.CARD,
        card={"cardType": 3, "cardId": PROTON},
        features={"card_id": PROTON},
    )

    _, reasons = scorer._card_selection_score(state, candidate, SelectContext.TO_HAND)

    assert "petrel_target_any_supporter" in reasons


def test_factory_in_play_keeps_ariana_available_for_comparison() -> None:
    """An active Factory removes the Petrel-to-Stadium advantage."""
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        turn=5,
        stadium=str(FACTORY),
        players=[
            PlayerState(
                active=PokemonState(MURKROW, 80, 80),
                hand=[{"id": PETREL}, {"id": ARIANA}, *({"id": ARCHER} for _ in range(6))],
                hand_count=8,
                deck_count=30,
            ),
            PlayerState(active=PokemonState(999, 200, 200)),
        ],
    )
    candidates = [
        _candidate(0, OptionType.PLAY, card_id=ARIANA, card={"cardType": 3}),
        _candidate(1, OptionType.PLAY, card_id=PETREL, card={"cardType": 3}),
    ]
    selections = [Selection((index,), (OptionType.PLAY,)) for index in range(2)]

    _, _, choices = agent._main_phase_selections(state, selections, candidates)

    assert [selection.indices for selection in choices] == [(0,)]


def test_poke_pad_commits_only_a_proven_honchkrow_ko_line() -> None:
    """Search, legal evolution, Energy, damage, and target are one commitment."""
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        turn=5,
        players=[
            PlayerState(
                active=PokemonState(MURKROW, 80, 80, serial=7, energies=[{}, {}]),
                hand=[{"id": POKE_PAD}, {"id": ARIANA}, {"id": PROTON}],
                deck_count=30,
            ),
            PlayerState(active=PokemonState(121, 120, 320, serial=9)),
        ],
    )
    poke_pad = _candidate(0, OptionType.PLAY, card_id=POKE_PAD, card={"cardType": 2})
    torment = _candidate(1, OptionType.ATTACK, attack_id=TORMENT)
    selections = [
        Selection((0,), (OptionType.PLAY,)),
        Selection((1,), (OptionType.ATTACK,)),
    ]

    _, reason, choices = agent._main_phase_selections(state, selections, [poke_pad, torment])

    assert reason == "commit_poke_pad_honchkrow_ko"
    assert [selection.indices for selection in choices] == [(0,)]
    assert agent._evolution_ko_commitment is not None
    assert agent._evolution_ko_commitment.murkrow_serial == 7
    assert agent.turn_ledger.poke_pad_ko_opportunities == 1


def test_poke_pad_does_not_invent_ko_without_each_public_precondition() -> None:
    """Missing Energy, deck target, or evolution legality prevents commitment."""
    poke_pad = _candidate(0, OptionType.PLAY, card_id=POKE_PAD, card={"cardType": 2})
    base = GameState(
        turn=5,
        players=[
            PlayerState(
                active=PokemonState(MURKROW, 80, 80, serial=7, energies=[{}, {}]),
                hand=[{"id": POKE_PAD}, {"id": ARIANA}, {"id": PROTON}],
                deck_count=30,
            ),
            PlayerState(active=PokemonState(121, 120, 320)),
        ],
    )
    states = [
        GameState(
            turn=5, players=[PlayerState(active=PokemonState(MURKROW, 80, 80)), base.players[1]]
        ),
        GameState(
            turn=5,
            players=[
                PlayerState(
                    active=PokemonState(MURKROW, 80, 80, energies=[{}, {}]),
                    hand=[{"id": HONCHKROW}] * 3,
                ),
                base.players[1],
            ],
        ),
        GameState(
            turn=5,
            players=[
                PlayerState(
                    active=PokemonState(MURKROW, 80, 80, energies=[{}, {}], appear_this_turn=True),
                    hand=base.players[0].hand,
                ),
                base.players[1],
            ],
        ),
    ]

    for state in states:
        agent = HonchkrowPorygonAgent(_profile())
        agent._refresh_evolution_ko_commitment(state, [poke_pad])
        assert agent._evolution_ko_commitment is None


def test_v3_trace_regression_keeps_productive_honchkrow_active() -> None:
    """A productive Honchkrow must not burn its Energy to promote an empty Bench."""
    agent = HonchkrowPorygonAgent(_profile(), "ko_priority_v3_retreat_guard")
    state = GameState(
        turn=15,
        players=[
            PlayerState(
                active=PokemonState(
                    HONCHKROW,
                    130,
                    130,
                    serial=10,
                    energies=[{"id": 15}, {"id": 15}],
                ),
                bench=[
                    PokemonState(PORYGON2, 90, 90, serial=20),
                    PokemonState(PORYGON, 60, 60, serial=21),
                    PokemonState(HONCHKROW, 130, 130, serial=22),
                    PokemonState(MURKROW, 80, 80, serial=23),
                ],
                hand=[{"id": ARIANA}],
            ),
            PlayerState(active=PokemonState(721, 150, 150, serial=30)),
        ],
    )
    feathers = _candidate(0, OptionType.ATTACK, attack_id=ROCKET_FEATHERS)
    retreat = _candidate(1, OptionType.RETREAT)

    assert not agent._candidate_is_forbidden(state, feathers, SelectContext.MAIN)
    assert agent._candidate_is_forbidden(state, retreat, SelectContext.MAIN)


def test_v3_paid_retreat_requires_ready_bench_attack() -> None:
    """Paid retreat is legal only when a specific Bench attacker can attack now."""
    agent = HonchkrowPorygonAgent(_profile(), "ko_priority_v3_retreat_guard")
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(PORYGON, 60, 60, serial=10, energies=[{}]),
                bench=[PokemonState(HONCHKROW, 130, 130, serial=22)],
                hand=[{"id": ARIANA}],
            ),
            PlayerState(active=PokemonState(721, 150, 150, serial=30)),
        ]
    )
    retreat = _candidate(0, OptionType.RETREAT)
    assert agent._candidate_is_forbidden(state, retreat, SelectContext.MAIN)

    state.players[0].bench[0].energies = [{}, {}]  # type: ignore[union-attr]
    assert not agent._candidate_is_forbidden(state, retreat, SelectContext.MAIN)


def test_v3_giovanni_free_switch_dominates_paid_retreat() -> None:
    """Giovanni must replace paid retreat when the opponent has no Bench."""
    agent = HonchkrowPorygonAgent(_profile(), "ko_priority_v3_retreat_guard")
    state = GameState(
        turn=4,
        players=[
            PlayerState(
                active=PokemonState(PORYGON, 60, 60, serial=10, energies=[{}]),
                bench=[
                    PokemonState(
                        HONCHKROW,
                        130,
                        130,
                        serial=22,
                        energies=[{}, {}],
                    )
                ],
                hand=[{"id": GIOVANNI}, {"id": ARIANA}],
            ),
            PlayerState(active=PokemonState(721, 150, 150, serial=30)),
        ],
    )
    plan = agent._giovanni_switch_plan(state)
    assert plan is not None
    assert plan.method == "giovanni"
    assert plan.target_serial == 22
    assert plan.attack_id == ROCKET_FEATHERS
    assert agent._candidate_is_forbidden(
        state, _candidate(0, OptionType.RETREAT), SelectContext.MAIN
    )

    giovanni = _candidate(
        0,
        OptionType.PLAY,
        card_id=GIOVANNI,
        card={"cardType": 3},
    )
    retreat = _candidate(1, OptionType.RETREAT)
    end = _candidate(2, OptionType.END)
    phase, reason, choices = agent._main_phase_selections(
        state,
        [
            Selection((0,), (OptionType.PLAY,)),
            Selection((1,), (OptionType.RETREAT,)),
            Selection((2,), (OptionType.END,)),
        ],
        [giovanni, retreat, end],
    )
    assert phase == DecisionPhase.ATTACK_PRIORITY.value
    assert reason == "giovanni_free_switch_to_committed_attacker"
    assert [selection.indices for selection in choices] == [(0,)]


def test_v3_giovanni_does_not_promote_an_unready_bench() -> None:
    """Neither Giovanni nor paid retreat may promote a zero-Energy attacker."""
    agent = HonchkrowPorygonAgent(_profile(), "ko_priority_v3_retreat_guard")
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(PORYGON, 60, 60, serial=10, energies=[{}]),
                bench=[PokemonState(HONCHKROW, 130, 130, serial=22)],
                hand=[{"id": GIOVANNI}, {"id": ARIANA}],
            ),
            PlayerState(active=PokemonState(721, 150, 150, serial=30)),
        ]
    )
    assert agent._giovanni_switch_plan(state) is None
    assert agent._paid_retreat_plan(state) is None


def test_v3_giovanni_uses_post_play_supporter_damage() -> None:
    """A lone Giovanni cannot pretend to fund Rocket Feathers after being played."""
    agent = HonchkrowPorygonAgent(_profile(), "ko_priority_v3_retreat_guard")
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(PORYGON, 60, 60, serial=10),
                bench=[PokemonState(HONCHKROW, 130, 130, serial=22, energies=[{}, {}])],
                hand=[{"id": GIOVANNI}],
            ),
            PlayerState(active=PokemonState(721, 150, 150, serial=30)),
        ]
    )
    assert agent._giovanni_switch_plan(state) is None


def test_v3_giovanni_can_complete_r_command_from_discard() -> None:
    """Giovanni in discard must be included in the committed R Command damage."""
    agent = HonchkrowPorygonAgent(_profile(), "ko_priority_v3_retreat_guard")
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(PORYGON, 60, 60, serial=10),
                bench=[PokemonState(PORYGON2, 90, 90, serial=22, energies=[{}, {}, {}])],
                hand=[{"id": GIOVANNI}],
                discard=[{"id": ARIANA}] * 17,
            ),
            PlayerState(active=PokemonState(MEGA_ABOMASNOW_EX, 350, 350, serial=30)),
        ]
    )
    plan = agent._giovanni_switch_plan(state)
    assert plan is not None
    assert plan.attack_id == R_COMMAND
    assert plan.planned_damage == 360


def test_v3_projects_ignition_before_promoting_porygon2() -> None:
    """Promotion planning must include the three Energy supplied by Ignition."""
    agent = HonchkrowPorygonAgent(_profile(), "ko_priority_v3_retreat_guard")
    state = GameState(
        turn=8,
        players=[
            PlayerState(
                active=PokemonState(PORYGON, 60, 60, serial=10),
                bench=[PokemonState(PORYGON2, 90, 90, serial=22)],
                hand=[{"id": GIOVANNI}, {"id": IGNITION_ENERGY}],
                discard=[{"id": ARIANA}] * 17,
            ),
            PlayerState(active=PokemonState(MEGA_ABOMASNOW_EX, 350, 350, serial=30)),
        ],
    )

    plan = agent._giovanni_switch_plan(state)

    assert plan is not None
    assert plan.target_serial == 22
    assert plan.attack_id == R_COMMAND
    assert plan.planned_damage == 360
    assert plan.requires_ignition


def test_v3_commits_ignition_and_r_command_after_porygon2_promotion() -> None:
    """The selected Porygon2 line must force its Ignition attachment and attack."""
    from src.agents.honchkrow_porygon import SwitchCommitment

    agent = HonchkrowPorygonAgent(_profile(), "ko_priority_v3_retreat_guard")
    agent._switch_commitment = SwitchCommitment(
        method="giovanni",
        turn=8,
        target_card_id=PORYGON2,
        target_serial=22,
        attack_id=R_COMMAND,
        planned_damage=360,
        requires_ignition=True,
    )
    state = GameState(
        turn=8,
        players=[
            PlayerState(
                active=PokemonState(PORYGON2, 90, 90, serial=22),
                hand=[{"id": IGNITION_ENERGY}],
                discard=[{"id": ARIANA}] * 18,
            ),
            PlayerState(active=PokemonState(MEGA_ABOMASNOW_EX, 350, 350, serial=30)),
        ],
    )
    ignition = Candidate(
        0,
        {"type": OptionType.ATTACH.value},
        OptionType.ATTACH,
        card={"cardType": 6},
        features={
            "card_id": IGNITION_ENERGY,
            "target_card_id": PORYGON2,
            "target_serial": 22,
            "target_energy_count": 0,
            "target_is_active": True,
        },
    )
    end = _candidate(1, OptionType.END)

    phase, reason, choices = agent._main_phase_selections(
        state,
        [
            Selection((0,), (OptionType.ATTACH,)),
            Selection((1,), (OptionType.END,)),
        ],
        [ignition, end],
    )

    assert phase == DecisionPhase.ATTACK_PRIORITY.value
    assert reason == "attach_ignition_to_committed_attacker"
    assert [selection.indices for selection in choices] == [(0,)]

    state.energy_attached = True
    state.players[0].active.energies = [  # type: ignore[union-attr]
        {"source": IGNITION_ENERGY},
        {"source": IGNITION_ENERGY},
        {"source": IGNITION_ENERGY},
    ]
    state.players[0].hand = []
    attack = _candidate(2, OptionType.ATTACK, attack_id=R_COMMAND)
    phase, reason, choices = agent._main_phase_selections(
        state,
        [
            Selection((2,), (OptionType.ATTACK,)),
            Selection((1,), (OptionType.END,)),
        ],
        [attack, end],
    )

    assert phase == DecisionPhase.ATTACK_PRIORITY.value
    assert reason == "execute_committed_switch_attack"
    assert [selection.indices for selection in choices] == [(2,)]


def test_v3_does_not_project_ignition_after_energy_was_attached() -> None:
    """A spent attachment cannot justify promoting an otherwise unready Porygon2."""
    agent = HonchkrowPorygonAgent(_profile(), "ko_priority_v3_retreat_guard")
    state = GameState(
        energy_attached=True,
        players=[
            PlayerState(
                active=PokemonState(PORYGON, 60, 60, serial=10),
                bench=[PokemonState(PORYGON2, 90, 90, serial=22)],
                hand=[{"id": GIOVANNI}, {"id": IGNITION_ENERGY}],
                discard=[{"id": ARIANA}] * 17,
            ),
            PlayerState(active=PokemonState(MEGA_ABOMASNOW_EX, 350, 350, serial=30)),
        ],
    )

    assert agent._giovanni_switch_plan(state) is None


def test_v3_switch_prompt_selects_exact_committed_serial() -> None:
    """A switch commitment must not promote an unready duplicate card ID."""
    agent = HonchkrowPorygonAgent(_profile(), "ko_priority_v3_retreat_guard")
    from src.agents.honchkrow_porygon import SwitchCommitment

    agent._switch_commitment = SwitchCommitment(
        method="giovanni",
        turn=4,
        target_card_id=HONCHKROW,
        target_serial=22,
        attack_id=ROCKET_FEATHERS,
        planned_damage=120,
    )
    candidates = [
        Candidate(
            0,
            {"type": OptionType.CARD.value},
            OptionType.CARD,
            features={"card_id": HONCHKROW, "card_serial": 21, "card_energy_count": 0},
        ),
        Candidate(
            1,
            {"type": OptionType.CARD.value},
            OptionType.CARD,
            features={"card_id": HONCHKROW, "card_serial": 22, "card_energy_count": 2},
        ),
    ]
    selections = [
        Selection((0,), (OptionType.CARD,)),
        Selection((1,), (OptionType.CARD,)),
    ]
    filtered = agent._filter_forbidden_selections(
        GameState(turn=4), selections, candidates, SelectContext.TO_ACTIVE
    )
    assert [selection.indices for selection in filtered] == [(1,)]


def test_v3_headset_is_not_spent_for_one_supporter_while_holding_ariana() -> None:
    """Headset cannot be consumed for a one-card recovery with Ariana already held."""
    agent = HonchkrowPorygonAgent(_profile(), "ko_priority_v3_retreat_guard")
    state = GameState(
        turn=5,
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{}, {}]),
                hand=[{"id": ARIANA}],
                discard=[{"id": ARCHER}],
            ),
            PlayerState(active=PokemonState(721, 150, 150)),
        ],
    )
    headset = _candidate(0, OptionType.PLAY, card_id=MIRACLE_HEADSET, card={"cardType": 1})
    assert agent._candidate_is_forbidden(state, headset, SelectContext.MAIN)


def test_v3_headset_recovers_exactly_two_nonduplicate_supporters_for_ko() -> None:
    """A committed Headset line takes two useful Supporters and avoids duplicate Ariana."""
    agent = HonchkrowPorygonAgent(_profile(), "ko_priority_v3_retreat_guard")
    state = GameState(
        turn=5,
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{}, {}]),
                hand=[{"id": ARIANA}],
                discard=[{"id": ARIANA}, {"id": ARCHER}, {"id": GIOVANNI}],
            ),
            PlayerState(active=PokemonState(721, 150, 150)),
        ],
    )
    headset = _candidate(0, OptionType.PLAY, card_id=MIRACLE_HEADSET, card={"cardType": 1})
    assert not agent._candidate_is_forbidden(state, headset, SelectContext.MAIN)
    agent._headset_turn = 5
    candidates = [
        Candidate(
            index,
            {"type": OptionType.CARD.value},
            OptionType.CARD,
            card={"cardType": 3},
            features={"card_id": card_id},
        )
        for index, card_id in enumerate((ARIANA, ARCHER, GIOVANNI))
    ]
    selections = [
        Selection((0,), (OptionType.CARD,)),
        Selection((1, 2), (OptionType.CARD, OptionType.CARD)),
        Selection((0, 1), (OptionType.CARD, OptionType.CARD)),
    ]
    filtered = agent._filter_forbidden_selections(
        state, selections, candidates, SelectContext.TO_HAND
    )
    assert [selection.indices for selection in filtered] == [(1, 2)]


def test_v3_headset_recovers_one_supporter_when_only_one_is_available() -> None:
    """Headset recovery is capped at two but may complete a one-card KO line."""
    agent = HonchkrowPorygonAgent(_profile(), "ko_priority_v3_retreat_guard")
    state = GameState(
        turn=5,
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{}, {}]),
                discard=[{"id": ARCHER}],
            ),
            PlayerState(active=PokemonState(721, 50, 50)),
        ],
    )
    headset = _candidate(0, OptionType.PLAY, card_id=MIRACLE_HEADSET, card={"cardType": 1})
    assert not agent._candidate_is_forbidden(state, headset, SelectContext.MAIN)
    agent._headset_turn = 5
    candidates = [
        Candidate(
            0,
            {"type": OptionType.CARD.value},
            OptionType.CARD,
            card={"cardType": 3},
            features={"card_id": ARCHER},
        )
    ]
    filtered = agent._filter_forbidden_selections(
        state,
        [Selection((), ()), Selection((0,), (OptionType.CARD,))],
        candidates,
        SelectContext.TO_HAND,
    )
    assert [selection.indices for selection in filtered] == [(0,)]


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


def test_pokepad_searches_honchkrow_for_attack_or_ariana_hand_refresh() -> None:
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        turn=3,
        players=[
            PlayerState(
                active=PokemonState(MURKROW, 60, 60),
                hand=[{"id": card_id} for card_id in range(8)],
            ),
            PlayerState(),
        ],
    )
    candidate = _candidate(
        0,
        OptionType.CARD,
        card_id=HONCHKROW,
        card={"cardType": 0},
    )
    assert not agent._candidate_is_forbidden(state, candidate, SelectContext.TO_HAND)


def test_archer_requires_public_own_ko_but_not_board_collapse() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    candidate = _candidate(0, OptionType.PLAY, card_id=ARCHER, card={"cardType": 3})
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(MURKROW, 10, 80),
                hand_count=6,
                deck_count=20,
                bench=[PokemonState(PORYGON, 30, 90)],
            ),
            PlayerState(active=PokemonState(999, 100, 100), hand_count=2),
        ]
    )
    assert not scorer._archer_is_safe_and_useful(state, candidate)
    scorer.set_own_ko_observed(True)
    assert scorer._archer_is_safe_and_useful(state, candidate)


def test_archer_remains_eligible_when_a_winning_attack_exists() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    candidate = _candidate(0, OptionType.PLAY, card_id=ARCHER, card={"cardType": 3})
    scorer.set_own_ko_observed(True)
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{}, {}]),
                hand_count=2,
                deck_count=20,
            ),
            PlayerState(active=PokemonState(999, 100, 100), hand_count=6),
        ]
    )
    assert scorer._archer_is_safe_and_useful(state, candidate)


def test_roto_does_not_become_needed_only_after_own_ko() -> None:
    """A KO window belongs to Archer and must not independently authorize Roto-Stick."""
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    scorer.set_own_ko_observed(True)
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130),
                hand=[{"id": ROTO_STICK}],
                deck_count=20,
            ),
            PlayerState(active=PokemonState(999, 100, 100)),
        ]
    )

    assert not scorer._roto_stick_is_needed(state)


def test_roto_is_needed_for_a_direct_supporter_deficit() -> None:
    """Roto becomes a priority when a ready Honchkrow lacks KO supporters."""
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{}, {}]),
                hand=[{"id": ROTO_STICK}],
                deck_count=20,
            ),
            PlayerState(active=PokemonState(999, 100, 100)),
        ]
    )

    assert scorer._roto_stick_is_needed(state)


def test_roto_probability_uses_four_revealed_cards() -> None:
    """Roto's expected value must model its four-card reveal."""
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{}, {}]),
                hand=[{"id": ROTO_STICK}],
                deck_count=20,
                discard=[{"id": 1216}] * 15,
            ),
            PlayerState(active=PokemonState(999, 100, 100)),
        ]
    )

    roto_probability = scorer._roto_hit_probability(state, 1)
    four_card_probability = scorer._supporter_hit_probability(state, 4, 1)

    assert roto_probability == four_card_probability


def test_special_roto_opening_selects_only_proton_or_nothing() -> None:
    agent = HonchkrowPorygonAgent(_profile(), "expert_turn_loop")
    state = GameState(
        turn=2,
        your_index=1,
        first_player=0,
        raw={"episodeId": 91190470},
        players=[PlayerState(), PlayerState(hand=[{"id": ROTO_STICK}], deck_count=30)],
    )
    candidates = [
        Candidate(
            index,
            {"type": OptionType.CARD.value, "sourceCardId": ROTO_STICK},
            OptionType.CARD,
            card={"cardType": 3},
            features={"card_id": card_id},
        )
        for index, card_id in enumerate((PROTON, ARIANA))
    ]
    selections = [Selection((0,), (OptionType.CARD,)), Selection((1,), (OptionType.CARD,))]
    count, choices = agent._roto_recovery_selections(state, selections, candidates) or (0, [])
    assert count == 1
    assert [selection.indices for selection in choices] == [(0,)]


def test_special_roto_can_be_burned_without_selecting_a_supporter() -> None:
    agent = HonchkrowPorygonAgent(_profile(), "expert_turn_loop")
    state = GameState(
        turn=2,
        your_index=1,
        first_player=0,
        raw={"episodeId": 91190470},
        players=[PlayerState(), PlayerState(hand=[{"id": ROTO_STICK}], deck_count=30)],
    )
    candidates = [
        Candidate(
            0,
            {"type": OptionType.CARD.value, "sourceCardId": ROTO_STICK},
            OptionType.CARD,
            card={"cardType": 3},
            features={"card_id": ARIANA},
        )
    ]
    count, choices = agent._roto_recovery_selections(state, [Selection((), ())], candidates) or (
        1,
        [],
    )
    assert count == 0
    assert [selection.indices for selection in choices] == [()]


def test_transceiver_selects_proton_even_when_ariana_is_in_hand() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(turn=1, players=[PlayerState(hand=[{"id": ARIANA}]), PlayerState()])
    candidate = _candidate(0, OptionType.CARD, card_id=PROTON, card={"cardType": 3})
    score, reasons = scorer._card_selection_score(state, candidate, SelectContext.TO_HAND)
    assert score > 1500
    assert "select_proton_for_early_setup" in reasons


def test_porygon_is_not_benched_before_the_opening_pokemon() -> None:
    agent = HonchkrowPorygonAgent(_profile())
    candidate = _candidate(0, OptionType.CARD, card_id=PORYGON2, card={"cardType": 0})
    state = GameState(players=[PlayerState(), PlayerState()])
    assert agent._candidate_is_forbidden(state, candidate, SelectContext.SETUP_BENCH_POKEMON)


def test_rocket_energy_is_not_attached_to_porygon() -> None:
    agent = HonchkrowPorygonAgent(_profile())
    candidate = Candidate(
        0,
        {"type": OptionType.ATTACH.value},
        OptionType.ATTACH,
        card={"cardType": 5},
        features={"card_id": ROCKET_ENERGY, "target_card_id": PORYGON2},
    )
    state = GameState(players=[PlayerState(), PlayerState()])
    assert agent._candidate_is_forbidden(state, candidate, SelectContext.ATTACH_ENERGY)


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


def test_non_damaging_hacking_loses_to_a_decisive_policy_signal() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    hacking = _candidate(0, OptionType.ATTACK, attack_id=HACKING)
    score, reasons = scorer._attack_score(
        GameState(players=[PlayerState(active=PokemonState(HONCHKROW, 130, 130)), PlayerState()]),
        hacking,
    )
    assert score < 0
    assert "hacking_without_decisive_interrupt" in reasons


def test_torment_is_contextual_and_deceit_requires_tempo() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(players=[PlayerState(), PlayerState(active=PokemonState(999, 100, 100))])
    torment = _candidate(0, OptionType.ATTACK, attack_id=TORMENT)
    torment.option["preventsAttack"] = True
    assert scorer._attack_score(state, torment)[0] > 500
    deceit = _candidate(1, OptionType.ATTACK, attack_id=DECEIT)
    assert scorer._attack_score(state, deceit)[0] < 0


def test_loss_classifier_prioritizes_terminal_causes() -> None:
    assert (
        classify_loss(owner_deck_count=0, owner_field_count=1, owner_prizes=3, opponent_prizes=1)
        == "DECK_OUT"
    )
    assert (
        classify_loss(owner_deck_count=20, owner_field_count=0, owner_prizes=3, opponent_prizes=3)
        == "DONK / BOARD_COLLAPSE"
    )
    assert (
        classify_loss(owner_deck_count=20, owner_field_count=1, owner_prizes=2, opponent_prizes=0)
        == "PRIZE_RACE_LOSS"
    )


def test_decision_evidence_captures_competing_attacks_and_supporters() -> None:
    record = {
        "episode_id": 90272101,
        "step_index": 12,
        "selected_indices": [1],
        "observation": {
            "current": {
                "turn": 6,
                "yourIndex": 0,
                "players": [
                    {
                        "active": [{"id": HONCHKROW}],
                        "bench": [{"id": PORYGON}],
                        "hand": [{"id": ARIANA}],
                        "deckCount": 18,
                        "prize": [None, None, None],
                    },
                    {"prize": [None, None]},
                ],
            },
            "select": {
                "context": 0,
                "option": [
                    {"type": 13, "attackId": HACKING},
                    {"type": 13, "attackId": TORMENT, "damage": 30},
                ],
            },
        },
    }
    evidence = decision_evidence(record)
    assert evidence.attack_id == TORMENT
    assert evidence.competing_attack_ids == (HACKING,)
    assert evidence.supporter_ids_in_hand == (ARIANA,)
    assert evidence.opponent_prizes == 2


def test_decision_evidence_flags_partial_attack_into_mega_abomasnow() -> None:
    record = {
        "episode_id": 90494772,
        "step_index": 48,
        "selected_indices": [0],
        "observation": {
            "current": {
                "turn": 7,
                "yourIndex": 0,
                "players": [
                    {
                        "active": [{"id": HONCHKROW}],
                        "bench": [],
                        "hand": [{"id": ARIANA}] * 3,
                        "discard": [{"id": PROTON}] * 3,
                        "deckCount": 27,
                        "prize": [None] * 6,
                    },
                    {
                        "active": [{"id": MEGA_ABOMASNOW_EX, "hp": 350}],
                        "prize": [None] * 6,
                    },
                ],
            },
            "select": {
                "context": 0,
                "option": [{"type": 13, "attackId": ROCKET_FEATHERS}],
            },
        },
    }
    evidence = decision_evidence(record)
    assert evidence.opponent_active_card_id == MEGA_ABOMASNOW_EX
    assert evidence.opponent_active_hp == 350
    assert evidence.rocket_supporters_in_discard == 3
    assert evidence.mega_abomasnow_partial_attack


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


def test_draw_first_prefers_factory_before_ariana_and_nonwinning_attack() -> None:
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        turn=4,
        players=[
            PlayerState(
                active=PokemonState(MURKROW, 80, 80),
                hand=[{"id": ARIANA}, {"id": FACTORY}, {"id": ROCKET_ENERGY}],
                hand_count=3,
                deck_count=12,
            ),
            PlayerState(active=PokemonState(999, 200, 200)),
        ],
    )
    candidates = [
        _candidate(0, OptionType.PLAY, card_id=ARIANA, card={"cardType": 3}),
        _candidate(1, OptionType.PLAY, card_id=FACTORY, card={"cardType": 4}),
        _candidate(2, OptionType.ATTACK, attack_id=TORMENT),
    ]
    selections = [
        Selection((candidate.option_index,), (candidate.option_type,)) for candidate in candidates
    ]
    _, reason, eligible = agent._main_phase_selections(state, selections, candidates)
    assert reason == "stadium_before_ariana"
    assert [selection.indices for selection in eligible] == [(1,)]


def test_expert_turn_loop_plays_factory_drawn_by_ariana_before_factory_effect() -> None:
    """A Factory drawn by Ariana is placed before its productive draw effect."""
    agent = HonchkrowPorygonAgent(_profile(), "expert_turn_loop")
    state = GameState(
        turn=4,
        supporter_played=True,
        players=[
            PlayerState(
                active=PokemonState(MURKROW, 80, 80),
                hand=[{"id": FACTORY}, {"id": ROCKET_ENERGY}],
                hand_count=2,
                deck_count=8,
            ),
            PlayerState(active=PokemonState(999, 200, 200)),
        ],
    )
    candidates = [
        _candidate(0, OptionType.PLAY, card_id=FACTORY, card={"cardType": 4}),
        _candidate(1, OptionType.ATTACK, attack_id=TORMENT),
    ]
    selections = [
        Selection((candidate.option_index,), (candidate.option_type,)) for candidate in candidates
    ]

    _, reason, eligible = agent._main_phase_selections(state, selections, candidates)

    assert reason == "canonical_place_factory_drawn_by_supporter"
    assert [selection.indices for selection in eligible] == [(0,)]
    state.stadium = str(FACTORY)
    state.stadium_played = True
    factory_effect = _candidate(2, OptionType.ABILITY, card_id=FACTORY)
    _, effect_reason, effect_choices = agent._main_phase_selections(
        state,
        [Selection((2,), (OptionType.ABILITY,))],
        [factory_effect],
    )
    assert effect_reason == "canonical_factory_after_supporter"
    assert [selection.indices for selection in effect_choices] == [(2,)]


def test_canonical_turn_loop_factory_precedes_roto_after_supporter(monkeypatch) -> None:
    """The canonical stage machine must activate Factory before Roto-Stick."""
    agent = HonchkrowPorygonAgent(_profile(), "expert_turn_loop")
    agent.turn_ledger.stage = "factory"
    state = GameState(
        turn=4,
        supporter_played=True,
        stadium=[{"id": FACTORY}],
        players=[PlayerState(active=PokemonState(HONCHKROW, 130, 130)), PlayerState()],
    )
    monkeypatch.setattr(agent._scorer, "_factory_is_useful", lambda _state: True)
    candidates = [
        _candidate(0, OptionType.PLAY, card_id=ROTO_STICK),
        _candidate(1, OptionType.ABILITY, card_id=FACTORY),
    ]
    selections = [
        Selection((candidate.option_index,), (candidate.option_type,)) for candidate in candidates
    ]
    _, reason, eligible = agent._main_phase_selections(state, selections, candidates)
    assert reason == "canonical_factory_after_supporter"
    assert [selection.indices for selection in eligible] == [(1,)]


def test_canonical_ultra_ball_requires_ariana(monkeypatch) -> None:
    """Ultra Ball is blocked unless Ariana can convert the hand reduction."""
    agent = HonchkrowPorygonAgent(_profile(), "expert_turn_loop")
    state = GameState(players=[PlayerState(hand=[{"id": ULTRA_BALL}]), PlayerState()])
    monkeypatch.setattr(agent._scorer, "_ultra_ball_is_productive", lambda _state: True)
    assert not agent._canonical_ultra_ball_is_productive(state)
    state.players[0].hand.append({"id": ARIANA})
    assert agent._canonical_ultra_ball_is_productive(state)


def test_night_stretcher_requires_immediate_bench_or_evolution_before_ariana() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    bench_state = GameState(
        players=[PlayerState(discard=[{"id": PORYGON}], bench_max=1), PlayerState()]
    )
    assert scorer._night_stretcher_is_productive(bench_state)

    evolve_state = GameState(
        players=[
            PlayerState(bench=[PokemonState(MURKROW, 80, 80)], discard=[{"id": HONCHKROW}]),
            PlayerState(),
        ]
    )
    assert scorer._night_stretcher_is_productive(evolve_state)

    blocked_state = GameState(
        players=[
            PlayerState(
                bench=[PokemonState(MURKROW, 80, 80)], bench_max=1, discard=[{"id": PORYGON}]
            ),
            PlayerState(),
        ]
    )
    assert not scorer._night_stretcher_is_productive(blocked_state)


def test_factory_is_only_useful_after_supporter_and_with_two_cards_left_to_draw() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(players=[PlayerState(deck_count=2), PlayerState()])
    assert not scorer._factory_is_useful(state)
    state.supporter_played = True
    state.players[0].deck_count = 3
    assert scorer._factory_is_useful(state)
    state.players[0].deck_count = 1
    assert not scorer._factory_is_useful(state)


def test_elective_draw_reserves_natural_draw_outside_mega_matchup() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(players=[PlayerState(deck_count=1), PlayerState()])
    assert scorer._elective_draw_reserve(state) == 1
    state.players[1].active = PokemonState(MEGA_ABOMASNOW_EX, 350, 350)
    assert scorer._elective_draw_reserve(state) == MEGA_ABOMASNOW_DECK_RESERVE


def test_energy_units_count_rocket_and_ignition_as_multi_unit_cards() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    pokemon = PokemonState(
        PORYGON2,
        90,
        90,
        energy_card_ids=[str(ROCKET_ENERGY), str(IGNITION_ENERGY)],
    )
    assert scorer._energy_units_for_pokemon(pokemon) == 5


def test_r_command_uses_all_discarded_rocket_supporters_without_darkness_weakness() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    target = PokemonState(999, 330, 330)
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(PORYGON2, 90, 90),
                discard=[{"id": ARIANA}] * 16,
            ),
            PlayerState(active=target),
        ]
    )
    candidate = _candidate(0, OptionType.ATTACK, attack_id=R_COMMAND)
    score, reasons = scorer._attack_score(state, candidate)
    assert score >= 820
    assert "r_command_ko" not in reasons
    state.players[0].discard.extend([{"id": ARCHER}] * 3)
    assert "r_command_ko" in scorer._attack_score(state, candidate)[1]


def test_deck_and_resource_guards_reject_wasteful_search_and_archer() -> None:
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(players=[PlayerState(deck_count=2, hand_count=2), PlayerState()])
    ultra_ball = _candidate(0, OptionType.PLAY, card_id=ULTRA_BALL, card={"cardType": 1})
    headset = _candidate(1, OptionType.PLAY, card_id=MIRACLE_HEADSET, card={"cardType": 1})
    archer = _candidate(2, OptionType.PLAY, card_id=ARCHER, card={"cardType": 3})
    archer.option["eligibleAfterKo"] = True
    assert agent._candidate_is_forbidden(state, ultra_ball, SelectContext.MAIN)
    assert agent._candidate_is_forbidden(state, headset, SelectContext.MAIN)
    assert agent._candidate_is_forbidden(state, archer, SelectContext.MAIN)


def test_articuno_and_benched_ignition_remain_forbidden() -> None:
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(players=[PlayerState(), PlayerState()])
    articuno_energy = Candidate(
        0,
        {"type": OptionType.ATTACH.value},
        OptionType.ATTACH,
        card={"cardType": 5},
        features={"card_id": ROCKET_ENERGY, "target_card_id": ARTICUNO},
    )
    ignition_bench = Candidate(
        1,
        {"type": OptionType.ATTACH.value, "enablesAttack": True},
        OptionType.ATTACH,
        card={"cardType": 6},
        features={
            "card_id": IGNITION_ENERGY,
            "target_card_id": HONCHKROW,
            "target_energy_count": 1,
            "target_is_active": False,
        },
    )
    assert agent._candidate_is_forbidden(state, articuno_energy, SelectContext.ATTACH_ENERGY)
    assert agent._candidate_is_forbidden(state, ignition_bench, SelectContext.ATTACH_ENERGY)


def test_mega_abomasnow_requires_six_supporters_for_rocket_feathers() -> None:
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{}, {}]),
                hand=[{"id": ARIANA}] * (MEGA_ABOMASNOW_ROCKET_FEATHERS_SUPPORTERS - 1),
            ),
            PlayerState(active=PokemonState(MEGA_ABOMASNOW_EX, 350, 350)),
        ]
    )
    feathers = _candidate(0, OptionType.ATTACK, attack_id=ROCKET_FEATHERS)
    assert agent._candidate_is_forbidden(state, feathers, SelectContext.MAIN)
    state.players[0].hand.append({"id": ARCHER})
    assert not agent._candidate_is_forbidden(state, feathers, SelectContext.MAIN)


def test_mega_abomasnow_requires_eighteen_supporters_for_r_command() -> None:
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(PORYGON2, 90, 90, energies=[{}, {}, {}]),
                discard=[{"id": ARIANA}] * (MEGA_ABOMASNOW_R_COMMAND_SUPPORTERS - 1),
            ),
            PlayerState(active=PokemonState(MEGA_ABOMASNOW_EX, 350, 350)),
        ]
    )
    r_command = _candidate(0, OptionType.ATTACK, attack_id=R_COMMAND)
    assert agent._candidate_is_forbidden(state, r_command, SelectContext.MAIN)
    state.players[0].discard.append({"id": ARCHER})
    assert not agent._candidate_is_forbidden(state, r_command, SelectContext.MAIN)


def test_porygon2_promotion_waits_for_mega_abomasnow_ko_line() -> None:
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        players=[
            PlayerState(
                bench=[PokemonState(PORYGON2, 90, 90, energies=[{}, {}, {}])],
                discard=[{"id": ARIANA}] * (MEGA_ABOMASNOW_R_COMMAND_SUPPORTERS - 1),
            ),
            PlayerState(active=PokemonState(MEGA_ABOMASNOW_EX, 350, 350)),
        ]
    )
    porygon2 = Candidate(
        0,
        {"type": OptionType.CARD.value, "cardId": PORYGON2},
        OptionType.CARD,
        features={"card_id": PORYGON2, "target_energy_count": 3},
    )
    score, reasons = agent._scorer._card_selection_score(state, porygon2, SelectContext.TO_ACTIVE)
    assert score < 0
    assert reasons == ["defer_porygon2_until_mega_abomasnow_ko_ready"]
    assert agent._candidate_is_forbidden(state, porygon2, SelectContext.TO_ACTIVE)
    state.players[0].discard.append({"id": ARCHER})
    score, reasons = agent._scorer._card_selection_score(state, porygon2, SelectContext.TO_ACTIVE)
    assert score > 0
    assert reasons == ["promote_porygon2_best_r_command"]
    assert not agent._candidate_is_forbidden(state, porygon2, SelectContext.TO_ACTIVE)


def test_porygon2_promotion_takes_the_last_prizes() -> None:
    """A lethal R Command that ends the Prize race dominates promotion scoring."""
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        players=[
            PlayerState(
                prize=[None, None],
                bench=[PokemonState(PORYGON2, 90, 90, energies=[{}, {}, {}])],
                discard=[{"id": ARIANA}] * 18,
            ),
            PlayerState(active=PokemonState(MEGA_ABOMASNOW_EX, 350, 350)),
        ]
    )
    agent._scorer.set_strategic_context(None, PrizeMapBuilder(agent._scorer.catalog).build(state))
    porygon2 = Candidate(
        0,
        {"type": OptionType.CARD.value, "cardId": PORYGON2},
        OptionType.CARD,
        features={"card_id": PORYGON2, "target_energy_count": 3},
    )

    score, reasons = agent._scorer._card_selection_score(state, porygon2, SelectContext.TO_ACTIVE)

    assert score == 5200.0
    assert reasons == [
        "promote_porygon2_game_winning_r_command",
        "r_command_takes_last_prizes",
    ]


def test_ignition_attack_line_is_available_without_preempting_choice() -> None:
    """An enabled Ignition line remains available without preempting other choices."""
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        turn=9,
        players=[
            PlayerState(
                active=PokemonState(PORYGON2, 90, 90, serial=22),
                hand=[{"id": IGNITION_ENERGY}],
                discard=[{"id": ARIANA}] * 18,
            ),
            PlayerState(active=PokemonState(MEGA_ABOMASNOW_EX, 350, 350, serial=30)),
        ],
    )
    ignition = Candidate(
        0,
        {"type": OptionType.ATTACH.value},
        OptionType.ATTACH,
        card={"cardType": 6},
        features={
            "card_id": IGNITION_ENERGY,
            "target_card_id": PORYGON2,
            "target_serial": 22,
            "target_energy_count": 0,
            "target_is_active": True,
        },
    )
    end = _candidate(1, OptionType.END)

    phase, reason, choices = agent._main_phase_selections(
        state,
        [Selection((0,), (OptionType.ATTACH,)), Selection((1,), (OptionType.END,))],
        [ignition, end],
    )

    assert phase != DecisionPhase.ATTACK_PRIORITY.value
    assert reason != "ignition_requires_same_turn_attack"
    assert [selection.indices for selection in choices] == [(0,)]
    assert not agent._candidate_is_forbidden(state, ignition, SelectContext.MAIN)


def test_attack_planner_counts_typed_rocket_energy_units() -> None:
    """Hammer In needs Darkness plus two total units, not merely three cards."""
    agent = HonchkrowPorygonAgent(_profile())
    honchkrow = PokemonState(
        HONCHKROW,
        130,
        130,
        energy_card_ids=[{"id": ROCKET_ENERGY}],  # type: ignore[list-item]
    )

    assert not agent._attack_cost_satisfied(honchkrow, HAMMER_IN)
    assert agent._attack_cost_satisfied(honchkrow, HAMMER_IN, include_ignition=True)

    honchkrow.energy_card_ids.append({"id": ROCKET_ENERGY})  # type: ignore[arg-type]
    assert agent._attack_cost_satisfied(honchkrow, HAMMER_IN)


def test_attack_planner_does_not_treat_wrong_energy_type_as_darkness() -> None:
    """A non-Darkness basic Energy cannot unlock Honchkrow's Hammer In."""
    agent = HonchkrowPorygonAgent(_profile())
    honchkrow = PokemonState(
        HONCHKROW,
        130,
        130,
        energy_card_ids=[{"id": 3}, {"id": 3}, {"id": 3}],  # type: ignore[list-item]
    )

    assert not agent._attack_cost_satisfied(honchkrow, HAMMER_IN)
    assert not agent._attack_cost_satisfied(honchkrow, HAMMER_IN, include_ignition=True)


def test_ignition_commitment_falls_back_to_any_legal_attack() -> None:
    """A legal post-Ignition attack precedes an otherwise safe Ariana play."""
    agent = HonchkrowPorygonAgent(_profile(), "expert_turn_loop")
    from src.agents.honchkrow_porygon import SwitchCommitment

    agent._switch_commitment = SwitchCommitment(
        method="ignition",
        turn=9,
        target_card_id=HONCHKROW,
        target_serial=22,
        attack_id=999999,
        planned_damage=100,
    )
    state = GameState(
        turn=9,
        energy_attached=True,
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, serial=22, energies=[{}, {}, {}]),
                hand=[{"id": ARIANA}],
                deck_count=30,
            ),
            PlayerState(active=PokemonState(999, 100, 100)),
        ],
    )
    attack = _candidate(0, OptionType.ATTACK, attack_id=999999)
    ariana = _candidate(1, OptionType.PLAY, card_id=ARIANA, card={"cardType": 3})

    phase, reason, choices = agent._main_phase_selections(
        state,
        [Selection((0,), (OptionType.ATTACK,)), Selection((1,), (OptionType.PLAY,))],
        [attack, ariana],
    )

    assert phase == DecisionPhase.ATTACK_PRIORITY.value
    assert reason == "canonical_execute_ignition_attack"
    assert [selection.indices for selection in choices] == [(0,)]


def test_ignition_hammer_line_uses_active_serial_when_area_flag_is_missing() -> None:
    """Ignition must find Hammer In when CABT omits the active-area enum."""
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        turn=9,
        players=[
            PlayerState(
                active=PokemonState(
                    HONCHKROW,
                    130,
                    130,
                    serial=22,
                    energies=[11],
                    energy_card_ids=["15"],
                ),
                hand=[{"id": IGNITION_ENERGY}],
            ),
            PlayerState(active=PokemonState(999, 80, 120, serial=44)),
        ],
    )
    ignition = _candidate(
        0,
        OptionType.ATTACH,
        card_id=IGNITION_ENERGY,
        card={"cardType": 6},
    )
    ignition.features.update(
        {"target_card_id": HONCHKROW, "target_serial": 22, "target_is_active": False}
    )
    end = _candidate(1, OptionType.END)

    phase, reason, choices = agent._main_phase_selections(
        state,
        [Selection((0,), (OptionType.ATTACH,)), Selection((1,), (OptionType.END,))],
        [ignition, end],
    )

    assert phase != DecisionPhase.ATTACK_PRIORITY.value
    assert reason != "ignition_requires_same_turn_attack"
    assert [selection.indices for selection in choices] == [(0,)]


def test_retreat_requires_ready_mega_abomasnow_ko_replacement() -> None:
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{}]),
                bench=[PokemonState(PORYGON2, 90, 90, energies=[{}, {}, {}])],
                discard=[{"id": ARIANA}] * (MEGA_ABOMASNOW_R_COMMAND_SUPPORTERS - 1),
            ),
            PlayerState(active=PokemonState(MEGA_ABOMASNOW_EX, 350, 350)),
        ]
    )
    retreat = _candidate(0, OptionType.RETREAT)
    assert agent._candidate_is_forbidden(state, retreat, SelectContext.MAIN)
    state.players[0].discard.append({"id": ARCHER})
    assert not agent._candidate_is_forbidden(state, retreat, SelectContext.MAIN)
    phase, reason = agent._candidate_phase(state, retreat)
    assert phase is DecisionPhase.ATTACK_PRIORITY
    assert reason == "retreat_enables_mega_abomasnow_ko"


def test_mega_abomasnow_elective_draws_keep_two_natural_draws() -> None:
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(
        supporter_played=True,
        players=[
            PlayerState(deck_count=3, hand_count=7, hand=[{"id": ARIANA}]),
            PlayerState(active=PokemonState(MEGA_ABOMASNOW_EX, 350, 350)),
        ],
    )
    assert not scorer._factory_is_useful(state)
    state.players[0].deck_count = 4
    assert scorer._factory_is_useful(state)


def test_main_phase_ends_instead_of_reintroducing_partial_mega_attack() -> None:
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{}, {}]),
                hand=[{"id": ARIANA}] * 5,
                hand_count=5,
                deck_count=2,
            ),
            PlayerState(active=PokemonState(MEGA_ABOMASNOW_EX, 350, 350)),
        ]
    )
    candidates = [
        _candidate(0, OptionType.ATTACK, attack_id=ROCKET_FEATHERS),
        _candidate(1, OptionType.END),
    ]
    selections = [
        Selection((candidate.option_index,), (candidate.option_type,)) for candidate in candidates
    ]
    phase, reason, eligible = agent._main_phase_selections(state, selections, candidates)
    assert phase == DecisionPhase.END.value
    assert reason == "end"
    assert [selection.indices for selection in eligible] == [(1,)]


def test_expert_loop_keeps_partial_rocket_line_against_non_mega_target() -> None:
    """A legal partial Rocket Feathers attack remains available outside Mega Abomasnow."""
    agent = HonchkrowPorygonAgent(_profile(), "expert_turn_loop")
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{}, {}]),
                hand=[{"id": ARIANA}],
                deck_count=20,
            ),
            PlayerState(active=PokemonState(721, 350, 350)),
        ]
    )
    feathers = _candidate(0, OptionType.ATTACK, attack_id=ROCKET_FEATHERS)

    assert not agent._candidate_is_forbidden(state, feathers, SelectContext.MAIN)


def test_rocket_energy_enabling_murkrow_attack_is_not_forbidden() -> None:
    """Rocket Energy may build an active Murkrow that can attack this turn."""
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        players=[
            PlayerState(active=PokemonState(MURKROW, 80, 80, serial=22)),
            PlayerState(active=PokemonState(999, 80, 80)),
        ]
    )
    rocket = Candidate(
        0,
        {"type": OptionType.ATTACH.value, "enablesAttack": True},
        OptionType.ATTACH,
        card={"cardType": 6},
        features={
            "card_id": ROCKET_ENERGY,
            "target_card_id": MURKROW,
            "target_serial": 22,
            "target_energy_count": 0,
            "target_is_active": True,
        },
    )

    assert not agent._candidate_is_forbidden(state, rocket, SelectContext.MAIN)


def test_articuno_in_hand_does_not_block_development_without_a_legal_play() -> None:
    """Unavailable Articuno cannot freeze the development stage against Dragapult."""
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        players=[
            PlayerState(hand=[{"id": ARTICUNO}]),
            PlayerState(active=PokemonState(119, 70, 70)),
        ]
    )

    assert not agent._articuno_should_precede_development(state, [])


def test_expert_loop_keeps_partial_rocket_line_with_next_ko_horizon() -> None:
    """The generic guard preserves a partial line that leaves a one-turn KO."""
    agent = HonchkrowPorygonAgent(_profile(), "expert_turn_loop")
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(
                    HONCHKROW,
                    130,
                    130,
                    energies=[{"id": ROCKET_ENERGY}, {"id": ROCKET_ENERGY}],
                ),
                hand=[{"id": ARIANA}] * 2,
                deck_count=20,
            ),
            PlayerState(active=PokemonState(721, 150, 150)),
        ]
    )
    feathers = _candidate(0, OptionType.ATTACK, attack_id=ROCKET_FEATHERS)

    assert not agent._candidate_is_forbidden(state, feathers, SelectContext.MAIN)


def test_91192258_holds_ultra_ball_and_factory_without_a_playable_supporter() -> None:
    """The replay state rejects both resource plays when neither converts this turn."""
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130),
                hand=[
                    {"id": FACTORY},
                    {"id": ULTRA_BALL},
                    {"id": NIGHT_STRETCHER},
                    {"id": ARCHER},
                ],
                deck_count=20,
            ),
            PlayerState(active=PokemonState(119, 70, 70)),
        ]
    )
    factory = _candidate(0, OptionType.PLAY, card_id=FACTORY, card={"cardType": 4})
    ultra_ball = _candidate(1, OptionType.PLAY, card_id=ULTRA_BALL, card={"cardType": 1})
    end = _candidate(2, OptionType.END)
    selections = [
        Selection((i,), (OptionType.PLAY if i < 2 else OptionType.END,)) for i in range(3)
    ]

    assert agent._candidate_is_forbidden(state, factory, SelectContext.MAIN)
    assert agent._candidate_is_forbidden(state, ultra_ball, SelectContext.MAIN)
    phase, reason, choices = agent._main_phase_selections(
        state, selections, [factory, ultra_ball, end]
    )
    assert phase == DecisionPhase.END.value
    assert reason == "end"
    assert [selection.indices for selection in choices] == [(2,)]


def test_transceiver_rejects_a_third_ariana_when_two_are_already_in_hand() -> None:
    """Transceiver should remain available for a missing supporter or future setup."""
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        players=[PlayerState(hand=[{"id": ARIANA}, {"id": ARCHER}], deck_count=20), PlayerState()]
    )
    candidate = Candidate(
        0,
        {"type": OptionType.CARD.value, "sourceCardId": TRANSCEIVER},
        OptionType.CARD,
        card={"cardType": 3},
        features={"card_id": ARIANA},
    )
    assert agent._candidate_is_forbidden(state, candidate, SelectContext.TO_HAND)


def test_dragapult_line_prioritizes_articuno_and_holds_evolution() -> None:
    """Public Dreepy evidence establishes the Articuno-before-evolution branch."""
    agent = HonchkrowPorygonAgent(_profile(), "expert_turn_loop")
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(MURKROW, 80, 80),
                hand=[{"id": ARTICUNO}, {"id": HONCHKROW}],
                deck_count=20,
            ),
            PlayerState(active=PokemonState(119, 70, 70)),
        ]
    )
    articuno = _candidate(0, OptionType.PLAY, card_id=ARTICUNO, card={"cardType": 0})
    evolution = _candidate(1, OptionType.EVOLVE, card_id=HONCHKROW, card={"cardType": 0})
    end = _candidate(2, OptionType.END)
    phase, reason, choices = agent._main_phase_selections(
        state,
        [
            Selection((0,), (OptionType.PLAY,)),
            Selection((1,), (OptionType.EVOLVE,)),
            Selection((2,), (OptionType.END,)),
        ],
        [articuno, evolution, end],
    )
    assert phase == DecisionPhase.PLAY_POKEMON.value
    assert reason == "canonical_articuno_before_evolution"
    assert [selection.indices for selection in choices] == [(0,)]
    assert agent._candidate_is_forbidden(state, evolution, SelectContext.MAIN)


def test_dragapult_line_keeps_articuno_on_the_bench() -> None:
    """Articuno is a protection resource, not a preferred promoted attacker."""
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(MURKROW, 80, 80),
                bench=[PokemonState(ARTICUNO, 100, 100)],
            ),
            PlayerState(active=PokemonState(119, 70, 70)),
        ]
    )
    promote = Candidate(
        0,
        {"type": OptionType.CARD.value},
        OptionType.CARD,
        features={"card_id": ARTICUNO},
    )
    assert agent._candidate_is_forbidden(state, promote, SelectContext.TO_ACTIVE)


def test_proton_selection_is_forced_to_articuno_against_dragapult() -> None:
    """When Proton reveals the tech, the defensive target outranks generic setup."""
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        players=[
            PlayerState(active=PokemonState(MURKROW, 80, 80)),
            PlayerState(active=PokemonState(119, 70, 70)),
        ]
    )
    candidates = [
        Candidate(
            0,
            {"type": OptionType.CARD.value, "sourceCardId": PROTON},
            OptionType.CARD,
            features={"card_id": MURKROW},
        ),
        Candidate(
            1,
            {"type": OptionType.CARD.value, "sourceCardId": PROTON},
            OptionType.CARD,
            features={"card_id": ARTICUNO},
        ),
    ]
    filtered = agent._filter_forbidden_selections(
        state,
        [Selection((0,), (OptionType.CARD,)), Selection((1,), (OptionType.CARD,))],
        candidates,
        SelectContext.TO_HAND,
    )
    assert [selection.indices for selection in filtered] == [(1,)]


def test_headset_recovers_ariana_after_unfair_stamp_reduces_hand() -> None:
    """Ariana recovery is allowed when Headset is the only productive recovery line."""
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130),
                hand=[{"id": PETREL}, {"id": ARCHER}],
                hand_count=2,
                discard=[{"id": ARIANA}],
                deck_count=20,
            ),
            PlayerState(active=PokemonState(112, 110, 110)),
        ]
    )
    assert scorer._miracle_headset_emergency_is_useful(state)


def test_munkidori_is_lethal_with_one_rocket_feathers_supporter() -> None:
    """Munkidori's 110 HP is covered by one 60-damage supporter attack at weakness."""
    scorer = HonchkrowPorygonScorer(deck_profile=_profile())
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{}, {}]),
                hand=[{"id": ARIANA}],
            ),
            PlayerState(active=PokemonState(112, 110, 110)),
        ]
    )
    attack = _candidate(0, OptionType.ATTACK, attack_id=ROCKET_FEATHERS)
    assert scorer._attack_damage(state, attack, 60) == 120
    assert scorer._supporters_needed_for_ko(state) == 1


def test_replay_facts_for_91193154_preserve_the_proton_articuno_nuance() -> None:
    """The replay records Proton selecting Articuno while Dreepy was publicly visible."""
    replay = json.loads((ROOT / "data/raw/kaggle/kaggle_gameplay_runs/91193154.json").read_text())
    frame = replay["steps"][10][1]
    assert frame["action"] == [3]
    assert any(log.get("cardId") == PROTON for log in frame["observation"]["logs"])
    assert any(
        log.get("cardId") == ARTICUNO
        for step in replay["steps"]
        for player_frame in step
        for log in player_frame.get("observation", {}).get("logs", [])
        if isinstance(log, dict)
    )
    assert any(
        log.get("cardId") == 119
        for step in replay["steps"]
        for player_frame in step
        for log in player_frame.get("observation", {}).get("logs", [])
        if isinstance(log, dict)
    )


def test_rocket_feathers_discards_exactly_six_for_mega_abomasnow_ko() -> None:
    agent = HonchkrowPorygonAgent(_profile())
    state = GameState(
        players=[
            PlayerState(hand=[{"id": ARIANA}] * 6),
            PlayerState(active=PokemonState(MEGA_ABOMASNOW_EX, 350, 350)),
        ]
    )
    candidates = [
        _candidate(index, OptionType.CARD, card_id=ARIANA, card={"cardType": 3})
        for index in range(6)
    ]
    selections = [
        Selection(tuple(range(5)), (OptionType.CARD,) * 5),
        Selection(tuple(range(6)), (OptionType.CARD,) * 6),
    ]
    filtered = agent._filter_forbidden_selections(
        state, selections, candidates, SelectContext.DISCARD
    )
    assert [selection.indices for selection in filtered] == [tuple(range(6))]
    assert agent.turn_ledger.resource_guard == "discard_six_for_mega_abomasnow_ko"


assert HonchkrowPorygonAgent
