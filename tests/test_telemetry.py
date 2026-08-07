from __future__ import annotations

from types import SimpleNamespace

from src.eval.telemetry import (
    aggregate_decisions,
    classify_terminal,
    failure_flags,
    public_snapshot,
    transition,
)


def _current(*, own_hp: int = 350, target_hp: int = 350, own_deck: int = 20) -> dict:
    return {
        "turn": 4,
        "yourIndex": 0,
        "players": [
            {
                "active": [{"id": 891, "hp": own_hp, "maxHp": 150, "energies": [15, 15]}],
                "bench": [{"id": 463, "hp": 70, "maxHp": 70, "energies": []}],
                "deckCount": own_deck,
                "prize": [None] * 6,
                "handCount": 5,
                "hand": [{"id": 1216}, {"id": 3}],
                "discard": [{"id": 1217}],
            },
            {
                "active": [{"id": 723, "hp": target_hp, "maxHp": 350, "energies": []}],
                "bench": [],
                "deckCount": 30,
                "prize": [None] * 3,
                "handCount": 4,
                "hand": None,
                "discard": [],
            },
        ],
    }


def test_public_snapshot_exposes_counts_without_hidden_hand_identity() -> None:
    snapshot = public_snapshot({"current": _current()})

    assert snapshot["own"]["deck_count"] == 20
    assert snapshot["own"]["hand_count"] == 5
    assert snapshot["own"]["hand_supporters"] == 1
    assert snapshot["own"]["discard_supporters"] == 1
    assert snapshot["opponent"]["active"]["card_id"] == 723
    assert snapshot["opponent"]["pokemon_in_play"] == 1


def test_transition_detects_damage_ko_prize_and_resource_changes() -> None:
    before = public_snapshot({"current": _current(target_hp=350, own_deck=20)})
    after = public_snapshot({"current": _current(target_hp=0, own_deck=18)})
    after["opponent"]["active"] = None
    after["opponent"]["prize_count"] = 0

    effects = transition(before, after)

    assert effects["target_damage"] == 350
    assert effects["target_ko"] is True
    assert effects["opponent_prize_delta"] == -3
    assert effects["own_deck_delta"] == -2


def test_terminal_classification_uses_loser_public_counts() -> None:
    snapshot = public_snapshot({"current": _current(own_deck=0)})

    reason, explicit = classify_terminal(snapshot, "loss", 0)

    assert reason == "DECK_OUT"
    assert explicit is False


def test_failure_flags_detect_critical_end_and_no_observed_damage() -> None:
    before = public_snapshot({"current": _current(target_hp=350, own_deck=2)})
    flags = failure_flags(
        selected_indices=[1],
        options=[{"type": 13, "attackId": 1285}, {"type": 14}],
        before=before,
        effects={"target_damage": 0},
    )

    assert "END_WITH_CRITICAL_DECK" in flags
    attack_flags = failure_flags(
        selected_indices=[0],
        options=[{"type": 13, "attackId": 1285}, {"type": 14}],
        before=before,
        effects={"target_damage": 0},
    )
    assert "ATTACK_WITHOUT_OBSERVED_DAMAGE" in attack_flags


def test_aggregate_decisions_reports_turn_planning_tactical_counters() -> None:
    decision = SimpleNamespace(
        failure_flags=[],
        selected_indices=[0],
        options=[{"type": 11, "cardId": 1216}],
        transition={},
        turn=3,
        tactical={
            "turn_ledger": {
                "ariana_marginal_draw": 1,
                "ariana_supporters_in_hand": 8,
                "ariana_with_required_proton": 1,
                "no_pokemon_risk": True,
            },
            "match_ledger": {
                "petrel_factory_opportunities": 1,
                "petrel_factory_conversions": 1,
                "poke_pad_ko_opportunities": 2,
                "poke_pad_ko_conversions": 1,
                "poke_pad_ko_misses": 1,
                "late_proton_without_gain": 0,
                "torment_with_superior_line": 0,
            },
        },
    )

    aggregate = aggregate_decisions([SimpleNamespace(decisions=[decision])])

    assert aggregate["tactical_counters"]["ariana_draw_at_most_one"] == 1
    assert aggregate["tactical_counters"]["ariana_with_required_proton"] == 1
    assert aggregate["tactical_counters"]["petrel_factory_conversions"] == 1
    assert aggregate["tactical_counters"]["poke_pad_ko_misses"] == 1
    assert aggregate["ariana_events"] == [{"turn": 3, "marginal_draw": 1, "supporters_in_hand": 8}]
