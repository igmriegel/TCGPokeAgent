from __future__ import annotations

import time
from dataclasses import dataclass, field

from src.core import ExecutionStatus


@dataclass(slots=True)
class MatchRecord:
    match_id: str
    seed: int
    agent_side: int
    status: ExecutionStatus
    result: str | None = None
    duration_ms: float = 0.0
    decision_count: int = 0
    error_category: str = "none"
    error_message: str = ""


@dataclass(slots=True)
class RunReport:
    config_name: str
    agent_mode: str
    matches: list[MatchRecord] = field(default_factory=list)
    started_at: float = 0.0
    finished_at: float = 0.0

    @property
    def total_matches(self) -> int:
        return len(self.matches)


class MatchRunner:
    def run_match(self, seed: int, agent_mode: str, side: int) -> MatchRecord:
        start = time.perf_counter()
        match_id = f"match_{seed}_{side}"

        try:
            from kaggle_environments import make

            env = make("cabt", debug=False)
            env.run([self._agent_for_mode(agent_mode), "random"])
            result = env.state[0].get("result") if env.state else None
            status = ExecutionStatus.OK
        except Exception:
            result = None
            status = ExecutionStatus.ERROR

        duration_ms = (time.perf_counter() - start) * 1000

        return MatchRecord(
            match_id=match_id,
            seed=seed,
            agent_side=side,
            status=status,
            result=str(result) if result else None,
            duration_ms=duration_ms,
        )

    def _agent_for_mode(self, mode: str) -> str:
        return mode

    def run_batch(
        self, seeds: list[int], agent_mode: str, sides: list[int] | None = None
    ) -> RunReport:
        if sides is None:
            sides = [0, 1]

        report = RunReport(
            config_name="batch",
            agent_mode=agent_mode,
            started_at=time.time(),
        )

        for seed in seeds:
            for side in sides:
                record = self.run_match(seed, agent_mode, side)
                report.matches.append(record)

        report.finished_at = time.time()
        return report
