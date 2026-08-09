# Project status

> Canonical current-state snapshot. Update this file when a gate, release,
> remote score, or active priority changes. Historical evidence belongs in
> [`strategy_notes.md`](strategy_notes.md), not here.

**Last verified:** 2026-08-08

**Code baseline:** `main`; exact revisions are preserved in Git and release
manifests rather than copied into this self-changing status page

## IMPORTANT ISSUE — Owner-observed strategy divergence

**Status:** Open P0; must be reviewed at the start of every work session.

Project Owner Igor reviewed agent replays and verified that the agent is not
following the documented game plan and action sequencing he provided. The
technical cause is not yet established. Existing implementation claims,
focused tests, replay reproduction, operational validity, and aggregate match
results must not be treated as evidence that the intended strategy is being
followed.

The investigation must trace representative replay decisions end to end: the
documented rule and intended sequence, parsed public state, generated legal
selections, persistent turn objective, scoring and hard filters, commitment and
fallback paths, selected option indices, and the exact packaged policy used in
the replay. Record distinct divergence classes and their first causal decision
before proposing fixes. Track execution and closure evidence under
[`T-034`](03_tasks/TASK_INDEX.md) and the Owner feedback under
[`FB-2026-019`](29_gameplay_feedback.md#fb-2026-019-agent-does-not-follow-the-documented-game-plan-and-sequencing).
Only explicit Owner acceptance after replay-based validation can close this
issue or remove its session-wide visibility.

**Current release:** `expert_turn_loop` is the official implementation. The
suffixed names are retained only as compatibility aliases for historical
replays and manifests.

Historical submission: `expert_turn_loop_v2` submitted from canonical commit
`2c554dc`; the prior immutable package remains the rollback reference

Submission `55333874` is `COMPLETE` at a dynamic public rating of 357.2,
observed at 2026-08-08T01:13:52-03:00 after 26 public/validation episodes.
The isolated audit reproduced all 1,434 real policy calls with zero divergence,
invalid selection, exception, or fallback. The corpus contains 8 wins and 18
losses; all 26 terminal reasons reconcile with the final state. Only 2 losses
were effective deck-outs, although the owner deck reached zero in 3 games.

No new replay-only correction met the evidence threshold. Candidate A was
therefore behaviorally identical to the submitted policy and candidate B
enabled only the already ratified expert Rounds 1–3 rules. Candidate B failed
the 300-match screening gate. Candidate A reached 862W/138L in its independent
1,000-match final block versus 840W/160L for the baseline, but the +2.2-point
difference had a 95% interval of -0.92 to +5.32 points and one tactical counter
regressed. No candidate was promoted, no new package was built, and no Kaggle
upload was attempted.

The 2026-08-07 audit of submissions `55320796` and `55322957` identified and
patched a fail-open forbidden-action path, missing global deck-out reserve,
typed-energy readiness gaps, and a missed terminal Porygon2 promotion line.
The post-audit code is now the comparison baseline after a clean 300-match CABT
run; Kaggle upload and remote ranking remain separate from this local baseline.

The expert strategy interview is paused after Rounds 1–3. Its remaining nine
rounds are frozen in `docs/34_honchkrow_expert_interview.md`. The isolated
`expert_rounds_1_3_v1` candidate completed its first local comparison at
264W/36L (88.0%) versus the independent 249W/51L (83.0%) promoted baseline.
The +5.0-point estimate is promising but not conclusive: its independent 95%
interval is -0.62 to +10.62 points. The candidate remains experimental.

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
| Submission `55333874` replay audit | 26 isolated replays, 8W/18L; 1,434/1,434 decisions reproduced; zero invalid/fallback/exception; rating 357.2 at 2026-08-08T01:13:52-03:00 | Audit complete; retain immutable package SHA-256 `f6a7c94e…4fac` as technical reference |
| Replay-fix candidate gate | Screening: baseline 251/300, A 254/300, B 247/300; final baseline 840/1000, A 862/1000; independent difference CI95 [-0.92, +5.32] points | No promotion; no package built or uploaded |
| Quality | 297 tests pass; scoped Ruff, mypy, and pre-commit gates pass for the HLV2 implementation | Green for the implemented scope |
| Official turn loop | Explicit `expert_turn_loop` variant, public tactical ledger, canonical stage machine, and comparison tooling | Promoted after 200 bilateral CABT matches; historical HLV2 artifacts remain audit references |
| Expert turn loop v2 CABT screening | 600 bilateral episodes per policy: baseline 511W/89L, candidate 518W/82L; both 600/600 operationally `ok`, equal 27 deck-out losses, +1.17 p.p. difference, 95% CI [-2.79, +5.12] p.p. | Statistical result `HOLD`; user authorized operational promotion with limitation recorded |
| Official turn loop release | Default entrypoint and package builder target `expert_turn_loop`; suffixed names remain compatibility aliases | Local package and CABT promotion validated; remote submission is separate |
| Expert turn loop v2 submission | Canonical package SHA-256 `e90c6b87687c75a033348be2891dc1e6625af6c7e3be4acf9f1ff85718e31262`, receipt `20260808T073233Z-e90c6b87687c.json`, source commit `2c554dc` | Submitted successfully; retain statistical `HOLD` limitation and await remote score/replays |
| Expert Rounds 1–3 candidate | 300 matches: 264W/36L (88.0%), zero execution failures, 9 deck-out losses; +5.0 points with independent 95% interval [-0.62, +10.62] | Promising but inconclusive; keep `expert_rounds_1_3_v1` experimental |
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

### Canonical sequencing corrective iteration

The implementation now contains an explicit `expert_turn_loop` stage machine.
It enforces development/search/calculation/supporter/Factory/Roto/
Headset/attack order, the restricted pre-supporter Roto exception, the
Ultra-Ball/Ariana gate, public Giovanni Prize targeting, and contextual Headset
recovery. Multi-observation goldens and the bilateral 200-match gate remain
required before promotion or package release.

The official promotion comparison used 200 CABT matches per policy. The
previous implementation achieved 171/200 wins (85.5%) and 8 deck-out losses;
`expert_turn_loop` achieved 176/200 wins (88.0%) and 6 deck-out losses. Both
policies completed all matches without operational failures. The observed
increase was +2.5 percentage points, with 95% interval [-4.14, +9.14] points;
the result supports operational promotion but is not statistically conclusive.

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
16. Use only the 26 replays from submission `55333874` as evidence for its
    strategy audit; older replay corpora remain context only.
17. Keep unproven strategic root causes as `unknown` and treat replay
    divergences as single-decision counterfactuals without alternate-win claims.
18. Do not promote either replay-fix candidate: B failed screening and A's
    final independent difference interval includes zero.
19. The user explicitly authorized operational promotion of `expert_turn_loop`
    despite the screening `HOLD`; preserve the old package for rollback and do
    not describe this as statistically significant promotion.

## Next work

The authoritative queue is [`03_tasks/TASK_INDEX.md`](03_tasks/TASK_INDEX.md).
The recommended order is:

1. investigate the Owner-observed game-plan and sequencing divergence under
   T-034, starting from representative replay decisions and exact package
   provenance;
2. review the prioritized `55333874` decision queue and gather independent
   evidence before converting any uncertain finding into a heuristic;
3. resume the Honchkrow/Porygon expert interview at Round 4 in
   [`34_honchkrow_expert_interview.md`](34_honchkrow_expert_interview.md) and
   approve a decision-complete implementation plan before changing runtime behavior;
4. close the remaining terminal-cause gap and rerun the promoted baseline at
   1,000 matches;
5. monitor the new turn-planning submission and collect its remote replays;
6. validate the heuristic priority fixes (T-015–T-021) and finish board-development scenarios;
7. validate Rule Box/PrizeMap and PrizeCheck transitions;
8. rebuild the replay dataset and close the release checklist.

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
- [Promoted CABT 300-match baseline](../reports/honchkrow_porygon_cabt_baseline_20260807.json)
- [Expert Rounds 1–3 comparison](../reports/honchkrow_porygon_expert_rounds_1_3_comparison_20260807.json)
- [Submission 55333874 replay audit](../reports/replay_audits/55333874/summary.md)
- [Submission 55333874 decision review](../reports/replay_audits/55333874/index.html)
- [Report storage and regeneration policy](../reports/README.md)
- [Promoted Honchkrow/Porygon baseline audit](../reports/honchkrow_v3_retreat_guard_audit_20260807.md)
- [Submitted package receipt](../reports/submissions/20260807T074354Z-062e4ecea1cc.json)
- [Turn-planning submission receipt](../reports/submissions/20260807T110209Z-762c0f524af0.json)
