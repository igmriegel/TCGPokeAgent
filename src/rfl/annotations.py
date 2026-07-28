"""Expert annotation schema and append-only JSONL persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class ExpertAnnotation:
    """A human ranking of legal plays for a turn."""

    deck_id: str
    deck_sha256: str
    matchup: str
    match_id: str
    turn: int
    preferred_actions: list[int]
    rejected_actions: list[list[int]] = field(default_factory=list)
    acceptable_actions: list[list[int]] = field(default_factory=list)
    justification: str = ""
    confidence: float = 0.0
    specialist_version: str = "unknown"
    schema_version: str = "v1"

    def validate_against(self, legal_options: Iterable[int]) -> None:
        """Reject annotations containing an option absent from the trace."""
        legal = set(legal_options)
        plays = [self.preferred_actions, *self.rejected_actions, *self.acceptable_actions]
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("annotation confidence must be between 0 and 1")
        if any(index not in legal for play in plays for index in play):
            raise ValueError("annotation contains an illegal option index")

    def to_dict(self) -> dict[str, Any]:
        """Serialize this annotation."""
        return {
            "kind": "ExpertAnnotation",
            "schema_version": self.schema_version,
            "deck_id": self.deck_id,
            "deck_sha256": self.deck_sha256,
            "matchup": self.matchup,
            "match_id": self.match_id,
            "turn": self.turn,
            "preferred_actions": self.preferred_actions,
            "rejected_actions": self.rejected_actions,
            "acceptable_actions": self.acceptable_actions,
            "justification": self.justification,
            "confidence": self.confidence,
            "specialist_version": self.specialist_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExpertAnnotation:
        """Deserialize an annotation."""
        return cls(
            deck_id=str(data["deck_id"]),
            deck_sha256=str(data["deck_sha256"]),
            matchup=str(data["matchup"]),
            match_id=str(data["match_id"]),
            turn=int(data["turn"]),
            preferred_actions=list(data["preferred_actions"]),
            rejected_actions=[list(x) for x in data.get("rejected_actions", [])],
            acceptable_actions=[list(x) for x in data.get("acceptable_actions", [])],
            justification=str(data.get("justification", "")),
            confidence=float(data.get("confidence", 0.0)),
            specialist_version=str(data.get("specialist_version", "unknown")),
            schema_version=str(data.get("schema_version", "v1")),
        )


class AnnotationStore:
    """Append and read versioned expert annotations from JSONL."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, annotation: ExpertAnnotation, legal_options: Iterable[int]) -> None:
        """Validate and append an annotation atomically enough for JSONL use."""
        annotation.validate_against(legal_options)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(annotation.to_dict(), sort_keys=True) + "\n")

    def read(self) -> list[ExpertAnnotation]:
        """Read all non-empty annotation records."""
        if not self.path.exists():
            return []
        return [
            ExpertAnnotation.from_dict(json.loads(line))
            for line in self.path.read_text().splitlines()
            if line.strip()
        ]
