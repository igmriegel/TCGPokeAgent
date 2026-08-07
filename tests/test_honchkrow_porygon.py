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
    GIOVANNI,
    HACKING,
    HONCHKROW,
    IGNITION_ENERGY,
    MEGA_ABOMASNOW_EX,
    MEGA_ABOMASNOW_R_COMMAND_SUPPORTERS,
    MEGA_ABOMASNOW_ROCKET_FEATHERS_SUPPORTERS,
    MIRACLE_HEADSET,
    MURKROW,
    NIGHT_STRETCHER,
    POKE_PAD,
    PORYGON,
    PORYGON2,
    PROTON,
    R_COMMAND,
    ROCKET_ENERGY,
    ROCKET_FEATHERS,
    ROTO_STICK,
    TORMENT,
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
                active=PokemonState(HONCHKROW, 130, 130, energies=[{}, {}]),
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


def test_draw_first_prefers_ariana_before_factory_or_nonwinning_attack() -> None:
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
    assert reason == "ariana_before_factory"
    assert [selection.indices for selection in eligible] == [(0,)]


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
    assert scorer._factory_is_useful(state)
    state.players[0].deck_count = 1
    assert not scorer._factory_is_useful(state)


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
