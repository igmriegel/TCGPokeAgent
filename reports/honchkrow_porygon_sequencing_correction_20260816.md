# Honchkrow/Porygon sequencing correction audit

This report records local state-based evidence only. The runs are independent
CABT samples; they do not establish replay-level strategic improvement.

| Check | Before correction (v2, 200 matches) | After correction (v3, 200 matches) |
|---|---:|---:|
| Operational failures | 0 | 0 |
| Ignition without attack | 21 | 0 |
| Late Proton without gain | 0 | 0 |
| Roto Supporters revealed | 392 | 373 |
| Roto Supporters selected | 392 | 373 |
| Partial attack events | 2 | 37 |
| Deck-out losses | 6 | 4 |
| Completed matches | 200 | 200 |

The v3 run also recorded zero fallback decisions, zero second-Supporter
attempts, zero Torment selections over a proven Poké Pad line, and zero
unresolved terminal reasons. The increase in partial attacks is a known
trade-off from preserving a committed Ignition attack; it is not evidence of
strategic improvement and requires a separate owner review.

Artifacts:

- v2: `/tmp/honchkrow_porygon_final_eval_v2.json`
- v3: `/tmp/honchkrow_porygon_final_eval_v3.json`
- v3 trace: `/tmp/honchkrow_porygon_final_eval_v3.jsonl.gz`
