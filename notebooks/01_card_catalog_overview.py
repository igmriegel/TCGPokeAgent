import marimo

__generated_with = "0.23.15"
app = marimo.App()


@app.cell
def _():
    import pathlib

    import marimo as mo
    import matplotlib.pyplot as plt
    import pandas as pd

    return mo, pathlib, pd, plt


@app.cell
def _(pathlib, pd):
    data_candidates = [
        pathlib.Path("data/raw/kaggle/simulation/EN_Card_Data.csv"),
        pathlib.Path("../data/raw/kaggle/simulation/EN_Card_Data.csv"),
    ]
    data_path = next(path for path in data_candidates if path.exists())
    cards = pd.read_csv(data_path)
    return cards, data_path


@app.cell
def _(cards, data_path, mo):
    mo.md(f"""
    # Card catalog overview

    Source: `{data_path}`
    Rows: **{len(cards):,}** · Columns: **{len(cards.columns)}**
    """)
    return


@app.cell
def _(cards, mo, pd):
    summary = pd.DataFrame(
        {
            "column": cards.columns,
            "dtype": cards.dtypes.astype(str).values,
            "missing": cards.isna().sum().values,
            "unique": cards.nunique(dropna=True).values,
        }
    )
    mo.vstack([mo.md("## Schema and missing values"), summary])
    return


@app.cell
def _(cards, mo):
    category_counts = cards["Stage (Pokémon)/Type (Energy and Trainer)"].value_counts()
    mo.vstack([mo.md("## Card categories"), category_counts.to_frame("cards")])
    return


@app.cell
def _(cards, plt):
    expansion_counts = cards["Expansion"].value_counts().head(20).sort_values()
    expansion_fig, expansion_ax = plt.subplots(figsize=(8, 6))
    expansion_counts.plot.barh(ax=expansion_ax, color="#4c78a8")
    expansion_ax.set_title("Top 20 expansions by catalog rows")
    expansion_ax.set_xlabel("Rows")
    expansion_ax.set_ylabel("Expansion")
    expansion_fig.tight_layout()
    expansion_fig
    return


@app.cell
def _(cards, pd, plt):
    hp = pd.to_numeric(cards["HP"].replace("n/a", pd.NA), errors="coerce").dropna()
    hp_fig, hp_ax = plt.subplots(figsize=(8, 4))
    hp_ax.hist(hp, bins=20, color="#f58518", edgecolor="white")
    hp_ax.set_title("Observed HP distribution")
    hp_ax.set_xlabel("HP")
    hp_ax.set_ylabel("Rows")
    hp_fig.tight_layout()
    hp_fig
    return


if __name__ == "__main__":
    app.run()
