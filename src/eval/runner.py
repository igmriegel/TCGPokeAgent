from __future__ import annotations

import random
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, cast

from src.core import ErrorCategory, ExecutionStatus
from src.eval.validation import check_legal_selection

AgentCallable = Callable[[dict[str, Any]], list[int]]
EnvironmentFactory = Callable[[], Any]


@dataclass(slots=True)
class DecisionRecord:
    """Record one policy call made during a match."""

    decision_index: int
    turn: int | None
    context: str | None
    select_type: str | None
    options: list[dict[str, Any]]
    option_count: int
    min_count: int
    max_count: int
    selected_indices: list[int]
    legal: bool
    duration_ms: float
    overage_balance_ms: float
    score: float | None = None
    reasons: list[str] = field(default_factory=list)
    search: dict[str, Any] | None = None
    error_category: str = ErrorCategory.NONE.value
    error_message: str = ""
    state_before: dict[str, Any] = field(default_factory=dict)
    state_after: dict[str, Any] | None = None
    action_sequence: list[dict[str, Any]] = field(default_factory=list)
    teacher_decision: list[int] | None = None

    def to_trace(self, match_id: str, deck_id: str = "default", matchup: str = "unknown") -> Any:
        """Convert the runner record to the versioned RFL decision schema."""
        from src.rfl.schemas import DecisionTrace

        return DecisionTrace(
            match_id=match_id,
            decision_index=self.decision_index,
            deck_id=deck_id,
            deck_sha256="unknown",
            matchup=matchup,
            turn=self.turn or 0,
            state_before=self.state_before,
            legal_options=self.options,
            original_indices=list(range(self.option_count)),
            selected_indices=self.selected_indices,
            agent_decision=self.selected_indices,
            teacher_decision=self.teacher_decision,
            score=self.score,
            reasons=self.reasons,
            duration_ms=self.duration_ms,
            state_after=self.state_after,
            action_sequence=self.action_sequence,
        )


@dataclass(slots=True)
class MatchRecord:
    """Serializable result and diagnostics for one SDK match."""

    match_id: str
    seed: int
    agent_side: int
    status: ExecutionStatus
    result: str | None = None
    duration_ms: float = 0.0
    decision_count: int = 0
    decisions: list[DecisionRecord] = field(default_factory=list)
    turns: int | None = None
    final_statuses: list[str] = field(default_factory=list)
    agent_mode: str = ""
    opponent: str = ""
    sdk_version: str = "unknown"
    deck_sha256: str = "unknown"
    started_at: float = 0.0
    finished_at: float = 0.0
    termination_reason: str = "unknown"
    error_category: str = ErrorCategory.NONE.value
    error_message: str = ""


@dataclass(slots=True)
class RunReport:
    """Collection of match records produced by one batch."""

    config_name: str
    agent_mode: str
    matches: list[MatchRecord] = field(default_factory=list)
    started_at: float = 0.0
    finished_at: float = 0.0

    @property
    def total_matches(self) -> int:
        """Return the number of attempted matches."""
        return len(self.matches)


