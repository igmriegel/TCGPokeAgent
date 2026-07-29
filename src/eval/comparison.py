from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

from .metrics import AggregateMetrics
from .runner import MatchRecord


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


@dataclass(frozen=True, slots=True)
class CompositeMetrics:
    """Normalized metrics used after mandatory operational gates."""

    match_score_rate: float
    worst_matchup_score: float
    prizes_taken: int
    prizes_conceded: int
    p95_decision_ms: float
    fallback_or_invalid_model_decisions: int
    decisions: int

    @property
    def prize_efficiency(self) -> float:
        """Return the fraction of exchanged Prizes taken by the agent."""
        total = self.prizes_taken + self.prizes_conceded
        return self.prizes_taken / total if total else 0.5

    @property
    def latency_score(self) -> float:
        """Return a normalized score against the 100 ms non-search budget."""
        return max(0.0, min(1.0, 1.0 - self.p95_decision_ms / 100.0))

    @property
    def stability_score(self) -> float:
        """Return the fraction of decisions without model fallback."""
        if not self.decisions:
            return 0.0
        return max(
            0.0,
            1.0 - self.fallback_or_invalid_model_decisions / self.decisions,
        )

    @property
    def promotion_score(self) -> float:
        """Return the agreed win-focused composite score."""
        return (
            0.60 * self.match_score_rate
            + 0.20 * self.worst_matchup_score
            + 0.10 * self.prize_efficiency
            + 0.05 * self.latency_score
            + 0.05 * self.stability_score
        )


def paired_bootstrap_lower_bound(
    baseline: Sequence[MatchRecord],
    candidate: Sequence[MatchRecord],
    *,
    samples: int = 2000,
    seed: int = 42,
) -> float:
    """Return the deterministic 95% lower bound of paired match-score delta.

    Args:
        baseline: Baseline matches keyed by seed and side.
        candidate: Candidate matches keyed by the same seed and side.
        samples: Bootstrap resamples.
        seed: Deterministic sampler seed.

    Returns:
        Lower percentile of candidate-minus-baseline match score.
    """
    baseline_by_key = {(match.seed, match.agent_side): match for match in baseline}
    candidate_by_key = {(match.seed, match.agent_side): match for match in candidate}
    keys = sorted(set(baseline_by_key).intersection(candidate_by_key))
    if not keys:
        return 0.0
    deltas = [
        _match_score(candidate_by_key[key].result) - _match_score(baseline_by_key[key].result)
        for key in keys
    ]
    generator = random.Random(seed)
    estimates = sorted(
        sum(generator.choice(deltas) for _ in deltas) / len(deltas) for _ in range(samples)
    )
    return estimates[int(0.025 * (len(estimates) - 1))]


def _match_score(result: str | None) -> float:
    return {"win": 1.0, "draw": 0.5, "loss": 0.0}.get(result or "", 0.0)
