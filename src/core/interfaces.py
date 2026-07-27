from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .candidate import Candidate
from .parsed_decision import ParsedDecision
from .selection import Selection
from .state import GameState


class ObservationParser(ABC):
    @abstractmethod
    def parse(self, observation: dict[str, Any]) -> ParsedDecision: ...


class SelectionGenerator(ABC):
    @abstractmethod
    def generate(
        self,
        candidates: list[Candidate],
        min_count: int,
        max_count: int,
        remain_energy_cost: int = 0,
        remain_damage_counter: int = 0,
    ) -> list[Selection]: ...


class HeuristicScorer(ABC):
    @abstractmethod
    def score(self, state: GameState, selection: Selection) -> tuple[float, list[str]]: ...


class AgentPolicy(ABC):
    @abstractmethod
    def select(self, observation: dict[str, Any]) -> list[int]: ...


class BeliefBuilder(ABC):
    @abstractmethod
    def build(
        self,
        observation: dict[str, Any],
        state: GameState,
        history: list[dict[str, Any]] | None = None,
    ) -> Any: ...


class StateEvaluator(ABC):
    @abstractmethod
    def evaluate(self, state: GameState, belief: Any) -> float: ...


class ShortSearch(ABC):
    @abstractmethod
    def choose(
        self,
        observation: dict[str, Any],
        belief: Any,
        ranked: list[Selection],
        budget_ms: int = 100,
    ) -> Selection: ...
