# Post-MVP research specifications

R1–R8 are deferred until the heuristic release gates are green. Current status
belongs in the [`roadmap`](../04_sprint_plan.md).

## Shared promotion gate

Every research candidate freezes the deck, SDK, data split, opponent matrix,
seeds/case identifiers, feature schema, and artifact hash. It must preserve
zero operational failures, pass isolated package and latency checks, improve
or remain non-inferior to the stable heuristic, and retain rollback.

## R1 — Configurable heuristic ablations

Produce a rule-level baseline by disabling one feature family at a time while
preserving all other inputs. Gate: deterministic matrix and paired report.

## R2 — Linear NumPy ranker

Train a regularized legal-selection ranker from leakage-safe decision groups.
Gate: temporal holdout, deterministic export, latency, and paired comparison.

## R3 — LightGBM LambdaRank

Evaluate a grouped listwise ranker only after dependency, package-size, and
runtime review. Gate: isolated package plus explainability and ablation report.

## R4 — NumPy MLP fallback

Provide a dependency-light nonlinear alternative when R3 is unsafe or
insufficient. Gate: numerical stability and at least 95% of the promoted
ranker's measured gain.

## R5 — PPO with action masking

Train against a frozen curriculum and opponent pool while masking illegal
selections. Gate: reproducible improvement over the fixed pool and heuristic.

## R6 — Recurrent belief model

Add history only when it improves hidden-information matchups without leaking
future state. Gate: calibration, ablation, and robust paired gain.

## R7 — Information-set search

Combine verified CABT search with multiple determinizations and learned or
heuristic priors. Gate: traceable budget, state cleanup, and gain that justifies
latency.

## R8 — Joint deck, policy, and priors

Optimize only after policy evaluation is stable. Gate: robustness across a
diverse fixed pool, isolated package, and preserved rollback.
