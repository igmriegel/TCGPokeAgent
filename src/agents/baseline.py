from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from src.core import (
    AgentPolicy,
    DefaultParser,
    DefaultSelectionGenerator,
    ParsedDecision,
    SelectContext,
    Selection,
    SelectionValidator,
)


class BaselineAgent(AgentPolicy):
    def __init__(self) -> None:
        self._parser = DefaultParser()
        self._generator = DefaultSelectionGenerator()
        self._validator = SelectionValidator()

    def select(self, observation: dict[str, Any]) -> list[int]:
        try:
            parsed = self._parser.parse(observation)
            selections = self._generator.generate(
                candidates=parsed.candidates,
                min_count=parsed.min_count,
                max_count=parsed.max_count,
                remain_energy_cost=parsed.remain_energy_cost,
                remain_damage_counter=parsed.remain_damage_counter,
            )
        except Exception:
            return self._raw_fallback(observation)

        if parsed.max_count == 0:
            return []

        chosen = self._fallback(parsed, selections)
        return list(chosen.indices)

    def _fallback(self, parsed: ParsedDecision, selections: list[Selection]) -> Selection:
        if not selections:
            return Selection(indices=(), option_types=())

        context = parsed.select_context
        for selection in selections:
            candidate = replace(selection, context=context)
            try:
                self._validator.validate(
                    candidate,
                    parsed.candidates,
                    parsed.min_count,
                    parsed.max_count,
                    parsed.remain_energy_cost,
                    parsed.remain_damage_counter,
                )
            except Exception:
                continue
            if context is None or self._context_preferred(context, candidate):
                return candidate

        return selections[0]

    def _context_preferred(self, context: SelectContext, selection: Selection) -> bool:
        return False

    def _raw_fallback(self, observation: Any) -> list[int]:
        if not isinstance(observation, Mapping):
            return []
        select = observation.get("select")
        if not isinstance(select, Mapping):
            return []
        options = select.get("option")
        if not isinstance(options, list):
            return []
        try:
            min_count = int(select.get("minCount", 0) or 0)
            max_count = int(select.get("maxCount", 0) or 0)
        except (TypeError, ValueError):
            return []
        if min_count < 0 or max_count < min_count or min_count > len(options):
            return []
        return list(range(min_count))
