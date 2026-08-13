from __future__ import annotations

from scripts.audit_turn_planning import audit_ledger_records


def test_audit_ledger_records_accepts_flat_decision_ledger_events() -> None:
    """Recognize decoded remote logs whose ledger is stored at the record root."""
    report = audit_ledger_records(
        [
            {
                "event": "audit_decision_ledger",
                "turn_ledger": {
                    "roto_sticks_played": 3,
                    "roto_supporters_revealed": 0,
                    "roto_supporters_selected": 0,
                },
            }
        ]
    )

    assert report["records"] == 1
    assert report["counters"]["roto_zero_over_zero_consistent"]
