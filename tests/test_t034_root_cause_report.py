"""Tests for the conservative T-034 replay evidence report."""

from __future__ import annotations

import json

from scripts.build_t034_root_cause_report import build_report


def test_report_preserves_missing_trace_as_unresolved(tmp_path) -> None:
    """A historical action without a candidate trace cannot prove a root cause."""
    audit_dir = tmp_path
    (audit_dir / "audit.json").write_text(
        json.dumps(
            {
                "submission": {"submission_id": 55333874, "archive_sha256": "archive"},
                "reproduction": {"decisions": 1, "matches": 1},
            }
        ),
        encoding="utf-8",
    )
    (audit_dir / "review_queue.json").write_text(
        json.dumps(
            [
                {
                    "episode_id": 1,
                    "step": 2,
                    "candidate_divergences": [
                        {"action": [3], "reasons": ["roto_opening_setup_or_survival"]}
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )
    (audit_dir / "replay_hashes.json").write_text(
        json.dumps({"replay_sha256": {"episode-1-replay.json": "hash"}}),
        encoding="utf-8",
    )
    (audit_dir / "decision_ledger.jsonl").write_text(
        json.dumps(
            {
                "episode_id": 1,
                "step": 2,
                "turn": 3,
                "executed_action": [1],
                "decision_trace": None,
                "legal_selection": True,
                "fallback_used": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_report(audit_dir)

    assert report["status"] == "OPEN"
    assert report["evidence_boundary"]["strategic_root_cause"] == "unknown"
    assert report["representative_findings"][0]["first_causal_divergence"] == (
        "unidentifiable_missing_submitted_candidate_trace"
    )
    assert not report["evidence_boundary"]["raw_replay_corpus_available"]
