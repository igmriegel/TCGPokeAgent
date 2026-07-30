# RFL experiment runbook

This document describes the reproducible post-MVP workflow for the hybrid
reinforcement-from-feedback (RFL) pipeline. The frozen MVP remains the default;
RFL is enabled explicitly with `AGENT_MODE=rfl`.

## 1. Prepare the environment

From the repository root:

```bash
uv sync --frozen
uv run --frozen python -m src.data.downloader --check
uv run --frozen pytest tests/ -q
```

The active deck is bound to the promoted profile by ID and SHA-256. Check the
profile before running an experiment:

```bash
PYTHONPATH=. uv run --frozen python - <<'PY'
from pathlib import Path
from src.rfl.profiles import load_profile

root = Path.cwd()
profile = root / "configs/decks/mega_abomasnow_kyogre/heuristic_rfl_0001.yaml"
deck = root / "src/artifacts/deck.csv"
loaded = load_profile(profile, active_deck_id="mega_abomasnow_kyogre", active_deck_path=deck)
if loaded is None:
    raise SystemExit("profile is absent or incompatible")
print(f"loaded {loaded.version}: {len(loaded.weights)} weights")
PY
```

## 2. Smoke test both policies

Run the frozen heuristic and the promoted RFL profile with the same smoke gate:

```bash
scripts/run_smoke.sh heuristic
scripts/run_smoke.sh rfl
```

The smoke gate must have zero `INVALID`, `ERROR` and `TIMEOUT` decisions. Stop
the experiment if this condition is not met.

## 3. Run validation matches

The full configuration runs 200 seeds on both sides (400 player-side matches):

```bash
scripts/run_full.sh heuristic configs/eval_full.yaml
scripts/run_full.sh rfl configs/eval_full.yaml
```

Reports are written to `reports/full_heuristic.json|md` and
`reports/full_rfl.json|md`. Preserve the reports with the seed range, deck
hash, SDK version, side, failure counts and latency percentiles.

For a quick ten-run iteration:

```bash
scripts/run_full.sh rfl configs/eval_small.yaml
```

Do not use the small run as promotion evidence.

## 4. Collect expert annotations

Start the Marimo annotation interface:

```bash
uv run --frozen marimo edit notebooks/05_rfl_annotation.py
```

Save annotations under a run-specific directory, for example:

```text
runs/rfl/<study_id>/annotations.jsonl
```

Every preferred, acceptable or rejected index must exist in the corresponding
trace. The annotation store rejects illegal indices and records the match ID,
deck hash, matchup, turn, confidence, specialist version and schema version.

## 5. Optimize heuristic weights

`WeightOptimizer` uses Optuna when installed and a deterministic fallback when
it is not. The evaluator callback must run the candidate against the frozen
validation seeds and return at least `objective` and
`operational_failures`:

```bash
PYTHONPATH=. uv run --frozen python - <<'PY'
from pathlib import Path
from src.agents.heuristic import WEIGHTS
from src.rfl.optimizer import WeightOptimizer

def evaluate(weights: dict[str, float]) -> dict[str, float]:
    # Replace this callback with the validation harness for the current study.
    # It must return metrics from fixed seeds, not training data.
    return {"objective": 0.0, "operational_failures": 0.0}

study = WeightOptimizer("rfl_0002", Path("runs/rfl/rfl_0002"), n_trials=100)
study.optimize(WEIGHTS, evaluate)
PY
```

The study directory contains `study.db`, `manifest.json`, `trials.jsonl`,
`best_profile.yaml` and `report.md`. Optuna visualization HTML files can be
generated with `generate_study_plots` when Optuna visualization dependencies are
available.

## 6. Apply the holdout promotion gate

Holdout data must contain complete matches only; no `match_id` may occur in more
than one of `train`, `validation` and `holdout`. Evaluate annotations and apply
the gates using `src.rfl.promotion`:

```python
from src.rfl.promotion import PromotionCriteria, apply_promotion_gates

decision = apply_promotion_gates(
    preference_metrics,
    candidate_metrics,
    baseline_metrics,
    criteria=PromotionCriteria(
        min_top1_agreement=0.60,
        min_top_k_agreement=0.75,
        max_p95_latency_ms=100.0,
    ),
    operational_failures=0,
    invalid_decisions=0,
    package_valid=True,
)
print(decision.promoted, decision.reasons)
```

Promotion is allowed only when `decision.promoted` is `True`. Persist the
decision with `write_promotion_manifest`; failed candidates remain artifacts
and must not replace the active profile.

## 7. Package gate

The current package allowlist is heuristic-only: it excludes `src/rfl/` and
`configs/decks/`. Therefore an RFL profile cannot be promoted or described as
package-valid today. The generic archive validator can validate the heuristic
fallback, but that is not evidence that an RFL profile loaded.

Before an RFL promotion attempt, create an executable task that:

1. extends the explicit package allowlist with the required RFL modules and
   selected deck-bound profile;
2. makes profile-load failure fatal in the RFL validation mode;
3. runs at least one in-game decision, not only the initial deck response;
4. verifies the loaded profile version and deck SHA-256 from extracted files.

## Required evidence before promotion

- fixed seed list and both player sides;
- deck ID, deck SHA-256 and SDK version;
- train/validation/holdout match IDs with no overlap;
- top-1, top-k and pairwise specialist agreement;
- win rate with Wilson interval and comparison to baseline;
- `INVALID`, `ERROR` and `TIMEOUT` counts;
- p50/p95/p99 decision latency;
- RFL-aware extracted-package validation result;
- promotion manifest and rollback profile.

The repository tests validate the contracts, but they do not substitute for the
200-seed holdout run required for a real promotion decision.
