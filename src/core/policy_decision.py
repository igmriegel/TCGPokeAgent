"""Auditable decision records shared by every selection policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .selection import Selection

if TYPE_CHECKING:
    from .strategy import RankedSelection


@dataclass(frozen=True, slots=True)
class SelectionFeatures:
    """Ordered feature vector for one legal selection.

    Attributes:
        selection: Legal simulator selection represented by the row.
        schema_version: Version of the ordered feature contract.
        values: Numeric values in exact schema order.
        heuristic_score: Reference heuristic score used for fallback and tracing.
        heuristic_reasons: Stable reason codes emitted by the reference scorer.
    """

    selection: Selection
    schema_version: str
    values: tuple[float, ...]
    heuristic_score: float
    heuristic_reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CandidateTrace:
    """Actor-visible candidate facts preserved for one audit trace."""

    option_index: int
    option_type: str
    option: dict[str, Any]
    card: dict[str, Any]
    attack: dict[str, Any]


@dataclass(frozen=True, slots=True)
class DecisionStageTrace:
    """Selection population before and after one policy stage."""

    name: str
    before: tuple[tuple[int, ...], ...]
    after: tuple[tuple[int, ...], ...]
    removed: tuple[tuple[int, ...], ...]
    reason: str = ""


@dataclass(frozen=True, slots=True)
class DecisionTrace:
    """JSON-friendly explanation of one policy decision."""

    schema_version: str
    select_context: str
    min_count: int
    max_count: int
    remain_energy_cost: int
    remain_damage_counter: int
    candidates: tuple[CandidateTrace, ...]
    stages: tuple[DecisionStageTrace, ...]
    ranked_scores: tuple[tuple[tuple[int, ...], float, tuple[str, ...]], ...]
    selected_indices: tuple[int, ...]
    objective_before: str = ""
    objective_after: str = ""
    policy_variant: str = ""
    source_commit: str = ""
    package_sha256: str = ""


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """Complete internal result for one externally compatible policy call.

    Attributes:
        selection: Selection returned to the simulator.
        ranked: Ordered alternatives produced by the active or fallback ranker.
        features: Feature vectors supplied to the ranker.
        decision_phase: Sequencing phase that won the final decision.
        decision_phase_reason: Stable audit reason for the winning phase.
        fallback_used: Whether learned inference failed and heuristic ranking ran.
        model_backend: Backend that produced the final ranking.
        model_version: Immutable model identifier or heuristic version.
        duration_ms: End-to-end policy latency in milliseconds.
    """

    selection: Selection
    ranked: tuple[RankedSelection, ...]
    features: tuple[SelectionFeatures, ...]
    decision_phase: str
    decision_phase_reason: str
    fallback_used: bool
    model_backend: str
    model_version: str
    duration_ms: float
    trace: DecisionTrace | None = None
