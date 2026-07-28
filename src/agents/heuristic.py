from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.core import (
    AgentPolicy,
    Candidate,
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

FEATURE_FLAGS = {
    "use_attack_signals",
    "use_resource_signals",
    "use_setup_signals",
}


def _validated_weights(weights: Mapping[str, Any] | None) -> dict[str, float]:
    """Validate and merge a caller-provided weight profile."""
    result = dict(WEIGHTS)
    for name, value in (weights or {}).items():
        if name not in WEIGHTS:
            raise ValueError(f"unknown heuristic weight: {name}")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"heuristic weight {name!r} must be numeric")
        result[name] = float(value)
    return result


def _validated_flags(flags: Mapping[str, Any] | None) -> dict[str, bool]:
    """Validate feature switches and fill enabled defaults."""
    result = {name: True for name in FEATURE_FLAGS}
    for name, value in (flags or {}).items():
        if name not in FEATURE_FLAGS:
            raise ValueError(f"unknown heuristic feature flag: {name}")
        if not isinstance(value, bool):
            raise ValueError(f"heuristic feature flag {name!r} must be boolean")
        result[name] = value
    return result


class SimpleHeuristicScorer(HeuristicScorer):
    """Score legal selections using deterministic, auditable option signals."""

    def __init__(
        self,
        weights: Mapping[str, Any] | None = None,
        feature_flags: Mapping[str, Any] | None = None,
    ) -> None:
        self.weights = _validated_weights(weights)
        self.feature_flags = _validated_flags(feature_flags)

    def score(
        self,
        state: GameState,
        selection: Selection,
        candidates: Sequence[Candidate] | None = None,
    ) -> tuple[float, list[str]]:
        """Return a weighted score and stable reason codes for a selection."""
        by_index = {candidate.option_index: candidate for candidate in candidates or ()}
        selected = [by_index[index] for index in selection.indices if index in by_index]
        if not selected:
            return 0.0, ["no_signal"]

        score = 0.0
        reasons: list[str] = []
        for candidate in selected:
            option = candidate.option
            context = selection.context.value if selection.context else ""
            is_attack = candidate.option_type.value == "ATTACK" or "ATTACK" in context
            is_energy = candidate.option_type.value in {"ENERGY", "ENERGY_CARD"}
            is_end = candidate.option_type.value == "END"

            if self._truthy(option, "win", "wins", "isWin", "gameOver"):
                score += self.weights["win_now"]
                reasons.append("win_now")
            if self.feature_flags["use_attack_signals"] and is_attack:
                damage = self._number(option, "damage", "expectedDamage", "value")
                cost = max(1.0, self._number(option, "cost", "energyCost"))
                if damage > 0:
                    score += self.weights["efficient_attack"] * min(1.0, damage / cost)
                    reasons.append("efficient_attack")
                if self._truthy(option, "ko", "knockout", "isKo"):
                    score += self.weights["win_now"] * 0.5
                    reasons.append("ko_threat")
            if self._truthy(option, "evolve", "isEvolution") or "EVOLVE" in context:
                if self._truthy(option, "useful", "enablesAttack", "survivalGain"):
                    score += self.weights["useful_evolution"]
                    reasons.append("useful_evolution")
                else:
                    score += self.weights["pointless_evolution"]
                    reasons.append("pointless_evolution")
            if self.feature_flags["use_attack_signals"] and is_energy:
                count = self._number(option, "count", "energyCount")
                if self._truthy(option, "enablesAttack", "enables"):
                    score += self.weights["attack_enabling_energy"]
                    reasons.append("attack_enabling_energy")
                elif count > 1 or self._truthy(option, "wasted", "waste"):
                    score += self.weights["wasted_energy"]
                    reasons.append("wasted_energy")
            if self.feature_flags["use_setup_signals"] and self._truthy(
                option, "bench", "developBench", "setup"
            ):
                score += self.weights["bench_development"]
                reasons.append("bench_development")
            if self._truthy(option, "draw", "search", "drawSearch"):
                score += self.weights["draw_search"]
                reasons.append("draw_search")
            if self.feature_flags["use_resource_signals"]:
                if self._truthy(option, "preserve", "preservesKeyPiece"):
                    score += self.weights["resource_preservation"]
                    reasons.append("resource_preservation")
                if self._truthy(option, "keyPiece", "keyCard") or (
                    candidate.option_type.value == "DISCARD" and self._truthy(option, "rare")
                ):
                    score += self.weights["key_piece_discard"]
                    reasons.append("key_piece_discard")
            if is_end:
                if state.turn_action_count == 0 or self._truthy(option, "premature"):
                    score += self.weights["premature_end"]
                    reasons.append("premature_end")
                else:
                    score += self.weights["safe_end_turn"]
                    reasons.append("safe_end_turn")
            if self._truthy(option, "blockedBench", "benchFull"):
                score += self.weights["blocked_bench"]
                reasons.append("blocked_bench")

        return score, list(dict.fromkeys(reasons)) or ["no_signal"]

    def _truthy(self, option: Mapping[str, Any], *names: str) -> bool:
        return any(bool(option.get(name, False)) for name in names)

    def _number(self, option: Mapping[str, Any], *names: str) -> float:
        for name in names:
            value = option.get(name)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
        return 0.0


class HeuristicAgent(AgentPolicy):
    """Select the highest-scoring legal option with deterministic tie-breaking."""

    def __init__(
        self,
        weights: Mapping[str, Any] | None = None,
        feature_flags: Mapping[str, Any] | None = None,
    ) -> None:
        self._parser = DefaultParser()
        self._generator = DefaultSelectionGenerator()
        self._scorer = SimpleHeuristicScorer(weights, feature_flags)

    def select(self, observation: dict[str, Any]) -> list[int]:
        """Return the best legal selection, or a deterministic empty fallback."""
        parsed = self._parser.parse(observation)
        if parsed.max_count == 0:
            return []
        selections = self._generator.generate(
            parsed.candidates,
            parsed.min_count,
            parsed.max_count,
            parsed.remain_energy_cost,
            parsed.remain_damage_counter,
        )
        if not selections:
            return []
        ranked = []
        for selection in selections:
            selection_with_context = Selection(
                indices=selection.indices,
                option_types=selection.option_types,
                context=parsed.select_context,
            )
            score, reasons = self._scorer.score(
                parsed.state, selection_with_context, parsed.candidates
            )
            ranked.append((score, selection_with_context.indices, reasons, selection_with_context))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return list(ranked[0][3].indices)
