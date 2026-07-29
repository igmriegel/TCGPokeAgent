from __future__ import annotations

import json

import pytest

from src.data.gameplay_annotations import (
    GameplayAnnotationStore,
    annotation_from_replay,
    inspect_replay,
)


def _replay() -> dict:
    current = {
        "turn": 11,
        "players": [
            {
                "active": [{"id": 723, "serial": 11, "hp": 120}],
                "bench": [],
                "hand": [{"id": 65, "serial": 3}],
                "deckCount": 40,
                "prizeCount": 4,
            },
            {
                "active": [{"id": 65, "serial": 61, "hp": 100}],
                "bench": [],
                "hand": [{"id": 999, "serial": 99}],
                "deckCount": 42,
                "prizeCount": 5,
            },
        ],
    }
    select = {
        "type": 0,
        "context": 0,
        "minCount": 1,
        "maxCount": 1,
        "remainDamageCounter": 0,
        "remainEnergyCost": 0,
        "option": [
            {"index": 0, "type": 7},
            {"attackId": 1046, "type": 13},
        ],
    }
    return {
        "name": "cabt",
        "info": {"EpisodeId": 123},
        "rewards": [-1, 1],
        "steps": [
            [
                {
                    "status": "ACTIVE",
                    "action": [],
                    "observation": {
                        "step": 0,
                        "current": current,
                        "logs": [],
                        "select": select,
                    },
                },
                {"status": "ACTIVE", "action": [], "observation": {}},
            ],
            [
                {"status": "DONE", "action": [1], "observation": {}},
                {"status": "DONE", "action": [], "observation": {}},
            ],
        ],
    }


def test_annotation_links_verified_agent_decision_without_hidden_opponent_hand(tmp_path) -> None:
    replay_path = tmp_path / "123.json"
    replay_path.write_text(json.dumps(_replay()), encoding="utf-8")

    annotation = annotation_from_replay(
        replay_path,
        annotation_id="REV-123-001",
        player_index=0,
        preferred_by_step={0: [0]},
        verdict="mistake",
        cause_code="board_collapse",
        reason_tags=["EMPTY_BENCH", "SECOND_ATTACKER"],
        raw_feedback="The engine should have played the available Pokémon.",
        technical_interpretation="A terminal attack was selected without a replacement attacker.",
        confidence=0.9,
        intended_follow_up="Attack after placing the Pokémon on the Bench.",
        created_at="2026-07-29T00:00:00+00:00",
    )

    assert annotation.actor_type == "agent"
    assert annotation.review_kind == "post_hoc_human_review"
    assert annotation.match_outcome == "loss"
    assert annotation.decisions[0].selected_indices == (1,)
    assert annotation.decisions[0].preferred_indices == (0,)
    assert annotation.intended_follow_up.startswith("Attack after")
    assert "hand" not in annotation.decisions[0].visible_state["opponent_public"]

    store = GameplayAnnotationStore(tmp_path / "annotations.jsonl")
    store.append(annotation)
    assert store.read() == [annotation]
    with pytest.raises(ValueError, match="already exists"):
        store.append(annotation)


def test_store_requires_existing_annotation_before_correction(tmp_path) -> None:
    replay_path = tmp_path / "123.json"
    replay_path.write_text(json.dumps(_replay()), encoding="utf-8")
    correction = annotation_from_replay(
        replay_path,
        annotation_id="REV-123-002",
        player_index=0,
        preferred_by_step={0: [0]},
        verdict="mistake",
        cause_code="sequencing",
        reason_tags=["DEVELOP_BEFORE_ATTACK"],
        raw_feedback="Develop the Bench, then attack.",
        technical_interpretation="The attack is correct after board development.",
        confidence=1.0,
        intended_follow_up="Attack on the next MAIN prompt.",
        supersedes="REV-123-001",
    )

    with pytest.raises(ValueError, match="superseded annotation does not exist"):
        GameplayAnnotationStore(tmp_path / "annotations.jsonl").append(correction)


def test_annotation_rejects_illegal_preferred_selection(tmp_path) -> None:
    replay_path = tmp_path / "123.json"
    replay_path.write_text(json.dumps(_replay()), encoding="utf-8")

    with pytest.raises(ValueError, match="illegal index"):
        annotation_from_replay(
            replay_path,
            annotation_id="REV-123-002",
            player_index=0,
            preferred_by_step={0: [4]},
            verdict="mistake",
            cause_code="board_collapse",
            reason_tags=["EMPTY_BENCH"],
            raw_feedback="Play the available Pokémon.",
            technical_interpretation="",
            confidence=0.8,
        )


def test_inspect_filters_card_and_empty_bench(tmp_path) -> None:
    replay_path = tmp_path / "123.json"
    replay_path.write_text(json.dumps(_replay()), encoding="utf-8")

    records = inspect_replay(replay_path, player_index=0, card_id=65, empty_bench=True)

    assert len(records) == 1
    assert records[0]["selected_indices"] == [1]
    assert records[0]["legal_options"][0]["card_id"] == 65
