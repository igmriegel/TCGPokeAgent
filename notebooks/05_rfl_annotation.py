"""Marimo annotation workbench for legal decision traces.

Run with ``marimo edit notebooks/05_rfl_annotation.py`` when the optional
notebooks dependency is installed. The persistence layer remains usable without
Marimo, which is important for the submission package.
"""

import marimo

__generated_with = "0.23.15"
app = marimo.App()


@app.cell
def _():
    from pathlib import Path

    import marimo as mo

    from src.rfl.annotations import AnnotationStore, ExpertAnnotation

    annotation_store_cls = AnnotationStore
    expert_annotation_cls = ExpertAnnotation
    path_cls = Path
    return annotation_store_cls, expert_annotation_cls, mo, path_cls


@app.cell
def _(mo):
    path = mo.ui.text(value="../runs/rfl/annotations.jsonl", label="Annotation JSONL")
    match_id = mo.ui.text(label="Match ID")
    deck_id = mo.ui.text(label="Deck ID")
    matchup = mo.ui.text(label="Matchup")
    turn = mo.ui.number(value=0, label="Turn")
    preferred = mo.ui.text(label="Preferred indices, e.g. 0,2")
    rejected = mo.ui.text(label="Rejected plays, e.g. 1;0,2")
    justification = mo.ui.text_area(label="Justification")
    confidence = mo.ui.slider(0, 1, value=0.5, step=0.05, label="Confidence")
    save = mo.ui.run_button(label="Save annotation")
    return (
        confidence,
        deck_id,
        justification,
        match_id,
        matchup,
        path,
        preferred,
        rejected,
        save,
        turn,
    )


@app.cell
def _(
    annotation_store_cls,
    confidence,
    deck_id,
    expert_annotation_cls,
    justification,
    match_id,
    matchup,
    path,
    path_cls,
    preferred,
    rejected,
    save,
    turn,
):
    if save.value:

        def parse_play(value: str) -> list[int]:
            return [int(item.strip()) for item in value.split(",") if item.strip()]

        rejected_plays = [parse_play(item) for item in rejected.value.split(";") if item.strip()]
        annotation = expert_annotation_cls(
            deck_id.value,
            "unknown",
            matchup.value,
            match_id.value,
            int(turn.value),
            parse_play(preferred.value),
            rejected_plays,
            justification=justification.value,
            confidence=confidence.value,
            specialist_version="marimo-v1",
        )
        annotation_store_cls(path_cls(path.value)).append(
            annotation, set(annotation.preferred_actions).union(*rejected_plays)
        )
        _status = "Saved"
    else:
        _status = ""
    _status
    return


if __name__ == "__main__":
    app.run()
