"""Versioned, JSON-safe schemas for RFL traces and annotations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar


def _json_dict(value: Any) -> dict[str, Any]:
    """Return a JSON-compatible mapping for a schema object."""
    return asdict(value)


@dataclass(frozen=True, slots=True)
class FeatureSchema:
    """Describe the ordered features used by a promoted policy."""

    version: str = "v1"
    names: tuple[str, ...] = ()
    groups: dict[str, tuple[str, ...]] = field(default_factory=dict)
    kind: ClassVar[str] = "FeatureSchema"

    def to_dict(self) -> dict[str, Any]:
        """Serialize the schema with stable list values."""
        return {
            "kind": self.kind,
            "version": self.version,
            "names": list(self.names),
            "groups": {key: list(value) for key, value in self.groups.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeatureSchema:
        """Load and validate a feature schema mapping."""
        if data.get("kind", cls.kind) != cls.kind:
            raise ValueError("unsupported feature schema kind")
        return cls(
            str(data.get("version", "v1")),
            tuple(data.get("names", ())),
            {str(k): tuple(v) for k, v in dict(data.get("groups", {})).items()},
        )


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

    def to_dict(self) -> dict[str, Any]:
        """Serialize this trace."""
        return _json_dict(self)
