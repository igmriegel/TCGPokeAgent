"""Explore aggregated experiment reports produced in ``reports/``."""

import marimo

__generated_with = "0.23.15"
app = marimo.App()


@app.cell
def _():
    import json
    import os
    import pathlib

    import marimo as mo
    import matplotlib.pyplot as plt
    import pandas as pd

    from src.data.replay_outcomes import load_replay_outcomes

    return json, load_replay_outcomes, mo, os, pathlib, pd, plt


@app.cell
def _(json, pathlib, pd):
    root_candidates = [pathlib.Path("reports"), pathlib.Path("../reports")]
    report_root = next((path for path in root_candidates if path.exists()), root_candidates[0])
    rows = []
    for report_path in sorted(report_root.rglob("*.json")):
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            required_fields = {"config", "agent_mode", "total_matches", "metrics"}
            if not isinstance(report, dict) or not required_fields.issubset(report):
                continue
            metrics = report.get("metrics", {})
            if not isinstance(metrics, dict):
                continue
            rows.append(
                {
                    "report": report_path.name,
                    "path": str(report_path),
                    "config": str(report.get("config", "unknown")),
                    "agent_mode": str(report.get("agent_mode", "unknown")),
                    "matches": report.get("total_matches", metrics.get("total", 0)),
                    "wins": metrics.get("wins", 0),
                    "draws": metrics.get("draws", 0),
                    "losses": metrics.get("losses", 0),
                    "errors": metrics.get("errors", 0),
                    "win_rate": metrics.get("win_rate", 0.0),
                    "avg_duration_ms": metrics.get("avg_duration_ms", 0.0),
                    "p95_duration_ms": metrics.get("p95_duration_ms", 0.0),
                }
            )
        except (OSError, json.JSONDecodeError, TypeError):
            continue
    columns = [
        "report",
        "path",
        "config",
        "agent_mode",
        "matches",
        "wins",
        "draws",
        "losses",
        "errors",
        "win_rate",
        "avg_duration_ms",
        "p95_duration_ms",
    ]
    reports = pd.DataFrame(rows, columns=columns)
    return report_root, reports


@app.cell
def _(mo, report_root, reports):
    if reports.empty:
        message = (
            f"No JSON reports found under `{report_root}`. Run an experiment first; "
            "the cells below will populate automatically."
        )
        _output = mo.md(f"# Run results dashboard\n\n> {message}")
    else:
        _output = mo.vstack(
            [
                mo.md("# Run results dashboard"),
                mo.md(f"Reports loaded: **{len(reports)}** from `{report_root}`"),
                reports.drop(columns=["path"]),
            ]
        )
    _output
    return


@app.cell
def _(mo, pd, reports):
    if reports.empty:
        _output = mo.md("## No comparison chart yet")
    else:
        outcome_rows = []
        for _, row in reports.iterrows():
            for outcome in ("wins", "draws", "losses", "errors"):
                outcome_rows.append(
                    {
                        "label": f"{row['agent_mode']} / {row['config']}",
                        "outcome": outcome,
                        "matches": row[outcome],
                    }
                )
        outcome_table = pd.DataFrame(outcome_rows)
        _output = mo.vstack([mo.md("## Outcome table"), outcome_table])
    _output
    return


@app.cell
def _(mo, plt, reports):
    if reports.empty:
        _output = mo.md("## No duration chart yet")
    else:
        figure, axes = plt.subplots(1, 2, figsize=(12, 4))
        labels = reports["agent_mode"] + " / " + reports["config"]
        axes[0].bar(labels, reports["win_rate"], color="#4c78a8")
        axes[0].set_title("Win rate")
        axes[0].set_ylim(0, 1)
        axes[0].tick_params(axis="x", rotation=35)
        axes[1].bar(labels, reports["p95_duration_ms"], color="#f58518")
        axes[1].set_title("p95 match duration (ms)")
        axes[1].tick_params(axis="x", rotation=35)
        figure.tight_layout()
        _output = figure
    _output
    return


@app.cell
def _(mo, os, pathlib):
    replay_root_candidates = [
        pathlib.Path("data/raw/kaggle/kaggle_gameplay_runs"),
        pathlib.Path("../data/raw/kaggle/kaggle_gameplay_runs"),
    ]
    replay_root = next(
        (path for path in replay_root_candidates if path.exists()),
        replay_root_candidates[0],
    )
    owner_name = mo.ui.text(
        value=os.getenv("KAGGLE_OWNER_NAME", ""),
        label="Owner agent name",
        placeholder="Enter the Kaggle agent name for W/D/L classification",
    )
    outcome_filter = mo.ui.dropdown(
        options=["all", "win", "loss", "draw", "unknown"],
        value="all",
        label="Owner outcome",
    )
    reason_filter = mo.ui.dropdown(
        options=[
            "all",
            "all_prizes_taken",
            "deck_out",
            "no_pokemon_in_play",
            "draw",
            "unknown",
        ],
        value="all",
        label="Termination reason",
    )
    mo.vstack(
        [
            mo.md("## Competitive replay termination monitor"),
            mo.md(
                "The terminal `Result` log is authoritative. Board, deck, and "
                "Prize counts are retained as consistency evidence."
            ),
            mo.hstack([owner_name, outcome_filter, reason_filter]),
        ]
    )
    return outcome_filter, owner_name, reason_filter, replay_root


