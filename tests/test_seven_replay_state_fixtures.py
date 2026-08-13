"""State-based regression fixtures for the seven reviewed replay divergences."""

from __future__ import annotations

import json
from pathlib import Path

from src.agents.honchkrow_porygon import (
    ARCHER,
    ARIANA,
    GIOVANNI,
    HONCHKROW,
    MIRACLE_HEADSET,
    NIGHT_STRETCHER,
    PORYGON,
    PORYGON2,
    PROTON,
    ROTO_STICK,
    TOOL_SCRAPPER,
    HonchkrowPorygonAgent,
)
from src.core import (
    Candidate,
    DeckProfile,
    GameState,
    OptionType,
    PlayerState,
    PokemonState,
    Selection,
)

ROOT = Path(__file__).parents[1]


def _profile() -> DeckProfile:
    """Load the production deck profile used by every fixture."""
    return DeckProfile.from_dict(
        json.loads(
            (ROOT / "src/artifacts/deck_profile_honchkrow_porygon.json").read_text(encoding="utf-8")
        )
    )


def _agent() -> HonchkrowPorygonAgent:
    """Build the executable policy variant under audit."""
    return HonchkrowPorygonAgent(_profile(), "expert_turn_loop")


def _play(index: int, card_id: int) -> Candidate:
    """Build a minimal legal play candidate for a state fixture."""
    return Candidate(
        index,
        {"type": OptionType.PLAY.value, "cardId": card_id},
        OptionType.PLAY,
        card={"cardType": 3},
        features={"card_id": card_id},
    )


def test_replay_fixture_roto_with_proton_in_hand_rejects_setup_only() -> None:
    """Proton in hand blocks setup Roto when no attack or survival line exists."""
    agent = _agent()
    state = GameState(
        turn=1,
        players=[
            PlayerState(
                active=PokemonState(463, 70, 70),
                hand=[{"id": PROTON}, {"id": ROTO_STICK}],
                deck_count=20,
            ),
            PlayerState(active=PokemonState(999, 100, 100)),
        ],
    )

    assert not agent._canonical_roto_is_productive(state)
    assert agent.turn_ledger.roto_mode == ""


def test_replay_fixture_roto_supporter_deficit_remains_attack_mode() -> None:
    """A ready Honchkrow may use Roto to fill a Rocket Feathers deficit."""
    agent = _agent()
    state = GameState(
        turn=3,
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130, energies=[{}, {}]),
                hand=[{"id": PROTON}, {"id": ROTO_STICK}],
                deck_count=20,
            ),
            PlayerState(active=PokemonState(999, 100, 100)),
        ],
    )

    assert agent._canonical_roto_is_productive(state)
    assert agent.turn_ledger.roto_mode == "attack_mode"


def test_replay_fixture_roto_survival_overrides_proton_setup_veto() -> None:
    """Roto remains available when the only visible Pokémon needs immediate help."""
    agent = _agent()
    state = GameState(
        turn=3,
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 20, 130),
                hand=[{"id": PROTON}, {"id": ROTO_STICK}],
                deck_count=20,
            ),
            PlayerState(active=PokemonState(999, 100, 100)),
        ],
    )

    assert agent._canonical_roto_is_productive(state)
    assert agent.turn_ledger.roto_mode == "survival_mode"


def test_replay_fixture_headset_defers_first_turn_ariana_draw() -> None:
    """A first-turn Ariana recovery waits when a normal next-turn draw is safe."""
    agent = _agent()
    state = GameState(
        turn=1,
        players=[
            PlayerState(
                active=PokemonState(HONCHKROW, 130, 130),
                bench=[PokemonState(PORYGON, 90, 90)],
                hand=[{"id": MIRACLE_HEADSET}],
                discard=[{"id": ARIANA}, {"id": PROTON}],
                hand_count=1,
                deck_count=20,
            ),
            PlayerState(active=PokemonState(999, 100, 100)),
        ],
    )

    assert not agent._headset_ariana_recovery_is_useful(state)
    assert agent.turn_ledger.headset_deferred_until_next_turn


def test_replay_fixture_petrel_recovers_porygon_line_before_draw() -> None:
    """Petrel's recovery target is the Porygon evolution line when it converts now."""
    agent = _agent()
    state = GameState(
        players=[
            PlayerState(
                active=PokemonState(PORYGON, 90, 90, energies=[{}, {}, {}]),
                discard=[{"id": PORYGON2}, {"id": NIGHT_STRETCHER}, {"id": ARCHER}],
                hand=[{"id": 1219}],
                hand_count=1,
                deck_count=20,
            ),
            PlayerState(active=PokemonState(999, 100, 100)),
        ]
    )
    candidate = Candidate(
        0,
        {"type": OptionType.CARD.value, "sourceCardId": 1219},
        OptionType.CARD,
        card={"cardType": 1},
        features={"card_id": NIGHT_STRETCHER},
    )

    assert agent._petrel_target_is_useful(state, candidate)


def test_replay_fixture_tool_scrapper_yields_to_terminal_ko() -> None:
    """A visible Tool is useful, but never ahead of a proven terminal attack."""
    agent = _agent()
    state = GameState(
        players=[
            PlayerState(active=PokemonState(HONCHKROW, 130, 130, energies=[{}, {}]), prize=[None]),
            PlayerState(active=PokemonState(999, 10, 100, tool_ids=["1159"])),
        ]
    )
    scrapper = _play(0, TOOL_SCRAPPER)
    attack = Candidate(1, {"type": OptionType.ATTACK.value, "win": True}, OptionType.ATTACK)
    choices = [Selection((0,), (OptionType.PLAY,)), Selection((1,), (OptionType.ATTACK,))]

    _, reason, selected = agent._canonical_main_phase_selections(state, choices, [scrapper, attack])

    assert reason == "canonical_immediate_win"
    assert selected == [choices[1]]


def test_replay_fixture_giovanni_without_conversion_is_rejected() -> None:
    """Giovanni is not a resource objective without a public KO or pivot."""
    agent = _agent()
    state = GameState(
        players=[
            PlayerState(hand=[{"id": GIOVANNI}], hand_count=1),
            PlayerState(active=PokemonState(999, 180, 180)),
        ]
    )
    candidate = _play(0, GIOVANNI)

    assert agent._candidate_is_forbidden(state, candidate, None)
