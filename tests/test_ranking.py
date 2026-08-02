"""Focused contracts for shared ranking features, groups, and fallback."""

from __future__ import annotations

from dataclasses import replace

from src.agents.heuristic import HeuristicAgent
from src.core import OptionType, Selection, SelectionFeatures
from src.ranking.dataset import (
    GroupedRankingDataset,
    RankGroup,
    RankingRow,
    expert_group,
    split_rank_groups,
)
from src.ranking.features import FEATURE_SCHEMA
from src.rfl.feedback import (
    FeedbackEventV2,
    InsightRecord,
    InsightStatus,
    ReviewCandidate,
    prioritize_review_queue,
)


class BrokenRanker:
    """Ranker fixture that deterministically exercises heuristic fallback."""

    backend = "xgboost_ranker"
    model_version = "broken"

    def rank(self, decision, selections, features):
        raise RuntimeError("inference failed")


def _feature(index: int, value: float = 0.0) -> SelectionFeatures:
    selection = Selection((index,), (OptionType.CARD,))
    values = (value,) * len(FEATURE_SCHEMA.names)
    return SelectionFeatures(selection, FEATURE_SCHEMA.version, values, value)


def test_policy_decision_records_ranking_features_margin_and_fallback(sample_observation) -> None:
    heuristic = HeuristicAgent()
    selected = heuristic.select(sample_observation)
    decision = heuristic.last_decision

    assert decision is not None
    assert list(decision.selection.indices) == selected
    assert len(decision.ranked) == len(decision.features) == 3
    assert [item.rank for item in decision.ranked] == [1, 2, 3]
    assert decision.ranked[0].margin_to_next >= 0.0
    assert decision.decision_phase == "ATTACK"
    assert decision.decision_phase_reason == "attack"
    assert decision.model_backend == "heuristic"
    assert not decision.fallback_used

    learned = HeuristicAgent(ranker=BrokenRanker())
    assert learned.select(sample_observation) == selected
    assert learned.last_decision is not None
    assert learned.last_decision.fallback_used
    assert learned.last_decision.model_backend == "heuristic"
    assert learned.fallback_count == 1


def test_expert_groups_only_label_reviewed_alternatives() -> None:
    event = FeedbackEventV2(
        feedback_id="f-1",
        origin="marimo",
        reviewer="reviewer",
        replay_id="r-1",
        replay_sha256="a" * 64,
        match_id="m-1",
        deck_id="d-1",
        decision_id="q-1",
        visible_state={"turn": 1},
        legal_options=({}, {}, {}, {}),
        actual_selection=(0,),
        preferred=((0,),),
        acceptable=((1,),),
        rejected=((2,),),
        justification="Develop the board before attacking.",
        confidence=1.0,
        created_at="2026-01-01T00:00:00Z",
    )
    group = expert_group(event, [_feature(index) for index in range(4)])

    assert [row.relevance for row in group.rows] == [3, 2, 0]
    assert {row.selection for row in group.rows} == {(0,), (1,), (2,)}
    assert (3,) not in {row.selection for row in group.rows}
    dataset = GroupedRankingDataset((group,))
    assert dataset.qids == ["q-1", "q-1", "q-1"]
    assert dataset.group_sizes == [3]


def test_rank_groups_do_not_cross_match_or_reserved_deck_splits() -> None:
    groups = []
    for index in range(10):
        decision_id = f"q-{index}"
        groups.append(
            RankGroup(
                decision_id,
                f"m-{index}",
                "reserved" if index == 2 else "active",
                f"2026-01-{index + 1:02d}",
                "expert",
                (
                    RankingRow(decision_id, (0,), 3, 1.0, (1.0,)),
                    RankingRow(decision_id, (1,), 0, 1.0, (0.0,)),
                ),
            )
        )

    splits = split_rank_groups(groups, holdout_decks={"reserved"})
    match_sets = {
        name: {group.match_id for group in dataset.groups} for name, dataset in splits.items()
    }

    assert match_sets["train"].isdisjoint(match_sets["validation"])
    assert match_sets["train"].isdisjoint(match_sets["holdout"])
    assert "m-2" in match_sets["holdout"]


def test_review_queue_prioritizes_frozen_signals_deterministically() -> None:
    base = ReviewCandidate("control", "win")
    candidates = [
        base,
        replace(base, decision_id="rare", rare_context=True),
        replace(
            base,
            decision_id="triple",
            ranker_choices=(
                ("heuristic", (0,)),
                ("xgboost_ranker", (1,)),
                ("lightgbm_ranker", (2,)),
            ),
        ),
        replace(base, decision_id="margin", top_margin=0.1),
        replace(
            base,
            decision_id="loss",
            outcome="loss",
            policy_divergence=True,
        ),
        replace(base, decision_id="failure", operational_failure=True),
    ]

    assert [item.decision_id for item in prioritize_review_queue(candidates)] == [
        "failure",
        "loss",
        "margin",
        "triple",
        "rare",
        "control",
    ]


def test_feature_schema_excludes_future_hidden_and_identity_signals() -> None:
    names = " ".join(FEATURE_SCHEMA.names)

    for forbidden in ("future", "hidden", "reward", "result", "player_identity"):
        assert forbidden not in names


def test_insight_requires_frozen_evidence_before_validation() -> None:
    insight = InsightRecord(
        insight_id="i-1",
        scope="board development",
        status=InsightStatus.CANDIDATE,
        feedback_ids=("f-1",),
    )

    triaged = insight.transition(InsightStatus.TRIAGED)
    ready = triaged.transition(InsightStatus.EXPERIMENT_READY)
    validated = ready.transition(
        InsightStatus.VALIDATED,
        fixture="tests/fixtures/board.json",
        experiment="exp-1",
        metric="top1_agreement",
    )

    assert validated.status is InsightStatus.VALIDATED
