# Project status

> Canonical current-state snapshot. Update this file when a gate, release,
> remote score, or active priority changes. Historical evidence belongs in
> [`strategy_notes.md`](strategy_notes.md), not here.

**Last verified:** 2026-08-07

**Code baseline:** `main`; exact revisions are preserved in Git and release
manifests rather than copied into this self-changing status page

**Current release:** Honchkrow/Porygon post-audit policy promoted as the new CABT comparison baseline; Kaggle promotion remains an explicit separate decision

The 2026-08-07 audit of submissions `55320796` and `55322957` identified and
patched a fail-open forbidden-action path, missing global deck-out reserve,
typed-energy readiness gaps, and a missed terminal Porygon2 promotion line.
The post-audit code is now the comparison baseline after a clean 300-match CABT
run; Kaggle upload and remote ranking remain separate from this local baseline.

## Executive summary

The agent is operational and the dedicated Honchkrow/Porygon policy
`supporter_resource_v2` is now the default and CABT comparison baseline. The
post-audit 300-match run finished 249W/51L (83.0%), with zero execution
failures and 12 audited deck-out losses. The historical 200-match reference
finished 162W/38L (81.0%) with 26 audited deck-out losses; the win-rate
difference is not statistically conclusive, while the deck-out reduction is a
strong operational signal. Full metrics are in
[`reports/honchkrow_porygon_cabt_baseline_20260807.json`](../reports/honchkrow_porygon_cabt_baseline_20260807.json).

The independent HDI v1 candidate was accepted as submission `55119505` and
scored 490.4, compared with 539.2 for reference submission `55088176`. This is
experimental evidence only: the required local 200-match comparison and
promotion matrix have not run, so the release policy remains heuristic.

## Verified snapshot

| Area | Current evidence | Decision |
|---|---|---|
| Quality | 281 tests pass; Ruff, mypy, and documentation audit pass | Green for the implemented scope |
| **New CABT comparison baseline** | `d5f42c5`, 300 matches: 249W/51L, 83.0%, zero execution failures, 12 deck-out losses | **Promoted by user decision; future CABT deltas compare against this report** |
| Dedicated local evaluation | Independent 200-match blocks: prior baseline 160W/40L (80.00%), lethal v1 165W/35L (82.50%), resource v2 168W/32L (84.00%); zero execution failures | Resource v2 promoted as production probe by user decision |
| Deck-out monitoring | Instrumented 40-game bilateral sample: 6 losses, 5 deck-outs, 1 other/unclassified | P0 next development |
| Mega Abomasnow fix smoke | 40 bilateral games vs CABT `random_agent`: 34W/0D/6L, zero execution failures | Operationally green; not sufficient for promotion |
| Kaggle stable candidate | `55088176`: 539.2 public score | Keep as remote reference |
| Kaggle HDI v1 experiment | `55119505`: 490.4 public score, -48.8 versus reference | Regression; do not promote |
| Prior experimental candidate | `55093119`: 479.8 public score | Do not promote |
| Package | Turn-planning archive passed extracted validation; SHA-256 `762c0f524af02a8dd14dba2d404e1a069bb9d4b923bec08c5c1963ea62b66f5d` | Submitted to Kaggle; public score and replay review pending |
| Kaggle turn-planning submission | Receipt `reports/submissions/20260807T110209Z-762c0f524af0.json`; package message `Honchkrow turn planning and tactical ledger` | Await score, submission identifier, and remote replays; do not infer promotion from upload acceptance |
| Search | Native lifecycle lacks a verified project Python adapter | Disabled and deferred |
| Raw replay corpus | 85 valid replays; 82 attributable matches; 62 distinct opponent decks | Source snapshot is current |
| Derived replay dataset | 31 matches, 2,047 decisions, 27 opponent decks | Stale; rebuild required |
| Human gameplay capture | No live human match captured | HD0–HD5 remain deferred |
| Heuristic priority fixes | Honchkrow/Porygon Proton/Supporter/Energy/Articuno/promotion/terminal-line rules plus Stadium ordering | Implemented; committed-switch subset validated in 400 matches per policy |
| Turn-planning P0 | Persistent objective, own-turn derivation, setup-aware Proton/Transceiver, marginal Ariana/Petrel comparison, and proven Poké Pad evolution-KO commitment | Implementation and first frozen comparison complete; deck-out corrective iteration pending under T-030 |
| Turn-planning 600-run gate | `bb38f95`: 257W/43L; candidate: 259W/41L; +0.67 pp, independent 95% interval [-4.89, +6.22]; zero operational failures | Do not promote: deck-out losses increased from 28 to 32 and non-inferiority was not established |
| Mega Abomasnow KO policy | Six-Supporter Rocket Feathers, eighteen-Supporter R Command, exact lethal discard, draw reserve, and justified retreat guards | Locally validated with zero partial Mega Abomasnow attacks in both 400-match samples |
| Committed switching and recovery | Exact-serial promotion, Giovanni before paid retreat, projected Ignition damage, forced Porygon2 attack, and exact two-Supporter Miracle Headset recovery | Promoted baseline; 0/44 retreats without same-turn attack and 106/106 exact Headset recoveries |
| CABT 200-match telemetry audit | 156W/0D/44L, zero execution failures; 152 no-Pokémon endings, 40 deck-outs, 8 unresolved pre-terminal states; zero partial Mega Abomasnow attacks | Instrumentation complete; resolve remaining terminal-state gap and eliminate deck-outs under T-026 |
| CABT 1,000-match full trace | Legacy policy: 776W/0D/224L (77.6%), zero execution failures; 166 deck-out losses, 76 unresolved terminal states, 50,688 full decisions, 1,520 observed KOs | Historical legacy-baseline evidence; rerun for the promoted baseline |
| Replay damage diagnostics | 643 replays; 343 losses, 64 deck-outs, 111 damage-not-converted losses | Use loss clusters to drive the next policy changes |
| Documentation integrity | All `src` modules inventoried; internal links, task IDs, counts, and stale claims checked automatically | Living gate |

