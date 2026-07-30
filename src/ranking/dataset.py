"""Grouped learning-to-rank datasets with match/deck leakage barriers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, Mapping, Sequence, cast

from src.core import SelectionFeatures
from src.rfl.feedback import FeedbackEventV2

GroupSource = Literal["expert", "behavior", "regression", "holdout"]


@dataclass(frozen=True, slots=True)
class RankingRow:
    """One evaluated alternative within a decision query group."""

    decision_id: str
    selection: tuple[int, ...]
    relevance: int
    weight: float
    features: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class RankGroup:
    """A complete supervised query group linked to one match and deck."""

    decision_id: str
    match_id: str
    deck_id: str
    timestamp: str
    source: GroupSource
    rows: tuple[RankingRow, ...]

    def validate(self) -> None:
        """Validate grouping, relevance, and source weight contracts."""
        if len(self.rows) < 2:
            raise ValueError("ranking group requires at least two evaluated alternatives")
        if any(row.decision_id != self.decision_id for row in self.rows):
            raise ValueError("ranking row qid differs from its decision group")
        if len({row.selection for row in self.rows}) != len(self.rows):
            raise ValueError("ranking group contains duplicate selections")
        if any(row.relevance not in {0, 1, 2, 3} for row in self.rows):
            raise ValueError("unsupported ranking relevance")
        if self.source == "behavior" and any(row.weight > 0.2 for row in self.rows):
            raise ValueError("behavior weight exceeds 20% of a human preference")


@dataclass(frozen=True, slots=True)
class GroupedRankingDataset:
    """Backend-neutral matrices and group identifiers in deterministic order."""

    groups: tuple[RankGroup, ...]

    def __post_init__(self) -> None:
        for group in self.groups:
            group.validate()

    @property
    def rows(self) -> tuple[RankingRow, ...]:
        """Return rows flattened without changing query contiguity."""
        return tuple(row for group in self.groups for row in group.rows)

    @property
    def values(self) -> list[list[float]]:
        """Return the shared feature matrix."""
        return [list(row.features) for row in self.rows]

    @property
    def labels(self) -> list[int]:
        """Return integer relevance labels."""
        return [row.relevance for row in self.rows]

    @property
    def weights(self) -> list[float]:
        """Return per-row confidence/source weights."""
        return [row.weight for row in self.rows]

    @property
    def qids(self) -> list[str]:
        """Return one query identifier per row for XGBoost."""
        return [group.decision_id for group in self.groups for _ in group.rows]

    @property
    def group_sizes(self) -> list[int]:
        """Return contiguous query sizes for LightGBM."""
        return [len(group.rows) for group in self.groups]


def expert_group(
    event: FeedbackEventV2,
    feature_rows: Sequence[SelectionFeatures],
    *,
    timestamp: str | None = None,
) -> RankGroup:
    """Build a group using only alternatives explicitly evaluated by a human.

    Args:
        event: Validated immutable human feedback.
        feature_rows: All legal feature rows for the same decision.
        timestamp: Optional split timestamp override.

    Returns:
        Supervised expert group with relevance 3, 2, and 0.
    """
    event.validate()
    by_selection = {row.selection.indices: row for row in feature_rows}
    labels = {
        **{selection: 3 for selection in event.preferred},
        **{selection: 2 for selection in event.acceptable},
        **{selection: 0 for selection in event.rejected},
    }
    rows = tuple(
        RankingRow(
            decision_id=event.decision_id,
            selection=selection,
            relevance=relevance,
            weight=event.confidence,
            features=by_selection[selection].values,
        )
        for selection, relevance in sorted(labels.items())
        if selection in by_selection
    )
    group = RankGroup(
        decision_id=event.decision_id,
        match_id=event.match_id,
        deck_id=event.deck_id,
        timestamp=timestamp or event.created_at,
        source="expert",
        rows=rows,
    )
    group.validate()
    return group


def behavior_group(
    *,
    decision_id: str,
    match_id: str,
    deck_id: str,
    timestamp: str,
    observed: tuple[int, ...],
    compared: Sequence[tuple[int, ...]],
    feature_rows: Sequence[SelectionFeatures],
    confidence: float,
) -> RankGroup:
    """Build a low-weight behavioral comparison without claiming optimality.

    Args:
        decision_id: Stable decision query identifier.
        match_id: Source replay match.
        deck_id: Source own-deck identifier.
        timestamp: Source match time for temporal splitting.
        observed: Action recorded in the trusted replay.
        compared: Explicit alternatives admitted by confidence filtering.
        feature_rows: Shared features for legal selections.
        confidence: Behavioral record confidence.

    Returns:
        Behavioral query group capped at 20% human weight.
    """
    if not 0.0 < confidence <= 1.0:
        raise ValueError("behavior confidence must be in (0, 1]")
    by_selection = {row.selection.indices: row for row in feature_rows}
    selections = [observed, *compared]
    if any(selection not in by_selection for selection in selections):
        raise ValueError("behavior group references a selection without features")
    weight = min(0.2, confidence * 0.2)
    rows = tuple(
        RankingRow(
            decision_id,
            selection,
            1 if selection == observed else 0,
            weight,
            by_selection[selection].values,
        )
        for selection in selections
    )
    group = RankGroup(decision_id, match_id, deck_id, timestamp, "behavior", rows)
    group.validate()
    return group


def split_rank_groups(
    groups: Iterable[RankGroup],
    *,
    holdout_decks: Iterable[str] = (),
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
) -> dict[str, GroupedRankingDataset]:
    """Split whole matches temporally and reserve complete holdout decks.

    Args:
        groups: Complete ranking groups.
        holdout_decks: Deck identifiers never admitted to training or validation.
        train_fraction: Fraction of non-holdout matches assigned to training.
        validation_fraction: Fraction assigned to validation.

    Returns:
        Train, validation, and holdout grouped datasets.
    """
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be in (0, 1)")
    if not 0.0 <= validation_fraction < 1.0:
        raise ValueError("validation_fraction must be in [0, 1)")
    if train_fraction + validation_fraction >= 1.0:
        raise ValueError("split fractions must leave a temporal holdout")
    all_groups = sorted(groups, key=lambda item: (item.timestamp, item.match_id, item.decision_id))
    by_match: dict[str, list[RankGroup]] = {}
    for group in all_groups:
        group.validate()
        by_match.setdefault(group.match_id, []).append(group)
    reserved_decks = set(holdout_decks)
    reserved_matches = {
        match_id
        for match_id, items in by_match.items()
        if any(item.deck_id in reserved_decks or item.source == "holdout" for item in items)
    }
    eligible_matches = [
        match_id
        for match_id in sorted(
            set(by_match) - reserved_matches,
            key=lambda item: (min(group.timestamp for group in by_match[item]), item),
        )
    ]
    train_end = int(len(eligible_matches) * train_fraction)
    validation_end = train_end + int(len(eligible_matches) * validation_fraction)
    memberships = {
        "train": set(eligible_matches[:train_end]),
        "validation": set(eligible_matches[train_end:validation_end]),
        "holdout": set(eligible_matches[validation_end:]) | reserved_matches,
    }
    _validate_split_membership(memberships, by_match)
    return {
        split: GroupedRankingDataset(
            tuple(group for group in all_groups if group.match_id in match_ids)
        )
        for split, match_ids in memberships.items()
    }


def write_grouped_dataset(dataset: GroupedRankingDataset, path: str | Path) -> Path:
    """Persist a backend-neutral grouped dataset as deterministic JSONL.

    Args:
        dataset: Grouped rows to persist.
        path: Destination JSONL file.

    Returns:
        Written path.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for group in dataset.groups:
        records.append(
            {
                "decision_id": group.decision_id,
                "match_id": group.match_id,
                "deck_id": group.deck_id,
                "timestamp": group.timestamp,
                "source": group.source,
                "rows": [
                    {
                        "selection": list(row.selection),
                        "relevance": row.relevance,
                        "weight": row.weight,
                        "features": list(row.features),
                    }
                    for row in group.rows
                ],
            }
        )
    destination.write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in records),
        encoding="utf-8",
    )
    return destination


