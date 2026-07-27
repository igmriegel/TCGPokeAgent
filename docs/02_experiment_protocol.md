# Experimental protocol

## Unit of change

Every alteration starts with a falsifiable hypothesis and ends with `promote`, `iterate` or `reject`. The record includes agent version, deck version, model hash when applicable, effective configuration, seeds, opponents and artifacts.

## Paired comparison

- Freeze the opponent pool.
- Use the same seeds for candidate and reference.
- Run both as player 0 and player 1.
- Keep the deck constant, except for an explicitly identified deck experiment.
- Compare first with the best stable version; also compare with direct ablation.
- Do not mix results from different SDKs or feature schemas.

## Stages

### Smoke

Run 20 matches distributed across both sides. The only gate is operational: zero `INVALID`, `ERROR` and `TIMEOUT`, complete reports and decisions within budget.

### Full

Run at least 200 matches, balanced by side and matchup. Report W/D/L, Wilson, duration and failures. Larger samples are mandatory when the interval does not support the decision.

### Candidate

Repeat the full against `random`, `first`, stable version and relevant ablation. Freeze the package and run post-extraction validation.

## Promotion rules

- Heuristic: promotes only with reproducible gain in the target matchup and no operational regression.
- Search: promotes only if it does not reduce win rate against pure heuristics and respects latency/failures.
- Model: promotes only after temporal holdout, paired matches and ablation.
- Inconclusive result generates more matches or a revised hypothesis; never promotion by visual inspection.

## Leakage

Separate training, validation and testing by trace generation time. Replays of the same match and derived states do not cross partitions. Ladder logs do not enter training before receiving version, origin and usage rule.
