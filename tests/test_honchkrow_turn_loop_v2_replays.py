"""Tests for the HLV2 replay reproduction summary."""

from __future__ import annotations

import json

from scripts.summarize_honchkrow_turn_loop_v2_replays import summarize


def test_replay_summary_keeps_divergence_counterfactual_local(tmp_path) -> None:
    """Divergences retain legality evidence but never claim alternate outcomes."""
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    baseline.write_text(
        json.dumps(
            {
                "variant": "supporter_resource_v2",
                "summary": {"decisions": 1, "divergences": 0},
                "decisions": [],
            }
        )
    )
    candidate.write_text(
        json.dumps(
            {
                "variant": "expert_turn_loop",
                "summary": {"decisions": 1, "divergences": 1},
                "decisions": [
                    {
                        "episode_id": 1,
                        "step": 2,
                        "turn": 3,
                        "executed_action": [0],
                        "generated_action": [1],
                        "decision_phase": "PLAY_ITEMS",
                        "reasons": ["roto_opening_setup_or_survival"],
                        "legal_selection": True,
                        "result_matches_submission": False,
                        "tactical": {"turn_ledger": {"stage": "play_items"}},
                    }
                ],
            }
        )
    )

    result = summarize(baseline, candidate, tmp_path / "output")
    divergence = json.loads(
        (tmp_path / "output/decision_divergences.jsonl").read_text(encoding="utf-8")
    )

    assert result["formal_gate_status"] == "PRE_GATE_EVIDENCE"
    assert divergence["legal_selection"] is True
    assert divergence["counterfactual_scope"] == "single_decision_only"
    assert divergence["outcome_inference_prohibited"] is True
    assert "game_result" not in divergence
