# MVP vertical implementation order

For task-level execution, use [`02_sprints/mvp_implementation_sprints.md`](02_sprints/mvp_implementation_sprints.md).
This document remains the authoritative dependency and gate order.

Each slice ends in an executable test; not all abstractions are built before the first match.

## F0 — environment and minimal package

1. Run `uv sync` to create the Python 3.12 environment with
   `kaggle-environments==1.32.2` from the frozen lockfile.
2. Locate `cabt.first_agent`, copy its 60-card deck, and validate it with the SDK.
3. Create thin `main.py` and `deck.csv`.
4. Run `first` versus `random` on both sides.
5. Package, extract, and repeat the test from the extracted content.

Gate: structurally valid package, portable imports, and zero failures.

## F1 — parser, candidates, and fallback

1. Model official enums and `Selection`.
2. Preserve raw `Observation`.
3. Map `State` to factual `GameState`.
4. Convert `Option` to `Candidate` without renumbering.
5. Generate selections of zero, simple, and multiple cardinality.
6. Implement total fallback by context.
7. Run smoke of 20 matches.

Gate: all legal decisions; zero `INVALID`, `ERROR`, and `TIMEOUT`.

## F2 — measurable heuristic

1. Implement card/attack catalog from SDK.
2. Create state and selection features.
3. Implement positive rules, penalties, and reasons.
4. Instrument duration and decision.
5. Compare against `random`, `first`, and ablations.

Gate: reproducible improvement, no operational regression.

## F3 — experimental harness

1. Persist manifest, matches, and decisions.
2. Aggregate W/D/L, Wilson, sides, and duration.
3. Produce paired comparison.
4. Run full of at least 200 matches.

Gate: complete report reproducible by configuration and seeds.

## F4 — belief and short search

1. Build deterministic `BeliefBuilder`.
2. Validate hidden zone cardinality.
3. Implement `StateEvaluator`.
4. Integrate Search API with state release and `search_end` in `finally`.
5. Measure coverage, failures, and gain over pure heuristic.

Gate: search does not reduce wins, does not violate 100 ms, and produces no operational failure.

## F5 — submittable candidate

1. Freeze deck, code, configuration, and versions.
2. Run final matrix on both sides.
3. Generate `.tar.gz` below 197.7 MiB.
4. Extract in clean directory and run only the package content.
5. Record hashes and Strategy evidence.

Gate: all items in [`24_handoff_spec.md`](24_handoff_spec.md).
