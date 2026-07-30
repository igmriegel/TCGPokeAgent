"""Heuristic, XGBoost, and LightGBM runtime selection rankers."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol

from src.core import ParsedDecision, RankedSelection, Selection, SelectionFeatures
from src.ranking.features import FEATURE_SCHEMA, feature_schema_sha256


class _Predictor(Protocol):
    def predict(self, values: Sequence[Sequence[float]]) -> Sequence[float]: ...


class HeuristicSelectionRanker:
    """Order shared feature rows by their recorded heuristic score."""

    backend = "heuristic"
    model_version = "heuristic-v1"

    def rank(
        self,
        decision: ParsedDecision,
        selections: Sequence[Selection],
        features: Sequence[SelectionFeatures],
    ) -> list[RankedSelection]:
        """Rank selections deterministically using the reference score.

        Args:
            decision: Parsed decision associated with the rows.
            selections: Legal selections to order.
            features: Shared features containing heuristic scores and reasons.

        Returns:
            Ranked selections with deterministic margins.
        """
        _validate_rows(selections, features)
        scored = [(row.heuristic_score, row.selection, row.heuristic_reasons) for row in features]
        return _ranked(scored)


class _ModelSelectionRanker:
    backend = "unknown"

    def __init__(self, model_dir: str | Path) -> None:
        self.model_dir = Path(model_dir)
        self.metadata = _load_metadata(self.model_dir, self.backend)
        self.model_version = str(self.metadata["model_version"])
        self._predictor = self._load_predictor()

    def rank(
        self,
        decision: ParsedDecision,
        selections: Sequence[Selection],
        features: Sequence[SelectionFeatures],
    ) -> list[RankedSelection]:
        """Predict and rank selections using a validated native model.

        Args:
            decision: Parsed decision associated with the rows.
            selections: Legal selections to order.
            features: Shared feature rows in schema order.

        Returns:
            Ranked model predictions with reference reasons attached.
        """
        _validate_rows(selections, features)
        predictions = list(self._predictor.predict([row.values for row in features]))
        if len(predictions) != len(features):
            raise RuntimeError("ranker returned a prediction count mismatch")
        scored = [
            (float(score), row.selection, row.heuristic_reasons)
            for score, row in zip(predictions, features)
        ]
        return _ranked(scored)

    def _load_predictor(self) -> _Predictor:
        raise NotImplementedError


class XGBoostSelectionRanker(_ModelSelectionRanker):
    """Load a native XGBoost Booster without pickle."""

    backend = "xgboost_ranker"

    def _load_predictor(self) -> _Predictor:
        try:
            import xgboost
        except ImportError as error:
            raise RuntimeError("xgboost backend is unavailable") from error
        _validate_library_version(self.metadata, "xgboost", str(xgboost.__version__))
        model_path = self.model_dir / str(self.metadata["model_file"])
        booster = xgboost.Booster()
        booster.load_model(model_path)

        class Predictor:
            def predict(self, values: Sequence[Sequence[float]]) -> Sequence[float]:
                matrix = xgboost.DMatrix(values, feature_names=list(FEATURE_SCHEMA.names))
                return [float(item) for item in booster.predict(matrix)]

        return Predictor()


class LightGBMSelectionRanker(_ModelSelectionRanker):
    """Load a native LightGBM Booster without pickle."""

    backend = "lightgbm_ranker"

    def _load_predictor(self) -> _Predictor:
        try:
            import lightgbm
        except ImportError as error:
            raise RuntimeError("lightgbm backend is unavailable") from error
        _validate_library_version(self.metadata, "lightgbm", str(lightgbm.__version__))
        model_path = self.model_dir / str(self.metadata["model_file"])
        booster = lightgbm.Booster(model_file=str(model_path))

        class Predictor:
            def predict(self, values: Sequence[Sequence[float]]) -> Sequence[float]:
                import numpy

                predictions = booster.predict(numpy.asarray(values, dtype=float))
                return list(float(item) for item in predictions)

        return Predictor()


def _ranked(
    scored: Sequence[tuple[float, Selection, tuple[str, ...]]],
) -> list[RankedSelection]:
    ordered = sorted(scored, key=lambda item: (-item[0], item[1].indices))
    result: list[RankedSelection] = []
    for index, (score, selection, reasons) in enumerate(ordered):
        margin = score - ordered[index + 1][0] if index + 1 < len(ordered) else 0.0
        result.append(
            RankedSelection(
                selection=selection,
                score=score,
                rank=index + 1,
                reasons=reasons,
                margin_to_next=float(margin),
            )
        )
    return result


def _validate_rows(selections: Sequence[Selection], features: Sequence[SelectionFeatures]) -> None:
    if len(selections) != len(features):
        raise ValueError("selection and feature counts differ")
    if any(row.schema_version != FEATURE_SCHEMA.version for row in features):
        raise ValueError("feature schema version mismatch")
    if any(len(row.values) != len(FEATURE_SCHEMA.names) for row in features):
        raise ValueError("feature vector length mismatch")
    if [item.indices for item in selections] != [row.selection.indices for row in features]:
        raise ValueError("feature rows are not aligned with selections")


def _load_metadata(model_dir: Path, backend: str) -> dict[str, Any]:
    metadata_path = model_dir / "ranker_manifest.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"ranker metadata is unavailable: {metadata_path}") from error
    if metadata.get("backend") != backend:
        raise RuntimeError("ranker backend does not match model metadata")
    if metadata.get("feature_schema_version") != FEATURE_SCHEMA.version:
        raise RuntimeError("ranker feature schema version is incompatible")
    if metadata.get("feature_schema_sha256") != feature_schema_sha256():
        raise RuntimeError("ranker feature schema hash is incompatible")
    model_file = metadata.get("model_file")
    if not isinstance(model_file, str) or not (model_dir / model_file).is_file():
        raise RuntimeError("ranker model file is unavailable")
    return dict(metadata)


def _validate_library_version(metadata: dict[str, Any], distribution: str, installed: str) -> None:
    expected = str(metadata.get("library_version", ""))
    if expected and installed != expected:
        raise RuntimeError(
            f"{distribution} version {installed} is incompatible with model version {expected}"
        )
