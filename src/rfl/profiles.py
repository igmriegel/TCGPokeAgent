"""Deck-bound promoted heuristic profiles with safe fallback behavior."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from src.agents.heuristic import WEIGHTS, HeuristicAgent


class ProfileCompatibilityError(ValueError):
    """Raised when a promoted profile cannot be used by the active deck."""


@dataclass(frozen=True, slots=True)
class PolicyProfile:
    """Validated weights and metadata for one deck/matchup."""

    deck_id: str
    deck_path: str
    deck_sha256: str
    version: str
    feature_schema: str
    weights: dict[str, float]
    matchup: str | None = None
    feature_flags: dict[str, bool] = field(default_factory=dict)

    def validate(
        self,
        active_deck_id: str | None = None,
        active_deck_path: str | Path | None = None,
        feature_schema: str = "v1",
    ) -> None:
        """Validate identity, hash, schema, known weights, and finite values."""
        if active_deck_id is not None and self.deck_id != active_deck_id:
            raise ProfileCompatibilityError("profile deck id does not match active deck")
        if self.feature_schema != feature_schema:
            raise ProfileCompatibilityError("profile feature schema is incompatible")
        if active_deck_path is not None:
            actual = hashlib.sha256(Path(active_deck_path).read_bytes()).hexdigest()
            if actual != self.deck_sha256:
                raise ProfileCompatibilityError("profile deck hash does not match active deck")
        if set(self.weights) - set(WEIGHTS) or any(
            not math.isfinite(v) for v in self.weights.values()
        ):
            raise ProfileCompatibilityError("profile contains unknown or non-finite weights")
        if self.weights.get("win_now", WEIGHTS["win_now"]) < max(
            self.weights.get(name, value) for name, value in WEIGHTS.items() if name != "win_now"
        ):
            raise ProfileCompatibilityError("win_now must dominate all other weights")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the profile in the documented YAML shape."""
        return {
            "deck": {"id": self.deck_id, "path": self.deck_path, "sha256": self.deck_sha256},
            "policy": {
                "kind": "heuristic",
                "version": self.version,
                "feature_schema": self.feature_schema,
            },
            "weights": self.weights,
            "feature_flags": self.feature_flags,
            **({"matchup": self.matchup} if self.matchup else {}),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PolicyProfile:
        """Parse the documented profile mapping."""
        deck, policy = dict(data.get("deck", {})), dict(data.get("policy", {}))
        return cls(
            str(deck.get("id", "")),
            str(deck.get("path", "")),
            str(deck.get("sha256", "")),
            str(policy.get("version", "")),
            str(policy.get("feature_schema", "v1")),
            {str(k): float(v) for k, v in dict(data.get("weights", {})).items()},
            str(data["matchup"]) if data.get("matchup") else None,
            {str(k): bool(v) for k, v in dict(data.get("feature_flags", {})).items()},
        )


def load_profile(
    path: str | Path,
    *,
    active_deck_id: str | None = None,
    active_deck_path: str | Path | None = None,
    feature_schema: str = "v1",
) -> PolicyProfile | None:
    """Load a compatible profile, returning ``None`` for absent/corrupt profiles."""
    try:
        profile = PolicyProfile.from_dict(yaml.safe_load(Path(path).read_text()) or {})
        profile.validate(active_deck_id, active_deck_path, feature_schema)
        return profile
    except (OSError, ValueError, TypeError, yaml.YAMLError):
        return None


def agent_from_profile(
    path: str | Path, *, active_deck_id: str, active_deck_path: str | Path
) -> HeuristicAgent:
    """Construct a heuristic agent, falling back to baseline weights on failure."""
    profile = load_profile(path, active_deck_id=active_deck_id, active_deck_path=active_deck_path)
    return HeuristicAgent(profile.weights, profile.feature_flags) if profile else HeuristicAgent()
