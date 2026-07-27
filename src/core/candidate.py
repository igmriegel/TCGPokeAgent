from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .types import OptionType


@dataclass(frozen=True, slots=True)
class Candidate:
    option_index: int
    option: dict[str, Any]
    option_type: OptionType
    card: dict[str, Any] | None = None
    features: Mapping[str, float | int | bool] = field(default_factory=dict)
