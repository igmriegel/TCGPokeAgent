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


def aggregate(matches: Sequence[MatchRecord]) -> AggregateMetrics:
    total = len(matches)
    if total == 0:
        return AggregateMetrics()

    wins = sum(1 for m in matches if m.result == "win")
    draws = sum(1 for m in matches if m.result == "draw")
    losses = sum(1 for m in matches if m.result == "loss")
    errors = sum(1 for m in matches if m.status != "ok")

    win_rate = wins / total if total > 0 else 0.0

    durations = sorted(m.duration_ms for m in matches)

    def percentile(p: float) -> float:
        if not durations:
            return 0.0
        k = (p / 100) * (len(durations) - 1)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return durations[f]
        return durations[f] * (c - k) + durations[c] * (k - f)

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
        p50_duration_ms=percentile(50),
        p95_duration_ms=percentile(95),
        p99_duration_ms=percentile(99),
    )


def _wilson(wins: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = wins / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return max(0.0, center - margin), min(1.0, center + margin)
