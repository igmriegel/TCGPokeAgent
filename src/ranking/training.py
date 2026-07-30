"""Equivalent, deterministic training workflows for both native rankers."""

from __future__ import annotations

import itertools
import json
import random
import time
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from statistics import mean
from typing import Any, Literal, Protocol, Sequence, cast

from src.ranking.dataset import GroupedRankingDataset
from src.ranking.features import FEATURE_SCHEMA, feature_schema_sha256, write_feature_schema

Backend = Literal["xgboost_ranker", "lightgbm_ranker"]


@dataclass(frozen=True, slots=True)
class TrainingProvenance:
    """Immutable dataset, deck, and split identifiers for a model candidate."""

    dataset_id: str
    split_ids: dict[str, str]
    deck_id: str
    deck_sha256: str
    seed: int = 42


@dataclass(frozen=True, slots=True)
class RankerMetrics:
    """Offline ranking quality and inference latency metrics."""

    ndcg_at_1: float
    ndcg_at_3: float
    ndcg_at_5: float
    pairwise_accuracy: float
    top1_human_agreement: float
    latency_p95_ms: float


@dataclass(frozen=True, slots=True)
class StudyResult:
    """One trained configuration and its validation metrics."""

    backend: Backend
    parameters: dict[str, Any]
    metrics: RankerMetrics
    model_dir: str


class _Estimator(Protocol):
    def predict(self, values: Sequence[Sequence[float]]) -> Any: ...


def deterministic_grid(
    backend: Backend, *, seed: int = 42, limit: int = 30
) -> list[dict[str, Any]]:
    """Select at most 30 configurations deterministically from the frozen grid.

    Args:
        backend: Native learning-to-rank backend.
        seed: Reproducible configuration sampling seed.
        limit: Maximum configurations to return.

    Returns:
        Deterministically sampled parameter dictionaries.
    """
    if backend not in {"xgboost_ranker", "lightgbm_ranker"}:
        raise ValueError(f"unsupported ranker backend: {backend}")
    keys = ("n_estimators", "max_depth", "learning_rate", "l2", "row_sample", "feature_sample")
    values = (
        (100, 200, 400),
        (3, 4, 6),
        (0.03, 0.05, 0.10),
        (1, 5, 10),
        (0.8, 1.0),
        (0.8, 1.0),
    )
    configurations = [dict(zip(keys, combination)) for combination in itertools.product(*values)]
    sampler = random.Random(f"{backend}:{seed}")
    selected = sampler.sample(configurations, min(limit, len(configurations)))
    return sorted(selected, key=lambda item: tuple(item[key] for key in keys))


