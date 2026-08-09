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
PLAYBOOK_RULES = {
    "roto_opening_setup_or_survival": "GR-022 public Dragapult evidence requires Articuno setup.",
    "deceit_searches_ariana_survival_line": "GR-022 restricts Deceit to a decisive line.",
    "factory_after_ariana_and_roto": "GR-023 activates Factory after a Rocket Supporter.",
    "ariana_before_factory": "GR-023 separates Factory play from its later activation.",
}
TRACE_LAYERS = (
    "documented_intent",
    "parsed_public_state",
    "objective",
    "candidate_generation",
    "scoring",
    "filtering",
    "commitment",
    "fallback",
    "final_selection",
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


def _trace_coverage(record: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Summarize which replay layers are observable in one ledger record.

    Args:
        record: Decision ledger entry for one replay step.

    Returns:
        Layer-by-layer evidence coverage that stays conservative about missing
        internal traces.
    """
    fallback_used = bool(record.get("fallback_used"))
    has_public_state = isinstance(record.get("visible_state"), Mapping)
    has_selection = record.get("executed_action") is not None
    has_counterfactual = isinstance(record.get("reasons"), list) or isinstance(
        record.get("generated_action"), list
    )
    coverage: dict[str, dict[str, Any]] = {
        "documented_intent": {
            "available": True,
            "evidence": ["playbook_rule"],
        },
        "parsed_public_state": {
            "available": has_public_state,
            "evidence": (
                ["visible_state", "original_options", "select_context", "select_type"]
                if has_public_state
                else []
            ),
        },
        "objective": {
            "available": False,
            "evidence": [],
        },
        "candidate_generation": {
            "available": has_counterfactual,
            "evidence": ["candidate_action", "submitted_action"] if has_counterfactual else [],
        },
        "scoring": {
            "available": False,
            "evidence": [],
        },
        "filtering": {
            "available": False,
            "evidence": [],
        },
        "commitment": {
            "available": False,
            "evidence": [],
        },
        "fallback": {
            "available": fallback_used,
            "evidence": ["fallback_used"] if fallback_used else [],
        },
        "final_selection": {
            "available": has_selection,
            "evidence": (
                ["generated_action", "executed_action", "legal_selection"]
                if has_selection
                else []
            ),
        },
    }
    return {name: coverage[name] for name in TRACE_LAYERS}


def build_report(audit_dir: Path, current_traces: Path | None = None) -> dict[str, Any]:
    """Create a replay-linked T-034 report without strategic inference.

    Args:
        audit_dir: Completed immutable-submission audit directory.

    Returns:
        Structured report identifying what the replay evidence proves and what
        remains unobservable in the historical package.
    """
    audit = _load_mapping(audit_dir / "audit.json")
    replay_hashes = _load_mapping(audit_dir / "replay_hashes.json")
    queue = json.loads((audit_dir / "review_queue.json").read_text(encoding="utf-8"))
    if not isinstance(queue, list):
        raise ValueError("expected review queue list")
    ledger = _load_ledger(audit_dir / "decision_ledger.jsonl")
    current_ledger: dict[tuple[int, int], Mapping[str, Any]] = {}
    current_summary: Mapping[str, Any] = {}
    if current_traces is not None:
        current = _load_mapping(current_traces)
        current_summary = current.get("summary", {})
        decisions = current.get("decisions", [])
        if isinstance(decisions, list):
            current_ledger = {
                (item["episode_id"], item["step"]): item
                for item in decisions
                if isinstance(item, Mapping)
                and isinstance(item.get("episode_id"), int)
                and isinstance(item.get("step"), int)
            }
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
        current_record = current_ledger.get((episode_id, step), {})
        current_trace = current_record.get("decision_trace")
        stages = current_trace.get("stages", []) if isinstance(current_trace, Mapping) else []
        main_stage = next(
            (
                stage
                for stage in stages
                if isinstance(stage, Mapping) and stage.get("name") == "main_phase"
            ),
            {},
        )
        trace_available = isinstance(record.get("decision_trace"), Mapping)
        trace_coverage = _trace_coverage(record)
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
                "playbook_rule": PLAYBOOK_RULES[reason],
                "current_policy_action": current_record.get("generated_action"),
                "current_policy_phase_reason": current_record.get("reasons"),
                "current_policy_first_causal_stage": main_stage.get("reason"),
                "trace_coverage": trace_coverage,
                "trace_gaps": [
                    name for name, layer in trace_coverage.items() if not layer["available"]
                ],
            }
        )
    reproduction = audit.get("reproduction", {})
    submission = audit.get("submission", {})
    submission_id = submission.get("submission_id")
    replay_dir = ROOT / "replays" / "remote" / str(submission_id)
    expected_replays = replay_hashes.get("replay_sha256", {})
    expected_names = set(expected_replays) if isinstance(expected_replays, Mapping) else set()
    available_names = {path.name for path in replay_dir.glob("episode-*-replay.json")}
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
            "raw_replay_corpus_available": expected_names.issubset(available_names),
            "missing_raw_replays": sorted(expected_names - available_names),
        },
        "representative_findings": findings,
        "current_policy_reexecution": {
            "available": current_traces is not None,
            "decisions": current_summary.get("decisions"),
            "traced_decisions": sum(
                isinstance(item.get("decision_trace"), Mapping) for item in current_ledger.values()
            ),
            "fallbacks": current_summary.get("fallbacks"),
            "exceptions": current_summary.get("exceptions"),
            "interpretation": (
                "The current policy was evaluated on historical observations only; "
                "a different action is not an alternate match result."
            ),
        },
        "next_action": (
            "Obtain Owner playbook judgment for each representative record; only then approve "
            "a focused regression or runtime policy correction."
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
        "| Class | Replay | Submitted action | Current action | Current causal stage |",
        "|---|---|---|---|---|",
    ]
    for finding in report["representative_findings"]:
        trace_coverage = finding["trace_coverage"]
        lines.append(
            f"| `{finding['class']}` | `{finding['episode_id']}:{finding['step']}` | "
            f"`{finding['submitted_action']}` | `{finding['current_policy_action']}` | "
            f"`{finding['current_policy_first_causal_stage']}` |"
        )
        available_layers = [
            layer for layer, details in trace_coverage.items() if details["available"]
        ]
        lines.append(f"- Trace coverage: {', '.join(available_layers) or 'none'}.")
        lines.append(f"- Trace gaps: {', '.join(finding['trace_gaps']) or 'none'}.")
    lines.extend(
        [
            "",
            "Each candidate difference is a single-decision review prompt only. "
            "It does not imply an alternate match result. The historic package "
            "exposed phase and reason labels, but no candidate/filter/score trace, "
            "so a deeper internal causal claim would be speculative.",
            "",
            "The hash-listed historical raw replay corpus is "
            + (
                "available."
                if report["evidence_boundary"]["raw_replay_corpus_available"]
                else "not available locally."
            ),
            "",
            report["current_policy_reexecution"]["interpretation"],
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
    parser.add_argument("--current-traces", type=Path)
    args = parser.parse_args()
    report = build_report(args.audit_dir, args.current_traces)
    output = args.output or args.audit_dir / "t034_root_cause_report.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output.with_suffix(".md").write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({"output": str(output), "findings": len(report["representative_findings"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
