# Objective readiness criteria

## Documentation ready

- [x] contract uses `Observation` and `list[int]`;
- [x] `Selection` covers zero, one and multiple options;
- [x] `SelectType`, `SelectContext` and `OptionType` have a defined role;
- [x] `GameState` contains facts and `BeliefState` contains hypotheses;
- [x] parser, scorer, belief, search and evaluation interfaces are independent;
- [x] smoke, full, search and package gates are measurable;
- [x] roadmap and Strategy track have promotion criteria;
- [x] external sources have verification date;
- [x] Kaggle downloads have hash, format, local schema and sanitized samples.

## MVP integrated

- [ ] Python 3.12 environment created by `uv sync --frozen`;
- [ ] SDK 1.32.2 and `kagglehub` installed from `uv.lock`;
- [ ] preflight confirms the exact SDK distribution version;
- [ ] official 60-card deck validated;
- [ ] initial wrapper and game branch pass;
- [ ] fallback covers all observed contexts;
- [ ] smoke 20/20 with no failures;
- [x] full report with >= 200 matches;
- [ ] both sides and four opponents;
- [x] complete metrics and Wilson.

## Search approved

Not applicable to the current heuristic-only release. Search is disabled by
configuration because the documented native lifecycle is not yet exposed
through a verified project Python adapter.

- [ ] only `MAIN`, more than one candidate and overage >= 30 s;
- [ ] top 3, depth <= 4, <= 100 ms;
- [ ] consistent determinization;
- [ ] released states and guaranteed `search_end`;
- [ ] failures fall back to heuristic;
- [ ] win rate does not drop against pure heuristic.

## Submission approved — heuristic-only release

- [x] `main.py` and `deck.csv` in root;
- [ ] imports work in `/kaggle_simulations/agent/`;
- [x] size < 197.7 MiB;
- [x] tar without path traversal;
- [x] smoke passes using only extracted content;
- [x] hashes and manifest frozen;
- [x] linked Strategy evidence.
- [x] search disabled explicitly with documented SDK reason.

Readiness requires all items from the corresponding block; partial percentage does not replace a gate.