def read_grouped_dataset(path: str | Path) -> GroupedRankingDataset:
    """Load and validate a backend-neutral grouped JSONL dataset.

    Args:
        path: Source JSONL file.

    Returns:
        Validated grouped ranking dataset.
    """
    source = Path(path)
    groups = []
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        decision_id = str(data["decision_id"])
        groups.append(
            RankGroup(
                decision_id=decision_id,
                match_id=str(data["match_id"]),
                deck_id=str(data["deck_id"]),
                timestamp=str(data["timestamp"]),
                source=cast(GroupSource, str(data["source"])),
                rows=tuple(
                    RankingRow(
                        decision_id=decision_id,
                        selection=tuple(int(index) for index in row["selection"]),
                        relevance=int(row["relevance"]),
                        weight=float(row["weight"]),
                        features=tuple(float(value) for value in row["features"]),
                    )
                    for row in data["rows"]
                ),
            )
        )
    return GroupedRankingDataset(tuple(groups))


def _validate_split_membership(
    memberships: Mapping[str, set[str]], by_match: Mapping[str, Sequence[RankGroup]]
) -> None:
    seen: set[str] = set()
    for match_ids in memberships.values():
        overlap = seen.intersection(match_ids)
        if overlap:
            raise ValueError(f"match leakage across ranking splits: {sorted(overlap)}")
        seen.update(match_ids)
    if seen != set(by_match):
        raise ValueError("ranking split omitted one or more matches")
