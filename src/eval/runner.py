"""Match execution and decision tracing for CABT evaluation runs.

The runner is responsible for executing seeded SDK matches, capturing every
policy call, and preserving the stable records consumed by evaluation reports
and replay analysis. It does not score decisions or aggregate statistics.
"""

from __future__ import annotations

import contextlib
import os
import random
import sys
import time
from collections.abc import Callable, Iterator, Mapping
from dataclasses import asdict, dataclass, field, is_dataclass
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, cast

from src.core import ErrorCategory, ExecutionStatus, PolicyDecision
from src.eval.telemetry import (
    aggregate_decisions,
    classify_terminal,
    failure_flags,
    public_snapshot,
    transition,
)
from src.eval.validation import check_legal_selection

AgentCallable = Callable[[dict[str, Any]], list[int]]
EnvironmentFactory = Callable[[], Any]


@dataclass(slots=True)
class DecisionRecord:
    """Capture one policy invocation and the legal decision it produced.

    The record stores the decision context, the available options, the chosen
    indices, timing, error category, and the ranking/feature metadata emitted
    by the policy owner. It is the atomic unit for decision-level observability.
    """

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
    decision_phase: str = ""
    decision_phase_reason: str = ""
    search: dict[str, Any] | None = None
    error_category: str = ErrorCategory.NONE.value
    error_message: str = ""
    state_before: dict[str, Any] = field(default_factory=dict)
    state_after: dict[str, Any] | None = None
    telemetry_before: dict[str, Any] = field(default_factory=dict)
    telemetry_after: dict[str, Any] | None = None
    transition: dict[str, Any] = field(default_factory=dict)
    failure_flags: list[str] = field(default_factory=list)
    action_sequence: list[dict[str, Any]] = field(default_factory=list)
    teacher_decision: list[int] | None = None
    ranked: list[dict[str, Any]] = field(default_factory=list)
    features: list[dict[str, Any]] = field(default_factory=list)
    fallback_used: bool = False
    model_backend: str = ""
    model_version: str = ""
    tactical: dict[str, Any] = field(default_factory=dict)

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
            decision_phase=self.decision_phase,
            decision_phase_reason=self.decision_phase_reason,
            duration_ms=self.duration_ms,
            state_after=self.state_after,
            action_sequence=self.action_sequence,
            ranked=self.ranked,
            features=self.features,
            fallback_used=self.fallback_used,
            model_backend=self.model_backend,
            model_version=self.model_version,
        )


@dataclass(slots=True)
class MatchRecord:
    """Capture the executable result of one seeded SDK match.

    Match records keep the player side, final result, runtime, decision traces,
    final SDK statuses, and run metadata required by serialized reports and
    downstream audit tooling.
    """

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
    termination_reason_explicit: bool = False
    terminal_state: dict[str, Any] = field(default_factory=dict)
    telemetry: dict[str, Any] = field(default_factory=dict)
    error_category: str = ErrorCategory.NONE.value
    error_message: str = ""


@dataclass(slots=True)
class RunReport:
    """Group the match records produced by one batch execution.

    The report preserves the batch name, the agent mode, timestamps, and the
    ordered list of per-match records. Aggregation and serialization read from
    this object without mutating it.
    """

    config_name: str
    agent_mode: str
    matches: list[MatchRecord] = field(default_factory=list)
    started_at: float = 0.0
    finished_at: float = 0.0

    @property
    def total_matches(self) -> int:
        """Return the number of attempted matches."""
        return len(self.matches)

    @property
    def telemetry_summary(self) -> dict[str, Any]:
        """Return decision-level telemetry aggregated across this batch."""
        return aggregate_decisions(self.matches)


