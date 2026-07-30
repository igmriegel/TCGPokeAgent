"""Shared strategic context and ranking contracts for all policy families."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence

from .belief import BeliefState
from .deck import DeckDefinition, DeckProfile
from .parsed_decision import ParsedDecision
from .policy_decision import SelectionFeatures
from .prize import PrizeCheckResult, PrizeMap
from .selection import Selection
from .state import GameState


@dataclass(frozen=True, slots=True)
class StrategicContext:
    """Deck-agnostic inputs shared by heuristic and learned rankers."""

    state: GameState
    deck: DeckDefinition
    deck_profile: DeckProfile
    prize_check: PrizeCheckResult
    prize_map: PrizeMap
    belief: BeliefState | None = None
    history: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class RankedSelection:
    """One legal selection with auditable policy output."""

    selection: Selection
    score: float
    rank: int
    reasons: tuple[str, ...] = ()
    margin_to_next: float = 0.0

    @property
    def indices(self) -> tuple[int, ...]:
        """Return unchanged simulator indices for trace serialization."""
        return self.selection.indices


class SelectionRanker(Protocol):
    """Common inference contract for heuristic and learned selection rankers."""

    def rank(
        self,
        decision: ParsedDecision,
        selections: Sequence[Selection],
        features: Sequence[SelectionFeatures],
    ) -> list[RankedSelection]:
        """Rank legal selections without changing their simulator indices."""
        ...
