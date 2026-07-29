from __future__ import annotations

from src.core.belief import BeliefState
from src.core.state import GameState


class StateEvaluator:
    """Evaluate factual positions plus explicitly separated belief features."""

    def evaluate(self, state: GameState, belief: BeliefState) -> float:
        """Return a deterministic leaf value from the acting player's perspective."""
        if not belief.consistent:
            return float("-inf")
        if state.result == "win":
            return 1_000_000.0
        if state.result == "loss":
            return -1_000_000.0
        own = (
            state.players[state.your_index]
            if state.players and state.your_index < len(state.players)
            else None
        )
        opponent = state.players[1 - state.your_index] if len(state.players) > 1 else None
        own_prizes = len(own.prize) if own is not None else 0
        opp_prizes = len(opponent.prize) if opponent is not None else 0
        own_hp = self._hp(own)
        opp_hp = self._hp(opponent)
        own_energy = sum(len(p.energy_card_ids) for p in (own.bench if own else []) if p)
        own_energy += len(own.active.energy_card_ids) if own is not None and own.active else 0
        bench_quality = sum(1 for p in (own.bench if own else []) if p is not None)
        deck_risk = 1.0 / max(1, own.deck_count if own is not None else 0)
        return (
            (opp_prizes - own_prizes) * 25.0
            + (own_hp - opp_hp) * 0.1
            + own_energy * 2.0
            + bench_quality
            - deck_risk * 5.0
            + len(belief.hand_hypotheses[0] if belief.hand_hypotheses else []) * 0.25
        )

    @staticmethod
    def _hp(player: object) -> int:
        return sum(
            pokemon.hp
            for pokemon in [getattr(player, "active", None), *getattr(player, "bench", [])]
            if pokemon is not None
        )
