"""Shared strategic context and ranking contracts for all policy families."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence

from .belief import BeliefState
from .candidate import Candidate
from .deck import DeckDefinition, DeckProfile
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
    reasons: tuple[str, ...] = ()


class SelectionRanker(Protocol):
    """Common inference contract for heuristic and learned selection rankers."""

    def rank(
        self,
        context: StrategicContext,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
    ) -> list[RankedSelection]:
        """Rank legal selections without changing their simulator indices."""
        ...
