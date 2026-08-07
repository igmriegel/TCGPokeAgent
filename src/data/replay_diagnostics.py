"""Aggregate replay-derived damage, KO, resource, and loss diagnostics."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from src.data.replay_deep_analysis import DeepReplayAnalysis, FrameData


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
    opponent_ko_count: int
    attack_count: int
    retreat_count: int
    damage_progression: list[int] = field(default_factory=list)
    loss_category: str = "NOT_A_LOSS"


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
    owner_deck_min: int,
    opponent_damage: int,
    opponent_ko_count: int,
) -> str:
    """Classify a loss using only replay-visible facts."""
    if analysis.owner_outcome != "loss":
        return "NOT_A_LOSS"
    if not analysis.frames or (
        not analysis.frames[-1].owner_state.active and not analysis.frames[-1].owner_state.bench
    ):
        return "BOARD_COLLAPSE"
    if owner_deck_min == 0:
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
    opponent_ko_count = sum(
        bool(frame.opponent_state.active)
        and not bool(next_frame.opponent_state.active)
        and frame.opponent_state.prize_count > next_frame.opponent_state.prize_count
        for frame, next_frame in zip(frames, frames[1:])
    )
    owner_damage = sum(
        max(0, before - after)
        for before, after in zip(
            [_active_hp(frame, True) for frame in frames],
            [_active_hp(frame, True) for frame in frames][1:],
        )
    )
    attack_count = sum(event.event_type == "Attack" for event in analysis.events)
    retreat_count = sum(event.event_type in {"Switch", "Retreat"} for event in analysis.events)
    return ReplayDiagnostic(
        episode_id=analysis.episode_id,
        outcome=analysis.owner_outcome,
        total_turns=analysis.total_turns,
        owner_deck_min=owner_deck_min,
        owner_prizes_start=owner_prizes[0] if owner_prizes else 0,
        owner_prizes_end=owner_prizes[-1] if owner_prizes else 0,
        opponent_prizes_start=opponent_prizes[0] if opponent_prizes else 0,
        opponent_prizes_end=opponent_prizes[-1] if opponent_prizes else 0,
        opponent_damage_observed=opponent_damage,
        owner_damage_taken=owner_damage,
        opponent_ko_count=opponent_ko_count,
        attack_count=attack_count,
        retreat_count=retreat_count,
        damage_progression=progression,
        loss_category=_loss_category(
            analysis,
            owner_deck_min=owner_deck_min,
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
        "total_attacks": sum(item.attack_count for item in diagnostics),
        "total_retreats": sum(item.retreat_count for item in diagnostics),
        "total_observed_damage": sum(item.opponent_damage_observed for item in diagnostics),
        "total_opponent_kos": sum(item.opponent_ko_count for item in diagnostics),
        "deck_out_replays": sum(item.owner_deck_min == 0 for item in losses),
    }