class MatchRunner:
    """Execute cabt matches and capture decision-level observability."""

    def __init__(
        self,
        environment_factory: EnvironmentFactory | None = None,
        opponent: str = "random",
        decision_budget_ms: float = 100.0,
    ) -> None:
        self._environment_factory = environment_factory
        self.opponent = opponent
        self.decision_budget_ms = decision_budget_ms

    def run_match(self, seed: int, agent_mode: str, side: int) -> MatchRecord:
        """Run one seeded match, returning a record even when execution fails."""
        start = time.perf_counter()
        started_at = time.time()
        match_id = f"match_{seed}_{side}"
        decisions: list[DecisionRecord] = []
        try:
            with _SeededRandom(seed):
                environment = self._make_environment(seed)
                agent = self._instrument(self._agent_for_mode(agent_mode), decisions)
                opponent = self._opponent_callable(self.opponent, agent_mode)
                players = [agent, opponent] if side == 0 else [opponent, agent]
                environment.run(players)
            statuses = [self._player_status(player) for player in environment.state]
            status = (
                ExecutionStatus.OK
                if all(value.endswith("DONE") for value in statuses)
                else ExecutionStatus.ERROR
            )
            result = self._result_for(environment, side)
            error_category = (
                ErrorCategory.NONE.value
                if status is ExecutionStatus.OK
                else ErrorCategory.RUNTIME.value
            )
            error_message = (
                ""
                if status is ExecutionStatus.OK
                else self._environment_error_message(environment)
                or "one or more players did not finish"
            )
            termination_reason = "completed" if status is ExecutionStatus.OK else "incomplete"
        except Exception as error:
            status = ExecutionStatus.ERROR
            result = None
            statuses = []
            error_category = self._error_category(error)
            error_message = str(error)
            termination_reason = "exception"

        finished_at = time.time()

        return MatchRecord(
            match_id=match_id,
            seed=seed,
            agent_side=side,
            status=status,
            result=result,
            duration_ms=(time.perf_counter() - start) * 1000,
            decision_count=len(decisions),
            decisions=decisions,
            turns=len(getattr(environment, "steps", [])) if "environment" in locals() else None,
            final_statuses=statuses,
            error_category=error_category,
            error_message=error_message,
            agent_mode=agent_mode,
            opponent=self.opponent,
            sdk_version=self._sdk_version(),
            deck_sha256=self._deck_sha256(),
            started_at=started_at,
            finished_at=finished_at,
            termination_reason=termination_reason,
        )

    def run_batch(
        self, seeds: list[int], agent_mode: str, sides: list[int] | None = None
    ) -> RunReport:
        """Run all seed/side combinations while isolating individual failures."""
        selected_sides = [0, 1] if sides is None else list(sides)
        report = RunReport(config_name="batch", agent_mode=agent_mode, started_at=time.time())
        for seed in seeds:
            for side in selected_sides:
                report.matches.append(self.run_match(seed, agent_mode, side))
        report.finished_at = time.time()
        return report

    def _make_environment(self, seed: int) -> Any:
        if self._environment_factory is not None:
            return self._environment_factory()
        from kaggle_environments import make

        return make("cabt", configuration={"seed": seed}, debug=False)

    def _agent_for_mode(self, mode: str) -> AgentCallable:
        """Build a policy with the SDK's initial-deck branch attached."""
        deck_path = Path(__file__).parents[1] / "artifacts" / "deck.csv"
        deck = [int(row) for row in deck_path.read_text(encoding="utf-8").splitlines() if row]

        def with_deck(policy: AgentCallable) -> AgentCallable:
            def wrapped(observation: dict[str, Any]) -> list[int]:
                if observation.get("select") is None:
                    return list(deck)
                return list(policy(observation))

            return wrapped

        if mode == "baseline":
            from src.agents.baseline import BaselineAgent

            return with_deck(BaselineAgent().select)
        if mode == "heuristic":
            from src.agents.heuristic import HeuristicAgent
            from src.config.loader import ConfigLoader

            config = ConfigLoader(Path(__file__).parents[2] / "configs").load("agent_heuristic")
            return with_deck(
                HeuristicAgent(
                    weights=config.extra.get("weights"),
                    feature_flags=config.extra.get("feature_flags"),
                ).select
            )
        if mode == "self_play":
            return self._agent_for_mode("heuristic")
        if mode == "rfl":
            from src.rfl.profiles import agent_from_profile

            root = Path(__file__).parents[2]
            profile = (
                root / "configs" / "decks" / "mega_abomasnow_kyogre" / "heuristic_rfl_0001.yaml"
            )
            deck_file = root / "src" / "artifacts" / "deck.csv"
            return with_deck(
                agent_from_profile(
                    profile, active_deck_id="mega_abomasnow_kyogre", active_deck_path=deck_file
                ).select
            )
        raise ValueError(f"unsupported agent mode: {mode}")

    def _opponent_callable(self, opponent: str, agent_mode: str) -> AgentCallable:
        from kaggle_environments.envs.cabt import cabt

        if opponent in {"baseline", "heuristic"}:
            return self._agent_for_mode(opponent)
        if opponent in {"self", "self_play"}:
            return self._agent_for_mode(agent_mode)
        try:
            return cast(
                AgentCallable, {"random": cabt.random_agent, "first": cabt.first_agent}[opponent]
            )
        except KeyError as error:
            raise ValueError(f"unsupported opponent: {opponent}") from error

    def _instrument(self, policy: AgentCallable, records: list[DecisionRecord]) -> AgentCallable:
        def wrapped(observation: dict[str, Any]) -> list[int]:
            start = time.perf_counter()
            select = observation.get("select")
            result = policy(observation)
            duration_ms = (time.perf_counter() - start) * 1000
            if not isinstance(select, Mapping):
                return result
            options = select.get("option", [])
            selected = list(result) if isinstance(result, list) else []
            legal = True
            error_category = ErrorCategory.NONE.value
            error_message = ""
            try:
                check_legal_selection(observation, selected)
            except Exception as error:
                legal = False
                error_category = ErrorCategory.INVALID.value
                error_message = str(error)
            current = observation.get("current")
            turn = current.get("turn") if isinstance(current, Mapping) else None
            records.append(
                DecisionRecord(
                    decision_index=len(records),
                    turn=turn if isinstance(turn, int) else None,
                    context=(
                        str(select.get("context")) if select.get("context") is not None else None
                    ),
                    select_type=(
                        str(select.get("type")) if select.get("type") is not None else None
                    ),
                    options=[dict(option) for option in options if isinstance(option, Mapping)],
                    option_count=len(options) if isinstance(options, list) else 0,
                    min_count=int(select.get("minCount", 0) or 0),
                    max_count=int(select.get("maxCount", 0) or 0),
                    selected_indices=selected,
                    legal=legal,
                    duration_ms=duration_ms,
                    overage_balance_ms=self.decision_budget_ms - duration_ms,
                    state_before=self._state_snapshot(observation),
                    error_category=error_category,
                    error_message=error_message,
                )
            )
            return result

        return wrapped

    @staticmethod
    def _state_snapshot(observation: Mapping[str, Any]) -> dict[str, Any]:
        """Return a factual, JSON-safe snapshot without hidden belief state."""
        current = observation.get("current")
        return dict(current) if isinstance(current, Mapping) else {}

    @staticmethod
    def _sdk_version() -> str:
        try:
            return version("kaggle-environments")
        except PackageNotFoundError:
            return "unknown"

    @staticmethod
    def _deck_sha256() -> str:
        deck_path = Path(__file__).parents[1] / "artifacts" / "deck.csv"
        try:
            return sha256(deck_path.read_bytes()).hexdigest()
        except OSError:
            return "unknown"

    @staticmethod
    def _result_for(environment: Any, side: int) -> str | None:
        state = getattr(environment, "state", [])
        if not state or side >= len(state):
            return None
        reward = getattr(state[side], "reward", None)
        if reward is None and isinstance(state[side], Mapping):
            reward = state[side].get("reward")
        if reward is None:
            return None
        return "win" if reward > 0 else "loss" if reward < 0 else "draw"

    @staticmethod
    def _player_status(player: Any) -> str:
        status = (
            player.get("status", "unknown")
            if isinstance(player, Mapping)
            else getattr(player, "status", "unknown")
        )
        return str(status)

    @staticmethod
    def _environment_error_message(environment: Any) -> str:
        """Return stderr emitted by agents in an incomplete environment run."""
        messages = [
            str(log.get("stderr", "")).strip()
            for turn in getattr(environment, "logs", [])
            for log in turn
            if isinstance(log, Mapping) and log.get("stderr")
        ]
        return "\n".join(dict.fromkeys(message for message in messages if message))

    @staticmethod
    def _error_category(error: Exception) -> str:
        return (
            ErrorCategory.TIMEOUT.value
            if isinstance(error, TimeoutError)
            else ErrorCategory.RUNTIME.value
        )


class _SeededRandom:
    def __init__(self, seed: int) -> None:
        self.seed = seed

    def __enter__(self) -> None:
        self._state = random.getstate()
        random.seed(self.seed)

    def __exit__(self, *_: object) -> None:
        random.setstate(self._state)
