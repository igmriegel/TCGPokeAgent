"""Explore aggregated experiment reports produced in ``reports/``."""

import marimo

__generated_with = "0.23.15"
app = marimo.App()


@app.cell
def _():
    import json
    import pathlib

    import marimo as mo
    import matplotlib.pyplot as plt
    import pandas as pd

    return json, mo, pathlib, pd, plt


@app.cell
def _(json, pathlib, pd):
    root_candidates = [pathlib.Path("reports"), pathlib.Path("../reports")]
    report_root = next((path for path in root_candidates if path.exists()), root_candidates[0])
    rows = []
    for report_path in sorted(report_root.rglob("*.json")):
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            metrics = report.get("metrics", {})
            rows.append(
                {
                    "report": report_path.name,
                    "path": str(report_path),
                    "config": report.get("config", "unknown"),
                    "agent_mode": report.get("agent_mode", "unknown"),
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
        mo.md(f"# Run results dashboard\n\n> {message}")
    else:
        mo.vstack(
            [
                mo.md("# Run results dashboard"),
                mo.md(f"Reports loaded: **{len(reports)}** from `{report_root}`"),
                reports.drop(columns=["path"]),
            ]
        )
    return


@app.cell
def _(mo, pd, reports):
    if reports.empty:
        mo.md("## No comparison chart yet")
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
        mo.vstack([mo.md("## Outcome table"), outcome_table])
    return


@app.cell
def _(mo, plt, reports):
    if reports.empty:
        mo.md("## No duration chart yet")
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
        figure
    return


if __name__ == "__main__":
    app.run()
