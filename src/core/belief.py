from __future__ import annotations

from dataclasses import dataclass, field


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
