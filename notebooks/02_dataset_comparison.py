import marimo

__generated_with = "0.23.15"

app = marimo.App()


@app.cell
def _():
    import pathlib

    import marimo as mo
    import pandas as pd

    return mo, pathlib, pd


@app.cell
def _(pathlib, pd):
    root_candidates = [pathlib.Path("data/raw/kaggle"), pathlib.Path("../data/raw/kaggle")]
    data_root = next(path for path in root_candidates if path.exists())

    paths = {
        "simulation_en": data_root / "simulation/EN_Card_Data.csv",
        "simulation_jp": data_root / "simulation/JP_Card_Data.csv",
        "strategy_en": data_root / "strategy/EN_Card_Data.csv",
        "strategy_jp": data_root / "strategy/JP_Card_Data.csv",
    }
    frames = {name: pd.read_csv(path) for name, path in paths.items()}
    return data_root, frames, paths


@app.cell
def _(frames, mo, paths, pd):
    overview = pd.DataFrame(
        [
            {
                "dataset": name,
                "path": str(paths[name]),
                "rows": len(frame),
                "columns": len(frame.columns),
                "duplicate_rows": int(frame.duplicated().sum()),
            }
            for name, frame in frames.items()
        ]
    )
    mo.vstack([mo.md("# Competition dataset comparison"), overview])
    return (overview,)


@app.cell
def _(frames, mo):
    english = frames["simulation_en"]
    strategy_same = english.equals(frames["strategy_en"])
    mo.md(
        f"""
        ## Basic consistency checks

        - English simulation and strategy tables identical: **{strategy_same}**
        - English catalog IDs: **{english["Card ID"].nunique():,}** unique values
        - English candidate keys `(Card ID, Move Name)`:
          **{english.duplicated(["Card ID", "Move Name"]).sum()}** duplicates
        """
    )
    return english, strategy_same


@app.cell
def _(english, mo):
    expansion_summary = (
        english.groupby("Expansion", dropna=False)
        .agg(rows=("Card ID", "size"), unique_cards=("Card ID", "nunique"))
        .sort_values("rows", ascending=False)
        .head(20)
    )
    mo.vstack([mo.md("## Largest expansions"), expansion_summary])
    return (expansion_summary,)


if __name__ == "__main__":
    app.run()
