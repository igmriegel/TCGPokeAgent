# Strategy writeup structure

## Sections

1. Problem, imperfect information and runtime constraints.
2. Official, external and generated data; license, version and leakage.
3. Fixed MVP deck and justification.
4. Factual representation, `BeliefState` and `Selection`.
5. Heuristic, fallback and short search.
6. Paired protocol, metrics and intervals.
7. Ablations and M1–M8 evolution.
8. Failures, limits, cost and reproducibility.
9. Conclusion supported by evidence.

## Minimum evidence

- W/D/L table by matchup and side;
- Wilson interval and sample size;
- p50/p95/maximum decision time;
- ablation of each rule group;
- search coverage and failures;
- short traces of representative decisions;
- hashes of deck, configuration, model and package;
- link of each claim to `experiment_id`.

## Editorial rule

A conclusion enters the writeup only if it is recorded in [`strategy_notes.md`](strategy_notes.md) with a verifiable artifact. Correlation is described as correlation; causal inference requires controlled ablation.
