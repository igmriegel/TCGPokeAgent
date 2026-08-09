"""Acceptance tests for grouped Honchkrow/Porygon opportunity audits."""

from __future__ import annotations

from src.agents.honchkrow_porygon import HonchkrowPorygonAgent
from src.data.honchkrow_audit import (
    OpportunityCategory,
    audit_opportunities,
)


def _decision(
    index: int,
    options: list[dict[str, object]],
    selected: list[int],
    transition: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build a small serialized decision trace for the grouping tests."""
    return {
        "decision_index": index,
        "context": "DISCARD" if index == 0 else "MAIN",
        "options": options,
        "selected_indices": selected,
        "telemetry_before": {
            "own": {
                "active": {"card_id": 891, "energy_count": 2},
                "hand_supporters": 6,
                "discard_supporters": 0,
                "deck_count": 20,
            },
            "opponent": {"active": {"card_id": 723, "hp": 350}},
        },
        "transition": transition or {},
        "reasons": ["test_trace"],
    }


def test_discard_preparation_and_attack_are_one_opportunity() -> None:
    """A discard prompt must not be counted as a second attack opportunity."""
    records = [
        _decision(
            0,
            [{"type": "DISCARD", "cardId": 1216}, {"type": "DISCARD", "cardId": 1217}],
            [0],
        ),
        _decision(
            1,
            [{"type": "ATTACK", "attackId": 1285}],
            [0],
            {"target_damage": 350, "target_ko": True},
        ),
    ]

    audits = audit_opportunities([{"events": records}])

    assert len(audits) == 1
    assert audits[0].line_chosen == "1285"
    assert audits[0].category == OpportunityCategory.UNRESOLVED_SEQUENCE
    assert audits[0].decision_indices == (0, 1)


def test_r_command_requires_eighteen_discarded_supporters() -> None:
    """R Command with fewer than eighteen Supporters is marked not ready."""
    record = _decision(
        0,
        [{"type": "ATTACK", "attackId": 670}],
        [0],
        {"target_damage": 340, "target_ko": False},
    )
    record["telemetry_before"]["own"]["discard_supporters"] = 17  # type: ignore[index]

    audits = audit_opportunities([{"events": [record]}])

    assert audits[0].category == OpportunityCategory.R_COMMAND_NOT_READY


def test_rocket_feathers_uses_target_hp_for_lethal_threshold() -> None:
    """Two Supporters are lethal against a 90 HP target, not underfunded."""
    record = _decision(
        0,
        [{"type": "ATTACK", "attackId": 1285}],
        [0],
        {"target_damage": 90, "target_ko": True},
    )
    record["telemetry_before"]["own"]["hand_supporters"] = 2  # type: ignore[index]
    record["telemetry_before"]["opponent"]["active"] = {"card_id": 722, "hp": 90}  # type: ignore[index]

    audits = audit_opportunities([{"events": [record]}])

    assert audits[0].lethal_line_available
    assert audits[0].category == OpportunityCategory.UNRESOLVED_SEQUENCE


def test_rocket_feathers_remains_underfunded_against_350_hp() -> None:
    """Six Supporters remain necessary for a 350 HP Rocket Feathers KO."""
    record = _decision(
        0,
        [{"type": "ATTACK", "attackId": 1285}],
        [0],
        {"target_damage": 300, "target_ko": False},
    )
    record["telemetry_before"]["own"]["hand_supporters"] = 5  # type: ignore[index]

    audits = audit_opportunities([{"events": [record]}])

    assert not audits[0].lethal_line_available
    assert audits[0].category == OpportunityCategory.PARTIAL_LINE_UNDERFUNDED


def test_end_with_lethal_attack_is_explicitly_classified() -> None:
    """An END chosen beside a lethal attack remains a single audited group."""
    record = _decision(
        0,
        [{"type": "ATTACK", "attackId": 1285}, {"type": "END"}],
        [1],
    )

    audits = audit_opportunities([{"events": [record]}])

    assert audits[0].category == OpportunityCategory.END_WITH_LETHAL_LINE


def test_promoted_baseline_and_legacy_policy_are_named() -> None:
    """The promoted guard is the default while the prior policy remains selectable."""
    import json
    from pathlib import Path

    from src.core import DeckProfile

    profile = DeckProfile.from_dict(
        json.loads(
            (
                Path(__file__).parents[1] / "src/artifacts/deck_profile_honchkrow_porygon.json"
            ).read_text()
        )
    )
    baseline = HonchkrowPorygonAgent(profile)
    legacy = HonchkrowPorygonAgent(profile, "legacy_baseline")
    assert baseline.policy_variant == "supporter_resource_v2"
    assert baseline._uses_retreat_guard
    assert legacy.policy_variant == "legacy_baseline"
    assert not legacy._uses_retreat_guard
    assert HonchkrowPorygonAgent(profile, "ko_priority_v1").policy_variant == "ko_priority_v1"
    assert (
        HonchkrowPorygonAgent(profile, "ko_priority_v2_strict").policy_variant
        == "ko_priority_v2_strict"
    )
    assert (
        HonchkrowPorygonAgent(profile, "ko_priority_v3_retreat_guard").policy_variant
        == "ko_priority_v3_retreat_guard"
    )
    assert (
        HonchkrowPorygonAgent(profile, "supporter_resource_v2_replay_fix_v1").policy_variant
        == "supporter_resource_v2_replay_fix_v1"
    )
    expert_fix = HonchkrowPorygonAgent(profile, "expert_rounds_1_3_replay_fix_v1")
    assert expert_fix._uses_expert_rounds_1_3
    expert_turn_loop = HonchkrowPorygonAgent(profile, "expert_turn_loop")
    assert expert_turn_loop.policy_variant == "expert_turn_loop"
    assert expert_turn_loop._uses_expert_turn_loop
    assert expert_turn_loop._uses_expert_rounds_1_3


def test_unselected_rocket_attack_is_not_an_executed_opportunity() -> None:
    """A legal but unselected attack must not start a sequence audit."""
    record = _decision(
        0,
        [{"type": "ATTACK", "attackId": 1285}, {"type": "END"}],
        [1],
    )
    assert audit_opportunities([{"events": [record]}])

    plain = _decision(0, [{"type": "ATTACK", "attackId": 1285}], [], {})
    assert audit_opportunities([{"events": [plain]}]) == []
