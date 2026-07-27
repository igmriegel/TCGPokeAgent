from __future__ import annotations

from typing import Any

from src.core import (
    AgentPolicy,
    DefaultParser,
    DefaultSelectionGenerator,
    OptionType,
    ParsedDecision,
    SelectContext,
    Selection,
)


class BaselineAgent(AgentPolicy):
    def __init__(self) -> None:
        self._parser = DefaultParser()
        self._generator = DefaultSelectionGenerator()

    def select(self, observation: dict[str, Any]) -> list[int]:
        parsed = self._parser.parse(observation)

        if parsed.max_count == 0:
            return []

        selections = self._generator.generate(
            candidates=parsed.candidates,
            min_count=parsed.min_count,
            max_count=parsed.max_count,
            remain_energy_cost=parsed.remain_energy_cost,
            remain_damage_counter=parsed.remain_damage_counter,
        )

        chosen = self._fallback(parsed, selections)
        return list(chosen.indices)

    def _fallback(self, parsed: ParsedDecision, selections: list[Selection]) -> Selection:
        if not selections:
            return Selection(indices=(), option_types=())

        if parsed.select_context is not None:
            for sel in selections:
                if sel.context is None:
                    object.__setattr__(sel, "context", parsed.select_context)
                if self._context_preferred(parsed.select_context, sel):
                    return sel

        return selections[0]

    def _context_preferred(self, context: SelectContext, selection: Selection) -> bool:
        return False
