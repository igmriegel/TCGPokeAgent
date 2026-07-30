# Learning-to-rank pipeline

This page owns the XGBoost and LightGBM model, dataset, runtime, and package
contract. Current release status remains in
[`PROJECT_STATUS.md`](PROJECT_STATUS.md); experiment evidence remains in
[`strategy_notes.md`](strategy_notes.md).

## Runtime contract

`AgentPolicy.select(observation) -> list[int]` is unchanged. Internally,
`HeuristicAgent.decide()` returns a `PolicyDecision` containing the chosen
selection, all ranked alternatives, the shared feature rows, model identity,
latency, and fallback state. The factory in `src/agents/factory.py` is the only
source of agent modes, deck assets, profiles, and model directories.

The supported learned modes are:

- `xgboost_ranker`;
- `lightgbm_ranker`.

Both use `selection-ranking-v1`. If learned inference fails after a decision
starts, the policy uses the exact `HeuristicSelectionRanker` output over the
already extracted rows and increments `fallback_count`. Missing or incompatible
models fail during ranker construction and package validation.

## Dataset contract

Each legal, reviewed selection is one `RankingRow`; every decision is one
contiguous `RankGroup`. Human relevance is `preferred=3`, `acceptable=2`, and
`rejected=0`. Unreviewed alternatives do not receive an invented label.
Behavioral comparisons are explicitly named behavioral evidence and their
weight cannot exceed `0.2`.

`split_rank_groups()` keeps complete matches together, applies a temporal cut,
and can reserve whole decks for holdout. XGBoost receives one qid per row;
LightGBM receives the equivalent contiguous group sizes.

The feature schema uses actor-visible facts, legal option metadata,
declarative own-deck roles, PrizeCheck confidence, and heuristic components.
It excludes terminal reward, future state, opponent hidden hand contents, and
player identity.

## Training

Install only the group needed for the selected study:

```bash
uv sync --frozen --group ranker-xgboost
uv sync --frozen --group ranker-lightgbm
```

The XGBoost group uses the pinned CPU-only distribution. Both training groups
also include the pinned scikit-learn API required by `XGBRanker` and
`LGBMRanker`.

`scripts/train_rankers.py` accepts grouped train/validation JSONL files.
`deterministic_grid()` samples no more than 30 configurations per backend from
the frozen tree/depth/rate/L2/row/feature grid. Selection uses validation
NDCG@1, then NDCG@3, pairwise accuracy, top-one human agreement, and latency.

Models are persisted through native Booster formats:

- XGBoost: `model.json`;
- LightGBM: `model.txt`.

Every model directory also contains `feature_schema.json` and
`ranker_manifest.json` with model/schema hashes and training lineage.

## Separate packages

Build one backend per archive:

```bash
scripts/build_package.sh submission-xgboost.tar.gz xgboost_ranker RUN_MODEL_DIR
scripts/build_package.sh submission-lightgbm.tar.gz lightgbm_ranker RUN_MODEL_DIR
```

The package builder vendors NumPy, SciPy, and only the selected native backend.
The validator enforces the size limit, hashes, backend exclusivity, extracted
imports, a real model decision, a forced heuristic fallback, latency, legal
output, and a CABT file-agent episode.

## Promotion gates

No learned ranker is currently promoted. Promotion requires all of:

- 200 independent matches and 10,000 non-forced decisions;
- 250 reviewed human groups and feedback from at least 30 matches;
- match/deck holdout with zero leakage;
- better top-one human agreement, pairwise accuracy, and NDCG@1 than heuristic;
- frozen four-opponent matrix with zero invalid, error, or timeout outcomes;
- extracted package validation and competitive gain or non-inferiority.

First compare the best ranker with heuristic. Then compare XGBoost and LightGBM
directly on identical seeds. The other backend remains a challenger and an
active-review disagreement source.

## Model matrix

| Backend | Dataset | Feature schema | Holdout | Package | Latency | State |
|---|---|---|---|---|---|---|
| heuristic | — | `selection-ranking-v1` | pending matrix | local smoke | measured by runner | stable |
| XGBoost | no promotion dataset | `selection-ranking-v1` | not run | extracted toy smoke passed | toy smoke only | candidate infrastructure |
| LightGBM | no promotion dataset | `selection-ranking-v1` | not run | extracted toy smoke passed | toy smoke only | candidate infrastructure |
