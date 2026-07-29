from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from src.core import DefaultBeliefBuilder, DefaultParser, Selection
from src.core.belief import BeliefState


@dataclass(slots=True)
class SearchStats:
    """Counters exposed for evaluation and trace reporting."""

    considered: int = 0
    opened: int = 0
    failures: int = 0
    elapsed_ms: float = 0.0
    last_error: str = ""


class BoundedShortSearch:
    """Safe bounded search adapter with deterministic heuristic fallback."""

    def __init__(
        self,
        search_api: Any | None = None,
        top_k: int = 3,
        max_depth: int = 4,
        max_decision_ms: int = 100,
        disable_below_overage_s: int = 30,
    ) -> None:
        self.search_api = search_api
        self.top_k = top_k
        self.max_depth = max_depth
        self.max_decision_ms = max_decision_ms
        self.disable_below_overage_s = disable_below_overage_s
        self.stats = SearchStats()

    def choose(
        self,
        observation: dict[str, Any],
        belief: BeliefState,
        ranked: Sequence[Selection],
        budget_ms: int = 100,
    ) -> Selection:
        """Choose from ranked candidates, always returning the heuristic top one on failure."""
        fallback = ranked[0] if ranked else Selection((), ())
        started = time.perf_counter()
        self.stats.considered += 1
        if not self._gate(observation, belief, ranked):
            return fallback
        self.stats.opened += 1
        api = self.search_api
        if api is None:
            return fallback
        released: list[Any] = []
        try:
            handle = api.search_begin(observation.get("search_begin_input"), self.max_depth)
            best = fallback
            deadline = started + min(budget_ms, self.max_decision_ms) / 1000
            for selection in list(ranked)[: self.top_k]:
                if time.perf_counter() >= deadline:
                    break
                value = api.search_step(handle, selection.indices, self.max_depth)
                if value > api.search_value(best):
                    best = selection
            return best
        except Exception as error:
            self.stats.failures += 1
            self.stats.last_error = str(error)
            return fallback
        finally:
            try:
                if api is not None and "handle" in locals():
                    api.search_release(handle)
            finally:
                if api is not None and "handle" in locals():
                    api.search_end(handle)
                self.stats.elapsed_ms = (time.perf_counter() - started) * 1000

    def _gate(
        self, observation: dict[str, Any], belief: BeliefState, ranked: Sequence[Selection]
    ) -> bool:
        select = observation.get("select")
        if not isinstance(select, dict) or str(select.get("type", "")) != "MAIN":
            return False
        if len(ranked) < 2 or not observation.get("search_begin_input") or not belief.consistent:
            return False
        overage = observation.get("remainingOverageTime", observation.get("overage", 0))
        try:
            return float(overage) >= self.disable_below_overage_s
        except (TypeError, ValueError):
            return False


class HybridAgent:
    """Heuristic policy decorated with bounded search and safe fallback."""

    def __init__(self, heuristic: Any, search: BoundedShortSearch | None = None) -> None:
        self.heuristic = heuristic
        self.search = search or BoundedShortSearch()
        self.parser = DefaultParser()
        self.beliefs = DefaultBeliefBuilder()

    def select(self, observation: dict[str, Any]) -> list[int]:
        """Select legally using heuristic policy; search is optional and non-fatal."""
        return list(self.heuristic.select(observation))
