"""Aggregate replay-derived damage, KO, resource, and loss diagnostics."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from src.data.replay_deep_analysis import DeepReplayAnalysis, FrameData
from src.data.replay_outcomes import extract_replay_outcome


@dataclass(slots=True)
class ReplayDiagnostic:
    """Decision-relevant summary for one fully parsed replay."""

    episode_id: int
    outcome: str
    total_turns: int
    owner_deck_min: int
    owner_prizes_start: int
    owner_prizes_end: int
    opponent_prizes_start: int
    opponent_prizes_end: int
    opponent_damage_observed: int
    owner_damage_taken: int
    owner_ko_count: int
    opponent_ko_count: int
    owner_action_count: int
    opponent_action_count: int
    owner_attack_count: int
    opponent_attack_count: int
    owner_retreat_count: int
    opponent_retreat_count: int
    owner_deck_reached_zero: bool
    owner_lost_by_deck_out: bool
    termination_reason: str
    reason_explicit: bool
    reason_consistent: bool
    result_consistent: bool
    damage_progression: list[int] = field(default_factory=list)
    loss_category: str = "NOT_A_LOSS"

    @property
    def attack_count(self) -> int:
        """Return owner attacks for compatibility with earlier reports."""
        return self.owner_attack_count

    @property
    def retreat_count(self) -> int:
        """Return owner retreats for compatibility with earlier reports."""
        return self.owner_retreat_count


def _active_hp(frame: FrameData, owner: bool) -> int:
    state = frame.owner_state if owner else frame.opponent_state
    return state.active[0].hp if state.active else 0


def _damage_progression(frames: list[FrameData], owner_index: int) -> tuple[list[int], int]:
    """Return opponent active HP trajectory and positive observed damage."""
    del owner_index
    values = [_active_hp(frame, False) for frame in frames]
    damage = sum(max(0, before - after) for before, after in zip(values, values[1:]))
    return values, damage


def _loss_category(
    analysis: DeepReplayAnalysis,
    *,
    termination_reason: str,
    opponent_damage: int,
    opponent_ko_count: int,
) -> str:
    """Classify a loss using only replay-visible facts."""
    if analysis.owner_outcome != "loss":
        return "NOT_A_LOSS"
    if (
        termination_reason == "no_pokemon_in_play"
        or not analysis.frames
        or (
            not analysis.frames[-1].owner_state.active and not analysis.frames[-1].owner_state.bench
        )
    ):
        return "BOARD_COLLAPSE"
    if termination_reason == "deck_out":
        return "DECK_OUT"
    if opponent_ko_count == 0 and opponent_damage > 0:
        return "DAMAGE_NOT_CONVERTED"
    if opponent_ko_count == 0:
        return "NO_OBSERVED_DAMAGE"
    return "PRIZE_RACE_LOSS"


def diagnose_replay(analysis: DeepReplayAnalysis) -> ReplayDiagnostic:
    """Build a diagnostic summary from a deep replay analysis."""
    frames = analysis.frames
    owner_states = [frame.owner_state for frame in frames]
    opponent_states = [frame.opponent_state for frame in frames]
    owner_deck_min = min((state.deck_count for state in owner_states), default=0)
    progression, opponent_damage = _damage_progression(frames, analysis.owner_index)
    owner_prizes = [state.prize_count for state in owner_states]
    opponent_prizes = [state.prize_count for state in opponent_states]
    owner_index = analysis.owner_index
    opponent_index = 1 - owner_index
    owner_damage = sum(
        max(0, -(event.value or 0))
        for event in analysis.events
        if event.event_type == "HpChange" and event.player_index == owner_index
    )
    opponent_damage = sum(
        max(0, -(event.value or 0))
        for event in analysis.events
        if event.event_type == "HpChange" and event.player_index == opponent_index
    )
    owner_ko_count = sum(
        event.event_type == "MoveCard"
        and event.player_index == opponent_index
        and event.area_from in {"4", "5"}
        and event.area_to == "3"
        for event in analysis.events
    )
    opponent_ko_count = sum(
        event.event_type == "MoveCard"
        and event.player_index == owner_index
        and event.area_from in {"4", "5"}
        and event.area_to == "3"
        for event in analysis.events
    )
    action_types = {"Play", "Attach", "Evolve", "Attack", "Switch", "Retreat"}
    try:
        outcome = extract_replay_outcome(
            analysis.source_path,
            owner_name=analysis.owner_name,
            owner_index=analysis.owner_index,
        )
    except ValueError:
        outcome = None
    termination_reason = outcome.termination_reason if outcome is not None else "unknown"
    reason_explicit = outcome.reason_explicit if outcome is not None else False
    reason_consistent = outcome.reason_consistent if outcome is not None else False
    result_consistent = bool(
        outcome is None
        or (
            outcome.owner_outcome == analysis.owner_outcome
            and outcome.winner_index == analysis.winner_index
        )
    )
    return ReplayDiagnostic(
        episode_id=analysis.episode_id,
        outcome=analysis.owner_outcome,
        total_turns=analysis.total_turns,
        owner_deck_min=owner_deck_min,
        owner_prizes_start=max(owner_prizes, default=0),
        owner_prizes_end=owner_prizes[-1] if owner_prizes else 0,
        opponent_prizes_start=max(opponent_prizes, default=0),
        opponent_prizes_end=opponent_prizes[-1] if opponent_prizes else 0,
        opponent_damage_observed=opponent_damage,
        owner_damage_taken=owner_damage,
        owner_ko_count=owner_ko_count,
        opponent_ko_count=opponent_ko_count,
        owner_action_count=sum(
            event.event_type in action_types and event.player_index == owner_index
            for event in analysis.events
        ),
        opponent_action_count=sum(
            event.event_type in action_types and event.player_index == opponent_index
            for event in analysis.events
        ),
        owner_attack_count=sum(
            event.event_type == "Attack" and event.player_index == owner_index
            for event in analysis.events
        ),
        opponent_attack_count=sum(
            event.event_type == "Attack" and event.player_index == opponent_index
            for event in analysis.events
        ),
        owner_retreat_count=sum(
            event.event_type in {"Switch", "Retreat"} and event.player_index == owner_index
            for event in analysis.events
        ),
        opponent_retreat_count=sum(
            event.event_type in {"Switch", "Retreat"} and event.player_index == opponent_index
            for event in analysis.events
        ),
        owner_deck_reached_zero=owner_deck_min == 0,
        owner_lost_by_deck_out=(
            analysis.owner_outcome == "loss" and termination_reason == "deck_out"
        ),
        termination_reason=termination_reason,
        reason_explicit=reason_explicit,
        reason_consistent=reason_consistent,
        result_consistent=result_consistent,
        damage_progression=progression,
        loss_category=_loss_category(
            analysis,
            termination_reason=termination_reason,
            opponent_damage=opponent_damage,
            opponent_ko_count=opponent_ko_count,
        ),
    )


def aggregate_replay_diagnostics(
    diagnostics: list[ReplayDiagnostic],
) -> dict[str, Any]:
    """Aggregate replay diagnostics into a stable report payload."""
    losses = [item for item in diagnostics if item.outcome == "loss"]
    return {
        "replays": len(diagnostics),
        "wins": sum(item.outcome == "win" for item in diagnostics),
        "draws": sum(item.outcome == "draw" for item in diagnostics),
        "losses": len(losses),
        "loss_categories": dict(Counter(item.loss_category for item in losses)),
        "owner_actions": sum(item.owner_action_count for item in diagnostics),
        "opponent_actions": sum(item.opponent_action_count for item in diagnostics),
        "owner_attacks": sum(item.owner_attack_count for item in diagnostics),
        "opponent_attacks": sum(item.opponent_attack_count for item in diagnostics),
        "owner_retreats": sum(item.owner_retreat_count for item in diagnostics),
        "opponent_retreats": sum(item.opponent_retreat_count for item in diagnostics),
        "total_observed_damage": sum(item.opponent_damage_observed for item in diagnostics),
        "total_owner_damage_taken": sum(item.owner_damage_taken for item in diagnostics),
        "total_owner_kos": sum(item.owner_ko_count for item in diagnostics),
        "total_opponent_kos": sum(item.opponent_ko_count for item in diagnostics),
        "owner_deck_reached_zero_replays": sum(
            item.owner_deck_reached_zero for item in diagnostics
        ),
        "deck_out_losses": sum(item.owner_lost_by_deck_out for item in losses),
        "explicit_terminal_reasons": sum(item.reason_explicit for item in diagnostics),
        "reconciled_results": sum(
            item.reason_consistent and item.result_consistent for item in diagnostics
        ),
    }
