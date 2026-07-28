"""Leak-free hybrid preference dataset construction."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .annotations import ExpertAnnotation
from .rewards import combine_signals
from .schemas import DecisionTrace


class TraceStore:
    """Persist complete decision traces as one JSONL record per decision."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def write(self, traces: Iterable[DecisionTrace], split: str) -> Path:
        """Write traces to ``train``, ``validation`` or ``holdout``."""
        if split not in {"train", "validation", "holdout"}:
            raise ValueError("unknown dataset split")
        path = self.root / split / "traces.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(trace.to_dict(), sort_keys=True) + "\n" for trace in traces)
        )
        return path


@dataclass(frozen=True, slots=True)
class HybridExample:
    """One preference example linked to exactly one match."""

    match_id: str
    preferred: list[int]
    alternative: list[int]
    expert_signal: float = 0.0
    teacher_signal: float = 0.0
    outcome_signal: float = 0.0

    @property
    def label(self) -> float:
        """Return the weighted preference label."""
        return combine_signals(self.expert_signal, self.teacher_signal, self.outcome_signal)


@dataclass(slots=True)
class HybridDataset:
    """In-memory examples with optional trace and annotation provenance."""

    examples: list[HybridExample] = field(default_factory=list)
    match_ids: set[str] = field(default_factory=set)

    @classmethod
    def from_traces(
        cls, traces: Iterable[DecisionTrace], annotations: Iterable[ExpertAnnotation] = ()
    ) -> HybridDataset:
        """Build preferences while keeping expert feedback ahead of teacher signals."""
        by_key = {(item.match_id, item.turn): item for item in annotations}
        dataset = cls()
        for trace in traces:
            dataset.match_ids.add(trace.match_id)
            annotation = by_key.get((trace.match_id, trace.turn))
            preferred = annotation.preferred_actions if annotation else trace.agent_decision
            alternatives = (
                annotation.rejected_actions
                if annotation
                else ([trace.teacher_decision] if trace.teacher_decision else [])
            )
            for alternative in alternatives:
                if alternative and alternative != preferred:
                    dataset.examples.append(
                        HybridExample(
                            trace.match_id,
                            preferred,
                            alternative,
                            expert_signal=1.0 if annotation else 0.0,
                            teacher_signal=1.0 if trace.teacher_decision else 0.0,
                            outcome_signal=trace.reward,
                        )
                    )
        return dataset


def partition_traces(
    traces: Iterable[DecisionTrace], splits: dict[str, set[str]], root: str | Path
) -> dict[str, Path]:
    """Write complete-match partitions and reject overlapping split membership."""
    all_traces = list(traces)
    seen: set[str] = set()
    result: dict[str, Path] = {}
    for split, match_ids in splits.items():
        overlap = seen.intersection(match_ids)
        if overlap:
            raise ValueError(f"match leakage across splits: {sorted(overlap)}")
        seen.update(match_ids)
        result[split] = TraceStore(root).write(
            (trace for trace in all_traces if trace.match_id in match_ids), split
        )
    return result


def split_matches(
    match_ids: Iterable[str], *, train_fraction: float = 0.70, validation_fraction: float = 0.15
) -> dict[str, set[str]]:
    """Split whole matches deterministically so no match leaks between sets."""
    ids = sorted(set(match_ids))
    if not 0.0 < train_fraction < 1.0 or not 0.0 <= validation_fraction < 1.0:
        raise ValueError("invalid split fractions")
    if train_fraction + validation_fraction >= 1.0:
        raise ValueError("train and validation fractions must leave holdout")
    train_end = int(len(ids) * train_fraction)
    validation_end = train_end + int(len(ids) * validation_fraction)
    return {
        "train": set(ids[:train_end]),
        "validation": set(ids[train_end:validation_end]),
        "holdout": set(ids[validation_end:]),
    }
