"""Generate a Petrel-versus-existing-Supporter audit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.eval.petrel_analysis import analyze_matches, load_matches  # noqa: E402


def _markdown(report: dict[str, Any]) -> str:
    """Serialize the Petrel audit as a review report."""
    ariana = report["ariana_already_in_hand_refresh_signal"]
    proton = report["proton_already_in_hand_deferred_setup_signal"]
    lines = [
        "# Petrel decision audit",
        "",
        "The report flags potential substitutions only when the Supporter was "
        "already in hand and the policy trace provides a matching state-based signal. "
        "It does not claim a counterfactual win.",
        "",
        "## Summary",
        "",
        f"- Petrel plays: **{report['petrel_plays']}**",
        "- Petrel plays with another Supporter in hand: "
        f"**{report['petrel_with_other_supporter_in_hand']}**",
        f"- Petrel with Ariana already in hand and hand-refresh signal: **{ariana['count']}**",
        f"- Petrel with Proton already in hand and deferred-setup signal: **{proton['count']}**",
        f"- Overall outcomes: `{json.dumps(report['outcomes'], sort_keys=True)}`",
        "",
        "## Candidate substitutions",
        "",
        "| Situation | Count | Wins | Losses |",
        "|---|---:|---:|---:|",
        "| Ariana already in hand / refresh signal | "
        f"{ariana['count']} | {ariana['outcomes']['win']} | "
        f"{ariana['outcomes']['loss']} |",
        "| Proton already in hand / deferred setup signal | "
        f"{proton['count']} | {proton['outcomes']['win']} | "
        f"{proton['outcomes']['loss']} |",
        "",
        "## Selection reasons",
        "",
    ]
    for reason, count in sorted(report["selection_reasons"].items()):
        lines.append(f"- `{reason}`: {count}")
    lines.extend(["", "## Decision evidence", ""])
    for row in report["rows"]:
        if not (row["ariana_refresh_signal"] or row["proton_deferred_signal"]):
            continue
        lines.append(
            f"- `{row['match_id']}` turn {row['turn']} ({row['result']}): "
            f"hand={row['hand_count']}, supporters={row['supporters_in_hand']}, "
            f"energy={row['energy_cards_in_hand']}, active={row['active_card_id']}, "
            f"bench={row['bench_count']}, opponent_hand={row['opponent_hand_count']}, "
            f"reasons={row['selection_reasons']}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    """Write JSON and Markdown Petrel audit artifacts."""
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = analyze_matches(load_matches(args.report))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    args.output.with_suffix(".md").write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({key: report[key] for key in report if key != "rows"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
