"""Holdout evaluation and promotion gates for RFL policy profiles."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Sequence

from src.eval.metrics import AggregateMetrics

from .annotations import ExpertAnnotation
from .schemas import DecisionTrace

PolicySelector = Callable[[DecisionTrace], list[int]]


@dataclass(frozen=True, slots=True)
class PreferenceMetrics:
    """Decision-level agreement metrics calculated on held-out annotations."""

    annotated_decisions: int = 0
    top1_agreement: float = 0.0
    top_k_agreement: float = 0.0
    pairwise_preference_accuracy: float = 0.0
    evaluated_decisions: int = 0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class PromotionCriteria:
    """Explicit thresholds required before a candidate can be promoted."""

    min_top1_agreement: float = 0.0
    min_top_k_agreement: float = 0.0
    max_p95_latency_ms: float = 100.0
    max_operational_failures: int = 0
    max_invalid_decisions: int = 0
    max_win_rate_regression: float = 0.0
    require_package_validation: bool = True


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    """Auditable result of applying promotion gates."""

    promoted: bool
    reasons: tuple[str, ...] = ()
    preference: PreferenceMetrics = field(default_factory=PreferenceMetrics)
    candidate: AggregateMetrics = field(default_factory=AggregateMetrics)
    baseline: AggregateMetrics = field(default_factory=AggregateMetrics)
    package_valid: bool = False

    def to_dict(self) -> dict[str, object]:
        """Serialize the decision for a run manifest."""
        return {
            "promoted": self.promoted,
            "reasons": list(self.reasons),
            "preference": asdict(self.preference),
            "candidate": asdict(self.candidate),
            "baseline": asdict(self.baseline),
            "package_valid": self.package_valid,
        }


def _percentile(values: Sequence[float], percentile: float) -> float:
    """Calculate an interpolated percentile without a third-party dependency."""
    if not values:
        return 0.0
    ordered = sorted(values)
    position = percentile / 100 * (len(ordered) - 1)
    lower, upper = int(position), min(len(ordered) - 1, int(position) + 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def evaluate_preferences(
    traces: Iterable[DecisionTrace],
    annotations: Iterable[ExpertAnnotation],
    selector: PolicySelector,
) -> PreferenceMetrics:
    """Evaluate a policy only on annotated decisions and legal trace options."""
    by_key = {(annotation.match_id, annotation.turn): annotation for annotation in annotations}
    top1 = top_k = evaluated = 0
    pairwise = 0.0
    latencies: list[float] = []
    for trace in traces:
        annotation = by_key.get((trace.match_id, trace.turn))
        if annotation is None:
            continue
        annotation.validate_against(trace.original_indices)
        selected = selector(trace)
        if any(index not in trace.original_indices for index in selected):
            continue
        evaluated += 1
        latencies.append(trace.duration_ms)
        if selected == annotation.preferred_actions:
            top1 += 1
        accepted = [annotation.preferred_actions, *annotation.acceptable_actions]
        if selected in accepted:
            top_k += 1
        if selected == annotation.preferred_actions:
            pairwise += len(annotation.rejected_actions)
        elif selected in annotation.rejected_actions:
            pairwise += 0
        else:
            pairwise += len(annotation.rejected_actions) / 2
    rejected_pairs = sum(len(annotation.rejected_actions) for annotation in by_key.values())
    return PreferenceMetrics(
        annotated_decisions=len(by_key),
        top1_agreement=top1 / evaluated if evaluated else 0.0,
        top_k_agreement=top_k / evaluated if evaluated else 0.0,
        pairwise_preference_accuracy=pairwise / rejected_pairs if rejected_pairs else 0.0,
        evaluated_decisions=evaluated,
        p50_latency_ms=_percentile(latencies, 50),
        p95_latency_ms=_percentile(latencies, 95),
        p99_latency_ms=_percentile(latencies, 99),
    )


def apply_promotion_gates(
    preference: PreferenceMetrics,
    candidate: AggregateMetrics,
    baseline: AggregateMetrics,
    *,
    criteria: PromotionCriteria | None = None,
    operational_failures: int = 0,
    invalid_decisions: int = 0,
    package_valid: bool = True,
) -> PromotionDecision:
    """Return a promotion decision with every failed gate named."""
    rules = criteria or PromotionCriteria()
    reasons: list[str] = []
    if preference.top1_agreement < rules.min_top1_agreement:
        reasons.append("specialist_top1_below_threshold")
    if preference.top_k_agreement < rules.min_top_k_agreement:
        reasons.append("specialist_top_k_below_threshold")
    if preference.p95_latency_ms > rules.max_p95_latency_ms:
        reasons.append("decision_latency_over_budget")
    effective_failures = max(operational_failures, candidate.errors)
    if effective_failures > rules.max_operational_failures:
        reasons.append("operational_failures_present")
    if invalid_decisions > rules.max_invalid_decisions:
        reasons.append("invalid_decisions_present")
    if candidate.win_rate < baseline.win_rate - rules.max_win_rate_regression:
        reasons.append("holdout_win_rate_regression")
    if rules.require_package_validation and not package_valid:
        reasons.append("package_validation_failed")
    return PromotionDecision(
        promoted=not reasons,
        reasons=tuple(reasons),
        preference=preference,
        candidate=candidate,
        baseline=baseline,
        package_valid=package_valid,
    )


def write_promotion_manifest(path: str | Path, decision: PromotionDecision) -> None:
    """Write a stable JSON promotion manifest."""
    Path(path).write_text(json.dumps(decision.to_dict(), indent=2, sort_keys=True))
