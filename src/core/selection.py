from __future__ import annotations

from dataclasses import dataclass

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
