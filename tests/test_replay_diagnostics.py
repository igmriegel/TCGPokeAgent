from __future__ import annotations

import json

from src.data.replay_deep_analysis import (
    DeepReplayAnalysis,
    FrameData,
    GameEvent,
    PlayerFrameState,
    PokemonState,
)
from src.data.replay_diagnostics import aggregate_replay_diagnostics, diagnose_replay


def _pokemon(card_id: int, hp: int) -> PokemonState:
    return PokemonState(
        name=str(card_id),
        card_id=card_id,
        hp=hp,
        max_hp=350,
        energies=(),
        tools=(),
        is_active=True,
    )


def _frame(owner_hp: int, target_hp: int, owner_deck: int, target_prizes: int) -> FrameData:
    owner = PlayerFrameState(
        active=[_pokemon(891, owner_hp)],
        bench=[],
        prize_count=6,
        deck_count=owner_deck,
        hand_count=4,
        energy_attached=False,
        supporter_played=False,
    )
    opponent = PlayerFrameState(
        active=[_pokemon(723, target_hp)] if target_hp else [],
        bench=[],
        prize_count=target_prizes,
        deck_count=30,
        hand_count=4,
        energy_attached=False,
        supporter_played=False,
    )
    return FrameData(
        turn=1,
        frame_index=0,
        owner_state=owner,
        opponent_state=opponent,
        first_player=0,
        events=[],
    )


def test_replay_diagnostic_detects_damage_without_ko() -> None:
    analysis = DeepReplayAnalysis(
        episode_id=1,
        source_path="fixture.json",
        owner_name="owner",
        opponent_name="opponent",
        owner_index=0,
        winner_index=1,
        owner_outcome="loss",
        total_turns=2,
        first_player=0,
        frames=[_frame(150, 350, 20, 6), _frame(80, 250, 18, 6)],
        events=[
            GameEvent(event_type="Attack", player_index=0),
            GameEvent(event_type="HpChange", player_index=1, value=-100),
        ],
        owner_archetype="owner",
        opponent_archetype="opponent",
    )

    diagnostic = diagnose_replay(analysis)

    assert diagnostic.opponent_damage_observed == 100
    assert diagnostic.owner_attack_count == 1
    assert diagnostic.opponent_attack_count == 0
    assert diagnostic.opponent_ko_count == 0
    assert diagnostic.loss_category == "DAMAGE_NOT_CONVERTED"


def test_replay_diagnostic_aggregates_loss_categories() -> None:
    analysis = DeepReplayAnalysis(
        episode_id=2,
        source_path="fixture.json",
        owner_name="owner",
        opponent_name="opponent",
        owner_index=0,
        winner_index=0,
        owner_outcome="win",
        total_turns=1,
        first_player=0,
        frames=[_frame(150, 350, 20, 6)],
        events=[],
        owner_archetype="owner",
        opponent_archetype="opponent",
    )

    report = aggregate_replay_diagnostics([diagnose_replay(analysis)])

    assert report["replays"] == 1
    assert report["wins"] == 1
    assert report["losses"] == 0


def test_empty_deck_is_distinct_from_effective_deck_out(tmp_path) -> None:
    replay = {
        "name": "cabt",
        "info": {
            "EpisodeId": 3,
            "Agents": [{"Name": "owner"}, {"Name": "opponent"}],
        },
        "steps": [
            [
                {
                    "visualize": [
                        {
                            "current": {
                                "result": 1,
                                "turn": 2,
                                "players": [
                                    {"active": [], "bench": [], "deckCount": 0, "prize": [None]},
                                    {
                                        "active": [{"id": 2}],
                                        "bench": [],
                                        "deckCount": 10,
                                        "prize": [None],
                                    },
                                ],
                            },
                            "logs": [{"type": "Result", "result": 1, "reason": 3}],
                        }
                    ]
                },
                {},
            ]
        ],
    }
    replay_path = tmp_path / "replay.json"
    replay_path.write_text(json.dumps(replay), encoding="utf-8")
    analysis = DeepReplayAnalysis(
        episode_id=3,
        source_path=str(replay_path),
        owner_name="owner",
        opponent_name="opponent",
        owner_index=0,
        winner_index=1,
        owner_outcome="loss",
        total_turns=2,
        first_player=0,
        frames=[_frame(0, 100, 0, 6)],
        events=[],
        owner_archetype="owner",
        opponent_archetype="opponent",
    )

    diagnostic = diagnose_replay(analysis)

    assert diagnostic.owner_deck_reached_zero
    assert not diagnostic.owner_lost_by_deck_out
    assert diagnostic.termination_reason == "no_pokemon_in_play"
    assert diagnostic.loss_category == "BOARD_COLLAPSE"