@app.cell
def _(load_replay_outcomes, owner_name, pd, replay_root):
    loaded_replay_outcomes, replay_load_errors = load_replay_outcomes(
        replay_root,
        owner_name=owner_name.value.strip() or None,
    )
    replay_columns = [
        "episode_id",
        "owner_outcome",
        "termination_reason",
        "reason_code",
        "reason_explicit",
        "reason_consistent",
        "terminal_turn",
        "winner_prizes_remaining",
        "loser_prizes_remaining",
        "winner_deck_remaining",
        "loser_deck_remaining",
        "winner_pokemon_in_play",
        "loser_pokemon_in_play",
        "source_path",
    ]
    replay_outcomes = pd.DataFrame(
        [outcome.to_dict() for outcome in loaded_replay_outcomes],
        columns=replay_columns,
    )
    replay_errors = pd.DataFrame(replay_load_errors, columns=["path", "error"])
    return replay_errors, replay_outcomes


@app.cell
def _(outcome_filter, reason_filter, replay_outcomes):
    filtered_replay_outcomes = replay_outcomes
    if outcome_filter.value != "all":
        filtered_replay_outcomes = filtered_replay_outcomes[
            filtered_replay_outcomes["owner_outcome"] == outcome_filter.value
        ]
    if reason_filter.value != "all":
        filtered_replay_outcomes = filtered_replay_outcomes[
            filtered_replay_outcomes["termination_reason"] == reason_filter.value
        ]
    return (filtered_replay_outcomes,)


@app.cell
def _(filtered_replay_outcomes, mo, replay_errors, replay_outcomes, replay_root):
    explicit_count = (
        int(replay_outcomes["reason_explicit"].sum()) if not replay_outcomes.empty else 0
    )
    inconsistent_count = (
        int((~replay_outcomes["reason_consistent"]).sum()) if not replay_outcomes.empty else 0
    )
    owner_classified_count = (
        int((replay_outcomes["owner_outcome"] != "unknown").sum())
        if not replay_outcomes.empty
        else 0
    )
    mo.md(
        f"""
        Replays loaded from `{replay_root}`: **{len(replay_outcomes)}**

        Result reasons explicit: **{explicit_count}** ·
        Owner outcomes classified: **{owner_classified_count}** ·
        Filtered rows: **{len(filtered_replay_outcomes)}** ·
        Consistency warnings: **{inconsistent_count}** ·
        Load errors: **{len(replay_errors)}**
        """
    )
    return


@app.cell
def _(filtered_replay_outcomes, mo, pd):
    if filtered_replay_outcomes.empty:
        _output = mo.md("### No termination outcomes match the current filters")
    else:
        termination_matrix = (
            pd.crosstab(
                filtered_replay_outcomes["owner_outcome"],
                filtered_replay_outcomes["termination_reason"],
            )
            .reindex(["win", "draw", "loss", "unknown"], fill_value=0)
            .dropna(axis=0, how="all")
        )
        _output = mo.vstack([mo.md("### Outcomes by termination reason"), termination_matrix])
    _output
    return


@app.cell
def _(filtered_replay_outcomes, mo, pd, plt):
    if filtered_replay_outcomes.empty:
        _output = mo.md("### No termination chart yet")
    else:
        chart_matrix = pd.crosstab(
            filtered_replay_outcomes["owner_outcome"],
            filtered_replay_outcomes["termination_reason"],
        ).reindex(["win", "draw", "loss", "unknown"], fill_value=0)
        chart_matrix = chart_matrix.loc[chart_matrix.sum(axis=1) > 0]
        termination_figure, termination_axis = plt.subplots(figsize=(10, 5))
        chart_matrix.plot(
            kind="bar",
            stacked=True,
            ax=termination_axis,
            color=["#4c78a8", "#f58518", "#e45756", "#72b7b2", "#bab0ac"],
        )
        termination_axis.set_title("Competitive replay outcomes by terminal condition")
        termination_axis.set_xlabel("Owner outcome")
        termination_axis.set_ylabel("Matches")
        termination_axis.tick_params(axis="x", rotation=0)
        termination_axis.legend(title="Termination reason")
        termination_figure.tight_layout()
        _output = termination_figure
    _output
    return


@app.cell
def _(filtered_replay_outcomes, mo):
    if filtered_replay_outcomes.empty:
        _output = mo.md("### No replay details yet")
    else:
        detail_columns = [
            "episode_id",
            "owner_outcome",
            "termination_reason",
            "reason_code",
            "terminal_turn",
            "winner_prizes_remaining",
            "loser_deck_remaining",
            "loser_pokemon_in_play",
            "reason_consistent",
        ]
        replay_detail_table = filtered_replay_outcomes[detail_columns].sort_values(
            "episode_id",
            ascending=False,
        )
        _output = mo.vstack([mo.md("### Replay-level terminal evidence"), replay_detail_table])
    _output
    return


@app.cell
def _(mo, replay_errors, replay_outcomes):
    consistency_warnings = (
        replay_outcomes[~replay_outcomes["reason_consistent"]]
        if not replay_outcomes.empty
        else replay_outcomes
    )
    if replay_errors.empty and consistency_warnings.empty:
        _output = mo.md(
            "### Data quality\n\nAll loaded terminal reasons match their terminal state."
        )
    else:
        quality_items = [mo.md("### Data quality warnings")]
        if not consistency_warnings.empty:
            quality_items.append(
                consistency_warnings[
                    [
                        "episode_id",
                        "reason_code",
                        "termination_reason",
                        "winner_prizes_remaining",
                        "loser_deck_remaining",
                        "loser_pokemon_in_play",
                    ]
                ]
            )
        if not replay_errors.empty:
            quality_items.append(replay_errors)
        _output = mo.vstack(quality_items)
    _output
    return


if __name__ == "__main__":
    app.run()
