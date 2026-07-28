"""Post-MVP hybrid reinforcement-from-feedback utilities."""

from .annotations import AnnotationStore, ExpertAnnotation
from .dataset import HybridDataset, HybridExample, TraceStore, partition_traces, split_matches
from .profiles import PolicyProfile, ProfileCompatibilityError, load_profile
from .promotion import (
    PreferenceMetrics,
    PromotionCriteria,
    PromotionDecision,
    apply_promotion_gates,
    evaluate_preferences,
    validate_extracted_package,
    write_promotion_manifest,
)
from .rewards import RewardBreakdown, hybrid_reward
from .schemas import DecisionTrace, FeatureSchema, TurnTrace

__all__ = [
    "AnnotationStore",
    "DecisionTrace",
    "ExpertAnnotation",
    "FeatureSchema",
    "HybridDataset",
    "HybridExample",
    "TraceStore",
    "PolicyProfile",
    "PreferenceMetrics",
    "ProfileCompatibilityError",
    "PromotionCriteria",
    "PromotionDecision",
    "RewardBreakdown",
    "TurnTrace",
    "hybrid_reward",
    "apply_promotion_gates",
    "evaluate_preferences",
    "load_profile",
    "partition_traces",
    "split_matches",
    "validate_extracted_package",
    "write_promotion_manifest",
]
