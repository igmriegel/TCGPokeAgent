"""Marimo workbench for prioritized FeedbackEventV2 review."""

from __future__ import annotations

import marimo

__generated_with = "0.23.15"
app = marimo.App()


@app.cell
def _():
    import json
    from pathlib import Path

    import marimo as mo

    from src.rfl.feedback import (
        FeedbackEventV2,
        FeedbackStoreV2,
        ReviewCandidate,
        prioritize_review_queue,
    )

    feedback_event_cls = FeedbackEventV2
    feedback_store_cls = FeedbackStoreV2
    path_cls = Path
    review_candidate_cls = ReviewCandidate
    return (
        feedback_event_cls,
        feedback_store_cls,
        json,
        mo,
        path_cls,
        prioritize_review_queue,
        review_candidate_cls,
    )


@app.cell
def _(mo):
    queue_path = mo.ui.text(
        value="../runs/rfl/review_candidates.jsonl", label="Review candidate JSONL"
    )
    feedback_path = mo.ui.text(value="../runs/rfl/feedback_v2.jsonl", label="FeedbackEventV2 JSONL")
    refresh = mo.ui.run_button(label="Refresh prioritized queue")
    return feedback_path, queue_path, refresh


@app.cell
def _(json, path_cls, prioritize_review_queue, queue_path, refresh, review_candidate_cls):
    _ = refresh.value
    _source = path_cls(queue_path.value)
    _records = []
    if _source.is_file():
        for _line in _source.read_text(encoding="utf-8").splitlines():
            if not _line.strip():
                continue
            _item = json.loads(_line)
            _records.append(
                review_candidate_cls(
                    decision_id=str(_item["decision_id"]),
                    outcome=str(_item.get("outcome", "unknown")),
                    operational_failure=bool(_item.get("operational_failure", False)),
                    board_collapse=bool(_item.get("board_collapse", False)),
                    policy_divergence=bool(_item.get("policy_divergence", False)),
                    top_margin=float(_item.get("top_margin", float("inf"))),
                    ranker_choices=tuple(
                        (str(_backend), tuple(int(_index) for _index in _selection))
                        for _backend, _selection in _item.get("ranker_choices", {}).items()
                    ),
                    rare_context=bool(_item.get("rare_context", False)),
                )
            )
    prioritized = prioritize_review_queue(_records)
    queue_rows = [
        {
            "position": _index + 1,
            "decision_id": _item.decision_id,
            "outcome": _item.outcome,
            "margin": _item.top_margin,
            "choices": dict(_item.ranker_choices),
        }
        for _index, _item in enumerate(prioritized)
    ]
    queue_rows
    return


@app.cell
def _(mo):
    feedback_id = mo.ui.text(label="Feedback ID")
    reviewer = mo.ui.text(label="Reviewer")
    replay_id = mo.ui.text(label="Replay ID")
    replay_sha256 = mo.ui.text(label="Replay SHA-256")
    match_id = mo.ui.text(label="Match ID")
    deck_id = mo.ui.text(label="Deck ID")
    decision_id = mo.ui.text(label="Decision ID")
    visible_state = mo.ui.text_area(label="Visible state JSON")
    legal_options = mo.ui.text_area(label="Legal options JSON list")
    actual = mo.ui.text(label="Actual selection, e.g. 0,2")
    preferred = mo.ui.text(label="Preferred selections, e.g. 0;0,2")
    acceptable = mo.ui.text(label="Acceptable selections")
    rejected = mo.ui.text(label="Rejected selections")
    justification = mo.ui.text_area(label="English justification")
    confidence = mo.ui.slider(0, 1, value=0.5, step=0.05, label="Confidence")
    tags = mo.ui.text(label="Tags, comma-separated")
    lineage = mo.ui.text(label="Lineage IDs, comma-separated")
    save = mo.ui.run_button(label="Save immutable feedback")
    return (
        acceptable,
        actual,
        confidence,
        decision_id,
        deck_id,
        feedback_id,
        justification,
        legal_options,
        lineage,
        match_id,
        preferred,
        rejected,
        replay_id,
        replay_sha256,
        reviewer,
        save,
        tags,
        visible_state,
    )


@app.cell
def _(
    acceptable,
    actual,
    confidence,
    decision_id,
    deck_id,
    feedback_id,
    feedback_path,
    feedback_event_cls,
    feedback_store_cls,
    json,
    justification,
    legal_options,
    lineage,
    match_id,
    path_cls,
    preferred,
    rejected,
    replay_id,
    replay_sha256,
    reviewer,
    save,
    tags,
    visible_state,
):
    def _selection(value: str) -> tuple[int, ...]:
        return tuple(int(item.strip()) for item in value.split(",") if item.strip())

    def _selection_group(value: str) -> tuple[tuple[int, ...], ...]:
        return tuple(_selection(item) for item in value.split(";") if item.strip())

    if save.value:
        _event = feedback_event_cls(
            feedback_id=feedback_id.value,
            origin="marimo",
            reviewer=reviewer.value,
            replay_id=replay_id.value,
            replay_sha256=replay_sha256.value,
            match_id=match_id.value,
            deck_id=deck_id.value,
            decision_id=decision_id.value,
            visible_state=dict(json.loads(visible_state.value)),
            legal_options=tuple(dict(item) for item in json.loads(legal_options.value)),
            actual_selection=_selection(actual.value),
            preferred=_selection_group(preferred.value),
            acceptable=_selection_group(acceptable.value),
            rejected=_selection_group(rejected.value),
            justification=justification.value,
            confidence=float(confidence.value),
            tags=tuple(item.strip() for item in tags.value.split(",") if item.strip()),
            lineage=tuple(item.strip() for item in lineage.value.split(",") if item.strip()),
        )
        feedback_store_cls(path_cls(feedback_path.value), feedback_event_cls).append(_event)
        _status = "Saved FeedbackEventV2"
    else:
        _status = ""
    _status
    return


if __name__ == "__main__":
    app.run()
