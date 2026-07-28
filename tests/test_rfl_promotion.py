from __future__ import annotations

from src.eval.metrics import AggregateMetrics
from src.rfl.annotations import ExpertAnnotation
from src.rfl.promotion import (
    PreferenceMetrics,
    PromotionCriteria,
    apply_promotion_gates,
    evaluate_preferences,
)
from src.rfl.schemas import DecisionTrace


def _trace() -> DecisionTrace:
    return DecisionTrace(
        "match-1",
        0,
        "deck",
        "hash",
        "matchup",
        1,
        {},
        [{"type": "YES"}],
        [0, 1],
        [0],
        [0],
        duration_ms=4,
    )


def test_preference_metrics_use_only_legal_annotated_decisions() -> None:
    annotation = ExpertAnnotation("deck", "hash", "matchup", "match-1", 1, [0], [[1]])
    metrics = evaluate_preferences([_trace()], [annotation], lambda trace: [0])
    assert metrics.top1_agreement == 1.0
    assert metrics.pairwise_preference_accuracy == 1.0


def test_promotion_rejects_failures_and_regression() -> None:
    decision = apply_promotion_gates(
        PreferenceMetrics(top1_agreement=1.0, top_k_agreement=1.0, p95_latency_ms=1.0),
        AggregateMetrics(win_rate=0.4),
        AggregateMetrics(win_rate=0.5),
        criteria=PromotionCriteria(min_top1_agreement=0.8),
        operational_failures=1,
    )
    assert not decision.promoted
    assert "operational_failures_present" in decision.reasons
    assert "holdout_win_rate_regression" in decision.reasons
