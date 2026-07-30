"""Immutable feedback evidence, insight lifecycle, and active-review ordering."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Iterable, Mapping, Sequence


class InsightStatus(str, Enum):
    """Allowed lifecycle states for an aggregated gameplay hypothesis."""

    CANDIDATE = "CANDIDATE"
    TRIAGED = "TRIAGED"
    EXPERIMENT_READY = "EXPERIMENT_READY"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True, slots=True)
class FeedbackEventV2:
    """Immutable human evidence tied to one actor-visible legal decision."""

    feedback_id: str
    origin: str
    reviewer: str
    replay_id: str
    replay_sha256: str
    match_id: str
    deck_id: str
    decision_id: str
    visible_state: dict[str, Any]
    legal_options: tuple[dict[str, Any], ...]
    actual_selection: tuple[int, ...]
    preferred: tuple[tuple[int, ...], ...] = ()
    acceptable: tuple[tuple[int, ...], ...] = ()
    rejected: tuple[tuple[int, ...], ...] = ()
    justification: str = ""
    confidence: float = 0.0
    tags: tuple[str, ...] = ()
    lineage: tuple[str, ...] = ()
    created_at: str = ""
    schema_version: str = "feedback-event-v2"

    def validate(self) -> None:
        """Validate identity, confidence, and original simulator indices."""
        if not self.feedback_id or not self.decision_id or not self.match_id:
            raise ValueError("feedback identity fields cannot be empty")
        if not self.reviewer or not self.origin:
            raise ValueError("feedback origin and reviewer cannot be empty")
        if not self.justification.strip():
            raise ValueError("feedback justification must be written in English")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("feedback confidence must be between 0 and 1")
        legal = set(range(len(self.legal_options)))
        selections = (
            self.actual_selection,
            *self.preferred,
            *self.acceptable,
            *self.rejected,
        )
        if any(len(selection) != len(set(selection)) for selection in selections):
            raise ValueError("feedback selection contains duplicate indices")
        if any(index not in legal for selection in selections for index in selection):
            raise ValueError("feedback selection contains an illegal simulator index")
        supervised = [*self.preferred, *self.acceptable, *self.rejected]
        if len(supervised) != len(set(supervised)):
            raise ValueError("feedback relevance classes overlap")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the immutable evidence to JSON-compatible values."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> FeedbackEventV2:
        """Deserialize and validate immutable feedback evidence."""
        event = cls(
            feedback_id=str(data["feedback_id"]),
            origin=str(data["origin"]),
            reviewer=str(data["reviewer"]),
            replay_id=str(data["replay_id"]),
            replay_sha256=str(data["replay_sha256"]),
            match_id=str(data["match_id"]),
            deck_id=str(data["deck_id"]),
            decision_id=str(data["decision_id"]),
            visible_state=dict(data["visible_state"]),
            legal_options=tuple(dict(item) for item in data["legal_options"]),
            actual_selection=tuple(int(item) for item in data["actual_selection"]),
            preferred=_selections(data.get("preferred", ())),
            acceptable=_selections(data.get("acceptable", ())),
            rejected=_selections(data.get("rejected", ())),
            justification=str(data.get("justification", "")),
            confidence=float(data.get("confidence", 0.0)),
            tags=tuple(str(item) for item in data.get("tags", ())),
            lineage=tuple(str(item) for item in data.get("lineage", ())),
            created_at=str(data.get("created_at", "")),
            schema_version=str(data.get("schema_version", "feedback-event-v2")),
        )
        event.validate()
        return event


@dataclass(frozen=True, slots=True)
class InsightRecord:
    """Aggregated hypothesis that cannot become a rule without frozen evidence."""

    insight_id: str
    scope: str
    status: InsightStatus
    feedback_ids: tuple[str, ...]
    counterexamples: tuple[str, ...] = ()
    rule: str = ""
    task_id: str = ""
    metric: str = ""
    fixture: str = ""
    experiment: str = ""
    decision: str = ""
    supersedes: str | None = None
    schema_version: str = "insight-record-v1"

    _TRANSITIONS: ClassVar[dict[InsightStatus, set[InsightStatus]]] = {
        InsightStatus.CANDIDATE: {InsightStatus.TRIAGED, InsightStatus.REJECTED},
        InsightStatus.TRIAGED: {
            InsightStatus.EXPERIMENT_READY,
            InsightStatus.REJECTED,
            InsightStatus.SUPERSEDED,
        },
        InsightStatus.EXPERIMENT_READY: {
            InsightStatus.VALIDATED,
            InsightStatus.REJECTED,
            InsightStatus.SUPERSEDED,
        },
        InsightStatus.VALIDATED: {InsightStatus.SUPERSEDED},
        InsightStatus.REJECTED: {InsightStatus.SUPERSEDED},
        InsightStatus.SUPERSEDED: set(),
    }

    def validate(self) -> None:
        """Validate lifecycle evidence requirements."""
        if not self.insight_id or not self.scope or not self.feedback_ids:
            raise ValueError("insight identity, scope, and feedback evidence are required")
        if self.status is InsightStatus.VALIDATED and (
            not self.fixture or not self.experiment or not self.metric
        ):
            raise ValueError("validated insight requires fixture, experiment, and metric")
        if self.status is InsightStatus.SUPERSEDED and not self.supersedes:
            raise ValueError("superseded insight must identify its replacement")

    def to_dict(self) -> dict[str, Any]:
        """Serialize this insight to JSON-compatible values."""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    def transition(self, status: InsightStatus, **changes: Any) -> InsightRecord:
        """Create the next immutable lifecycle record.

        Args:
            status: Allowed next lifecycle state.
            **changes: Evidence fields supplied at the transition.

        Returns:
            Validated replacement record.
        """
        if status not in self._TRANSITIONS[self.status]:
            raise ValueError(f"invalid insight transition: {self.status.value} -> {status.value}")
        updated = replace(self, status=status, **changes)
        updated.validate()
        return updated

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> InsightRecord:
        """Deserialize and validate one insight."""
        record = cls(
            insight_id=str(data["insight_id"]),
            scope=str(data["scope"]),
            status=InsightStatus(str(data["status"])),
            feedback_ids=tuple(str(item) for item in data["feedback_ids"]),
            counterexamples=tuple(str(item) for item in data.get("counterexamples", ())),
            rule=str(data.get("rule", "")),
            task_id=str(data.get("task_id", "")),
            metric=str(data.get("metric", "")),
            fixture=str(data.get("fixture", "")),
            experiment=str(data.get("experiment", "")),
            decision=str(data.get("decision", "")),
            supersedes=(str(data["supersedes"]) if data.get("supersedes") is not None else None),
            schema_version=str(data.get("schema_version", "insight-record-v1")),
        )
        record.validate()
        return record


class FeedbackStoreV2:
    """Append unique immutable feedback and insight JSONL records."""

    def __init__(self, path: str | Path, record_type: type[FeedbackEventV2]) -> None:
        self.path = Path(path)
        self.record_type = record_type

    def append(self, event: FeedbackEventV2) -> None:
        """Validate and append one unique event."""
        event.validate()
        if any(item.feedback_id == event.feedback_id for item in self.read()):
            raise ValueError(f"feedback already exists: {event.feedback_id}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")

    def read(self) -> list[FeedbackEventV2]:
        """Read all immutable feedback events."""
        if not self.path.is_file():
            return []
        return [
            self.record_type.from_dict(json.loads(line))
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


@dataclass(frozen=True, slots=True)
class ReviewCandidate:
    """Signals used to prioritize one decision for human review."""

    decision_id: str
    outcome: str
    operational_failure: bool = False
    board_collapse: bool = False
    policy_divergence: bool = False
    top_margin: float = float("inf")
    ranker_choices: tuple[tuple[str, tuple[int, ...]], ...] = ()
    rare_context: bool = False


def prioritize_review_queue(
    candidates: Iterable[ReviewCandidate], *, low_margin: float = 1.0
) -> list[ReviewCandidate]:
    """Order review candidates by the frozen active-review policy.

    Args:
        candidates: Candidate decisions with precomputed factual signals.
        low_margin: Inclusive top-one versus top-two margin threshold.

    Returns:
        Deterministically ordered candidates.
    """

    def priority(item: ReviewCandidate) -> tuple[int, float, str]:
        choices = {selection for _, selection in item.ranker_choices}
        if item.operational_failure or item.board_collapse:
            tier = 0
        elif item.outcome == "loss" and item.policy_divergence:
            tier = 1
        elif item.top_margin <= low_margin:
            tier = 2
        elif len(choices) >= 3:
            tier = 3
        elif item.rare_context:
            tier = 4
        else:
            tier = 5
        return tier, item.top_margin, item.decision_id

    return sorted(candidates, key=priority)


def _selections(value: Any) -> tuple[tuple[int, ...], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("feedback selections must be a sequence")
    return tuple(tuple(int(index) for index in selection) for selection in value)
