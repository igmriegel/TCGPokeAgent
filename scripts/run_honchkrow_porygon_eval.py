"""Run a deterministic CABT evaluation with Honchkrow/Porygon telemetry."""

from __future__ import annotations

import argparse
import contextlib
import gzip
import json
import os
import shutil
import sys
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.honchkrow_porygon import (  # noqa: E402
    MEGA_ABOMASNOW_EX,
    MEGA_ABOMASNOW_R_COMMAND_SUPPORTERS,
    MEGA_ABOMASNOW_ROCKET_FEATHERS_SUPPORTERS,
    R_COMMAND,
    ROCKET_FEATHERS,
    HonchkrowPorygonAgent,
)
from src.core import DeckDefinition, DeckProfile  # noqa: E402
from src.data.honchkrow_audit import audit_opportunities  # noqa: E402
from src.eval.telemetry import public_snapshot, transition  # noqa: E402

PROFILE_PATH = ROOT / "src" / "artifacts" / "deck_profile_honchkrow_porygon.json"
DECK_PATH = ROOT / "src" / "artifacts" / "deck_team_rocket_murkrow.csv"
TERMINATION_REASONS = {1: "all_prizes_taken", 2: "deck_out", 3: "no_pokemon_in_play"}
ROCKET_SUPPORTERS = {1216, 1217, 1218, 1219, 1220}


@contextlib.contextmanager
def quiet_sdk_output() -> Iterator[None]:
    """Suppress native SDK diagnostics while preserving the JSON report."""
    stdout_fd, stderr_fd = os.dup(1), os.dup(2)
    try:
        with open(os.devnull, "w", encoding="utf-8") as sink:
            os.dup2(sink.fileno(), 1)
            os.dup2(sink.fileno(), 2)
            yield
    finally:
        os.dup2(stdout_fd, 1)
        os.dup2(stderr_fd, 2)
        os.close(stdout_fd)
        os.close(stderr_fd)


def _card_id(value: Any) -> int:
    """Extract a card identifier from a public card mapping."""
    if not isinstance(value, Mapping):
        return 0
    raw = value.get("id", value.get("cardId", 0))
    return int(raw) if isinstance(raw, int) and not isinstance(raw, bool) else 0


def _player(current: Mapping[str, Any], index: int) -> Mapping[str, Any]:
    """Return one public player snapshot."""
    players = current.get("players", [])
    value = players[index] if isinstance(players, list) and index < len(players) else {}
    return value if isinstance(value, Mapping) else {}


