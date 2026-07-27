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
- [ ] full report with >= 200 matches;
- [ ] both sides and four opponents;
- [ ] complete metrics and Wilson.

## Search approved

- [ ] only `MAIN`, more than one candidate and overage >= 30 s;
- [ ] top 3, depth <= 4, <= 100 ms;
- [ ] consistent determinization;
- [ ] released states and guaranteed `search_end`;
- [ ] failures fall back to heuristic;
- [ ] win rate does not drop against pure heuristic.

## Submission approved

- [ ] `main.py` and `deck.csv` in root;
- [ ] imports work in `/kaggle_simulations/agent/`;
- [ ] size < 197.7 MiB;
- [ ] tar without path traversal;
- [ ] smoke passes using only extracted content;
- [ ] hashes and manifest frozen;
- [ ] linked Strategy evidence.

Readiness requires all items from the corresponding block; partial percentage does not replace a gate.
