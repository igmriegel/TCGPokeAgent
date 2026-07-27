# Roadmap from MVP to research

| Milestone | Delivery | Gate |
|---|---|---|
| M0 | SDK 1.32.2, official deck, wrapper, parser and fallback | smoke of 20; zero failures |
| M1 | configurable heuristics and per-rule ablations | reproducible gain without new failures |
| M2 | linear NumPy ranker | beats heuristics on temporal holdout and paired matches |
| M3 | LightGBM LambdaRank | local gain, SHAP/ablation and compatible package |
| M4 | small NumPy MLP, if LightGBM is unsafe | preserves at least 95% of ranker gain |
| M5 | PPO with action masking and curriculum | beats fixed pool and previous version with confidence |
| M6 | GRU-PPO or belief model | gain in hidden information matchups |
| M7 | ISMCTS/PUCT with multiple determinizations | gain justifies CPU and latency |
| M8 | joint optimization of deck, policy and priors | robustness against diverse pool and ladder meta |

## Mandatory sequence

No milestone skips the previous one as a comparable baseline. Each promotion preserves rollback to the best stable version and records hypothesis, ablation, deck, model and report.

## Deferred approaches

- LLM at runtime: size, latency and non-determinism do not solve a textual need.
- Initial tabular DQN: variable options and combinations make the representation fragile.
- Initial full MCTS: hidden information requires a validated belief and evaluator first.
