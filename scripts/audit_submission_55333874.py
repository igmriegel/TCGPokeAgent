"""Reproduce and audit submission 55333874 on its isolated replay corpus."""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from collections import Counter
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Mapping, cast

ROOT = Path(__file__).resolve().parents[1]
SUBMISSION_ID = 55333874
EXPECTED_ARCHIVE_SHA256 = "f6a7c94e7cc94e6507c9db965f29845b141ae0b047e504e839884067547e4fac"
DEFAULT_ARCHIVE = ROOT / "submissions" / "honchkrow_porygon_post_audit_20260807.tar.gz"
DEFAULT_REPLAYS = ROOT / "data" / "raw" / "kaggle" / "replays" / "remote" / str(SUBMISSION_ID)
DEFAULT_OUTPUT = ROOT / "reports" / "replay_audits" / str(SUBMISSION_ID)
CANDIDATE_VARIANTS = (
    "supporter_resource_v2_replay_fix_v1",
    "expert_rounds_1_3_replay_fix_v1",
)
ACTION_EVENT_TYPES = {"Play", "Attach", "Evolve", "Attack", "Switch", "Retreat"}


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_replay(path: Path) -> dict[str, Any]:
    """Load one CABT replay mapping."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("name") != "cabt":
        raise ValueError(f"unsupported replay: {path}")
    return value


def _sync_local_corpus(replay_paths: list[Path]) -> dict[str, Any]:
    """Copy the isolated corpus into raw storage and refresh local metadata."""
    raw_root = ROOT / "data" / "raw" / "kaggle"
    raw_replays = raw_root / "replays" / "remote" / str(SUBMISSION_ID)
    mapping_path = raw_root / "episode_to_submission.json"
    metadata_path = raw_root / "submission_metadata.json"
    raw_replays.mkdir(parents=True, exist_ok=True)
    mapping = json.loads(mapping_path.read_text(encoding="utf-8")) if mapping_path.exists() else {}
    copied = 0
    for replay_path in replay_paths:
        episode_id = replay_path.name.split("-")[1]
        destination = raw_replays / replay_path.name
        if not destination.exists():
            shutil.copy2(replay_path, destination)
            copied += 1
        mapping[episode_id] = str(SUBMISSION_ID)
    mapping_path.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if isinstance(metadata, list):
            for submission in metadata:
                if isinstance(submission, dict) and submission.get("ref") == str(SUBMISSION_ID):
                    submission["status"] = "SubmissionStatus.COMPLETE"
                    submission["publicScore"] = "357.2"
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return {
        "raw_replay_count": len(replay_paths),
        "new_files_copied": copied,
        "mapping_entries_for_submission": sum(
            value == str(SUBMISSION_ID) for value in mapping.values()
        ),
    }


def _deck_from_replay(replay: Mapping[str, Any], side: int) -> list[int]:
    """Extract one initial deck without changing its card order."""
    try:
        cards = replay["steps"][0][0]["visualize"][0]["action"][side]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("replay does not expose initial decks") from error
    return [int(card) for card in cards]


def _resolve_owner(replay: Mapping[str, Any], deck: list[int]) -> int:
    """Resolve the submitted side by frozen deck, then by unique owner name."""
    target = Counter(deck)
    matches = [side for side in (0, 1) if Counter(_deck_from_replay(replay, side)) == target]
    if len(matches) == 1:
        return matches[0]
    agents = replay.get("info", {}).get("Agents", [])
    named = [
        index
        for index, agent in enumerate(agents)
        if isinstance(agent, Mapping) and agent.get("Name") == "Igor Riegel"
    ]
    if len(named) == 1:
        return named[0]
    if matches:
        return matches[0]
    raise ValueError("could not resolve submitted agent side")


def _card_id(card: Any) -> int | None:
    """Extract a visible card identifier."""
    if not isinstance(card, Mapping):
        return None
    raw = card.get("id", card.get("cardId"))
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _visible_player(player: Any) -> dict[str, Any]:
    """Retain decision-visible counts and revealed zone identities."""
    if not isinstance(player, Mapping):
        return {}

    def visible_cards(zone: str) -> list[int | None]:
        cards = player.get(zone)
        if not isinstance(cards, list):
            return []
        return [_card_id(card) for card in cards]

    return {
        "active": visible_cards("active"),
        "bench": visible_cards("bench"),
        "hand": visible_cards("hand") if isinstance(player.get("hand"), list) else None,
        "hand_count": int(player.get("handCount", 0) or 0),
        "discard": visible_cards("discard"),
        "prize": visible_cards("prize"),
        "deck_count": int(player.get("deckCount", 0) or 0),
    }


def _visible_state(observation: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize only facts visible to the acting agent."""
    current = observation.get("current")
    if not isinstance(current, Mapping):
        return {}
    players = current.get("players", [])
    your_index = int(current.get("yourIndex", 0) or 0)
    return {
        "turn": int(current.get("turn", 0) or 0),
        "turn_action_count": int(current.get("turnActionCount", 0) or 0),
        "your_index": your_index,
        "first_player": int(current.get("firstPlayer", 0) or 0),
        "energy_attached": bool(current.get("energyAttached", False)),
        "supporter_played": bool(current.get("supporterPlayed", False)),
        "retreated": bool(current.get("retreated", False)),
        "stadium": [_card_id(card) for card in current.get("stadium", [])]
        if isinstance(current.get("stadium"), list)
        else [],
        "own": _visible_player(players[your_index])
        if isinstance(players, list) and 0 <= your_index < len(players)
        else {},
        "opponent": _visible_player(players[1 - your_index])
        if isinstance(players, list) and len(players) == 2
        else {},
    }