## Delivery status

| Track | Status | What is complete | What closes the track |
|---|---|---|---|
| MVP S0–S1 | Done | Environment, SDK, deck, wrapper, package smoke | None |
| MVP S2–S7 | In progress | Core implementation and focused tests exist | Revalidate real observations, gameplay metrics, opponent matrix, and belief evidence |
| Search S8 | Deferred | Gate, limits, fallback, and cleanup logic exist | Verified native adapter plus latency/non-regression gate |
| Release S9 | In progress | Heuristic-only package and remote submissions exist | Final checklist and stable promotion evidence |
| Feedback FB-2026-001–015 | Implemented or accepted; FB-2026-013 and committed-switch portions are locally validated | Core rules, deck-out evidence, committed-KO guards, and focused tests exist | Remaining deck-out P0 gate T-026 and new gameplay observations |
| Human capture HD0–HD5 | Deferred | Design only; post-hoc agent replay review is separate | First live human trace and staged delivery gates |
| Learned policies | Runtime implemented, not promoted | Shared schema, grouped datasets, XGBoost/LightGBM native runtime, fallback, and separate extracted-package smoke | Required human data, temporal holdout, valid controlled matrix, and promotion gates |
| HDI v1 | Experimental, not promoted | Ordinal runtime, declarative profile, 40-episode smoke, extracted package, and remote score | Full reproducible local comparison and formal promotion decision |

## Current decisions

1. Keep `55088176` as the remote comparison reference.
2. Treat `55119505` as an HDI v1 experiment, not an automatic promotion.
3. Run the frozen local comparison before deciding whether HDI v1 can replace
   the heuristic release policy.
4. Finish board-development evidence before adding more heuristic rules.
5. Rebuild the derived replay dataset from the 85-file raw snapshot.
6. Keep search and human-capture delivery outside the immediate release path.
7. Require `scripts/audit_documentation.py` to pass with every code or
   documentation change.
8. Use the post-audit 300-match policy at commit `d5f42c5` as the CABT
   comparison `baseline`; preserve the committed-switch policy as
   `legacy_baseline` for historical regression comparisons.
9. Keep the existing submission `55304212` as historical remote evidence; the
   new turn-planning package is submitted for observation but is not promoted.
10. Treat deck-out prevention and terminal-cause telemetry as the next P0
    development gate; the baseline promotion records a user decision and
    tactical invariants, not a statistically significant win-rate claim.
11. Keep Kaggle upload and remote ranking separate from the promoted local CABT
    baseline; local baseline promotion records a comparison reference, not a
    claim of statistically significant win-rate improvement.
12. Track remote submission `55304212` as the current Honchkrow/Porygon
    observation baseline; do not infer strategic improvement until its score
    and replays are available.
13. Against Mega Abomasnow ex, spend attack or retreat resources only on a
    visible KO line; partial damage is not sufficient progress.
14. Do not use McNemar or nominal `(seed, agent_side)` episode conversion for
    CABT 1.32.2 reports: the environment does not forward the configured seed
    into `battle_start`, so these samples are independent.
15. Keep T-030 open: the turn-planning candidate removed the target tactical
    violations but failed the mandatory deck-out and statistical promotion
    gates in its first 300-match-per-policy comparison.

## Next work

The authoritative queue is [`03_tasks/TASK_INDEX.md`](03_tasks/TASK_INDEX.md).
The recommended order is:

1. audit the new gameplay observations against the promoted baseline;
2. close the remaining terminal-cause gap and rerun the promoted baseline at
   1,000 matches;
3. monitor the new turn-planning submission and collect its remote replays;
4. validate the heuristic priority fixes (T-015–T-021) and finish board-development scenarios;
5. validate Rule Box/PrizeMap and PrizeCheck transitions;
6. rebuild the replay dataset and close the release checklist.

## Evidence links

- [Task registry](03_tasks/TASK_INDEX.md)
- [Codebase map](CODEBASE_MAP.md)
- [Roadmap](04_sprint_plan.md)
- [Acceptance checklist](19_final_harness_checklist.md)
- [Feedback register](29_gameplay_feedback.md)
- [Evidence log](strategy_notes.md)
- [Release manifest](../reports/release_heuristic_manifest.json)
- [Full local report](../reports/runs/full_heuristic_final/27d3df870485/report.json)
- [Honchkrow/Porygon local baseline](../reports/honchkrow_porygon_local_eval_20260806.json)
- [Mega Abomasnow fix smoke](../reports/honchkrow_porygon_mega_commit_smoke_20260807.json)
- [CABT 200-match telemetry audit](../reports/honchkrow_porygon_cabt_200_telemetry_20260807.json)
- [Promoted CABT 300-match baseline](../reports/honchkrow_porygon_cabt_baseline_20260807.json)
- [CABT 1,000-match full-trace summary](../reports/honchkrow_porygon_cabt_1000_fulltrace_20260807.json)
- [CABT 1,000-match compressed full trace](../reports/honchkrow_porygon_cabt_1000_fulltrace_20260807.jsonl.gz)
- [CABT replay damage diagnostics](../reports/cabt_replay_damage_diagnostics_20260807.json)
- [Promoted Honchkrow/Porygon baseline audit](../reports/honchkrow_v3_retreat_guard_audit_20260807.md)
- [Submitted package receipt](../reports/submissions/20260807T074354Z-062e4ecea1cc.json)
- [Turn-planning submission receipt](../reports/submissions/20260807T110209Z-762c0f524af0.json)