class MatchRunner:
    """Execute cabt matches and capture decision-level observability."""

    def __init__(
        self,
        environment_factory: EnvironmentFactory | None = None,
        opponent: str = "random",
        decision_budget_ms: float = 100.0,
        quiet_native_output: bool = True,
    ) -> None:
        self._environment_factory = environment_factory
        self.opponent = opponent
        self.decision_budget_ms = decision_budget_ms
        self.quiet_native_output = quiet_native_output

    def run_match(self, seed: int, agent_mode: str, side: int) -> MatchRecord:
        """Run one seeded match, returning a record even when execution fails."""
        start = time.perf_counter()
        started_at = time.time()
        match_id = f"match_{seed}_{side}"
        decisions: list[DecisionRecord] = []
        try:
            with _SeededRandom(seed):
                with _quiet_native_sdk_output(
                    self.quiet_native_output and self._environment_factory is None
                ):
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
            terminal_raw = self._latest_public_state(environment)
            terminal_snapshot = public_snapshot(terminal_raw)
            if terminal_snapshot.get("own") and terminal_snapshot.get("opponent"):
                termination_reason, reason_explicit = classify_terminal(
                    terminal_snapshot, result, side
                )
            else:
                termination_reason, reason_explicit = "completed", False
            if status is not ExecutionStatus.OK:
                termination_reason = "INCOMPLETE"
                reason_explicit = False
            self._finalize_decisions(decisions, terminal_raw)
        except Exception as error:
            status = ExecutionStatus.ERROR
            result = None
            statuses = []
            error_category = self._error_category(error)
            error_message = str(error)
            termination_reason = "exception"
            reason_explicit = False
            terminal_snapshot = {}

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
            termination_reason_explicit=reason_explicit,
            terminal_state=terminal_snapshot,
            telemetry=aggregate_decisions(
                [
                    MatchRecord(
                        match_id=match_id,
                        seed=seed,
                        agent_side=side,
                        status=status,
                        decisions=decisions,
                    )
                ]
            ),
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
        from src.agents.factory import build_agent, load_deck

        root = Path(__file__).parents[2]
        deck = load_deck(root, mode)

        def with_deck(policy: Any) -> AgentCallable:
            def wrapped(observation: dict[str, Any]) -> list[int]:
                if observation.get("select") is None:
                    start_match = getattr(policy, "start_match", None)
                    if callable(start_match):
                        from src.core import DeckDefinition

                        start_match(DeckDefinition.from_cards(deck, "evaluation"))
                    return list(deck)
                return list(policy.select(observation))

            setattr(wrapped, "policy_owner", policy)
            return wrapped

        if mode == "self_play":
            return self._agent_for_mode("heuristic")
        return with_deck(build_agent(mode, root=root))

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
        pending: DecisionRecord | None = None

        def wrapped(observation: dict[str, Any]) -> list[int]:
            nonlocal pending
            start = time.perf_counter()
            select = observation.get("select")
            raw_before = observation.get("current")
            telemetry_before = public_snapshot(observation)
            if pending is not None:
                pending.state_after = dict(raw_before) if isinstance(raw_before, Mapping) else {}
                pending.telemetry_after = telemetry_before
                pending.transition = transition(pending.telemetry_before, telemetry_before)
                pending.failure_flags = failure_flags(
                    selected_indices=pending.selected_indices,
                    options=pending.options,
                    before=pending.telemetry_before,
                    effects=pending.transition,
                )
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
            policy_decision = self._policy_decision(policy)
            options_mappings = [dict(option) for option in options if isinstance(option, Mapping)]
            record = DecisionRecord(
                decision_index=len(records),
                turn=turn if isinstance(turn, int) else None,
                context=(str(select.get("context")) if select.get("context") is not None else None),
                select_type=(str(select.get("type")) if select.get("type") is not None else None),
                options=options_mappings,
                option_count=len(options) if isinstance(options, list) else 0,
                min_count=int(select.get("minCount", 0) or 0),
                max_count=int(select.get("maxCount", 0) or 0),
                selected_indices=selected,
                legal=legal,
                duration_ms=duration_ms,
                overage_balance_ms=self.decision_budget_ms - duration_ms,
                state_before=self._state_snapshot(observation),
                telemetry_before=telemetry_before,
                error_category=error_category,
                error_message=error_message,
                score=(
                    policy_decision.ranked[0].score
                    if policy_decision and policy_decision.ranked
                    else None
                ),
                reasons=(
                    list(policy_decision.ranked[0].reasons)
                    if policy_decision and policy_decision.ranked
                    else []
                ),
                decision_phase=(policy_decision.decision_phase if policy_decision else ""),
                decision_phase_reason=(
                    policy_decision.decision_phase_reason if policy_decision else ""
                ),
                ranked=self._serialize_ranking(policy_decision),
                features=self._serialize_features(policy_decision),
                fallback_used=policy_decision.fallback_used if policy_decision else False,
                model_backend=policy_decision.model_backend if policy_decision else "",
                model_version=policy_decision.model_version if policy_decision else "",
                tactical=self._policy_tactical(policy),
            )
            records.append(record)
            pending = record
            return result

        return wrapped

    @staticmethod
    def _finalize_decisions(
        decisions: list[DecisionRecord], terminal_raw: Mapping[str, Any]
    ) -> None:
        """Attach the final public snapshot and transition to the last decision."""
        if not decisions:
            return
        last = decisions[-1]
        after = public_snapshot(terminal_raw)
        last.state_after = dict(terminal_raw)
        last.telemetry_after = after
        last.transition = transition(last.telemetry_before, after)
        last.failure_flags = failure_flags(
            selected_indices=last.selected_indices,
            options=last.options,
            before=last.telemetry_before,
            effects=last.transition,
        )

    @staticmethod
    def _latest_public_state(environment: Any) -> Mapping[str, Any]:
        """Return the latest current mapping exposed by CABT's step history."""
        candidates: list[Mapping[str, Any]] = []
        for step in getattr(environment, "steps", []):
            if not isinstance(step, list):
                continue
            for player_step in step:
                if not isinstance(player_step, Mapping):
                    continue
                observation = player_step.get("observation")
                current = observation.get("current") if isinstance(observation, Mapping) else None
                if isinstance(current, Mapping):
                    candidates.append(current)
        if not candidates:
            return {}
        return max(
            candidates,
            key=lambda current: (
                int(current.get("turn", 0) or 0),
                int(current.get("turnActionCount", 0) or 0),
            ),
        )

    @staticmethod
    def _policy_decision(policy: AgentCallable) -> PolicyDecision | None:
        owner = getattr(policy, "policy_owner", None)
        decision = getattr(owner, "last_decision", None)
        return decision if isinstance(decision, PolicyDecision) else None

    @staticmethod
    def _policy_tactical(policy: AgentCallable) -> dict[str, Any]:
        """Serialize optional public tactical ledgers owned by a policy."""
        owner = getattr(policy, "policy_owner", None)
        result: dict[str, Any] = {}
        for name in ("turn_ledger", "match_ledger"):
            ledger = getattr(owner, name, None)
            if ledger is not None and is_dataclass(ledger):
                result[name] = asdict(cast(Any, ledger))
        return result

    @staticmethod
    def _serialize_ranking(decision: PolicyDecision | None) -> list[dict[str, Any]]:
        if decision is None:
            return []
        return [
            {
                "indices": list(item.indices),
                "score": item.score,
                "rank": item.rank,
                "reasons": list(item.reasons),
                "margin_to_next": item.margin_to_next,
            }
            for item in decision.ranked
        ]

    @staticmethod
    def _serialize_features(decision: PolicyDecision | None) -> list[dict[str, Any]]:
        if decision is None:
            return []
        return [
            {
                "indices": list(item.selection.indices),
                "schema_version": item.schema_version,
                "values": list(item.values),
            }
            for item in decision.features
        ]

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


@contextlib.contextmanager
def _quiet_native_sdk_output(enabled: bool) -> Iterator[None]:
    """Suppress noisy native CABT diagnostics without altering SDK state."""
    if not enabled:
        yield
        return

    sys.stderr.flush()
    stderr_fd = os.dup(2)
    try:
        with open(os.devnull, "w", encoding="utf-8") as sink:
            os.dup2(sink.fileno(), 2)
            yield
    finally:
        sys.stderr.flush()
        os.dup2(stderr_fd, 2)
        os.close(stderr_fd)


class _SeededRandom:
    def __init__(self, seed: int) -> None:
        self.seed = seed

    def __enter__(self) -> None:
        self._state = random.getstate()
        random.seed(self.seed)

    def __exit__(self, *_: object) -> None:
        random.setstate(self._state)