def _selection_is_legal(select: Mapping[str, Any], action: Any) -> bool:
    """Validate an action against original simulator indices and cardinality."""
    options = select.get("option", [])
    if not isinstance(options, list) or not isinstance(action, list):
        return False
    minimum = int(select.get("minCount", 0) or 0)
    maximum = int(select.get("maxCount", 0) or 0)
    return bool(
        minimum <= len(action) <= maximum
        and len(action) == len(set(action))
        and all(
            isinstance(index, int) and not isinstance(index, bool) and 0 <= index < len(options)
            for index in action
        )
    )


def _decision_details(
    agent: Any,
) -> tuple[str, list[str], bool, dict[str, Any], dict[str, Any] | None]:
    """Extract stable policy reasons and public tactical telemetry."""
    decision = getattr(agent, "last_decision", None)
    selection = getattr(decision, "selection", None)
    phase = str(getattr(decision, "decision_phase", "") or "")
    phase_reason = str(getattr(decision, "decision_phase_reason", "") or "")
    reasons = [str(reason) for reason in getattr(selection, "reasons", ())]
    if phase_reason:
        reasons.insert(0, phase_reason)
    tactical: dict[str, Any] = {}
    for name in ("turn_ledger", "match_ledger"):
        value = getattr(agent, name, None)
        if value is not None and is_dataclass(value):
            tactical[name] = asdict(cast(Any, value))
    trace = getattr(decision, "trace", None)
    trace_payload = asdict(trace) if is_dataclass(trace) else None
    return phase, reasons, bool(getattr(decision, "fallback_used", False)), tactical, trace_payload


