from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .types import TurnPhase


@dataclass(slots=True)
class PokemonState:
    card_id: str
    hp: int
    max_hp: int
    energies: list[dict[str, Any]] = field(default_factory=list)
    energy_card_ids: list[str] = field(default_factory=list)
    tool_ids: list[str] = field(default_factory=list)
    pre_evolutions: list[str] = field(default_factory=list)
    appear_this_turn: bool = False
    poisoned: bool = False
    burned: bool = False
    asleep: bool = False
    paralyzed: bool = False
    confused: bool = False


@dataclass(slots=True)
class PlayerState:
    active: PokemonState | None = None
    bench: list[PokemonState | None] = field(default_factory=list)
    bench_max: int = 8
    deck_count: int = 0
    discard: list[str] = field(default_factory=list)
    prize: list[str | None] = field(default_factory=list)
    hand_count: int = 0
    hand: list[str] | None = None


@dataclass(slots=True)
class GameState:
    turn: int = 0
    turn_action_count: int = 0
    your_index: int = 0
    first_player: int = 0
    result: str | None = None
    supporter_played: bool = False
    stadium_played: bool = False
    energy_attached: bool = False
    retreated: bool = False
    stadium: str | None = None
    looking: int | None = None
    players: list[PlayerState] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return {
            "turn": self.turn,
            "turn_action_count": self.turn_action_count,
            "your_index": self.your_index,
            "first_player": self.first_player,
            "result": self.result,
            "supporter_played": self.supporter_played,
            "stadium_played": self.stadium_played,
            "energy_attached": self.energy_attached,
            "retreated": self.retreated,
            "stadium": self.stadium,
            "looking": self.looking,
            "player_count": len(self.players),
        }
