from __future__ import annotations

from collections.abc import Mapping
from itertools import combinations

from .candidate import Candidate
from .interfaces import SelectionGenerator as SelectionGeneratorInterface
from .selection import Selection, SelectionValidator


class DefaultSelectionGenerator(SelectionGeneratorInterface):
    def generate(
        self,
        candidates: list[Candidate],
        min_count: int,
        max_count: int,
        remain_energy_cost: int = 0,
        remain_damage_counter: int = 0,
    ) -> list[Selection]:
        if min_count < 0 or max_count < min_count:
            return []

        validator = SelectionValidator()
        results: list[Selection] = []

        for size in range(min_count, max_count + 1):
            if size == 0:
                results.append(
                    Selection(
                        indices=(),
                        option_types=(),
                        context=None,
                        score=None,
                        reasons=("empty selection",),
                    )
                )
                continue

            for combo in combinations(candidates, size):
                indices = tuple(c.option_index for c in combo)
                types = tuple(c.option_type for c in combo)

                selection = Selection(indices=indices, option_types=types)
                try:
                    validator.validate(
                        selection,
                        candidates,
                        min_count,
                        max_count,
                        remain_energy_cost,
                        remain_damage_counter,
                    )
                except Exception:
                    continue
                results.append(selection)

        results.sort(key=lambda s: s.indices)
        return results

    def _meets_energy_constraint(self, combo: tuple[Candidate, ...], required: int) -> bool:
        if required <= 0:
            return True
        total = 0
        for c in combo:
            count = c.option.get("count", 1) if isinstance(c.option, Mapping) else 1
            total += count
        return total >= required

    def _meets_damage_constraint(self, combo: tuple[Candidate, ...], required: int) -> bool:
        if required <= 0:
            return True
        total = 0
        for c in combo:
            count = c.option.get("count", 1) if isinstance(c.option, Mapping) else 1
            total += count
        return total >= required

    def _no_duplicate_indices(self, indices: tuple[int, ...]) -> bool:
        return len(indices) == len(set(indices))
