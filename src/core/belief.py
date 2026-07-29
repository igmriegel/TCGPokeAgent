from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from .state import GameState


@dataclass(slots=True)
class BeliefState:
    own_deck_remaining: list[str] = field(default_factory=list)
    opp_deck_remaining: list[str] = field(default_factory=list)
    hand_hypotheses: list[list[str]] = field(default_factory=list)
    prize_hypotheses: list[list[str]] = field(default_factory=list)
    opp_active_hypothesis: str | None = None
    incorporated_log_events: int = 0
    consistent: bool = True
    violations: list[str] = field(default_factory=list)


class DefaultBeliefBuilder:
    """Construct deterministic hidden-zone hypotheses without mutating facts."""

    def __init__(self, deck: Sequence[str] | None = None) -> None:
        self._deck = tuple(str(card) for card in (deck or ()))

    def build(
        self,
        observation: dict[str, Any],
        state: GameState,
        history: list[dict[str, Any]] | None = None,
    ) -> BeliefState:
        """Build a belief state and mark impossible observations as inconsistent."""
        logs = observation.get("logs", [])
        event_count = len(logs) if isinstance(logs, list) else 0
        known = self._known_cards(state)
        available = Counter(self._deck)
        violations: list[str] = []
        for card in known:
            available[card] -= 1
            if available[card] < 0:
                violations.append(f"card_count:{card}")

        own = (
            state.players[state.your_index]
            if state.players and state.your_index < len(state.players)
            else None
        )
        opponent = state.players[1 - state.your_index] if len(state.players) > 1 else None
        own_deck_count = own.deck_count if own is not None else 0
        prize_count = len(own.prize) if own is not None else 0
        opponent_hand_count = opponent.hand_count if opponent is not None else 0
        if own_deck_count < 0 or prize_count < 0 or opponent_hand_count < 0:
            violations.append("negative_zone_count")
        hidden = sorted(card for card, count in available.items() for _ in range(max(0, count)))
        if own_deck_count > len(hidden):
            violations.append("deck_cardinality")
        prizes = [hidden[i] for i in range(min(prize_count, len(hidden)))]
        hand_start = min(prize_count, len(hidden))
        hand = [
            hidden[i] for i in range(hand_start, min(hand_start + opponent_hand_count, len(hidden)))
        ]
        active = (
            str(opponent.active.card_id)
            if opponent and opponent.active and opponent.active.card_id is not None
            else None
        )
        return BeliefState(
            own_deck_remaining=hidden[:own_deck_count],
            opp_deck_remaining=hidden[own_deck_count:],
            hand_hypotheses=[hand],
            prize_hypotheses=[prizes],
            opp_active_hypothesis=active,
            incorporated_log_events=event_count,
            consistent=not violations,
            violations=violations,
        )

    @staticmethod
    def _known_cards(state: GameState) -> list[str]:
        """Return publicly known card identifiers in stable traversal order."""
        cards: list[str] = []
        for player in state.players:
            cards.extend(str(card) for card in player.discard)
            cards.extend(str(card) for card in player.prize if card is not None)
            if player.hand:
                cards.extend(str(card) for card in player.hand)
            for pokemon in [player.active, *player.bench]:
                if pokemon and pokemon.card_id:
                    cards.append(str(pokemon.card_id))
                if pokemon:
                    cards.extend(str(card) for card in pokemon.energy_card_ids)
        return cards
