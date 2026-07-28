"""Generate optional Optuna/Plotly study visualizations."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def generate_study_plots(study: Any, output_dir: str | Path) -> list[Path]:
    """Write Optuna HTML plots when Plotly support is available.

    Missing optional visualization packages are a valid no-op for the runtime.
    """
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    try:
        from optuna.visualization import (
            plot_optimization_history,
            plot_parallel_coordinate,
            plot_param_importances,
            plot_pareto_front,
        )
    except ImportError:
        return []
    builders = {
        "optimization_history": plot_optimization_history,
        "parameter_importances": plot_param_importances,
        "parallel_coordinate": plot_parallel_coordinate,
        "pareto_front": plot_pareto_front,
    }
    written: list[Path] = []
    for name, builder in builders.items():
        try:
            path = destination / f"{name}.html"
            builder(study).write_html(path)
            written.append(path)
        except (ValueError, RuntimeError):
            continue
    return written
