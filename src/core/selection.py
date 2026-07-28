from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .candidate import Candidate
from .exceptions import LegalityViolationError
from .types import OptionType, SelectContext


@dataclass(frozen=True, slots=True)
class Selection:
    indices: tuple[int, ...]
    option_types: tuple[OptionType, ...]
    context: SelectContext | None = None
    score: float | None = None
    reasons: tuple[str, ...] = ()

    def to_debug_string(self) -> str:
        parts = [
            f"indices={self.indices}",
            f"option_types={[t.value for t in self.option_types]}",
        ]
        if self.context is not None:
            parts.append(f"context={self.context.value}")
        if self.score is not None:
            parts.append(f"score={self.score:.4f}")
        if self.reasons:
            parts.append(f"reasons={self.reasons}")
        return "Selection(" + ", ".join(parts) + ")"


class SelectionValidator:
    """Validate a selection against one parsed decision's legal constraints."""

    def validate(
        self,
        selection: Selection,
        candidates: Sequence[Candidate],
        min_count: int,
        max_count: int,
        remain_energy_cost: int = 0,
        remain_damage_counter: int = 0,
    ) -> None:
        """Raise when ``selection`` is not legal for the supplied decision.

        Args:
            selection: Selection to validate.
            candidates: Options available in the active decision.
            min_count: Minimum number of options required.
            max_count: Maximum number of options allowed.
            remain_energy_cost: Minimum energy count that must be selected.
            remain_damage_counter: Minimum damage-counter count that must be selected.

        Raises:
            LegalityViolationError: If any legality constraint is violated.
        """
        if min_count < 0 or max_count < min_count:
            raise LegalityViolationError("selection bounds are invalid")
        if len(selection.indices) != len(selection.option_types):
            raise LegalityViolationError("selection indices and option types differ")
        if len(selection.indices) < min_count or len(selection.indices) > max_count:
            raise LegalityViolationError("selection cardinality is outside decision bounds")
        if len(selection.indices) != len(set(selection.indices)):
            raise LegalityViolationError("selection contains duplicate option indices")

        by_index = {candidate.option_index: candidate for candidate in candidates}
        selected = []
        for index, option_type in zip(selection.indices, selection.option_types):
            candidate = by_index.get(index)
            if candidate is None:
                raise LegalityViolationError(f"unknown option index: {index}")
            if candidate.option_type is not option_type:
                raise LegalityViolationError(f"option type mismatch for index: {index}")
            selected.append(candidate)

        self._validate_count(selected, remain_energy_cost, "energy")
        self._validate_count(selected, remain_damage_counter, "damage")

    def _validate_count(
        self, candidates: Sequence[Candidate], required: int, label: str
    ) -> None:
        if required <= 0:
            return
        total = sum(self._option_count(candidate.option) for candidate in candidates)
        if total < required:
            raise LegalityViolationError(
                f"selection provides {total} {label} count, expected at least {required}"
            )

    def _option_count(self, option: Mapping[str, Any]) -> int:
        count = option.get("count", 1)
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise LegalityViolationError("option count must be a non-negative integer")
        return count
