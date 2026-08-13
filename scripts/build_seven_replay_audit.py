"""Build a state-based audit report for the seven reviewed replays."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

EPISODES = (92410349, 92351382, 92344156, 92301028, 92280407, 92269436, 92201785)


def _card_id(candidate: Mapping[str, Any]) -> int | None:
    """Resolve a candidate card ID from the extracted public trace."""
    features = candidate.get("features")
    if isinstance(features, Mapping) and isinstance(features.get("card_id"), int):
        return int(features["card_id"])
    card = candidate.get("card")
    if isinstance(card, Mapping):
        value = card.get("cardId", card.get("id"))
        return int(value) if isinstance(value, int) else None
    return None


def _compact_candidates(trace: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Keep legal candidates and original indices without copying bulky metadata."""
    result: list[dict[str, Any]] = []
    for candidate in trace.get("candidates", []):
        if not isinstance(candidate, Mapping):
            continue
        option = candidate.get("option")
        result.append(
            {
                "index": candidate.get("option_index"),
                "type": candidate.get("option_type"),
                "card_id": _card_id(candidate),
                "attack_id": (option.get("attackId") if isinstance(option, Mapping) else None),
            }
        )
    return result


def _category(decision: Mapping[str, Any]) -> str:
    """Classify one state-based divergence from its public trace evidence."""
    reasons = " ".join(str(reason) for reason in decision.get("reasons", ())).casefold()
    trace = decision.get("decision_trace")
    candidates = trace.get("candidates", []) if isinstance(trace, Mapping) else []
    card_ids = {_card_id(item) for item in candidates if isinstance(item, Mapping)}
    if "redundant" in reasons or "already" in reasons:
        return "recurso_redundante"
    if "setup" in reasons or 1121 in card_ids:
        return "linha_incompleta"
    if "roto" in reasons or 1077 in card_ids:
        return "prioridade"
    if "headset" in reasons or 1109 in card_ids:
        return "linha_incompleta"
    if "giovanni" in reasons or 1218 in card_ids:
        return "prioridade"
    return "estado_incorreto"


def _audit_decision(decision: Mapping[str, Any]) -> dict[str, Any]:
    """Convert one reprocessed decision to the final audit contract."""
    trace = decision.get("decision_trace")
    trace_map = trace if isinstance(trace, Mapping) else {}
    historical = list(decision.get("executed_action", []))
    final = list(decision.get("generated_action", []))
    diverged = not bool(decision.get("result_matches_submission", False))
    reasons = [str(reason) for reason in decision.get("reasons", [])]
    return {
        "step": decision.get("step"),
        "turn": decision.get("turn"),
        "select_context": decision.get("select_context"),
        "state_public": decision.get("visible_state", {}),
        "legal_candidates": _compact_candidates(trace_map),
        "objective": {
            "before": trace_map.get("objective_before"),
            "after": trace_map.get("objective_after"),
        },
        "ranking": trace_map.get("ranked_scores", []),
        "historical_action": historical,
        "final_action": final,
        "divergence": diverged,
        "corrected_line": (
            "Execute final action "
            + json.dumps(final, separators=(",", ":"))
            + "; "
            + (reasons[0] if reasons else "state-based policy line")
            if diverged
            else "Historical action agrees with the final policy line."
        ),
        "error_category": _category(decision) if diverged else None,
        "policy_phase": decision.get("decision_phase"),
        "policy_reasons": reasons,
        "legal_selection": bool(decision.get("legal_selection", False)),
    }


def build_report(reprocessed: Mapping[str, Any], source: str) -> dict[str, Any]:
    """Build the replay-by-replay state audit from worker output."""
    decisions = [item for item in reprocessed.get("decisions", []) if isinstance(item, Mapping)]
    by_episode: dict[int, list[Mapping[str, Any]]] = {}
    for decision in decisions:
        episode = int(decision.get("episode_id", 0))
        by_episode.setdefault(episode, []).append(decision)
    reports = []
    for episode in EPISODES:
        episode_decisions = by_episode.get(episode, [])
        audited = [_audit_decision(decision) for decision in episode_decisions]
        divergences = [item for item in audited if item["divergence"]]
        reports.append(
            {
                "replay_id": episode,
                "decision_count": len(audited),
                "divergence_count": len(divergences),
                "categories": dict(Counter(item["error_category"] for item in divergences)),
                "decisions": audited,
            }
        )
    return {
        "report_type": "seven_replay_state_based_audit_v1",
        "source_reprocessed_output": source,
        "replay_ids": list(EPISODES),
        "runtime_id_dependency": False,
        "worker_summary": reprocessed.get("summary", {}),
        "replays": reports,
    }


def _markdown(report: Mapping[str, Any]) -> str:
    """Render a compact human-readable companion to the complete JSON audit."""
    lines = [
        "# Seven replay state-based audit",
        "",
        "Runtime replay-ID dependency: `false`.",
        "",
        "| Replay | Decisions | Divergences | Categories |",
        "|---:|---:|---:|---|",
    ]
    for replay in report["replays"]:
        categories = ", ".join(f"{key}: {value}" for key, value in replay["categories"].items())
        lines.append(
            f"| {replay['replay_id']} | {replay['decision_count']} | "
            f"{replay['divergence_count']} | {categories or 'none'} |"
        )
    lines.extend(["", "## Divergences", ""])
    for replay in report["replays"]:
        lines.extend([f"### Replay {replay['replay_id']}", ""])
        for decision in replay["decisions"]:
            if not decision["divergence"]:
                continue
            lines.extend(
                [
                    f"#### Step {decision['step']} (turn {decision['turn']}) — "
                    f"`{decision['error_category']}`",
                    "",
                    f"- Objective: `{decision['objective']['after']}`",
                    f"- Historical action: `{decision['historical_action']}`",
                    f"- Final action: `{decision['final_action']}`",
                    f"- Corrected line: {decision['corrected_line']}",
                    f"- Public state: `{json.dumps(decision['state_public'], sort_keys=True)}`",
                    "- Legal candidates: `"
                    f"{json.dumps(decision['legal_candidates'], sort_keys=True)}`",
                    f"- Ranking: `{json.dumps(decision['ranking'], sort_keys=True)}`",
                    "",
                ]
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    """Read worker output and write the final replay audit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reprocessed", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    reprocessed = json.loads(args.reprocessed.read_text(encoding="utf-8"))
    report = build_report(reprocessed, str(args.reprocessed))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    args.output.with_suffix(".md").write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report["worker_summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
