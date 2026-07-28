"""Optional-dependency Optuna optimization for heuristic profiles."""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .profiles import PolicyProfile

WeightEvaluator = Callable[[Mapping[str, float]], Mapping[str, float]]


@dataclass(frozen=True, slots=True)
class TrialResult:
    """Portable trial record independent of Optuna installation."""

    number: int
    weights: dict[str, float]
    metrics: dict[str, float]
    state: str = "COMPLETE"

    def to_dict(self) -> dict[str, Any]:
        """Serialize this trial."""
        return {
            "number": self.number,
            "weights": self.weights,
            "metrics": self.metrics,
            "state": self.state,
        }


class WeightOptimizer:
    """Run deterministic fallback trials or Optuna when it is installed."""

    def __init__(self, study_id: str, output_dir: str | Path, n_trials: int = 100) -> None:
        self.study_id, self.output_dir, self.n_trials = study_id, Path(output_dir), n_trials

    def optimize(
        self, base_weights: Mapping[str, float], evaluator: WeightEvaluator
    ) -> PolicyProfile | None:
        """Optimize weights and write resumable study artifacts.

        ``evaluator`` must return metrics including ``objective`` and may raise for
        operational failures; failed trials are retained but never promoted.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_sqlite_artifact()
        results: list[TrialResult] = []
        try:
            import optuna
        except ImportError:
            optuna = None
        if optuna is not None:
            study = optuna.create_study(
                study_name=self.study_id,
                storage=f"sqlite:///{self.output_dir / 'study.db'}",
                load_if_exists=True,
                direction="maximize",
                sampler=optuna.samplers.TPESampler(seed=42),
                pruner=optuna.pruners.MedianPruner(),
            )
            names = list(base_weights)

            def objective(trial: Any) -> float:
                weights = {
                    name: trial.suggest_float(
                        name,
                        base_weights[name] * 0.5,
                        base_weights[name] * 1.5 if base_weights[name] else 1.0,
                    )
                    for name in names
                }
                if weights["win_now"] < max(
                    (value for key, value in weights.items() if key != "win_now"), default=0.0
                ):
                    raise optuna.TrialPruned()
                metrics = dict(evaluator(weights))
                if metrics.get("operational_failures", 0.0) > 0:
                    raise optuna.TrialPruned()
                trial.set_user_attr("metrics", metrics)
                return float(metrics.get("objective", -math.inf))

            study.optimize(objective, n_trials=self.n_trials)
            for trial in study.trials:
                metrics = dict(trial.user_attrs.get("metrics", {}))
                results.append(
                    TrialResult(trial.number, dict(trial.params), metrics, trial.state.name)
                )
        else:
            for number in range(self.n_trials):
                weights = dict(base_weights)
                try:
                    metrics = dict(evaluator(weights))
                    state = (
                        "COMPLETE" if metrics.get("operational_failures", 0.0) == 0 else "FAILED"
                    )
                except Exception as error:  # pragma: no cover - defensive operational boundary
                    metrics, state = {"error": str(error), "objective": -math.inf}, "FAILED"
                results.append(TrialResult(number, weights, metrics, state))
        self._write_artifacts(results)
        valid = [
            item
            for item in results
            if item.state == "COMPLETE" and item.metrics.get("operational_failures", 0) == 0
        ]
        return (
            None
            if not valid
            else PolicyProfile(
                "",
                "",
                "",
                self.study_id,
                "v1",
                max(valid, key=lambda x: x.metrics.get("objective", -math.inf)).weights,
            )
        )

    def _write_artifacts(self, results: list[TrialResult]) -> None:
        (self.output_dir / "trials.jsonl").write_text(
            "".join(json.dumps(item.to_dict(), sort_keys=True) + "\n" for item in results)
        )
        (self.output_dir / "manifest.json").write_text(
            json.dumps(
                {"study_id": self.study_id, "n_trials": len(results), "schema_version": "v1"},
                indent=2,
            )
        )
        best = max(
            (item for item in results if item.state == "COMPLETE"),
            key=lambda x: x.metrics.get("objective", -math.inf),
            default=None,
        )
        if best:
            import yaml

            (self.output_dir / "best_profile.yaml").write_text(
                yaml.safe_dump(
                    {
                        "weights": best.weights,
                        "policy": {"version": self.study_id, "feature_schema": "v1"},
                    },
                    sort_keys=False,
                )
            )
        (self.output_dir / "report.md").write_text(
            f"# RFL study {self.study_id}\n\nTrials: {len(results)}\n"
        )

    def _ensure_sqlite_artifact(self) -> None:
        """Create a resumable SQLite marker even without Optuna installed."""
        database = self.output_dir / "study.db"
        connection = sqlite3.connect(database)
        connection.execute(
            "create table if not exists rfl_metadata (key text primary key, value text)"
        )
        connection.execute(
            "insert or replace into rfl_metadata values (?, ?)", ("study_id", self.study_id)
        )
        connection.commit()
        connection.close()


def study_is_resumable(path: str | Path) -> bool:
    """Return whether an existing SQLite study file is readable."""
    try:
        connection = sqlite3.connect(path)
        connection.execute("select 1")
        connection.close()
        return True
    except sqlite3.Error:
        return False