def _active(player: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return the public Active snapshot or an empty mapping."""
    active = player.get("active", [])
    value = active[0] if isinstance(active, list) and active else {}
    return value if isinstance(value, Mapping) else {}


def _supporter_count(cards: Any) -> int:
    """Count visible Team Rocket Supporters."""
    return sum(_card_id(card) in ROCKET_SUPPORTERS for card in cards if isinstance(cards, list))


def _option_type(option: Mapping[str, Any]) -> int | str | None:
    """Return the raw CABT option type."""
    value = option.get("type")
    return value if isinstance(value, (int, str)) and not isinstance(value, bool) else None


def _terminal_snapshot(environment: Any) -> Mapping[str, Any]:
    """Find the last public current state exposed by the environment."""
    for step in reversed(getattr(environment, "steps", [])):
        if not isinstance(step, list):
            continue
        for player_step in reversed(step):
            observation = (
                player_step.get("observation") if isinstance(player_step, Mapping) else None
            )
            current = observation.get("current") if isinstance(observation, Mapping) else None
            if isinstance(current, Mapping) and isinstance(current.get("players"), list):
                return current
    return {}


def _terminal_reason(environment: Any, current: Mapping[str, Any]) -> tuple[int | None, str, bool]:
    """Extract the explicit CABT termination reason when available."""
    for step in reversed(getattr(environment, "steps", [])):
        if not isinstance(step, list):
            continue
        for player_step in reversed(step):
            observation = (
                player_step.get("observation") if isinstance(player_step, Mapping) else None
            )
            logs = observation.get("logs", []) if isinstance(observation, Mapping) else []
            if not isinstance(logs, list):
                continue
            for event in reversed(logs):
                if not isinstance(event, Mapping) or "reason" not in event:
                    continue
                raw = event.get("reason")
                code = int(raw) if isinstance(raw, int) else None
                reason = TERMINATION_REASONS.get(code, "unknown") if code is not None else "unknown"
                return code, reason, code in TERMINATION_REASONS if code is not None else False
    result = current.get("result")
    return None, "draw" if result == 2 else "unknown", False


def _terminal_counts(current: Mapping[str, Any], side: int) -> dict[str, Any]:
    """Return factual terminal counts for the evaluated side."""
    own = _player(current, side)
    active = _active(own)
    bench = own.get("bench", [])
    occupied_bench = sum(item is not None for item in bench) if isinstance(bench, list) else 0
    prizes = own.get("prize", [])
    return {
        "deck_count": int(own.get("deckCount", 0) or 0),
        "prize_count": len(prizes) if isinstance(prizes, list) else None,
        "hand_count": int(own.get("handCount", 0) or 0),
        "discard_count": len(own.get("discard", []))
        if isinstance(own.get("discard", []), list)
        else 0,
        "pokemon_in_play": occupied_bench + int(bool(active)),
        "bench_count": occupied_bench,
        "active_card_id": _card_id(active),
        "active_hp": int(active.get("hp", 0) or 0),
    }


def _inferred_reason(current: Mapping[str, Any], loser_side: int) -> str:
    """Infer the terminal reason from the loser's last public counts."""
    loser = _terminal_counts(current, loser_side)
    winner = _terminal_counts(current, 1 - loser_side)
    if winner["prize_count"] == 0:
        return "all_prizes_taken"
    if loser["deck_count"] == 0:
        return "deck_out"
    if loser["pokemon_in_play"] == 0:
        return "no_pokemon_in_play"
    return "unknown"


POLICY_VARIANTS = (
    "baseline",
    "legacy_baseline",
    "ko_priority_v1",
    "ko_priority_v2_strict",
    "ko_priority_v3_retreat_guard",
    "supporter_lethal_v1",
    "supporter_resource_v2",
    "expert_rounds_1_3_v1",
    "expert_turn_loop_v2",
    "supporter_resource_v2_replay_fix_v1",
    "expert_rounds_1_3_replay_fix_v1",
)


def _build_agent(policy_variant: str | None = None) -> tuple[HonchkrowPorygonAgent, DeckDefinition]:
    """Load the dedicated profile and deck."""
    profile = DeckProfile.from_dict(json.loads(PROFILE_PATH.read_text(encoding="utf-8")))
    deck = DeckDefinition.from_path(DECK_PATH, "honchkrow_porygon")
    return HonchkrowPorygonAgent(profile, policy_variant), deck


def _run_match(seed: int, side: int, policy_variant: str | None = None) -> dict[str, Any]:
    """Run one match and retain result, terminal, and policy telemetry."""
    agent, deck = _build_agent(policy_variant)
    events: list[dict[str, Any]] = []
    decisions = 0
    decision_ms: list[float] = []
    last_current: Mapping[str, Any] = {}
    pending_event: dict[str, Any] | None = None

    def policy(observation: dict[str, Any]) -> list[int]:
        nonlocal decisions, last_current, pending_event
        if observation.get("select") is None:
            agent.start_match(deck)
            return list(deck.card_ids)
        started = time.perf_counter()
        result = agent.select(observation)
        elapsed_ms = (time.perf_counter() - started) * 1000
        decision_ms.append(elapsed_ms)
        decisions += 1
        select = observation.get("select", {})
        current = observation.get("current", {})
        if not isinstance(select, Mapping) or not isinstance(current, Mapping):
            return result
        telemetry_before = public_snapshot(observation)
        if pending_event is not None:
            pending_event["state_after"] = dict(current)
            telemetry_after = telemetry_before
            pending_event["telemetry_after"] = telemetry_after
            pending_event["transition"] = transition(
                pending_event["telemetry_before"], telemetry_after
            )
        last_current = current
        own_index = int(current.get("yourIndex", side) or side)
        own = _player(current, own_index)
        opponent = _player(current, 1 - own_index)
        active = _active(own)
        target = _active(opponent)
        own_bench = own.get("bench", [])
        opponent_bench = opponent.get("bench", [])
        own_bench_count = (
            sum(item is not None for item in own_bench) if isinstance(own_bench, list) else 0
        )
        opponent_bench_count = (
            sum(item is not None for item in opponent_bench)
            if isinstance(opponent_bench, list)
            else 0
        )
        options = select.get("option", [])
        options = options if isinstance(options, list) else []
        selected = [options[index] for index in result if 0 <= index < len(options)]
        attacks = [
            option.get("attackId")
            for option in options
            if isinstance(option, Mapping) and option.get("attackId") is not None
        ]
        selected_attacks = [
            option.get("attackId")
            for option in selected
            if isinstance(option, Mapping) and option.get("attackId") is not None
        ]
        hand_supporters = _supporter_count(own.get("hand", []))
        discard_supporters = _supporter_count(own.get("discard", []))
        partial = bool(
            _card_id(target) == MEGA_ABOMASNOW_EX
            and (
                ROCKET_FEATHERS in selected_attacks
                and hand_supporters < MEGA_ABOMASNOW_ROCKET_FEATHERS_SUPPORTERS
                or R_COMMAND in selected_attacks
                and discard_supporters < MEGA_ABOMASNOW_R_COMMAND_SUPPORTERS
            )
        )
        selected_types = [
            _option_type(option) for option in selected if isinstance(option, Mapping)
        ]
        ledger = agent.turn_ledger
        match_ledger = agent.match_ledger
        policy_decision = agent.last_decision
        event = {
            "turn": int(current.get("turn", 0) or 0),
            "deck_count": int(own.get("deckCount", 0) or 0),
            "prize_count": len(own.get("prize", []))
            if isinstance(own.get("prize", []), list)
            else 0,
            "hand_count": int(own.get("handCount", 0) or 0),
            "discard_count": len(own.get("discard", []))
            if isinstance(own.get("discard", []), list)
            else 0,
            "bench_count": own_bench_count,
            "pokemon_in_play": own_bench_count + int(bool(active)),
            "active_card_id": _card_id(active),
            "active_energy_count": len(active.get("energies", []))
            if isinstance(active.get("energies", []), list)
            else 0,
            "target_card_id": _card_id(target),
            "target_hp": int(target.get("hp", 0) or 0),
            "opponent_deck_count": int(opponent.get("deckCount", 0) or 0),
            "opponent_prize_count": len(opponent.get("prize", []))
            if isinstance(opponent.get("prize", []), list)
            else 0,
            "opponent_bench_count": opponent_bench_count,
            "opponent_pokemon_in_play": opponent_bench_count + int(bool(target)),
            "hand_supporters": hand_supporters,
            "discard_supporters": discard_supporters,
            "select_type": select.get("type"),
            "option_types": [
                _option_type(option) for option in options if isinstance(option, Mapping)
            ],
            "options": [dict(option) for option in options if isinstance(option, Mapping)],
            "attack_ids": attacks,
            "selected_indices": result,
            "selected_types": selected_types,
            "selected_attack_ids": selected_attacks,
            "duration_ms": round(elapsed_ms, 3),
            "resource_guard": ledger.resource_guard,
            "own_turn": ledger.own_turn,
            "turn_action_count": ledger.turn_action_count,
            "first_own_turn": ledger.first_own_turn,
            "turn_objective": ledger.objective,
            "turn_stage": ledger.stage,
            "previous_turn_stage": ledger.previous_stage,
            "replans": ledger.replans,
            "last_replan_reason": ledger.last_replan_reason,
            "last_replan_previous_stage": ledger.last_replan_previous_stage,
            "last_replan_new_stage": ledger.last_replan_new_stage,
            "supporters_in_hand": ledger.supporters_in_hand,
            "supporters_in_discard": ledger.supporters_in_discard,
            "supporters_needed_for_ko": ledger.supporters_needed_for_ko,
            "rocket_feathers_damage": ledger.rocket_feathers_damage,
            "r_command_damage": ledger.r_command_damage,
            "active_attacker_card_id": ledger.active_attacker_card_id,
            "bench_attacker_card_id": ledger.bench_attacker_card_id,
            "active_energy_units": ledger.active_energy_units,
            "energy_cards_in_hand": ledger.energy_cards_in_hand,
            "energy_attachable": ledger.energy_attachable,
            "deck_reserve": ledger.deck_reserve,
            "deck_risk": ledger.deck_risk,
            "roto_sticks_played": ledger.roto_sticks_played,
            "roto_supporters_revealed": ledger.roto_supporters_revealed,
            "roto_supporters_selected": ledger.roto_supporters_selected,
            "roto_damage_acquired": ledger.roto_damage_acquired,
            "roto_preserved_reason": ledger.roto_preserved_reason,
            "transceiver_proton_in_hand": ledger.transceiver_proton_in_hand,
            "transceiver_target": ledger.transceiver_target,
            "transceiver_lethal_exception": ledger.transceiver_lethal_exception,
            "transceiver_objective": ledger.transceiver_objective,
            "ariana_opportunities": ledger.ariana_opportunities,
            "ariana_plays": ledger.ariana_plays,
            "ariana_marginal_draw": ledger.ariana_marginal_draw,
            "ariana_supporters_in_hand": ledger.ariana_supporters_in_hand,
            "ariana_with_required_proton": ledger.ariana_with_required_proton,
            "petrel_factory_opportunities": ledger.petrel_factory_opportunities,
            "petrel_factory_conversions": ledger.petrel_factory_conversions,
            "poke_pad_ko_opportunities": ledger.poke_pad_ko_opportunities,
            "poke_pad_ko_conversions": ledger.poke_pad_ko_conversions,
            "poke_pad_ko_misses": ledger.poke_pad_ko_misses,
            "torment_with_superior_line": ledger.torment_with_superior_line,
            "no_pokemon_risk": ledger.no_pokemon_risk,
            "supporter_played": ledger.supporter_played,
            "second_supporter_attempts": ledger.second_supporter_attempts,
            "rocket_planned_damage": ledger.rocket_planned_damage,
            "rocket_supporters_needed": ledger.rocket_supporters_needed,
            "rocket_supporters_available": ledger.rocket_supporters_available,
            "rocket_supporters_discarded": ledger.rocket_supporters_discarded,
            "rocket_supporters_preserved": ledger.rocket_supporters_preserved,
            "lethal_lines_executed": ledger.lethal_lines_executed,
            "lethal_lines_missed": ledger.lethal_lines_missed,
            "lethal_lines_converted": ledger.lethal_lines_converted,
            "miracle_headsets_played": ledger.miracle_headsets_played,
            "miracle_supporters_recovered": ledger.miracle_supporters_recovered,
            "porygon_terminal_opportunities": match_ledger.porygon_terminal_opportunities,
            "porygon_terminal_conversions": match_ledger.porygon_terminal_conversions,
            "ignition_attachments": match_ledger.ignition_attachments,
            "ignition_attacks": match_ledger.ignition_attacks,
            "ignition_without_attack": match_ledger.ignition_without_attack,
            "late_proton_without_gain": match_ledger.late_proton_without_gain,
            "match_petrel_factory_opportunities": match_ledger.petrel_factory_opportunities,
            "match_petrel_factory_conversions": match_ledger.petrel_factory_conversions,
            "match_poke_pad_ko_opportunities": match_ledger.poke_pad_ko_opportunities,
            "match_poke_pad_ko_conversions": match_ledger.poke_pad_ko_conversions,
            "match_poke_pad_ko_misses": match_ledger.poke_pad_ko_misses,
            "match_torment_with_superior_line": match_ledger.torment_with_superior_line,
            "partial_mega_abomasnow_attack": partial,
            "fallback_used": bool(getattr(agent.last_decision, "fallback_used", False)),
            "decision_phase": getattr(policy_decision, "decision_phase", ""),
            "decision_phase_reason": getattr(policy_decision, "decision_phase_reason", ""),
            "selection_reasons": list(
                getattr(getattr(policy_decision, "selection", None), "reasons", ())
            ),
            "state_before": dict(current),
            "telemetry_before": telemetry_before,
        }
        events.append(event)
        pending_event = event
        return result

    started = time.perf_counter()
    with quiet_sdk_output():
        from kaggle_environments import make
        from kaggle_environments.envs.cabt.cabt import random_agent

        environment = make("cabt", configuration={"seed": seed}, debug=False)
        players = [policy, random_agent] if side == 0 else [random_agent, policy]
        environment.run(players)
    elapsed_ms = (time.perf_counter() - started) * 1000
    statuses = [str(getattr(player, "status", "unknown")) for player in environment.state]
    status_ok = all(value.endswith("DONE") for value in statuses)
    reward = getattr(environment.state[side], "reward", None)
    result = (
        "win"
        if reward is not None and reward > 0
        else "loss"
        if reward is not None and reward < 0
        else "draw"
    )
    current = last_current or _terminal_snapshot(environment)
    if pending_event is not None:
        telemetry_after = public_snapshot(current)
        pending_event["state_after"] = dict(current)
        pending_event["telemetry_after"] = telemetry_after
        pending_event["transition"] = transition(pending_event["telemetry_before"], telemetry_after)
    reason_code, reason, reason_explicit = _terminal_reason(environment, current)
    loser_side = 1 - side if result == "win" else side
    inferred_reason = _inferred_reason(current, loser_side)
    if not reason_explicit:
        reason = inferred_reason
    terminal = _terminal_counts(current, side)
    opportunities = [
        asdict(opportunity) for opportunity in audit_opportunities([{"events": events}])
    ]
    return {
        "match_id": f"honchkrow_{seed}_{side}",
        "seed": seed,
        "agent_side": side,
        "policy_variant": agent.policy_variant,
        "result": result,
        "reward": reward,
        "status": "ok" if status_ok else "error",
        "statuses": statuses,
        "duration_ms": round(elapsed_ms, 3),
        "decision_count": decisions,
        "decision_p50_ms": round(sorted(decision_ms)[len(decision_ms) // 2], 3)
        if decision_ms
        else 0.0,
        "decision_p95_ms": round(sorted(decision_ms)[int(len(decision_ms) * 0.95)], 3)
        if decision_ms
        else 0.0,
        "termination_reason": reason,
        "termination_reason_code": reason_code,
        "termination_reason_explicit": reason_explicit,
        "termination_reason_inferred": inferred_reason,
        "terminal_turn": int(current.get("turn", 0) or 0),
        "terminal": terminal,
        "terminal_opponent": _terminal_counts(current, 1 - side),
        "telemetry": {
            "partial_mega_abomasnow_attacks": sum(
                event["partial_mega_abomasnow_attack"] for event in events
            ),
            "end_with_critical_deck": sum(
                14 in event["selected_types"] and event["deck_count"] <= 2 for event in events
            ),
            "retreats": sum(12 in event["selected_types"] for event in events),
            "attacks": sum(bool(event["selected_attack_ids"]) for event in events),
            "fallbacks": sum(event["fallback_used"] for event in events),
            "roto_sticks_played": sum(event["roto_sticks_played"] for event in events),
            "roto_supporters_revealed": sum(event["roto_supporters_revealed"] for event in events),
            "roto_supporters_selected": sum(event["roto_supporters_selected"] for event in events),
            "second_supporter_attempts": sum(
                event["second_supporter_attempts"] for event in events
            ),
            "rocket_lethal_lines": sum(event["lethal_lines_executed"] for event in events),
            "miracle_headsets_played": sum(event["miracle_headsets_played"] for event in events),
            "porygon_terminal_opportunities": agent.match_ledger.porygon_terminal_opportunities,
            "porygon_terminal_conversions": agent.match_ledger.porygon_terminal_conversions,
            "ignition_attachments": agent.match_ledger.ignition_attachments,
            "ignition_attacks": agent.match_ledger.ignition_attacks,
            "ignition_without_attack": agent.match_ledger.ignition_without_attack,
            "late_proton_without_gain": agent.match_ledger.late_proton_without_gain,
            "petrel_factory_opportunities": agent.match_ledger.petrel_factory_opportunities,
            "petrel_factory_conversions": agent.match_ledger.petrel_factory_conversions,
            "poke_pad_ko_opportunities": agent.match_ledger.poke_pad_ko_opportunities,
            "poke_pad_ko_conversions": agent.match_ledger.poke_pad_ko_conversions,
            "poke_pad_ko_misses": agent.match_ledger.poke_pad_ko_misses,
            "torment_with_superior_line": agent.match_ledger.torment_with_superior_line,
            "resource_guards": dict(
                Counter(event["resource_guard"] for event in events if event["resource_guard"])
            ),
            "decision_phase_reasons": dict(
                Counter(
                    event["decision_phase_reason"]
                    for event in events
                    if event["decision_phase_reason"]
                )
            ),
        },
        "events": events,
        "opportunities": opportunities,
    }


def run(
    matches_per_side: int,
    seed_base: int,
    policy_variant: str | None = None,
) -> dict[str, Any]:
    """Run both sides and aggregate all requested outcome and telemetry metrics."""
    matches = [
        _run_match(seed_base + index, side, policy_variant)
        for index in range(matches_per_side)
        for side in (0, 1)
    ]
    outcomes = Counter(match["result"] for match in matches)
    reasons = Counter(match["termination_reason"] for match in matches)
    failures = Counter(match["status"] for match in matches)
    telemetry: Counter[str] = Counter()
    guards: Counter[str] = Counter()
    opportunities: Counter[str] = Counter()
    for match in matches:
        opportunities.update(item["category"] for item in match["opportunities"])
        telemetry.update(
            {key: value for key, value in match["telemetry"].items() if isinstance(value, int)}
        )
        telemetry.update(
            {
                "observed_target_damage": sum(
                    int(event.get("transition", {}).get("target_damage", 0) or 0)
                    for event in match["events"]
                ),
                "observed_target_kos": sum(
                    bool(event.get("transition", {}).get("target_ko", False))
                    for event in match["events"]
                ),
                "own_active_kos_taken": sum(
                    bool(event.get("transition", {}).get("own_active_ko", False))
                    for event in match["events"]
                ),
            }
        )
        guards.update(match["telemetry"]["resource_guards"])
    losses = [match for match in matches if match["result"] == "loss"]
    audit = {
        "matches_with_explicit_reason": sum(
            match["termination_reason_explicit"] for match in matches
        ),
        "matches_with_consistent_reason": sum(
            match["termination_reason"] != "unknown"
            and match["termination_reason"] == match["termination_reason_inferred"]
            for match in matches
        ),
        "unresolved_terminal_reasons": sum(
            match["termination_reason"] == "unknown" for match in matches
        ),
        "losses": len(losses),
        "losses_by_reason": dict(Counter(match["termination_reason"] for match in losses)),
        "deck_out_losses": sum(
            match["result"] == "loss" and match["termination_reason"] == "deck_out"
            for match in matches
        ),
        "partial_attack_matches": sum(
            match["telemetry"]["partial_mega_abomasnow_attacks"] > 0 for match in matches
        ),
        "partial_attack_events": telemetry["partial_mega_abomasnow_attacks"],
    }
    return {
        "report_type": "honchkrow_porygon_cabt_200_with_telemetry",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sdk_version": "1.32.2",
        "agent": "honchkrow_porygon",
        "policy_variant": next(
            (match["policy_variant"] for match in matches),
            "baseline",
        ),
        "opponent": "cabt.random_agent",
        "matches_per_side": matches_per_side,
        "total_matches": len(matches),
        "seed_base": seed_base,
        "outcomes": dict(outcomes),
        "execution_status": dict(failures),
        "termination_reasons": dict(reasons),
        "telemetry_totals": dict(telemetry),
        "resource_guard_totals": dict(guards),
        "opportunity_audit": {
            "category_totals": dict(opportunities),
            "total": sum(opportunities.values()),
        },
        "audit": audit,
        "matches": matches,
    }


def run_stream(
    matches_per_side: int,
    seed_base: int,
    output: Path,
    policy_variant: str | None = None,
) -> dict[str, Any]:
    """Run matches while persisting each complete trace before continuing."""
    trace_path = output.with_suffix(output.suffix + ".jsonl")
    progress_path = output.with_suffix(output.suffix + ".progress.json")
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    total = matches_per_side * 2
    summaries: list[dict[str, Any]] = []
    outcomes: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    telemetry: Counter[str] = Counter()
    guards: Counter[str] = Counter()
    opportunities: Counter[str] = Counter()
    with trace_path.open("w", encoding="utf-8") as trace:
        for index in range(matches_per_side):
            for side in (0, 1):
                match = _run_match(seed_base + index, side, policy_variant)
                trace.write(json.dumps(match, sort_keys=True) + "\n")
                trace.flush()
                outcomes[match["result"]] += 1
                reasons[match["termination_reason"]] += 1
                statuses[match["status"]] += 1
                telemetry.update(
                    {
                        key: value
                        for key, value in match["telemetry"].items()
                        if isinstance(value, int)
                    }
                )
                telemetry.update(
                    {
                        "observed_target_damage": sum(
                            int(event.get("transition", {}).get("target_damage", 0) or 0)
                            for event in match["events"]
                        ),
                        "observed_target_kos": sum(
                            bool(event.get("transition", {}).get("target_ko", False))
                            for event in match["events"]
                        ),
                        "own_active_kos_taken": sum(
                            bool(event.get("transition", {}).get("own_active_ko", False))
                            for event in match["events"]
                        ),
                    }
                )
                guards.update(match["telemetry"]["resource_guards"])
                opportunities.update(item["category"] for item in match["opportunities"])
                summary = {key: value for key, value in match.items() if key != "events"}
                summary["event_count"] = len(match["events"])
                summaries.append(summary)
                completed = len(summaries)
                progress = {
                    "completed": completed,
                    "total": total,
                    "remaining": total - completed,
                    "outcomes": dict(outcomes),
                    "last_match_id": match["match_id"],
                }
                progress_path.write_text(
                    json.dumps(progress, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
    compressed_trace_path = output.with_suffix(".jsonl.gz")
    with (
        trace_path.open("rb") as source,
        gzip.open(compressed_trace_path, "wb", compresslevel=9) as target,
    ):
        shutil.copyfileobj(source, target)
    trace_path.unlink()
    losses = [match for match in summaries if match["result"] == "loss"]
    return {
        "report_type": "honchkrow_porygon_cabt_1000_fulltrace",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sdk_version": "1.32.2",
        "agent": "honchkrow_porygon",
        "policy_variant": next(
            (match["policy_variant"] for match in summaries),
            "supporter_resource_v2",
        ),
        "opponent": "cabt.random_agent",
        "matches_per_side": matches_per_side,
        "total_matches": total,
        "completed_matches": len(summaries),
        "seed_base": seed_base,
        "trace_compression": "gzip",
        "trace_jsonl": str(compressed_trace_path),
        "progress_json": str(progress_path),
        "outcomes": dict(outcomes),
        "execution_status": dict(statuses),
        "termination_reasons": dict(reasons),
        "telemetry_totals": dict(telemetry),
        "resource_guard_totals": dict(guards),
        "opportunity_audit": {
            "category_totals": dict(opportunities),
            "total": sum(opportunities.values()),
        },
        "audit": {
            "matches_with_explicit_reason": sum(
                match["termination_reason_explicit"] for match in summaries
            ),
            "unresolved_terminal_reasons": sum(
                match["termination_reason"] == "unknown" for match in summaries
            ),
            "losses": len(losses),
            "losses_by_reason": dict(Counter(match["termination_reason"] for match in losses)),
            "deck_out_losses": sum(
                match["result"] == "loss" and match["termination_reason"] == "deck_out"
                for match in summaries
            ),
            "partial_attack_matches": sum(
                match["telemetry"]["partial_mega_abomasnow_attacks"] > 0 for match in summaries
            ),
            "partial_attack_events": telemetry["partial_mega_abomasnow_attacks"],
        },
        "matches": summaries,
    }


def main() -> None:
    """Parse arguments, run CABT, and write a JSON report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--matches-per-side", type=int, default=100)
    parser.add_argument("--seed-base", type=int, default=20260807)
    parser.add_argument(
        "--policy-variant",
        choices=POLICY_VARIANTS,
        default="supporter_resource_v2",
        help="Honchkrow/Porygon policy variant to evaluate.",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_stream(
        args.matches_per_side,
        args.seed_base,
        args.output,
        args.policy_variant,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                key: report[key]
                for key in ("outcomes", "execution_status", "termination_reasons", "audit")
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
