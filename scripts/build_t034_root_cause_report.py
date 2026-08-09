"""Build a conservative evidence report for the T-034 replay investigation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIT_DIR = ROOT / "reports" / "replay_audits" / "55333874"
REPRESENTATIVE_REASONS = (
    "roto_opening_setup_or_survival",
    "deceit_searches_ariana_survival_line",
    "factory_after_ariana_and_roto",
    "ariana_before_factory",
)


def _load_mapping(path: Path) -> dict[str, Any]:
    """Load a JSON object from a report artifact.

    Args:
        path: JSON file to read.

    Returns:
        Parsed JSON mapping.
    """
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _load_ledger(path: Path) -> dict[tuple[int, int], dict[str, Any]]:
    """Index the immutable-package ledger by episode and replay step.

    Args:
        path: JSONL decision ledger produced by the replay audit.

    Returns:
        Ledger records keyed by their stable replay coordinates.
    """
    records: dict[tuple[int, int], dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        value = json.loads(line)
        if not isinstance(value, dict):
            continue
        episode_id = value.get("episode_id")
        step = value.get("step")
        if isinstance(episode_id, int) and isinstance(step, int):
            records[(episode_id, step)] = value
    return records


def build_report(audit_dir: Path) -> dict[str, Any]:
    """Create a replay-linked T-034 report without strategic inference.

    Args:
        audit_dir: Completed immutable-submission audit directory.

    Returns:
        Structured report identifying what the replay evidence proves and what
        remains unobservable in the historical package.
    """
    audit = _load_mapping(audit_dir / "audit.json")
    queue = json.loads((audit_dir / "review_queue.json").read_text(encoding="utf-8"))
    if not isinstance(queue, list):
        raise ValueError("expected review queue list")
    ledger = _load_ledger(audit_dir / "decision_ledger.jsonl")
    findings: list[dict[str, Any]] = []
    for reason in REPRESENTATIVE_REASONS:
        queue_item = next(
            (
                item
                for item in queue
                if isinstance(item, Mapping)
                and any(
                    reason in candidate.get("reasons", [])
                    for candidate in item.get("candidate_divergences", [])
                    if isinstance(candidate, Mapping)
                )
            ),
            None,
        )
        if not isinstance(queue_item, Mapping):
            continue
        episode_id = queue_item.get("episode_id")
        step = queue_item.get("step")
        if not isinstance(episode_id, int) or not isinstance(step, int):
            continue
        record = ledger.get((episode_id, step), {})
        trace_available = isinstance(record.get("decision_trace"), Mapping)
        findings.append(
            {
                "class": reason,
                "episode_id": episode_id,
                "step": step,
                "turn": record.get("turn"),
                "submitted_action": record.get("executed_action"),
                "decision_phase": record.get("decision_phase"),
                "decision_reasons": record.get("reasons"),
                "candidate_action": queue_item.get("candidate_divergences", [{}])[0].get("action"),
                "legal": record.get("legal_selection"),
                "fallback_used": record.get("fallback_used"),
                "decision_trace_available": trace_available,
                "first_causal_divergence": (
                    "unidentifiable_missing_submitted_candidate_trace"
                    if not trace_available
                    else "requires_human_playbook_comparison"
                ),
                "counterfactual_scope": "single_decision_only",
                "outcome_inference_prohibited": True,
            }
        )
    reproduction = audit.get("reproduction", {})
    submission = audit.get("submission", {})
    return {
        "schema": "t034_root_cause_report_v1",
        "task": "T-034",
        "status": "OPEN",
        "package_provenance": {
            "submission_id": submission.get("submission_id"),
            "archive_sha256": submission.get("archive_sha256"),
            "reproduced_decisions": reproduction.get("decisions"),
            "matched_decisions": reproduction.get("matches"),
        },
        "evidence_boundary": {
            "owner_feedback_established": True,
            "strategic_root_cause": "unknown",
            "alternate_outcome_claims": False,
            "missing_historical_candidate_trace": any(
                not item["decision_trace_available"] for item in findings
            ),
        },
        "representative_findings": findings,
        "next_action": (
            "Obtain Owner playbook judgment for each representative record, then add a "
            "candidate/filter/score trace to the next package before changing policy behavior."
        ),
    }


def _markdown(report: Mapping[str, Any]) -> str:
    """Render the concise human-readable companion for a T-034 report."""
    provenance = report["package_provenance"]
    lines = [
        "# T-034 replay root-cause evidence",
        "",
        "Status: **OPEN**. Owner-observed strategic divergence is established; its technical root "
        "cause remains unknown.",
        "",
        f"Immutable package: `{provenance['archive_sha256']}`; reproduction: "
        f"{provenance['matched_decisions']}/{provenance['reproduced_decisions']} decisions.",
        "",
        "| Class | Replay | Submitted action | Internal first cause |",
        "|---|---|---|---|",
    ]
    for finding in report["representative_findings"]:
        lines.append(
            f"| `{finding['class']}` | `{finding['episode_id']}:{finding['step']}` | "
            f"`{finding['submitted_action']}` | `{finding['first_causal_divergence']}` |"
        )
    lines.extend(
        [
            "",
            "Each candidate difference is a single-decision review prompt only. "
            "It does not imply an alternate match result. The historic package "
            "exposed phase and reason labels, but no candidate/filter/score trace, "
            "so a deeper internal causal claim would be speculative.",
            "",
            f"Next action: {report['next_action']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    """Build the T-034 report from an immutable replay audit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report(args.audit_dir)
    output = args.output or args.audit_dir / "t034_root_cause_report.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output.with_suffix(".md").write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({"output": str(output), "findings": len(report["representative_findings"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
