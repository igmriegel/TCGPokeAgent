"""Inspect heuristic score contributions and compare configuration profiles."""

import marimo

__generated_with = "0.23.15"
app = marimo.App()


@app.cell
def _():
    import pathlib

    import marimo as mo
    import matplotlib.pyplot as plt
    import pandas as pd

    from src.agents.heuristic import SimpleHeuristicScorer
    from src.config.loader import ConfigLoader
    from src.core import Candidate, GameState, OptionType, Selection

    candidate_cls = Candidate
    config_loader_cls = ConfigLoader
    game_state_cls = GameState
    option_type_cls = OptionType
    scorer_cls = SimpleHeuristicScorer
    selection_cls = Selection

    return (
        candidate_cls,
        config_loader_cls,
        game_state_cls,
        mo,
        option_type_cls,
        pathlib,
        pd,
        plt,
        scorer_cls,
        selection_cls,
    )


@app.cell
def _(config_loader_cls, pathlib):
    config_root = next(
        path
        for path in (pathlib.Path("configs"), pathlib.Path("../configs"))
        if path.exists()
    )
    config = config_loader_cls(config_root).load("agent_heuristic")
    base_weights = config.extra.get("weights", {})
    base_flags = config.extra.get("feature_flags", {})
    return base_flags, base_weights, config


@app.cell
def _(candidate_cls, game_state_cls, option_type_cls, selection_cls):
    scenarios = [
        ("win_now", option_type_cls.ATTACK, {"damage": 10, "win": True}),
        ("efficient_attack", option_type_cls.ATTACK, {"damage": 90, "cost": 1}),
        ("attack_enabling_energy", option_type_cls.ENERGY, {"count": 1, "enablesAttack": True}),
        ("useful_evolution", option_type_cls.EVOLVE, {"useful": True}),
        ("key_piece_discard", option_type_cls.DISCARD, {"keyPiece": True}),
        ("premature_end", option_type_cls.END, {}),
        ("no_signal", option_type_cls.CARD, {}),
    ]
    state = game_state_cls(turn_action_count=0)
    scenario_candidates = [
        candidate_cls(index, {"type": option_type.value, **option}, option_type)
        for index, (_, option_type, option) in enumerate(scenarios)
    ]
    scenario_selections = [
        selection_cls((index,), (candidate.option_type,))
        for index, candidate in enumerate(scenario_candidates)
    ]
    return scenario_candidates, scenario_selections, scenarios, state


@app.cell
def _(base_flags, base_weights):
    profiles = {
        "configured": {"weights": base_weights, "flags": base_flags},
        "no_attack_signals": {
            "weights": base_weights,
            "flags": {**base_flags, "use_attack_signals": False},
        },
        "win_priority_20": {
            "weights": {**base_weights, "win_now": 20.0},
            "flags": base_flags,
        },
        "resource_conservative": {
            "weights": {
                **base_weights,
                "key_piece_discard": -16.0,
                "wasted_energy": -10.0,
            },
            "flags": base_flags,
        },
    }
    return (profiles,)


@app.cell
def _(
    profiles,
    scenario_candidates,
    scenario_selections,
    scenarios,
    scorer_cls,
    state,
    pd,
):
    score_rows = []
    for profile_name, profile in profiles.items():
        scorer = scorer_cls(profile["weights"], profile["flags"])
        for (scenario_name, _, _), candidate, selection in zip(
            scenarios, scenario_candidates, scenario_selections
        ):
            score, reasons = scorer.score(state, selection, [candidate])
            score_rows.append(
                {
                    "profile": profile_name,
                    "scenario": scenario_name,
                    "score": score,
                    "reasons": ", ".join(reasons),
                }
            )
    scores = pd.DataFrame(score_rows)
    return scores


@app.cell
def _(mo, scores):
    mo.vstack(
        [
            mo.md(
                "# Heuristic score lab\n\n"
                "Profiles are controlled fixtures for ablation analysis."
            ),
            scores,
        ]
    )
    return


@app.cell
def _(mo, plt, scores):
    pivot = scores.pivot(index="scenario", columns="profile", values="score")
    figure, axis = plt.subplots(figsize=(11, 5))
    pivot.plot.bar(ax=axis)
    axis.set_title("Score impact by heuristic profile")
    axis.set_ylabel("weighted score")
    axis.tick_params(axis="x", rotation=35)
    figure.tight_layout()
    mo.vstack([mo.md("## Configuration impact"), figure, pivot])
    return


if __name__ == "__main__":
    app.run()
