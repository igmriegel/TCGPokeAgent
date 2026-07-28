"""Reward shaping for match and decision-level RFL signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class RewardBreakdown:
    """Auditable components of a shaped episode reward."""

    outcome: float = 0.0
    prizes: float = 0.0
    ko: float = 0.0
    preparation: float = 0.0
    resource_loss: float = 0.0
    illegal: float = 0.0
    operational_failure: float = 0.0
    duration: float = 0.0

    @property
    def total(self) -> float:
        """Return the sum of all reward components."""
        return sum(
            (
                self.outcome,
                self.prizes,
                self.ko,
                self.preparation,
                self.resource_loss,
                self.illegal,
                self.operational_failure,
                self.duration,
            )
        )


def _number(data: Mapping[str, Any], *names: str) -> float:
    for name in names:
        value = data.get(name)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return 0.0


def hybrid_reward(
    result: str | None = None,
    *,
    before: Mapping[str, Any] | None = None,
    after: Mapping[str, Any] | None = None,
    illegal: bool = False,
    operational_failure: bool = False,
    duration_ms: float = 0.0,
    duration_budget_ms: float = 100.0,
) -> RewardBreakdown:
    """Compute deterministic outcome and turn shaping signals.

    The function accepts flat state snapshots, making it useful both for traces and
    for lightweight tests without requiring a simulator dependency.
    """
    old, new = before or {}, after or {}
    outcome = {"win": 1.0, "loss": -1.0, "draw": 0.0}.get(str(result).lower(), 0.0)
    prizes = _number(old, "prizes_remaining", "prize_count") - _number(
        new, "prizes_remaining", "prize_count"
    )
    ko = max(0.0, _number(old, "opponent_hp") - _number(new, "opponent_hp")) / 100.0
    preparation = max(0.0, _number(new, "attack_ready") - _number(old, "attack_ready"))
    resource_loss = min(0.0, _number(new, "resources") - _number(old, "resources"))
    return RewardBreakdown(
        outcome=outcome,
        prizes=prizes,
        ko=ko,
        preparation=preparation,
        resource_loss=resource_loss,
        illegal=-2.0 if illegal else 0.0,
        operational_failure=-2.0 if operational_failure else 0.0,
        duration=-0.1 if duration_ms > duration_budget_ms else 0.0,
    )


def combine_signals(
    expert: float,
    teacher: float,
    outcome: float,
    *,
    expert_weight: float = 0.60,
    teacher_weight: float = 0.25,
    outcome_weight: float = 0.15,
) -> float:
    """Combine the three RFL signals, with expert feedback taking precedence."""
    if expert != 0.0:
        return expert_weight * expert + teacher_weight * teacher + outcome_weight * outcome
    return teacher_weight * teacher + outcome_weight * outcome
