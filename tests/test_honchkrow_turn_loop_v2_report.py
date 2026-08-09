"""Tests for the HLV2 report bundle."""

from __future__ import annotations

import json

from scripts.build_honchkrow_turn_loop_v2_report import build_bundle


def _report(variant: str, wins: int, losses: int) -> dict[str, object]:
    """Return a minimal independent CABT report."""
    matches = [
        {
            "agent_side": index % 2,
            "result": "win" if index < wins else "loss",
            "status": "ok",
            "termination_reason": "all_prizes_taken" if index < wins else "deck_out",
        }
        for index in range(wins + losses)
    ]
    return {
        "policy_variant": variant,
        "matches": matches,
        "audit": {"deck_out_losses": losses},
        "telemetry_totals": {},
    }


def test_bundle_is_hold_before_independent_final_gate(tmp_path) -> None:
    """Small reports produce every artifact without claiming promotion."""
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    baseline.write_text(json.dumps(_report("supporter_resource_v2", 7, 3)))
    candidate.write_text(json.dumps(_report("expert_turn_loop", 8, 2)))
    output = tmp_path / "run"

    comparison = build_bundle(baseline, candidate, output, "baseline command", "candidate command")

    assert comparison["decision"] == "HOLD"
    assert not comparison["gates"]["sample_1000_each"]
    expected = {
        "manifest.json",
        "baseline_report.json",
        "candidate_report.json",
        "comparison.json",
        "comparison.md",
        "comparison.html",
        "decision_divergences.jsonl",
        "terminal_cause_matrix.json",
        "matchup_matrix.json",
        "review_queue.json",
        "replay_hashes.json",
    }
    assert {path.name for path in output.iterdir()} == expected
