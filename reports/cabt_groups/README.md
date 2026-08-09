# CABT grouped validation

**Invalidated:** these reports were generated while the Roto-Stick model
incorrectly assumed a seven-card reveal. Do not use them as performance
evidence. They are retained only as historical artifacts; a new evaluation
must be run with the corrected four-card model.

The corrected reference run is
`corrected_roto4_reference_100.json` (84 wins / 16 losses).

All four reports use the integrated `expert_turn_loop` implementation and 100
independent CABT matches (50 from each side). The group names identify the
correction being monitored; these are not paired ablation experiments because
each group uses a different seed range.

| Group | Seed base | Wins | Losses | Execution errors | Deck-out losses |
| --- | ---: | ---: | ---: | ---: | ---: |
| Roto/filter consistency | 20260820 | 86 | 14 | 0 | 2 |
| Empty-bench development | 20260920 | 85 | 15 | 0 | 4 |
| Archer post-KO comparison | 20261020 | 81 | 19 | 0 | 4 |
| Non-lethal fallback guard | 20261120 | 76 | 24 | 0 | 1 |

The non-lethal fallback result is a regression signal, not an accepted gain.
Its guard should be narrowed before promotion. The other results are positive
but require a same-seed paired ablation or a larger evaluation before causal
claims are made.

Each JSON file contains the full match records and telemetry. The compressed
JSONL files are the resumable decision traces produced by the evaluator.
