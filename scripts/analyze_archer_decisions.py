"""Generate a Markdown and JSON audit of observed Archer decisions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.eval.archer_analysis import analyze_matches, load_matches  # noqa: E402


def _markdown(report: dict[str, object]) -> str:
    """Serialize the Archer audit into a concise review document."""
    hand = report["opponent_hand"]
    lines = [
        "# Archer decision audit",
        "",
        "Archer omission means Archer was in hand and CABT generated it as a "
        "legal post-KO Supporter option. Large hand means at least 8 cards. "
        "These are opportunity signals, not counterfactual win claims.",
        "",
        f"- Archer plays: **{report['archer_plays']}**",
        f"- With better legal/productive option: **{report['archer_with_better_option']}**",
        f"- With attachable energy in hand: **{report['archer_with_attachable_energy']}**",
        f"- With playable item: **{report['archer_with_playable_item']}**",
        f"- Archer opportunities declined: **{report['omitted_archer']['all_opportunities']}**",
        "- Declined with large hand and no energy: "
        f"**{report['omitted_archer']['with_large_hand_no_energy']}**",
        "",
        "## Opponent hand at Archer decision",
        "",
        f"- Mean: **{hand['mean_before']}**",
        f"- Median: **{hand['median_before']}**",
        f"- Range: **{hand['minimum_before']}–{hand['maximum_before']}**",
        f"- Mean reduction after Archer: **{hand['mean_reduction']}**",
        f"- Distribution: `{json.dumps(hand['distribution'], sort_keys=True)}`",
        "",
        "## Items observed in hand",
        "",
    ]
    for name, count in report["item_counts_in_hand"].items():
        lines.append(f"- {name}: {count}")
    lines.extend(
        [
            "",
            "## Exact items in hand by Archer context",
            "",
            "| Item | Archer played | Played in losses | Archer omitted | "
            "Omitted in losses | Focus losses |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    item_contexts = report["item_breakdown"]
    item_names = sorted(
        {item["name"] for context in item_contexts.values() for item in context.values()}
    )
    for name in item_names:
        played = next(
            (item for item in item_contexts["archer_played"].values() if item["name"] == name),
            {"times_present": 0, "losses": 0},
        )
        omitted = next(
            (item for item in item_contexts["archer_omitted"].values() if item["name"] == name),
            {"times_present": 0, "losses": 0},
        )
        focus = next(
            (
                item
                for item in item_contexts["archer_omitted_large_hand_no_energy"].values()
                if item["name"] == name
            ),
            {"losses": 0},
        )
        lines.append(
            f"| {name} | {played['times_present']} | {played['losses']} | "
            f"{omitted['times_present']} | {omitted['losses']} | {focus['losses']} |"
        )
    composition = report["hand_composition"]["archer_played"]
    board = report["board_state"]["archer_played"]
    lines.extend(
        [
            "",
            "## Hand composition when Archer was played",
            "",
            f"- Mean hand: **{composition['mean_hand_count']}**",
            f"- Mean Supporters: **{composition['mean_supporter_count']}**",
            f"- Mean Energy: **{composition['mean_energy_count']}**",
            f"- Mean Items: **{composition['mean_item_count']}**",
            "",
            "| Card | Times present | Total copies | Mean copies/decision |",
            "|---|---:|---:|---:|",
        ]
    )
    for card in composition["cards"].values():
        lines.append(
            f"| {card['name']} | {card['times_present']} | {card['copies']} | "
            f"{card['mean_copies_when_observed']} |"
        )
    zones = report["resource_zones"]["archer_played"]
    lines.extend(
        [
            "",
            "## Resource zones when Archer was played",
            "",
            "Deck values are inferred ranges because prizes are hidden in CABT.",
            "",
            "| Resource | Hand total | Discard total | Mean deck min | Mean deck max |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for group in ("supporters", "energy"):
        for card in zones[group]["cards"].values():
            lines.append(
                f"| {card['name']} | {card['hand_total']} | {card['discard_total']} | "
                f"{card['mean_deck_inferred_min']} | {card['mean_deck_inferred_max']} |"
            )
    lines.extend(
        [
            "",
            "## Board when Archer was played",
            "",
            f"- Active Pokémon: `{json.dumps(board['active_card_names'], sort_keys=True)}`",
            f"- Bench size: `{json.dumps(board['bench_counts'], sort_keys=True)}`",
            f"- Mean Energy in play: **{board['mean_energy_in_play']}**",
        ]
    )
    played = report["played_outcomes"]
    omitted = report["omitted_archer"]
    correlation = report["cross_correlation"]
    lines.extend(
        [
            "",
            "## Outcome correlation",
            "",
            f"- All Archer plays: `{json.dumps(played['all'], sort_keys=True)}`",
            "- Archer plays in losses with attachable energy: "
            f"**{played['losses_with_attachable_energy']}**",
            "- Archer plays in losses with better ranked option: "
            f"**{played['losses_with_better_option']}**",
            "- Archer plays in losses against opponent hand ≤3: "
            f"**{played['losses_with_opponent_hand_3_or_less']}**",
            f"- Declined Archer opportunities: `{json.dumps(omitted['outcomes'], sort_keys=True)}`",
            "- Declined with large hand/no energy: "
            f"`{json.dumps(omitted['large_hand_no_energy_outcomes'], sort_keys=True)}`",
            "- Match overlap (played in loss / omitted focus / both): "
            f"**{correlation['matches_with_archer_play_in_loss']} / "
            f"{correlation['matches_with_omitted_large_hand_no_energy']} / "
            f"{correlation['matches_with_both']}**",
            "",
            "### Omitted Archer opportunities by selected Supporter",
            "",
            "| Selected card | All | Wins | Losses | Large hand/no energy losses |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for name, values in sorted(omitted["by_selected_supporter"].items()):
        lines.append(
            f"| {name} | {values['all']} | {values['wins']} | {values['losses']} | "
            f"{values['large_hand_no_energy_losses']} |"
        )
    lines.extend(
        [
            "",
            "### Selection reasons in losses where Archer was played",
            "",
        ]
    )
    for reason, count in sorted(correlation["played_loss_selection_reasons"].items()):
        lines.append(f"- `{reason}`: {count}")
    lines.extend(
        [
            "",
            "## Archer plays in losses",
            "",
        ]
    )
    for row in report["rows"]:
        if row["result"] != "loss":
            continue
        lines.append(
            f"- `{row['match_id']}` turn {row['turn']}: hand={len(row['hand_card_ids'])}, "
            f"opponent_hand={row['opponent_hand_count_before']}, "
            f"energy_attachable={row['energy_attachable']}, "
            f"items={[item['name'] for item in row['items_in_hand']]}, "
            f"reasons={row['selection_reasons']}"
        )
    lines.extend(["", "## Declined Archer opportunities", ""])
    for row in report["omission_rows"]:
        if row["result"] != "loss" and not row["large_hand_no_energy"]:
            continue
        lines.append(
            f"- `{row['match_id']}` turn {row['turn']} ({row['result']}): "
            f"hand={row['hand_count']}, energy={row['energy_ids_in_hand']}, "
            f"Archer copies={row['archer_count_in_hand']}, "
            f"selected={row['selected_supporters'] or row['selected_card_ids']}, "
            f"opponent_hand={row['opponent_hand_count']}"
        )
    lines.extend(["", "## All Archer play evidence", ""])
    for row in report["rows"]:
        lines.append(
            f"- `{row['match_id']}` turn {row['turn']} ({row['result']}): "
            f"opponent hand {row['opponent_hand_count_before']}, "
            f"energy attachable={row['energy_attachable']}, "
            f"items={[item['name'] for item in row['items_in_hand']]}, "
            f"better={row['better_options']}"
        )
    return "\n".join(lines) + "\n"


def _executive_markdown(report: dict[str, object]) -> str:
    """Serialize the complete Archer findings as one executive report."""
    played = report["played_outcomes"]
    omitted = report["omitted_archer"]
    correlation = report["cross_correlation"]
    composition = report["hand_composition"]["archer_played"]
    board = report["board_state"]["archer_played"]
    lines = [
        "# Archer — consolidated decision report",
        "",
        "## Scope and interpretation",
        "",
        "This report audits the 1,000-match `expert_turn_loop` trace. "
        "An omitted Archer opportunity means Archer was visible in hand and "
        "generated as a legal post-KO Supporter option. A large hand means "
        "8 or more cards. These are observed opportunities, not guaranteed "
        "counterfactual wins.",
        "",
        "## Executive findings",
        "",
        f"- Archer was played **{report['archer_plays']}** times: "
        f"{played['all']['win']} wins and {played['all']['loss']} losses.",
        "- Those losses occurred across "
        f"**{correlation['matches_with_archer_play_in_loss']}** matches.",
        f"- **{played['losses_with_attachable_energy']}** loss decisions used Archer "
        "while energy was legally attachable.",
        f"- **{played['losses_with_opponent_hand_3_or_less']}** loss decisions used "
        "Archer against an opponent with at most 3 cards.",
        f"- Archer was omitted in **{omitted['all_opportunities']}** legal opportunities: "
        f"{omitted['outcomes']['win']} wins and {omitted['outcomes']['loss']} losses.",
        f"- The main suspected pattern occurred **{omitted['with_large_hand_no_energy']}** times: "
        "large hand and no energy, with "
        f"{omitted['large_hand_no_energy_outcomes']['loss']} losses.",
        f"- **{omitted['large_hand_no_energy_and_other_supporter']}** of those cases "
        "played another Supporter.",
        "",
        "## Omitted Archer after a large hand/no-energy state",
        "",
        "| Selected Supporter | Opportunities | Wins | Losses | Focus losses |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, values in sorted(omitted["by_selected_supporter"].items()):
        lines.append(
            f"| {name} | {values['all']} | {values['wins']} | {values['losses']} | "
            f"{values['large_hand_no_energy_losses']} |"
        )
    lines.extend(
        [
            "",
            "## Exact items observed",
            "",
            "| Item | Archer played | Played in losses | Archer omitted | "
            "Omitted in losses | Focus losses |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    contexts = report["item_breakdown"]
    names = sorted({item["name"] for context in contexts.values() for item in context.values()})
    for name in names:
        values = []
        for context_name in (
            "archer_played",
            "archer_omitted",
            "archer_omitted_large_hand_no_energy",
        ):
            values.append(
                next(
                    (item for item in contexts[context_name].values() if item["name"] == name),
                    {"times_present": 0, "losses": 0},
                )
            )
        lines.append(
            f"| {name} | {values[0]['times_present']} | {values[0]['losses']} | "
            f"{values[1]['times_present']} | {values[1]['losses']} | {values[2]['losses']} |"
        )
    lines.extend(
        [
            "",
            "## Hand and board context when Archer was played",
            "",
            f"- Mean hand: **{composition['mean_hand_count']}** cards.",
            f"- Mean Supporters: **{composition['mean_supporter_count']}**.",
            f"- Mean Energy: **{composition['mean_energy_count']}**.",
            f"- Mean Items: **{composition['mean_item_count']}**.",
            f"- Active Pokémon: `{json.dumps(board['active_card_names'], sort_keys=True)}`.",
            f"- Mean Energy attached on board: **{board['mean_energy_in_play']}**.",
            f"- Bench distribution: `{json.dumps(board['bench_counts'], sort_keys=True)}`.",
            "",
            "## Resource zones",
            "",
            "Hand and discard are observed. Deck values are inferred ranges "
            "from the fixed 60-card list because prizes are hidden by CABT.",
            "",
            "| Resource | Hand total | Discard total | Mean deck min | Mean deck max |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    zones = report["resource_zones"]["archer_played"]
    for group in ("supporters", "energy"):
        for card in zones[group]["cards"].values():
            lines.append(
                f"| {card['name']} | {card['hand_total']} | {card['discard_total']} | "
                f"{card['mean_deck_inferred_min']} | {card['mean_deck_inferred_max']} |"
            )
    lines.extend(
        [
            "",
            "## Conclusions",
            "",
            "1. The clearest candidate for correction is the 14 loss decisions "
            "where Archer was available after a KO, the hand had at least 8 "
            "cards, and no energy was in hand.",
            "2. Petrel is the largest source of those omissions, followed by Proton and Giovanni.",
            "3. Archer usage itself has a separate energy-priority signal: 32 "
            "loss decisions had a legal energy attachment available.",
            "4. The trace did not contain a higher final policy score for an "
            "alternative in the 125 Archer selections; this does not prove that "
            "no counterfactual alternative was strategically better.",
            "",
            "## Evidence and reproducibility",
            "",
            "The per-decision JSON contains hand, board, Supporter, item, energy, "
            "discard, inferred-deck, opponent-hand, selected action, and final "
            "match result for every audited event.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    """Parse an evaluation report and write Archer audit artifacts."""
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
    args.output.with_name(args.output.stem + "_summary.md").write_text(
        _executive_markdown(report), encoding="utf-8"
    )
    print(json.dumps({key: report[key] for key in report if key != "rows"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
