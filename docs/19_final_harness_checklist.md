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

## Replay-learning foundation

- [x] replay observations are aligned with the following recorded action;
- [x] simulator option indices are preserved and selections are validated;
- [x] opponent decks are extracted as immutable 60-card multisets;
- [x] train, validation, and holdout groups do not share actor deck hashes;
- [x] model inputs exclude identity, future state, reward, and opaque payloads;
- [x] manifest records source and output hashes;
- [x] Rule Box, PrizeMap, and PrizeCheck have focused tests;
- [x] the current deck profile is data rather than policy code;
- [x] agent-versus-agent replay reviews preserve legal decisions and raw feedback;
- [ ] linear ranker data-volume and paired promotion gates pass;
- [ ] MLP data-volume and paired promotion gates pass;
- [ ] RFL self-play and paired promotion gates pass.

The checked items establish a reproducible learning harness. They do not
promote a learned policy or prove that the current heuristic has reached the
performance ceiling of the submitted deck.

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
