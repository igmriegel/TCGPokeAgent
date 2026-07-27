from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .candidate import Candidate
from .selection import Selection
from .state import GameState
from .types import SelectContext, SelectType


@dataclass(slots=True)
class ParsedDecision:
    raw_observation: dict[str, Any]
    state: GameState
    select_type: SelectType | None = None
    select_context: SelectContext | None = None
    min_count: int = 0
    max_count: int = 0
    remain_energy_cost: int = 0
    remain_damage_counter: int = 0
    candidates: list[Candidate] = field(default_factory=list)
    selections: list[Selection] = field(default_factory=list)
