# Replay learning and deck-agnostic engine

**Status:** `FOUNDATION IMPLEMENTED`

This roadmap turns Kaggle gameplay replays into reproducible evidence while
removing policy code that is bound to one submitted deck.

## Foundation evidence

Dataset `data/derived/gameplay_replays/v1` contains:

- 31 complete CABT 1.32.2 matches;
- 2,047 aligned and legal decisions, including 1,836 non-forced decisions;
- 27 distinct opponent deck multisets;
- model-safe train, validation, holdout, and own-policy regression partitions;
- source and output hashes, a passed leakage audit, local metrics, and a
  decision-level policy divergence report.

The transformation is deterministic and excludes opponent identities,
`visualize`, future state, terminal reward, and the opaque search payload from
model inputs.

## Runtime architecture

The generic core now separates:

- `DeckDefinition`, which identifies the submitted 60-card multiset;
- `DeckProfile`, which declares roles and synergy without Python policy code;
- catalog-derived Rule Box and base Prize traits;
- `PrizeMap`, which ranks the public route to the remaining Prizes;
- `PrizeCheckResult`, which distinguishes probabilistic, exact, and
  inconsistent own-card availability;
- `StrategicContext` and `SelectionRanker`, which are shared contracts for
  heuristic and learned policies.

The bundled Mega Abomasnow/Kyogre behavior is data in
`src/artifacts/deck_profile.json`. A different deck with no matching profile
uses a deterministic catalog-derived profile.

## Learning sequence

1. Keep every observed opponent action as behavior evidence, not automatic
   optimality.
2. Exclude forced decisions and split complete deck groups rather than
   individual decisions.
3. Train a regularized linear selection ranker after at least 200 independent
   matches, 10,000 non-forced decisions, and 10 actor decks.
4. Train a compact MLP only after 1,000 matches, 50,000 non-forced decisions,
   20 actor decks, and a 200-match holdout.
5. Start RFL/RL only after a learned ranker is promoted and 10,000 versioned
   self-play matches are available.

All learned policies preserve the legal selection generator and fall back to
the generic heuristic on missing, incompatible, or non-finite artifacts.

## Promotion contract

Operational gates remain mandatory: zero `INVALID`, `ERROR`, and `TIMEOUT`,
valid extracted package, both sides, and p95 non-search decision latency at or
below 100 ms.

After those gates, compare:

```text
0.60 * match_score_rate
+ 0.20 * worst_matchup_score
+ 0.10 * prize_efficiency
+ 0.05 * latency_score
+ 0.05 * stability_score
```

Promotion requires at least `+0.01` composite score, paired bootstrap lower
bound of match-score delta at least `-0.02`, and no worst-matchup regression
greater than five percentage points.

## Current harness decision

The foundation passed 89 unit tests, Ruff, mypy, all pre-commit hooks, a
40-game CABT operational smoke with zero failures, deterministic dataset
regeneration, and isolated package validation. The evidence is registered as
`EXP-20260729-003` in `strategy_notes.md`.

This is not learned-policy promotion evidence. The 31 replay matches are below
the linear, MLP, and RFL data gates, and a new current-deck submission must be
treated as a measurement of the combined deck-and-engine system rather than
proof that either component alone is the limiting factor.
