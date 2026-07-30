"""Train equivalent XGBoost and LightGBM ranking studies from grouped JSONL."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from src.ranking.dataset import read_grouped_dataset
from src.ranking.training import TrainingProvenance, run_study


def main() -> None:
    """Parse CLI arguments, train requested backends, and write a study summary."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", required=True)
    parser.add_argument("--validation", required=True)
    parser.add_argument("--holdout")
    parser.add_argument("--output-root", required=True)
    parser.add_argument(
        "--backend",
        action="append",
        choices=("xgboost_ranker", "lightgbm_ranker"),
        required=True,
    )
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--train-split-id", required=True)
    parser.add_argument("--validation-split-id", required=True)
    parser.add_argument("--deck-id", required=True)
    parser.add_argument("--deck-sha256", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()

    train = read_grouped_dataset(args.train)
    validation = read_grouped_dataset(args.validation)
    holdout = read_grouped_dataset(args.holdout) if args.holdout else None
    provenance = TrainingProvenance(
        dataset_id=args.dataset_id,
        split_ids={
            "train": args.train_split_id,
            "validation": args.validation_split_id,
        },
        deck_id=args.deck_id,
        deck_sha256=args.deck_sha256,
        seed=args.seed,
    )
    results = [
        run_study(
            backend,
            train,
            validation,
            args.output_root,
            provenance,
            limit=args.limit,
            holdout=holdout,
        )
        for backend in args.backend
    ]
    summary = Path(args.output_root) / "study_summary.json"
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(
        json.dumps([asdict(result) for result in results], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(summary)


if __name__ == "__main__":
    main()
