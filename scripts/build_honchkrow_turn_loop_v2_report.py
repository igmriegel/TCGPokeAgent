"""Build the complete HLV2 comparison bundle from independent CABT reports."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from scripts.compare_honchkrow_reports import compare

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION_MANIFEST = ROOT / "reports/honchkrow_turn_loop_v2/foundation/manifest.json"
REPLAY_HASHES = ROOT / "reports/replay_audits/55333874/replay_hashes.json"
REPLAY_DIVERGENCES = ROOT / "reports/honchkrow_turn_loop_v2/replay_gate/decision_divergences.jsonl"


def _sha256(path: Path) -> str:
    """Return one file's SHA-256 digest."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    """Load a JSON mapping from disk."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _terminal_matrix(report: Mapping[str, Any]) -> dict[str, dict[str, int]]:
    """Count terminal causes by evaluated side."""
    matrix: dict[str, Counter[str]] = {}
    for match in report.get("matches", []):
        if not isinstance(match, Mapping):
            continue
        side = str(match.get("agent_side", "unknown"))
        reason = str(match.get("termination_reason", "unknown"))
        matrix.setdefault(side, Counter())[reason] += 1
    return {side: dict(counts) for side, counts in sorted(matrix.items())}


def _tactical_gates(baseline: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Compare the tactical counters that are mandatory for promotion."""
    baseline_telemetry = baseline.get("telemetry_totals", {})
    candidate_telemetry = candidate.get("telemetry_totals", {})
    counters = (
        "ignition_without_attack",
        "torment_with_superior_line",
        "partial_mega_abomasnow_attacks",
    )
    values = {
        name: {
            "baseline": int(baseline_telemetry.get(name, 0)),
            "candidate": int(candidate_telemetry.get(name, 0)),
        }
        for name in counters
    }
    regressions = [name for name, item in values.items() if item["candidate"] > item["baseline"]]
    return {"counters": values, "regressions": regressions, "passed": not regressions}


def build_bundle(
    baseline_path: Path,
    candidate_path: Path,
    output_dir: Path,
    baseline_command: str = "",
    candidate_command: str = "",
) -> dict[str, Any]:
    """Build all required HLV2 comparison artifacts.

    Args:
        baseline_path: Independent baseline CABT report.
        candidate_path: Independent candidate CABT report.
        output_dir: Destination run directory.
        baseline_command: Exact command used for the baseline report.
        candidate_command: Exact command used for the candidate report.

    Returns:
        The generated comparison mapping.
    """
    baseline = _load(baseline_path)
    candidate = _load(candidate_path)
    if baseline.get("policy_variant") != "supporter_resource_v2":
        raise ValueError("baseline report must use supporter_resource_v2")
    if candidate.get("policy_variant") != "expert_turn_loop_v2":
        raise ValueError("candidate report must use expert_turn_loop_v2")
    output_dir.mkdir(parents=True, exist_ok=True)
    statistical = compare(baseline_path, candidate_path)
    baseline_total = int(statistical["sample_sizes"]["baseline"])
    candidate_total = int(statistical["sample_sizes"]["variant"])
    operational = statistical["operational_status"]
    operational_passed = all(
        sum(count for status, count in values.items() if status != "ok") == 0
        for values in operational.values()
    )
    deck_out_passed = (
        statistical["deck_out_losses"]["variant"] <= statistical["deck_out_losses"]["baseline"]
    )
    tactical = _tactical_gates(baseline, candidate)
    statistical_passed = bool(
        statistical["win_rate_difference"] > 0 and statistical["difference_ci95"][0] > 0
    )
    sample_passed = baseline_total >= 1000 and candidate_total >= 1000
    gates = {
        "sample_1000_each": sample_passed,
        "operational": operational_passed,
        "deck_out_non_regression": deck_out_passed,
        "tactical_non_regression": tactical["passed"],
        "positive_significant_win_rate": statistical_passed,
    }
    decision = "PROMOTE" if all(gates.values()) else "REJECT" if sample_passed else "HOLD"
    comparison = {
        "schema": "honchkrow_turn_loop_v2_comparison_v1",
        "baseline_variant": "supporter_resource_v2",
        "candidate_variant": "expert_turn_loop_v2",
        "statistical": statistical,
        "tactical": tactical,
        "gates": gates,
        "decision": decision,
        "counterfactual_policy": (
            "Independent CABT matches are not paired. Replay divergences are single-decision "
            "only and never imply an alternate match result."
        ),
    }
    shutil.copy2(baseline_path, output_dir / "baseline_report.json")
    shutil.copy2(candidate_path, output_dir / "candidate_report.json")
    (output_dir / "comparison.json").write_text(
        json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    foundation = _load(FOUNDATION_MANIFEST)
    manifest = {
        **foundation,
        "inputs": {
            "baseline_report_sha256": _sha256(baseline_path),
            "candidate_report_sha256": _sha256(candidate_path),
            "baseline_command": baseline_command,
            "candidate_command": candidate_command,
        },
        "decision": decision,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    terminal = {
        "baseline": _terminal_matrix(baseline),
        "candidate": _terminal_matrix(candidate),
    }
    (output_dir / "terminal_cause_matrix.json").write_text(
        json.dumps(terminal, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    matchup = {
        "opponent": "cabt.random_agent",
        "baseline_by_side": statistical["by_side"]["baseline"],
        "candidate_by_side": statistical["by_side"]["variant"],
    }
    (output_dir / "matchup_matrix.json").write_text(
        json.dumps(matchup, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    review_queue = [
        {"gate": gate, "status": "review", "reason": "promotion gate did not pass"}
        for gate, passed in gates.items()
        if not passed
    ]
    (output_dir / "review_queue.json").write_text(
        json.dumps(review_queue, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if REPLAY_DIVERGENCES.is_file():
        shutil.copy2(REPLAY_DIVERGENCES, output_dir / "decision_divergences.jsonl")
    else:
        (output_dir / "decision_divergences.jsonl").write_text("", encoding="utf-8")
    shutil.copy2(REPLAY_HASHES, output_dir / "replay_hashes.json")
    markdown = (
        "# Honchkrow turn loop v2 comparison\n\n"
        f"Decision: `{decision}`\n\n"
        f"Baseline: {statistical['outcomes']['baseline']}\n\n"
        f"Candidate: {statistical['outcomes']['variant']}\n\n"
        f"Win-rate difference: {statistical['win_rate_difference']:.4f}; "
        f"95% CI {statistical['difference_ci95']}.\n\n"
        f"Gates: {gates}\n\n"
        "Decision divergences are intentionally empty for independent CABT blocks; "
        "replay divergences require the separate reproduction gate.\n"
    )
    (output_dir / "comparison.md").write_text(markdown, encoding="utf-8")
    (output_dir / "comparison.html").write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>HLV2 comparison</title>"
        "</head><body><pre>" + html.escape(markdown) + "</pre></body></html>\n",
        encoding="utf-8",
    )
    return comparison


def main() -> int:
    """Parse CLI arguments and build a comparison bundle."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--baseline-command", default="")
    parser.add_argument("--candidate-command", default="")
    args = parser.parse_args()
    result = build_bundle(
        args.baseline,
        args.candidate,
        args.output_dir,
        args.baseline_command,
        args.candidate_command,
    )
    print(result["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
