from __future__ import annotations

from dataclasses import dataclass

from .metrics import AggregateMetrics


@dataclass(slots=True)
class PairedComparison:
    baseline: AggregateMetrics
    candidate: AggregateMetrics
    win_rate_diff: float = 0.0
    ci_overlap: bool = True


def compare(baseline: AggregateMetrics, candidate: AggregateMetrics) -> PairedComparison:
    diff = candidate.win_rate - baseline.win_rate
    overlap = not (
        candidate.wilson_lower > baseline.wilson_upper
        or candidate.wilson_upper < baseline.wilson_lower
    )
    return PairedComparison(
        baseline=baseline,
        candidate=candidate,
        win_rate_diff=diff,
        ci_overlap=overlap,
    )
