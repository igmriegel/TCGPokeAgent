"""Versioned contract for ordered numeric policy features."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar


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
            {str(key): tuple(value) for key, value in dict(data.get("groups", {})).items()},
        )
