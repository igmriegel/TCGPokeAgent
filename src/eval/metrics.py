from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from .runner import MatchRecord


@dataclass(slots=True)
class AggregateMetrics:
    total: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    errors: int = 0
    win_rate: float = 0.0
    wilson_lower: float = 0.0
    wilson_upper: float = 0.0
    avg_duration_ms: float = 0.0
    p50_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0
    p99_duration_ms: float = 0.0
    p50_decision_ms: float = 0.0
    p95_decision_ms: float = 0.0
    p99_decision_ms: float = 0.0
    invalid: int = 0
    timeouts: int = 0


def aggregate(matches: Sequence[MatchRecord]) -> AggregateMetrics:
    total = len(matches)
    if total == 0:
        return AggregateMetrics()

    wins = sum(1 for m in matches if m.result == "win")
    draws = sum(1 for m in matches if m.result == "draw")
    losses = sum(1 for m in matches if m.result == "loss")
    errors = sum(1 for m in matches if str(m.status) not in {"ok", "ExecutionStatus.OK"})
    invalid = sum(1 for m in matches if str(m.status) in {"invalid", "ExecutionStatus.INVALID"})
    timeouts = sum(1 for m in matches if str(m.status) in {"timeout", "ExecutionStatus.TIMEOUT"})

    win_rate = wins / total if total > 0 else 0.0

    durations = sorted(m.duration_ms for m in matches)
    decision_durations = sorted(
        decision.duration_ms for match in matches for decision in match.decisions
    )

    def percentile(values: list[float], p: float) -> float:
        if not values:
            return 0.0
        k = (p / 100) * (len(values) - 1)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return values[f]
        return values[f] * (c - k) + values[c] * (k - f)

    z = 1.96
    wilson_lower, wilson_upper = _wilson(wins, total, z)

    return AggregateMetrics(
        total=total,
        wins=wins,
        draws=draws,
        losses=losses,
        errors=errors,
        win_rate=win_rate,
        wilson_lower=wilson_lower,
        wilson_upper=wilson_upper,
        avg_duration_ms=sum(durations) / len(durations) if durations else 0.0,
        p50_duration_ms=percentile(durations, 50),
        p95_duration_ms=percentile(durations, 95),
        p99_duration_ms=percentile(durations, 99),
        p50_decision_ms=percentile(decision_durations, 50),
        p95_decision_ms=percentile(decision_durations, 95),
        p99_decision_ms=percentile(decision_durations, 99),
        invalid=invalid,
        timeouts=timeouts,
    )


def _wilson(wins: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = wins / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return max(0.0, center - margin), min(1.0, center + margin)
