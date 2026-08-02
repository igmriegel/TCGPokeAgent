"""Behavioral gameplay metrics derived from runner decision traces.

These metrics answer a narrower question than match outcomes: did the agent
actually play the game in observable main-turn contexts, or did it mostly end
turns and avoid attacks? The values are used by the gameplay smoke gate and by
investigation reports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.core import ExecutionStatus
from src.eval.runner import RunReport

_OPTION_TYPE_NAMES = {
    7: "PLAY",
    8: "ATTACH",
    9: "EVOLVE",
    10: "ABILITY",
    12: "RETREAT",
    13: "ATTACK",
    14: "END",
}
_PRODUCTIVE_MAIN_TYPES = {"PLAY", "ATTACH", "EVOLVE", "ABILITY", "RETREAT", "ATTACK"}


@dataclass(frozen=True, slots=True)
class GameplayMetrics:
    """Aggregate observable gameplay actions selected by an agent.

    The fields are counts and derived rates computed from ``RunReport``
    decision traces. They intentionally ignore hidden belief state and only
    consider actions that are visible in the runner output.
    """

    matches: int
    operational_failures: int
    wins: int
    main_decisions: int
    productive_main_actions: int
    attacks: int
    matches_with_attack: int
    end_turns: int
    action_counts: dict[str, int]

    @property
    def end_turn_rate(self) -> float:
        """Return the fraction of main decisions that selected END."""
        return self.end_turns / self.main_decisions if self.main_decisions else 0.0

    @property
    def attack_match_rate(self) -> float:
        """Return the fraction of matches in which the agent attacked."""
        return self.matches_with_attack / self.matches if self.matches else 0.0

    def assert_minimum_gameplay(self) -> None:
        """Fail when a candidate is legal but demonstrably does not play the game."""
        if self.operational_failures:
            raise ValueError(f"gameplay gate found {self.operational_failures} runtime failures")
        if self.productive_main_actions == 0:
            raise ValueError("gameplay gate found no productive main actions")
        if self.attacks == 0:
            raise ValueError("gameplay gate found no attacks")
        if self.end_turn_rate >= 0.95:
            raise ValueError(f"gameplay gate end-turn rate is {self.end_turn_rate:.1%}")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the metrics for command output and sprint evidence."""
        return {
            "matches": self.matches,
            "operational_failures": self.operational_failures,
            "wins": self.wins,
            "main_decisions": self.main_decisions,
            "productive_main_actions": self.productive_main_actions,
            "attacks": self.attacks,
            "matches_with_attack": self.matches_with_attack,
            "attack_match_rate": self.attack_match_rate,
            "end_turns": self.end_turns,
            "end_turn_rate": self.end_turn_rate,
            "action_counts": dict(sorted(self.action_counts.items())),
        }

    @classmethod
    def from_report(cls, report: RunReport) -> GameplayMetrics:
        """Build gameplay metrics from decision-level runner traces.

        Args:
            report: Batch run containing per-match decision records.

        Returns:
            Behavioral metrics summarizing observable main-turn actions.
        """
        action_counts: dict[str, int] = {}
        main_decisions = 0
        productive = 0
        end_turns = 0
        matches_with_attack = 0
        for match in report.matches:
            attacked = False
            for decision in match.decisions:
                if decision.select_type not in {"0", "MAIN"}:
                    continue
                main_decisions += 1
                selected_types = {
                    _option_type_name(decision.options[index])
                    for index in decision.selected_indices
                    if 0 <= index < len(decision.options)
                }
                for option_type in selected_types:
                    action_counts[option_type] = action_counts.get(option_type, 0) + 1
                if selected_types & _PRODUCTIVE_MAIN_TYPES:
                    productive += 1
                if "ATTACK" in selected_types:
                    attacked = True
                if "END" in selected_types:
                    end_turns += 1
            matches_with_attack += int(attacked)
        return cls(
            matches=len(report.matches),
            operational_failures=sum(
                match.status is not ExecutionStatus.OK for match in report.matches
            ),
            wins=sum(match.result == "win" for match in report.matches),
            main_decisions=main_decisions,
            productive_main_actions=productive,
            attacks=action_counts.get("ATTACK", 0),
            matches_with_attack=matches_with_attack,
            end_turns=end_turns,
            action_counts=action_counts,
        )


def _option_type_name(option: Mapping[str, Any]) -> str:
    value = option.get("type")
    if isinstance(value, int) and not isinstance(value, bool):
        return _OPTION_TYPE_NAMES.get(value, f"TYPE_{value}")
    return str(value).upper()
