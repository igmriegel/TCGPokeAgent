"""Summarize the HLV2 baseline and candidate replay reproductions."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


def _load(path: Path) -> dict[str, Any]:
    """Load one replay-reproduction JSON object."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    """Return one file's SHA-256 digest."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(baseline_path: Path, candidate_path: Path, output_dir: Path) -> dict[str, Any]:
    """Write the replay-gate summary and safe divergence ledger.

    Args:
        baseline_path: Baseline reproduction JSON.
        candidate_path: Candidate reproduction JSON.
        output_dir: Destination directory.

    Returns:
        The replay-gate summary.
    """
    baseline = _load(baseline_path)
    candidate = _load(candidate_path)
    if baseline.get("variant") != "supporter_resource_v2":
        raise ValueError("unexpected replay baseline variant")
    if candidate.get("variant") != "expert_turn_loop_v2":
        raise ValueError("unexpected replay candidate variant")
    divergences = [
        decision
        for decision in candidate.get("decisions", [])
        if isinstance(decision, Mapping) and not decision.get("result_matches_submission", False)
    ]
    safe_divergences = [
        {
            "episode_id": decision.get("episode_id"),
            "step": decision.get("step"),
            "turn": decision.get("turn"),
            "baseline_action": decision.get("executed_action"),
            "candidate_action": decision.get("generated_action"),
            "decision_phase": decision.get("decision_phase"),
            "reasons": decision.get("reasons", []),
            "legal_selection": decision.get("legal_selection", False),
            "fallback_used": decision.get("fallback_used", False),
            "fallback_exception": decision.get("fallback_exception", ""),
            "counterfactual_scope": "single_decision_only",
            "outcome_inference_prohibited": True,
            "turn_ledger": decision.get("tactical", {}).get("turn_ledger", {}),
        }
        for decision in divergences
    ]
    reasons = Counter(
        str((decision.get("reasons") or ["unclassified"])[0]) for decision in divergences
    )
    baseline_summary = dict(baseline.get("summary", {}))
    candidate_summary = dict(candidate.get("summary", {}))
    summary = {
        "schema": "honchkrow_turn_loop_v2_replay_gate_v1",
        "corpus": {"submission_id": 55333874, "episodes": 26, "decisions": 1434},
        "baseline": {
            "variant": baseline["variant"],
            "sha256": _sha256(baseline_path),
            **baseline_summary,
        },
        "candidate": {
            "variant": candidate["variant"],
            "sha256": _sha256(candidate_path),
            **candidate_summary,
        },
        "divergences_by_reason": dict(sorted(reasons.items())),
        "counterfactual_scope": "single_decision_only",
        "outcome_inference_prohibited": True,
        "formal_gate_status": "PRE_GATE_EVIDENCE",
        "formal_gate_blocker": "HLV2-019 and its prerequisite golden gates remain open",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "decision_divergences.jsonl").write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in safe_divergences),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    """Parse CLI arguments and write replay reproduction evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.baseline, args.candidate, args.output_dir), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
