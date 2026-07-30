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

    from src.core import catalog as card_catalog
    from src.data.replay_outcomes import load_replay_outcomes

    return card_catalog, json, load_replay_outcomes, mo, os, pathlib, pd, plt


@app.cell
def _(card_catalog):
    catalog = card_catalog.CardCatalog.from_cg()
    return (catalog,)


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
    replay_reload = mo.ui.run_button(label="Reload downloaded replays")
    mo.vstack(
        [
            mo.md("## Competitive replay termination monitor"),
            mo.md(
                "The terminal `Result` log is authoritative. Board, deck, and "
                "Prize counts are retained as consistency evidence."
            ),
            mo.hstack([owner_name, outcome_filter, reason_filter, replay_reload]),
        ]
    )
    return outcome_filter, owner_name, reason_filter, replay_reload, replay_root


@app.cell
def _(load_replay_outcomes, owner_name, pd, replay_reload, replay_root, catalog):
    replay_reload.value
    loaded_replay_outcomes, replay_load_errors = load_replay_outcomes(
        replay_root,
        owner_name=owner_name.value.strip() or None,
        catalog=catalog,
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
        "opponent_name",
        "opponent_deck_archetype",
        "opponent_deck_hash",
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
    latest_episode = (
        str(int(replay_outcomes["episode_id"].max())) if not replay_outcomes.empty else "n/a"
    )
    mo.md(
        f"""
        Replays loaded from `{replay_root}`: **{len(replay_outcomes)}**

        Latest episode: **{latest_episode}** ·
        Result reasons explicit: **{explicit_count}** ·
        Owner outcomes classified: **{owner_classified_count}** ·
        Filtered rows: **{len(filtered_replay_outcomes)}** ·
        Consistency warnings: **{inconsistent_count}** ·
        Load errors: **{len(replay_errors)}**
        """
    )
    return


@app.cell
def _(mo, replay_outcomes):
    if replay_outcomes.empty:
        _output = mo.md("### No downloaded replay snapshot yet")
    else:
        recent_columns = [
            "episode_id",
            "owner_outcome",
            "termination_reason",
            "terminal_turn",
            "reason_consistent",
            "source_path",
        ]
        recent_replays = (
            replay_outcomes[recent_columns]
            .sort_values("episode_id", ascending=False)
            .head(20)
            .assign(
                source_file=lambda frame: frame["source_path"].map(
                    lambda value: value.rsplit("/", maxsplit=1)[-1]
                )
            )
            .drop(columns=["source_path"])
        )
        _output = mo.vstack(
            [
                mo.md("### Latest downloaded competitive replays"),
                mo.md(
                    "Newest 20 episodes discovered in the raw Kaggle replay directory. "
                    "Use **Reload downloaded replays** after fetching another snapshot."
                ),
                recent_replays,
            ]
        )
    _output
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
def _(mo):
    top_n_decks = mo.ui.dropdown(
        options=["5", "10", "15", "20", "all"],
        value="10",
        label="Top N decks to show",
    )
    mo.vstack(
        [
            mo.md("## Matchup analysis"),
            top_n_decks,
        ]
    )
    return (top_n_decks,)


@app.cell
def _(filtered_replay_outcomes, pd, top_n_decks):
    if filtered_replay_outcomes.empty:
        matchup = pd.DataFrame()
    else:
        matchup = (
            filtered_replay_outcomes.groupby("opponent_deck_archetype")
            .agg(
                wins=("owner_outcome", lambda x: (x == "win").sum()),
                losses=("owner_outcome", lambda x: (x == "loss").sum()),
                draws=("owner_outcome", lambda x: (x == "draw").sum()),
                total=("owner_outcome", "count"),
            )
            .assign(win_rate=lambda df: (df["wins"] / df["total"]).round(3))
            .sort_values("total", ascending=False)
        )
        if top_n_decks.value != "all":
            matchup = matchup.head(int(top_n_decks.value))
    return (matchup,)


@app.cell
def _(matchup, mo):
    if matchup.empty:
        _output = mo.md("### No matchup data yet")
    else:
        _output = mo.vstack([mo.md("### Win/loss by opponent deck"), matchup])
    _output
    return


@app.cell
def _(matchup, mo, plt):
    if matchup.empty:
        _output = mo.md("### No matchup chart yet")
    else:
        colors = ["#4c78a8" if wr >= 0.5 else "#e45756" for wr in matchup["win_rate"]]
        fig, ax = plt.subplots(figsize=(10, max(3, len(matchup) * 0.5)))
        bars = ax.barh(matchup.index, matchup["win_rate"], color=colors)
        ax.set_xlabel("Win rate")
        ax.set_title("Win rate by opponent deck")
        ax.set_xlim(0, 1)
        ax.axvline(x=0.5, color="gray", linestyle="--", alpha=0.5)
        for bar, wr in zip(bars, matchup["win_rate"]):
            ax.text(
                bar.get_width() + 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{wr:.1%}",
                va="center",
                fontsize=9,
            )
        fig.tight_layout()
        _output = fig
    _output
    return


@app.cell
def _(filtered_replay_outcomes, mo, pd):
    if filtered_replay_outcomes.empty:
        _output = mo.md("### No opponent data yet")
    else:
        opp = (
            filtered_replay_outcomes.groupby("opponent_name")
            .agg(
                wins=("owner_outcome", lambda x: (x == "win").sum()),
                losses=("owner_outcome", lambda x: (x == "loss").sum()),
                draws=("owner_outcome", lambda x: (x == "draw").sum()),
                total=("owner_outcome", "count"),
            )
            .assign(win_rate=lambda df: (df["wins"] / df["total"]).round(3))
            .sort_values("total", ascending=False)
        )
        _output = mo.vstack([mo.md("### Win/loss by opponent name"), opp])
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