def _import_policy(package_root: Path | None, variant: str) -> tuple[Any, list[int], str]:
    """Import either the immutable package policy or an explicit local variant."""
    os.environ.pop("HONCHKROW_POLICY_VARIANT", None)
    if package_root is not None:
        manifest_path = package_root / "package_manifest.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            os.environ["AGENT_SOURCE_COMMIT"] = str(manifest.get("source_commit", ""))
            os.environ["AGENT_PACKAGE_SHA256"] = str(manifest.get("package_payload_sha256", ""))
        sys.path.insert(0, str(package_root))
        spec = importlib.util.spec_from_file_location("submitted_main", package_root / "main.py")
        if spec is None or spec.loader is None:
            raise RuntimeError("could not load submitted main.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        agent = module._build_agent()
        deck = module._load_deck()
        return agent, deck, str(agent.policy_variant)

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from src.agents.honchkrow_porygon import HonchkrowPorygonAgent
    from src.core import DeckDefinition, DeckProfile

    deck_path = ROOT / "src" / "artifacts" / "deck_team_rocket_murkrow.csv"
    profile_path = ROOT / "src" / "artifacts" / "deck_profile_honchkrow_porygon.json"
    deck_definition = DeckDefinition.from_path(deck_path, "honchkrow_porygon")
    profile = DeckProfile.from_dict(json.loads(profile_path.read_text(encoding="utf-8")))
    return HonchkrowPorygonAgent(profile, variant), list(deck_definition.card_ids), variant


def _run_worker(
    replay_dir: Path,
    output: Path,
    variant: str,
    package_root: Path | None,
) -> None:
    """Execute one policy over every real active replay decision."""
    initial_agent, deck, resolved_variant = _import_policy(package_root, variant)
    del initial_agent
    ledgers: list[dict[str, Any]] = []
    episodes: list[dict[str, Any]] = []
    for replay_path in sorted(replay_dir.glob("episode-*-replay.json")):
        replay = _load_replay(replay_path)
        owner_index = _resolve_owner(replay, deck)
        replay_deck = _deck_from_replay(replay, owner_index)
        agent, current_deck, resolved_variant = _import_policy(package_root, variant)
        from src.core import DeckDefinition

        del current_deck
        agent.start_match(DeckDefinition.from_cards(replay_deck, "honchkrow_porygon"))
        episode_id = int(replay.get("info", {}).get("EpisodeId", 0))
        episode_decisions = 0
        episode_divergences = 0
        episode_failures = 0
        steps = replay.get("steps", [])
        for step_index, step in enumerate(steps[:-1]):
            if not isinstance(step, list) or owner_index >= len(step):
                continue
            record = step[owner_index]
            if not isinstance(record, Mapping) or record.get("status") != "ACTIVE":
                continue
            observation = record.get("observation")
            if not isinstance(observation, Mapping):
                continue
            select = observation.get("select")
            if not isinstance(select, Mapping):
                continue
            next_step = steps[step_index + 1]
            next_record = (
                next_step[owner_index]
                if isinstance(next_step, list) and owner_index < len(next_step)
                else {}
            )
            executed = next_record.get("action") if isinstance(next_record, Mapping) else None
            fallback_exception = ""
            try:
                generated = agent.select(dict(observation))
            except Exception as error:  # noqa: BLE001
                fallback_exception = f"{type(error).__name__}: {error}"
                minimum = max(0, int(select.get("minCount", 0) or 0))
                generated = list(range(minimum))
            phase, reasons, fallback_used, tactical, decision_trace = _decision_details(agent)
            executed = list(executed) if isinstance(executed, list) else []
            generated = list(generated)
            matches = generated == executed
            legal = _selection_is_legal(select, generated)
            options = select.get("option", [])
            options = [
                dict(option) if isinstance(option, Mapping) else option for option in options
            ]
            ledgers.append(
                {
                    "episode_id": episode_id,
                    "step": step_index,
                    "turn": int((observation.get("current") or {}).get("turn", 0) or 0),
                    "owner_index": owner_index,
                    "visible_state": _visible_state(observation),
                    "select_type": select.get("type"),
                    "select_context": select.get("context"),
                    "min_count": int(select.get("minCount", 0) or 0),
                    "max_count": int(select.get("maxCount", 0) or 0),
                    "original_options": options,
                    "executed_action": executed,
                    "generated_action": generated,
                    "decision_phase": phase,
                    "reasons": reasons,
                    "variant": resolved_variant,
                    "result_matches_submission": matches,
                    "legal_selection": legal,
                    "fallback_used": fallback_used,
                    "fallback_exception": fallback_exception,
                    "tactical": tactical,
                    "decision_trace": decision_trace,
                    "counterfactual_scope": "single_decision_only" if not matches else None,
                    "outcome_inference_prohibited": not matches,
                }
            )
            episode_decisions += 1
            episode_divergences += int(not matches)
            episode_failures += int(not legal or fallback_used or bool(fallback_exception))
        episodes.append(
            {
                "episode_id": episode_id,
                "owner_index": owner_index,
                "decisions": episode_decisions,
                "divergences": episode_divergences,
                "operational_failures": episode_failures,
            }
        )
    payload = {
        "variant": resolved_variant,
        "summary": {
            "episodes": len(episodes),
            "decisions": len(ledgers),
            "matches": sum(item["result_matches_submission"] for item in ledgers),
            "divergences": sum(not item["result_matches_submission"] for item in ledgers),
            "invalid_indices": sum(not item["legal_selection"] for item in ledgers),
            "fallbacks": sum(item["fallback_used"] for item in ledgers),
            "exceptions": sum(bool(item["fallback_exception"]) for item in ledgers),
        },
        "episodes": episodes,
        "decisions": ledgers,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _worker_command(
    replay_dir: Path,
    output: Path,
    variant: str,
    package_root: Path | None = None,
) -> list[str]:
    """Build the isolated worker command."""
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--replay-dir",
        str(replay_dir),
        "--worker-output",
        str(output),
        "--variant",
        variant,
    ]
    if package_root is not None:
        command.extend(("--package-root", str(package_root)))
    return command


def _terminal_chain(diagnostic: Mapping[str, Any]) -> dict[str, Any]:
    """Classify only replay-proven terminal facts and preserve unknown roots."""
    reason = str(diagnostic["termination_reason"])
    if reason == "deck_out":
        facts = ["owner_deck_reached_zero", "explicit_deck_out_loss"]
        causal_class = "DECK_OUT"
    elif reason == "no_pokemon_in_play":
        facts = ["owner_pokemon_in_play_reached_zero", "explicit_no_pokemon_loss"]
        causal_class = "BOARD_COLLAPSE"
    elif reason == "all_prizes_taken":
        facts = ["opponent_prizes_reached_zero", "explicit_prize_loss"]
        causal_class = "PRIZE_RACE"
    else:
        facts = ["terminal_reason_not_proven"]
        causal_class = "UNKNOWN"
    return {
        "causal_class": causal_class,
        "proven_chain": facts,
        "strategic_root_cause": "unknown",
        "counterfactual_win_claim": False,
    }


def _evaluation_summary(path: Path) -> dict[str, Any]:
    """Extract promotion-relevant metrics from one CABT report."""
    report = json.loads(path.read_text(encoding="utf-8"))
    outcomes = report.get("outcomes", {})
    total = int(report.get("total_matches", 0) or 0)
    wins = int(outcomes.get("win", 0) or 0)
    telemetry = report.get("telemetry_totals", {})
    audit = report.get("audit", {})
    opportunities = int(telemetry.get("poke_pad_ko_opportunities", 0) or 0)
    misses = int(telemetry.get("poke_pad_ko_misses", 0) or 0)
    return {
        "report": str(path.relative_to(ROOT)),
        "policy_variant": report.get("policy_variant"),
        "matches": total,
        "wins": wins,
        "draws": int(outcomes.get("draw", 0) or 0),
        "losses": int(outcomes.get("loss", 0) or 0),
        "win_rate": wins / total if total else 0.0,
        "execution_failures": total - int(report.get("execution_status", {}).get("ok", 0) or 0),
        "deck_out_losses": int(audit.get("deck_out_losses", 0) or 0),
        "unknown_terminal_losses": int(audit.get("losses_by_reason", {}).get("unknown", 0) or 0),
        "ignition_without_attack": int(telemetry.get("ignition_without_attack", 0) or 0),
        "partial_attacks": int(telemetry.get("partial_mega_abomasnow_attacks", 0) or 0),
        "second_supporter_attempts": int(telemetry.get("second_supporter_attempts", 0) or 0),
        "late_proton_without_gain": int(telemetry.get("late_proton_without_gain", 0) or 0),
        "torment_with_superior_line": int(telemetry.get("torment_with_superior_line", 0) or 0),
        "poke_pad_ko_opportunities": opportunities,
        "poke_pad_ko_misses": misses,
        "poke_pad_ko_miss_rate": misses / opportunities if opportunities else 0.0,
        "observed_target_kos": int(telemetry.get("observed_target_kos", 0) or 0),
    }


def _available_evaluation(output_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load completed screening and final reports and apply promotion gates."""
    screen_paths = {
        "baseline": output_dir / "cabt_screen_baseline_300.json",
        "candidate_a": output_dir / "cabt_screen_candidate_a_300.json",
        "candidate_b": output_dir / "cabt_screen_candidate_b_300.json",
    }
    evaluation: dict[str, Any] = {"comparison_mode": "independent", "paired_seeds": False}
    if all(path.is_file() for path in screen_paths.values()):
        screening = {name: _evaluation_summary(path) for name, path in screen_paths.items()}
        baseline = screening["baseline"]
        for name in ("candidate_a", "candidate_b"):
            candidate = screening[name]
            candidate["passes_screening"] = bool(
                candidate["execution_failures"] == 0
                and candidate["deck_out_losses"] <= baseline["deck_out_losses"]
                and candidate["unknown_terminal_losses"] <= baseline["unknown_terminal_losses"]
                and candidate["win_rate"] >= baseline["win_rate"]
                and candidate["ignition_without_attack"] <= baseline["ignition_without_attack"]
                and candidate["partial_attacks"] <= baseline["partial_attacks"]
                and candidate["second_supporter_attempts"] <= baseline["second_supporter_attempts"]
                and candidate["late_proton_without_gain"] <= baseline["late_proton_without_gain"]
            )
        evaluation["screening"] = screening

    final_paths = {
        "baseline": output_dir / "cabt_final_baseline_1000.json",
        "candidate_a": output_dir / "cabt_final_candidate_a_1000.json",
    }
    promotion = {
        "status": "NOT_EVALUATED",
        "decision": (
            "No candidate package is promoted by replay evidence alone. CABT screening and "
            "the independent 1,000-match final gate remain required."
        ),
        "package_built": False,
        "upload_authorized": False,
    }
    if all(path.is_file() for path in final_paths.values()):
        from scripts.compare_honchkrow_reports import compare

        final = {name: _evaluation_summary(path) for name, path in final_paths.items()}
        comparison = compare(final_paths["baseline"], final_paths["candidate_a"])
        baseline = final["baseline"]
        candidate = final["candidate_a"]
        tactical_no_regression = bool(
            candidate["ignition_without_attack"] <= baseline["ignition_without_attack"]
            and candidate["partial_attacks"] <= baseline["partial_attacks"]
            and candidate["second_supporter_attempts"] <= baseline["second_supporter_attempts"]
            and candidate["late_proton_without_gain"] <= baseline["late_proton_without_gain"]
            and candidate["poke_pad_ko_miss_rate"] <= baseline["poke_pad_ko_miss_rate"]
            and candidate["torment_with_superior_line"] <= baseline["torment_with_superior_line"]
        )
        passes = bool(
            candidate["win_rate"] > baseline["win_rate"]
            and comparison["difference_ci95"][0] > 0.0
            and candidate["execution_failures"] == 0
            and candidate["deck_out_losses"] <= baseline["deck_out_losses"]
            and candidate["unknown_terminal_losses"] <= baseline["unknown_terminal_losses"]
            and tactical_no_regression
        )
        evaluation["final"] = final
        evaluation["final_comparison"] = comparison
        evaluation["tactical_no_regression"] = tactical_no_regression
        evaluation["promotion_gate_passed"] = passes
        if passes:
            promotion.update(
                {
                    "status": "WINNER_SELECTED",
                    "winner": candidate["policy_variant"],
                    "decision": "Candidate A passed every independent promotion gate.",
                }
            )
        else:
            promotion.update(
                {
                    "status": "NO_PROMOTION",
                    "decision": (
                        "No candidate passed every final gate; keep the immutable submitted "
                        "package as the technical reference and do not build a new package."
                    ),
                }
            )
    return evaluation, promotion


def _selected_options(decision: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    """Resolve selected original options for a recorded action."""
    options = decision.get("original_options", [])
    indices = decision.get(key, [])
    if not isinstance(options, list) or not isinstance(indices, list):
        return []
    return [
        options[index]
        for index in indices
        if isinstance(index, int)
        and 0 <= index < len(options)
        and isinstance(options[index], Mapping)
    ]


def _review_queue(
    baseline: Mapping[str, Any],
    outcome_by_episode: Mapping[int, str],
    candidate_runs: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Prioritize factual loss decisions without asserting alternate outcomes."""
    candidate_by_key = {
        (decision["episode_id"], decision["step"], run["variant"]): decision
        for run in candidate_runs
        for decision in run["decisions"]
    }
    queue: list[dict[str, Any]] = []
    for decision in baseline["decisions"]:
        episode_id = int(decision["episode_id"])
        if outcome_by_episode.get(episode_id) != "loss":
            continue
        options = decision["original_options"]
        legal_attacks = [
            option
            for option in options
            if isinstance(option, Mapping) and option.get("attackId") is not None
        ]
        chosen = _selected_options(decision, "executed_action")
        chosen_attack = any(option.get("attackId") is not None for option in chosen)
        divergences = []
        for run in candidate_runs:
            candidate = candidate_by_key[(episode_id, decision["step"], run["variant"])]
            if not candidate["result_matches_submission"]:
                divergences.append(
                    {
                        "variant": run["variant"],
                        "action": candidate["generated_action"],
                        "phase": candidate["decision_phase"],
                        "reasons": candidate["reasons"],
                    }
                )
        if not divergences and not (legal_attacks and not chosen_attack):
            continue
        priority = 100 * bool(divergences) + 40 * bool(legal_attacks and not chosen_attack)
        deck_count = int(decision["visible_state"].get("own", {}).get("deck_count", 0) or 0)
        priority += max(0, 10 - deck_count)
        queue.append(
            {
                "priority": priority,
                "episode_id": episode_id,
                "step": decision["step"],
                "turn": decision["turn"],
                "executed_action": decision["executed_action"],
                "legal_attack_count": len(legal_attacks),
                "candidate_divergences": divergences,
                "review_status": "human_review_required",
                "counterfactual_scope": "single_decision_only",
                "outcome_inference_prohibited": True,
            }
        )
    return sorted(queue, key=lambda item: (-item["priority"], item["episode_id"], item["step"]))


def _write_markdown(report: Mapping[str, Any], path: Path) -> None:
    """Write the concise audit summary."""
    source = report["reproduction"]
    aggregate = report["aggregate"]
    submission = report["submission"]
    lines = [
        f"# Submission {SUBMISSION_ID} replay audit",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Remote rating: **{submission['public_score']}** "
        f"({submission['rating_observed_at']}, {submission['episodes']} episodes)",
        f"Immutable source: `{submission['archive_sha256']}`",
        "",
        "## Reproduction gate",
        "",
        f"The submitted package reproduced **{source['matches']}/{source['decisions']}** real "
        f"policy decisions with {source['divergences']} divergences, "
        f"{source['invalid_indices']} invalid selections, and {source['fallbacks']} fallbacks.",
        "",
        "## Outcomes",
        "",
        f"- {aggregate['wins']} wins, {aggregate['losses']} losses, {aggregate['draws']} draws",
        f"- {aggregate['deck_out_losses']} effective deck-out losses; "
        f"{aggregate['owner_deck_reached_zero_replays']} games where the deck merely reached zero",
        f"- {aggregate['explicit_terminal_reasons']}/{aggregate['replays']} "
        "explicit terminal reasons",
        f"- {aggregate['reconciled_results']}/{aggregate['replays']} "
        "reconciled result/reason/final states",
        "",
        "## Candidate replay divergences",
        "",
    ]
    for candidate in report["candidates"]:
        summary = candidate["summary"]
        lines.append(
            f"- `{candidate['variant']}`: {summary['divergences']} intentional single-decision "
            f"divergences; {summary['invalid_indices']} invalid; {summary['fallbacks']} fallbacks"
        )
    evaluation = report.get("evaluation", {})
    screening = evaluation.get("screening", {})
    if screening:
        lines.extend(["", "## CABT validation", ""])
        for name in ("baseline", "candidate_a", "candidate_b"):
            item = screening[name]
            passed = item.get("passes_screening")
            suffix = ""
            if passed is not None:
                suffix = "; passed screening" if passed else "; failed screening"
            lines.append(
                f"- {name}: {item['wins']}W/{item['losses']}L in {item['matches']} matches; "
                f"{item['deck_out_losses']} deck-out losses; "
                f"{item['execution_failures']} operational failures{suffix}"
            )
    final = evaluation.get("final", {})
    comparison = evaluation.get("final_comparison", {})
    if final and comparison:
        baseline = final["baseline"]
        candidate = final["candidate_a"]
        lower, upper = comparison["difference_ci95"]
        lines.extend(
            [
                "",
                f"Final independent gate: baseline {baseline['wins']}/{baseline['matches']} "
                f"({baseline['win_rate']:.1%}) versus candidate A "
                f"{candidate['wins']}/{candidate['matches']} ({candidate['win_rate']:.1%}).",
                f"Difference: {comparison['win_rate_difference']:+.1%}; "
                f"95% interval [{lower:+.1%}, {upper:+.1%}].",
                f"Tactical no-regression gate: {evaluation['tactical_no_regression']}.",
            ]
        )
    lines.extend(
        [
            "",
            "No replay divergence is interpreted as an alternate win after the observed state "
            "would have diverged. Unproven strategic root causes remain `unknown`.",
            "",
            "## Promotion status",
            "",
            report["promotion"]["decision"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_html(report: Mapping[str, Any], path: Path) -> None:
    """Write a navigable, self-contained episode and decision review page."""
    decisions = report["ledger"]
    by_episode: dict[int, list[Mapping[str, Any]]] = {}
    result_by_episode = {int(item["episode_id"]): str(item["outcome"]) for item in report["matrix"]}
    for decision in decisions:
        by_episode.setdefault(int(decision["episode_id"]), []).append(decision)
    sections = []
    for episode_id, episode_decisions in sorted(by_episode.items()):
        rows = []
        for decision in episode_decisions:
            details = html.escape(
                json.dumps(
                    {
                        "visible_state": decision["visible_state"],
                        "original_options": decision["original_options"],
                        "tactical": decision["tactical"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            rows.append(
                "<tr>"
                f"<td>{decision['step']}</td><td>{decision['turn']}</td>"
                f"<td>{decision['select_context']}</td>"
                f"<td><code>{html.escape(str(decision['executed_action']))}</code></td>"
                f"<td>{html.escape(decision['decision_phase'])}</td>"
                f"<td>{html.escape(', '.join(decision['reasons']))}</td>"
                f"<td><details><summary>state/options</summary><pre>{details}</pre></details></td>"
                "</tr>"
            )
        sections.append(
            f'<details id="episode-{episode_id}"><summary>Episode {episode_id} '
            f"({result_by_episode[episode_id]}, {len(episode_decisions)} decisions)"
            "</summary><table><thead><tr>"
            "<th>Step</th><th>Turn</th><th>Context</th><th>Executed</th>"
            "<th>Phase</th><th>Reasons</th><th>Evidence</th></tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table></details>"
        )
    links = " ".join(
        f'<a href="#episode-{episode_id}">{episode_id}</a>' for episode_id in sorted(by_episode)
    )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Submission {SUBMISSION_ID} audit</title>
<style>body{{font:14px system-ui;margin:2rem;color:#17202a}}
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ccd1d1;padding:.35rem;vertical-align:top}}
th{{background:#eef2f3;position:sticky;top:0}}
pre{{white-space:pre-wrap;max-height:32rem;overflow:auto}}
details{{margin:.7rem 0}}code{{white-space:nowrap}}
.nav{{line-height:2}}summary{{cursor:pointer;font-weight:600}}</style></head><body>
<h1>Submission {SUBMISSION_ID} replay audit</h1>
<p>Rating {report["submission"]["public_score"]} at {report["submission"]["rating_observed_at"]};
{report["submission"]["episodes"]} isolated episodes; source
<code>{report["submission"]["archive_sha256"]}</code>.</p>
<p>Reproduction: {report["reproduction"]["matches"]}/
{report["reproduction"]["decisions"]} decisions.</p>
<nav class="nav">{links}</nav>{"".join(sections)}</body></html>"""
    path.write_text(document, encoding="utf-8")


def _run_audit(args: argparse.Namespace) -> dict[str, Any]:
    """Run package reproduction, candidate traces, and factual diagnostics."""
    archive = args.archive.resolve()
    replay_dir = args.replay_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_sha = _sha256(archive)
    if archive_sha != EXPECTED_ARCHIVE_SHA256:
        raise ValueError(f"immutable archive hash mismatch: {archive_sha}")
    replay_paths = sorted(replay_dir.glob("episode-*-replay.json"))
    if len(replay_paths) != 26:
        raise ValueError(f"expected 26 isolated replays, found {len(replay_paths)}")
    local_sync = _sync_local_corpus(replay_paths)

    with tempfile.TemporaryDirectory(prefix="submission-55333874-") as directory:
        temporary = Path(directory)
        package_root = temporary / "package"
        package_root.mkdir()
        with tarfile.open(archive, "r:gz") as package:
            package.extractall(package_root, filter="data")
        source_path = temporary / "source.json"
        subprocess.run(
            _worker_command(replay_dir, source_path, "submitted_package", package_root),
            cwd=package_root,
            check=True,
        )
        source_run = json.loads(source_path.read_text(encoding="utf-8"))
        candidate_runs = []
        for index, variant in enumerate(CANDIDATE_VARIANTS):
            candidate_path = temporary / f"candidate-{index}.json"
            subprocess.run(
                _worker_command(replay_dir, candidate_path, variant),
                cwd=ROOT,
                check=True,
            )
            candidate_runs.append(json.loads(candidate_path.read_text(encoding="utf-8")))

    if source_run["summary"]["decisions"] != 1434:
        raise ValueError("real policy decision count no longer matches the frozen gate")

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from src.data.replay_deep_analysis import extract_deep_analysis
    from src.data.replay_diagnostics import aggregate_replay_diagnostics, diagnose_replay
    from src.data.replay_outcomes import extract_replay_outcome

    deck = [
        int(line.split(",")[0])
        for line in (ROOT / "src/artifacts/deck_team_rocket_murkrow.csv").read_text().splitlines()
    ]
    diagnostics = []
    outcomes = []
    matrix = []
    for replay_path in replay_paths:
        replay = _load_replay(replay_path)
        owner_index = _resolve_owner(replay, deck)
        analysis = extract_deep_analysis(
            replay_path,
            owner_name="Igor Riegel",
            owner_index=owner_index,
        )
        diagnostic = diagnose_replay(analysis)
        outcome = extract_replay_outcome(
            replay_path,
            owner_name="Igor Riegel",
            owner_index=owner_index,
        )
        diagnostics.append(diagnostic)
        outcomes.append(outcome)
        matrix.append(
            {
                "episode_id": outcome.episode_id,
                "outcome": outcome.owner_outcome,
                "matchup": outcome.opponent_name,
                "opponent_deck_hash": outcome.opponent_deck_hash,
                "went_first": analysis.first_player == owner_index,
                "owner_actions": diagnostic.owner_action_count,
                "opponent_actions": diagnostic.opponent_action_count,
                "owner_attacks": diagnostic.owner_attack_count,
                "opponent_attacks": diagnostic.opponent_attack_count,
                "damage_dealt": diagnostic.opponent_damage_observed,
                "damage_taken": diagnostic.owner_damage_taken,
                "owner_kos": diagnostic.owner_ko_count,
                "opponent_kos": diagnostic.opponent_ko_count,
                "owner_deck_min": diagnostic.owner_deck_min,
                "owner_deck_reached_zero": diagnostic.owner_deck_reached_zero,
                "owner_lost_by_deck_out": diagnostic.owner_lost_by_deck_out,
                "owner_prizes_start": diagnostic.owner_prizes_start,
                "owner_prizes_end": diagnostic.owner_prizes_end,
                "opponent_prizes_start": diagnostic.opponent_prizes_start,
                "opponent_prizes_end": diagnostic.opponent_prizes_end,
                "termination_reason": diagnostic.termination_reason,
            }
        )
    aggregate = aggregate_replay_diagnostics(diagnostics)
    outcome_by_episode = {outcome.episode_id: outcome.owner_outcome for outcome in outcomes}
    for decision in source_run["decisions"]:
        decision["game_result"] = outcome_by_episode[int(decision["episode_id"])]
    losses = [
        {
            "episode_id": diagnostic.episode_id,
            "outcome": diagnostic.outcome,
            "termination_reason": diagnostic.termination_reason,
            **_terminal_chain(asdict(diagnostic)),
        }
        for diagnostic in diagnostics
        if diagnostic.outcome == "loss"
    ]
    queue = _review_queue(source_run, outcome_by_episode, candidate_runs)
    replay_hashes = {path.name: _sha256(path) for path in replay_paths}
    candidate_summaries = [
        {
            "variant": run["variant"],
            "summary": run["summary"],
            "intentional_divergences": [
                {
                    "episode_id": item["episode_id"],
                    "step": item["step"],
                    "turn": item["turn"],
                    "submitted_action": item["executed_action"],
                    "candidate_action": item["generated_action"],
                    "phase": item["decision_phase"],
                    "reasons": item["reasons"],
                    "counterfactual_scope": "single_decision_only",
                    "outcome_inference_prohibited": True,
                }
                for item in run["decisions"]
                if not item["result_matches_submission"]
            ],
        }
        for run in candidate_runs
    ]
    evaluation, promotion = _available_evaluation(output_dir)
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report = {
        "report_type": "submission_replay_audit_v1",
        "generated_at": generated_at,
        "scope": {
            "submission_id": SUBMISSION_ID,
            "exclusive_replay_evidence": True,
            "historical_replays_used": False,
        },
        "submission": {
            "submission_id": SUBMISSION_ID,
            "status": "COMPLETE",
            "public_score": 357.2,
            "rating_observed_at": args.rating_observed_at,
            "episodes": len(replay_paths),
            "archive": str(archive.relative_to(ROOT)),
            "archive_sha256": archive_sha,
            "deck_sha256": _sha256(ROOT / "src/artifacts/deck_team_rocket_murkrow.csv"),
        },
        "corpus": {
            "episode_ids": [int(path.name.split("-")[1]) for path in replay_paths],
            "replay_sha256": replay_hashes,
            "corpus_sha256": hashlib.sha256(
                "".join(f"{name}:{digest}\n" for name, digest in replay_hashes.items()).encode()
            ).hexdigest(),
            "local_sync": local_sync,
        },
        "reproduction": source_run["summary"],
        "aggregate": aggregate,
        "diagnostics": [asdict(item) for item in diagnostics],
        "loss_causal_chains": losses,
        "controls": [
            {"episode_id": item.episode_id, "role": "win_control"}
            for item in outcomes
            if item.owner_outcome == "win"
        ],
        "matrix": matrix,
        "qualified_replay_fixes": [],
        "uncertain_findings": [
            {
                "finding": "legal attack present but not selected",
                "status": "human_review_required",
                "reason_not_promoted": "legality alone does not prove tactical superiority",
            }
        ],
        "candidates": candidate_summaries,
        "evaluation": evaluation,
        "review_queue": queue,
        "ledger": source_run["decisions"],
        "promotion": promotion,
    }
    (output_dir / "audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "decision_ledger.jsonl").write_text(
        "".join(
            json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in report["ledger"]
        ),
        encoding="utf-8",
    )
    (output_dir / "review_queue.json").write_text(
        json.dumps(queue, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "replay_hashes.json").write_text(
        json.dumps(report["corpus"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_markdown(report, output_dir / "summary.md")
    _write_html(report, output_dir / "index.html")
    return report


def main() -> int:
    """Parse CLI arguments and execute the requested audit mode."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--replay-dir", type=Path, default=DEFAULT_REPLAYS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--rating-observed-at", default="2026-08-08T00:00:00-03:00")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--worker-output", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--package-root", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--variant", default="submitted_package", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        if args.worker_output is None:
            parser.error("--worker-output is required in worker mode")
        _run_worker(args.replay_dir, args.worker_output, args.variant, args.package_root)
        return 0
    report = _run_audit(args)
    print(
        json.dumps(
            {
                "reproduction": report["reproduction"],
                "aggregate": report["aggregate"],
                "candidate_divergences": {
                    item["variant"]: item["summary"]["divergences"] for item in report["candidates"]
                },
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
