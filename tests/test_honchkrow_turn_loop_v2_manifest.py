"""Tests for the expert turn-loop foundation manifest."""

from __future__ import annotations

import json

from scripts.create_honchkrow_turn_loop_v2_manifest import build_manifest, write_manifest


def test_manifest_freezes_baseline_candidate_and_public_corpus(tmp_path) -> None:
    """The foundation manifest names both policies and all 26 replay hashes."""
    output = write_manifest(tmp_path / "manifest.json")
    manifest = json.loads(output.read_text(encoding="utf-8"))

    assert manifest == build_manifest()
    assert manifest["baseline_variant"] == "supporter_resource_v2"
    assert manifest["candidate_variant"] == "expert_turn_loop_v2"
    assert manifest["immutable_inputs"]["deck_or_profile_changes_allowed"] is False
    assert manifest["historical_corpus"]["submission_id"] == 55333874
    assert manifest["historical_corpus"]["episode_count"] == 26
    assert len(manifest["historical_corpus"]["episode_ids"]) == 26