def train_ranker(
    backend: Backend,
    train: GroupedRankingDataset,
    validation: GroupedRankingDataset,
    output_dir: str | Path,
    parameters: dict[str, Any],
    provenance: TrainingProvenance,
    *,
    holdout: GroupedRankingDataset | None = None,
) -> StudyResult:
    """Train, persist, reload metadata, and evaluate one ranker candidate.

    Args:
        backend: XGBoost or LightGBM runtime backend.
        train: Training query groups.
        validation: Early-stopping and selection query groups.
        output_dir: Candidate artifact directory.
        parameters: Frozen bounded-tree configuration.
        provenance: Dataset, split, deck, and seed lineage.
        holdout: Optional untouched holdout evaluated after model fitting.

    Returns:
        Persisted candidate and validation metrics.
    """
    if not train.groups or not validation.groups:
        raise ValueError("training and validation datasets must contain groups")
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    estimator, library_version = _fit(backend, train, validation, parameters, provenance.seed)
    predictions, latency = _timed_predictions(estimator, validation.values)
    metrics = evaluate_ranking(validation, predictions, latency)
    training_predictions, _ = _timed_predictions(estimator, train.values)
    training_metrics = evaluate_ranking(train, training_predictions)
    holdout_metrics = None
    if holdout is not None and holdout.groups:
        holdout_predictions, holdout_latency = _timed_predictions(estimator, holdout.values)
        holdout_metrics = evaluate_ranking(holdout, holdout_predictions, holdout_latency)
    model_file = "model.json" if backend == "xgboost_ranker" else "model.txt"
    model_path = destination / model_file
    if backend == "xgboost_ranker":
        estimator.get_booster().save_model(model_path)
    else:
        estimator.booster_.save_model(str(model_path))
    model_sha = sha256(model_path.read_bytes()).hexdigest()
    write_feature_schema(destination / "feature_schema.json")
    manifest = {
        "backend": backend,
        "library_version": library_version,
        "model_file": model_file,
        "model_sha256": model_sha,
        "model_version": f"{backend}-{model_sha[:12]}",
        "feature_schema_version": FEATURE_SCHEMA.version,
        "feature_schema_sha256": feature_schema_sha256(),
        "dataset_id": provenance.dataset_id,
        "split_ids": provenance.split_ids,
        "deck_id": provenance.deck_id,
        "deck_sha256": provenance.deck_sha256,
        "seed": provenance.seed,
        "parameters": parameters,
        "training_metrics": asdict(training_metrics),
        "validation_metrics": asdict(metrics),
        "holdout_metrics": asdict(holdout_metrics) if holdout_metrics else {},
        "latency": {
            "validation_p95_ms": metrics.latency_p95_ms,
            "holdout_p95_ms": holdout_metrics.latency_p95_ms if holdout_metrics else None,
        },
    }
    (destination / "ranker_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    reloaded_predictions = _reload_predictions(backend, model_path, validation.values)
    if _group_orders(validation, predictions) != _group_orders(validation, reloaded_predictions):
        raise RuntimeError("native model reload changed validation rankings")
    return StudyResult(backend, dict(parameters), metrics, str(destination))


def run_study(
    backend: Backend,
    train: GroupedRankingDataset,
    validation: GroupedRankingDataset,
    output_root: str | Path,
    provenance: TrainingProvenance,
    *,
    limit: int = 30,
    holdout: GroupedRankingDataset | None = None,
) -> StudyResult:
    """Train equivalent bounded grids and select by the frozen tie-break order.

    Args:
        backend: Native backend to study.
        train: Training groups.
        validation: Validation groups.
        output_root: Root directory for separate candidates.
        provenance: Immutable dataset and deck lineage.
        limit: Maximum deterministic configurations.
        holdout: Optional untouched holdout evaluated for reporting, not selection.

    Returns:
        Best persisted candidate.
    """
    results = [
        train_ranker(
            backend,
            train,
            validation,
            Path(output_root) / backend / f"candidate-{index:02d}",
            parameters,
            provenance,
            holdout=holdout,
        )
        for index, parameters in enumerate(
            deterministic_grid(backend, seed=provenance.seed, limit=limit)
        )
    ]
    return max(
        results,
        key=lambda item: (
            item.metrics.ndcg_at_1,
            item.metrics.ndcg_at_3,
            item.metrics.pairwise_accuracy,
            item.metrics.top1_human_agreement,
            -item.metrics.latency_p95_ms,
        ),
    )


def evaluate_ranking(
    dataset: GroupedRankingDataset,
    predictions: Sequence[float],
    latency_ms: Sequence[float] = (),
) -> RankerMetrics:
    """Evaluate grouped predictions without crossing decision boundaries.

    Args:
        dataset: Ground-truth query groups.
        predictions: Flat scores aligned with dataset rows.
        latency_ms: Optional per-inference latency observations.

    Returns:
        NDCG, pairwise accuracy, top-one agreement, and p95 latency.
    """
    if len(predictions) != len(dataset.rows):
        raise ValueError("prediction count differs from ranking rows")
    offsets = 0
    ndcg_values: dict[int, list[float]] = {1: [], 3: [], 5: []}
    pairwise: list[float] = []
    agreements: list[float] = []
    for group in dataset.groups:
        scores = list(float(value) for value in predictions[offsets : offsets + len(group.rows)])
        labels = [row.relevance for row in group.rows]
        offsets += len(group.rows)
        order = sorted(range(len(scores)), key=lambda index: (-scores[index], index))
        for cutoff in ndcg_values:
            ndcg_values[cutoff].append(_ndcg(labels, order, cutoff))
        comparable = [
            float((scores[left] - scores[right]) * (labels[left] - labels[right]) > 0)
            for left in range(len(labels))
            for right in range(left + 1, len(labels))
            if labels[left] != labels[right]
        ]
        if comparable:
            pairwise.append(mean(comparable))
        best_label = max(labels)
        agreements.append(float(labels[order[0]] == best_label))
    return RankerMetrics(
        ndcg_at_1=mean(ndcg_values[1]) if ndcg_values[1] else 0.0,
        ndcg_at_3=mean(ndcg_values[3]) if ndcg_values[3] else 0.0,
        ndcg_at_5=mean(ndcg_values[5]) if ndcg_values[5] else 0.0,
        pairwise_accuracy=mean(pairwise) if pairwise else 0.0,
        top1_human_agreement=mean(agreements) if agreements else 0.0,
        latency_p95_ms=_percentile(latency_ms, 0.95),
    )


def _fit(
    backend: Backend,
    train: GroupedRankingDataset,
    validation: GroupedRankingDataset,
    parameters: dict[str, Any],
    seed: int,
) -> tuple[Any, str]:
    if backend == "xgboost_ranker":
        import xgboost

        estimator = xgboost.XGBRanker(
            objective="rank:ndcg",
            eval_metric=["ndcg@1", "ndcg@3", "ndcg@5"],
            n_estimators=int(parameters["n_estimators"]),
            max_depth=int(parameters["max_depth"]),
            learning_rate=float(parameters["learning_rate"]),
            reg_lambda=float(parameters["l2"]),
            subsample=float(parameters["row_sample"]),
            colsample_bytree=float(parameters["feature_sample"]),
            random_state=seed,
            n_jobs=1,
            tree_method="hist",
            early_stopping_rounds=25,
        )
        estimator.fit(
            train.values,
            train.labels,
            qid=_numeric_qids(train),
            sample_weight=_group_weights(train),
            eval_set=[(validation.values, validation.labels)],
            eval_qid=[_numeric_qids(validation)],
            verbose=False,
        )
        return estimator, str(xgboost.__version__)
    if backend == "lightgbm_ranker":
        import lightgbm
        import numpy

        estimator = lightgbm.LGBMRanker(
            objective="lambdarank",
            metric=["ndcg"],
            eval_at=[1, 3, 5],
            n_estimators=int(parameters["n_estimators"]),
            max_depth=int(parameters["max_depth"]),
            num_leaves=min(31, 2 ** int(parameters["max_depth"])),
            learning_rate=float(parameters["learning_rate"]),
            reg_lambda=float(parameters["l2"]),
            subsample=float(parameters["row_sample"]),
            colsample_bytree=float(parameters["feature_sample"]),
            random_state=seed,
            n_jobs=1,
            verbosity=-1,
        )
        estimator.fit(
            numpy.asarray(train.values, dtype=float),
            train.labels,
            group=train.group_sizes,
            sample_weight=train.weights,
            eval_set=[(numpy.asarray(validation.values, dtype=float), validation.labels)],
            eval_group=[validation.group_sizes],
            eval_at=[1, 3, 5],
            callbacks=[lightgbm.early_stopping(25, verbose=False)],
        )
        return estimator, str(lightgbm.__version__)
    raise ValueError(f"unsupported ranker backend: {backend}")


def _numeric_qids(dataset: GroupedRankingDataset) -> list[int]:
    return [index for index, group in enumerate(dataset.groups) for _ in group.rows]


def _group_weights(dataset: GroupedRankingDataset) -> list[float]:
    return [mean(row.weight for row in group.rows) for group in dataset.groups]


def _timed_predictions(
    estimator: _Estimator, values: Sequence[Sequence[float]]
) -> tuple[list[float], list[float]]:
    latencies: list[float] = []
    predictions: list[float] = []
    for row in values:
        started = time.perf_counter()
        result = estimator.predict([row])
        latencies.append((time.perf_counter() - started) * 1000.0)
        predictions.append(float(cast(Sequence[float], result)[0]))
    return predictions, latencies


def _reload_predictions(
    backend: Backend, model_path: Path, values: Sequence[Sequence[float]]
) -> list[float]:
    if backend == "xgboost_ranker":
        import xgboost

        xgboost_booster = xgboost.Booster()
        xgboost_booster.load_model(model_path)
        matrix = xgboost.DMatrix(values, feature_names=list(FEATURE_SCHEMA.names))
        return [float(item) for item in xgboost_booster.predict(matrix)]
    import lightgbm
    import numpy

    lightgbm_booster = lightgbm.Booster(model_file=str(model_path))
    return [float(item) for item in lightgbm_booster.predict(numpy.asarray(values, dtype=float))]


def _group_orders(
    dataset: GroupedRankingDataset, predictions: Sequence[float]
) -> list[tuple[int, ...]]:
    orders = []
    offset = 0
    for group in dataset.groups:
        scores = predictions[offset : offset + len(group.rows)]
        orders.append(tuple(sorted(range(len(scores)), key=lambda index: (-scores[index], index))))
        offset += len(group.rows)
    return orders


def _ndcg(labels: Sequence[int], predicted_order: Sequence[int], cutoff: int) -> float:
    ranked = list(predicted_order[:cutoff])
    ideal = sorted(labels, reverse=True)[:cutoff]
    dcg = sum(
        (2 ** labels[index] - 1) / _log2(position + 2) for position, index in enumerate(ranked)
    )
    ideal_dcg = sum((2**label - 1) / _log2(position + 2) for position, label in enumerate(ideal))
    return dcg / ideal_dcg if ideal_dcg else 0.0


def _log2(value: int) -> float:
    import math

    return math.log2(value)


def _percentile(values: Sequence[float], quantile: float) -> float:
    ordered = sorted(float(item) for item in values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, max(0, int((len(ordered) - 1) * quantile + 0.5)))
    return ordered[index]
