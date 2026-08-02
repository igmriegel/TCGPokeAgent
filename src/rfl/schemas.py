"""Versioned, JSON-safe schemas for RFL traces and annotations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from src.core.feature_schema import FeatureSchema

__all__ = ["DecisionTrace", "FeatureSchema"]


def _json_dict(value: Any) -> dict[str, Any]:
    """Return a JSON-compatible mapping for a schema object."""
    return asdict(value)


@dataclass(frozen=True, slots=True)
class DecisionTrace:
    """Capture one legal decision and its factual before/after context."""

    match_id: str
    decision_index: int
    deck_id: str
    deck_sha256: str
    matchup: str
    turn: int
    state_before: dict[str, Any]
    legal_options: list[dict[str, Any]]
    original_indices: list[int]
    selected_indices: list[int]
    agent_decision: list[int]
    teacher_decision: list[int] | None = None
    score: float | None = None
    reasons: list[str] = field(default_factory=list)
    reward: float = 0.0
    duration_ms: float = 0.0
    state_after: dict[str, Any] | None = None
    action_sequence: list[dict[str, Any]] = field(default_factory=list)
    feature_schema: str = "v1"
    schema_version: str = "v1"
    decision_phase: str = ""
    decision_phase_reason: str = ""
    ranked: list[dict[str, Any]] = field(default_factory=list)
    features: list[dict[str, Any]] = field(default_factory=list)
    fallback_used: bool = False
    model_backend: str = ""
    model_version: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize this trace."""
        return _json_dict(self)
