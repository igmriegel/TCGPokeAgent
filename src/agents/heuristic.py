from __future__ import annotations

from typing import Any

from src.core import (
    AgentPolicy,
    DefaultParser,
    DefaultSelectionGenerator,
    GameState,
    HeuristicScorer,
    Selection,
)

WEIGHTS: dict[str, float] = {
    "win_now": 100.0,
    "efficient_attack": 10.0,
    "useful_evolution": 8.0,
    "attack_enabling_energy": 6.0,
    "bench_development": 4.0,
    "draw_search": 5.0,
    "resource_preservation": 3.0,
    "safe_end_turn": 2.0,
    "wasted_energy": -5.0,
    "key_piece_discard": -8.0,
    "pointless_evolution": -6.0,
    "blocked_bench": -4.0,
    "premature_end": -10.0,
}


class SimpleHeuristicScorer(HeuristicScorer):
    def score(self, state: GameState, selection: Selection) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []
        return score, reasons


class HeuristicAgent(AgentPolicy):
    def __init__(self) -> None:
        self._parser = DefaultParser()
        self._generator = DefaultSelectionGenerator()
        self._scorer = SimpleHeuristicScorer()

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

        if not selections:
            return []

        ranked = []
        for sel in selections:
            score, reasons = self._scorer.score(parsed.state, sel)
            ranked.append((score, reasons, sel))

        ranked.sort(key=lambda x: -x[0])
        best = ranked[0][2]
        return list(best.indices)
