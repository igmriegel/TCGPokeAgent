# Strategy evidence log

This file is append-only historical evidence. It does not report current
project status. Use [`PROJECT_STATUS.md`](PROJECT_STATUS.md) for current
metrics and decisions. Drafts may be edited; accepted records only receive
explicit correction records.

## States

`planned` → `running` → `accepted` | `rejected` | `inconclusive`

## Template

```yaml
experiment_id: EXP-YYYYMMDD-NNN
status: planned
hypothesis: "Alteração X melhora a métrica Y no matchup Z."
agent_version: null
baseline_version: null
deck_version: null
deck_sha256: null
model_sha256: null
sdk_version: "1.32.2"
config:
  files: []
  overrides: {}
seeds: []
games_planned: 0
matchups: []
started_at: null
finished_at: null
results:
  wins: null
  draws: null
  losses: null
  wilson_95: null
  decision_ms_p50: null
  decision_ms_p95: null
  decision_ms_max: null
  invalid: null
  error: null
  timeout: null
ablation: null
decision: null
limitations: []
evidence:
  manifest: null
  report: null
  traces: []
writeup_claim: null
```

## Initial record

```yaml
experiment_id: DOC-20260727-001
status: accepted
hypothesis: "Contracts aligned with the official API reduce pending architectural decisions."
agent_version: null
baseline_version: null
deck_version: null
sdk_version: "1.32.2"
finished_at: "2026-07-27"
decision: "Adopt Selection list[int], factual GameState and separate BeliefState."
limitations:
  - "No policy was implemented or evaluated in this revision."
evidence:
  manifest: "docs/20_master_index.md"
  report: "docs/07_core_contracts.md"
  traces: []
writeup_claim: null
```

## Evaluation record

```yaml
experiment_id: EXP-20260729-001
status: accepted
hypothesis: "The implemented heuristic policy can complete the full SDK gate without operational failures."
agent_version: dev
baseline_version: null
deck_version: frozen-local
deck_sha256: 1156379af39e71bc83eecb50d1e04c5cc480501d293621fcc89c2d355d99be78
sdk_version: "1.32.2"
config:
  files: [configs/eval_full.yaml, configs/agent_heuristic.yaml]
  overrides: {}
seeds: "42..241"
games_planned: 400
matchups: [random]
started_at: "2026-07-29"
finished_at: "2026-07-29"
results:
  wins: 239
  draws: 0
  losses: 161
  wilson_95: [0.5487, 0.6444]
  decision_ms_p50: null
  decision_ms_p95: null
  decision_ms_max: 0.0
  invalid: 0
  error: 0
  timeout: 0
ablation: null
decision: "Accept heuristic operational gate; do not claim search promotion."
limitations:
  - "Full run currently uses the random opponent; the four-opponent matrix is pending."
  - "Search is disabled until the documented native lifecycle is integrated through a verified Python adapter."
evidence:
  manifest: "reports/runs/full_heuristic_final/27d3df870485/manifest.json"
  report: "reports/runs/full_heuristic_final/27d3df870485/report.json"
  traces: []
writeup_claim: "The heuristic completed 400 player-side matches with zero operational failures; recorded match-duration p50/p95 were 270.75/1033.70 ms."
```

## Gameplay recovery record

```yaml
experiment_id: EXP-20260729-002
status: accepted
hypothesis: "Resolving real CABT cards and prioritizing productive actions eliminates the end-turn-only policy without operational regressions."
agent_version: c41ca40
baseline_version: 55086902
deck_version: mega_abomasnow_kyogre
deck_sha256: 1156379af39e71bc83eecb50d1e04c5cc480501d293621fcc89c2d355d99be78
sdk_version: "1.32.2"
config:
  files: [configs/agent_heuristic.yaml]
  overrides:
    opponent: random
seeds: "native-unseeded balanced matrix"
games_planned: 200
matchups: [random]
started_at: "2026-07-29"
finished_at: "2026-07-29"
results:
  wins: 179
  draws: 0
  losses: 21
  attacks: 472
  matches_with_attack: 200
  productive_main_actions: 1942
  end_turn_rate: 0.0934
  invalid: 0
  error: 0
  timeout: 0
remote_validation:
  submission_id: 55088176
  episode_id: 88836243
  state: COMPLETED
  initial_public_score: 600.0
  previous_final_public_score: 179.7
  package_sha256: ee0a20585a423b33b2f8205671bb6e3f32539451c0b45b929dd8c74ed837e775
  package_bytes: 513976
decision: "Accept minimum observable-gameplay recovery; do not claim strategic or matchup-complete promotion."
limitations:
  - "The new public score may still change after additional evaluation."
  - "The 200-game behavioral matrix uses only the random opponent."
  - "Knock Out, Prize, donk, and termination-cause metrics remain pending."
  - "Remote first-load latency was 335.6 ms; subsequent decisions stayed below 2 ms."
evidence:
  manifest: null
  report: "docs/27_gameplay_rules.md"
  traces:
    - "tests/fixtures/cabt_main_turn.json"
writeup_claim: "The recovered heuristic attacked in every game of a 200-game random-opponent smoke matrix and passed remote validation without agent stderr."
```

## Release decision

The current release is heuristic-only. Search is disabled explicitly because
the documented native lifecycle is not yet integrated through a verified
Python adapter. The release archive, manifest, and isolated validation are
recorded in `reports/release_heuristic_manifest.json`.

## Replay-learning foundation record

```yaml
experiment_id: EXP-20260729-003
status: foundation_accepted
hypothesis: "Kaggle gameplay runs can produce leak-free, deck-grouped decision evidence while the runtime policy remains deck-agnostic."
agent_version: 35eebd9
dataset_version: gameplay_replays_v1
dataset_manifest_sha256: 26b7c7e18e744b2b56b1afc7b7fd83cf1e6870351a55bd4b92c5467720bb1d50
sdk_version: "1.32.2"
results:
  matches: 31
  decisions: 2047
  non_forced_decisions: 1836
  own_decisions: 748
  opponent_decisions: 1299
  distinct_opponent_decks: 27
  opponent_reference_divergences: 577
  own_reference_divergences: 7
  leakage_findings: 0
  unit_tests_passed: 89
  cabt_smoke_games_completed: 40
  cabt_smoke_failures: 0
decision: "Accept the replay-learning foundation; retain the heuristic and do not promote a learned model."
limitations:
  - "Only 31 independent matches are available, below every learned-ranker promotion threshold."
  - "Opponent actions are behavioral evidence, not labels of optimal play."
  - "Rule Box and exact PrizeCheck behavior still require a paired tactical and matchup evaluation."
evidence:
  engine_commit: 35eebd9
  metrics_commit: 6e6bf7a
  ingestion_commit: e5cc635
  dataset_manifest: "data/derived/gameplay_replays/v1/manifest.json"
  leakage_report: "data/derived/gameplay_replays/v1/leakage_report.json"
  divergence_report: "data/derived/gameplay_replays/v1/divergence_report.json"
  summary: "data/derived/gameplay_replays/v1/summary.md"
writeup_claim: "The versioned corpus preserves 2,047 legal decisions and 27 opponent deck multisets without promoting replay actions as ground truth."
```

## Current-deck engine ceiling probe

```yaml
experiment_id: EXP-20260729-004
status: pending_remote_evaluation
hypothesis: "With the submitted deck held fixed, Rule Box-aware combat, PrizeCheck, and the deck-agnostic policy improve the remote result over the gameplay-recovery engine."
agent_version: 16f1e8b
baseline_submission_id: 55088176
baseline_public_score_observed: 521.4
candidate_submission_id: 55093119
candidate_initial_public_score: 600.0
candidate_evaluated_public_score: 581.0
score_observed_at: "2026-07-29T22:51:49Z"
evaluation_status: UPDATING
current_public_score_delta: 59.6
deck_version: mega_abomasnow_kyogre
package_sha256: a16493a362645ed25cdeb7fce50cf72f8be85bb4120487221063ceb7cfb66aaa
package_bytes: 523391
local_gates:
  unit_tests: "89 passed"
  type_check: passed
  lint: passed
  cabt_operational_smoke: "40 completed, 0 failed"
  gameplay_smoke:
    matches: 10
    wins: 9
    matches_with_attack: 10
    operational_failures: 0
    end_turn_rate: 0.0935
decision: "Record the current +59.6 delta as provisional and wait for the remote score to stabilize before promotion or deck-ceiling conclusions."
limitations:
  - "Kaggle initializes a new submission at 600.0; that value is not evaluation evidence."
  - "The remote opponent mix and evaluation variance are not controlled locally."
  - "Holding the deck fixed measures engine progress, but a plateau alone does not prove a deck ceiling."
  - "Separating deck and engine effects requires a crossed comparison with at least two decks and frozen engine versions."
evidence:
  receipt: "reports/submissions/20260729T221617Z-a16493a36264.json"
  archive: "submissions/candidate-16f1e8b.tar.gz"
```

## Competitive replay review record

```yaml
annotation_id: KGR-88879568-002
supersedes: KGR-88879568-001
status: accepted_evidence
episode_id: 88879568
actor_type: agent
review_kind: post_hoc_human_review
reviewed_side: 0
match_outcome: loss
verdict: mistake
cause_code: sequencing
confidence: 1.0
finding: "The engine omitted a legal Kyogre Bench play before attacking on turns 11, 13, and 15."
first_mistake:
  decision_id: "88879568:72:0"
  selected: "Hammer-lanche, index 3"
  preferred: "Play Kyogre, index 1"
repeated_mistakes:
  - "88879568:81:0"
  - "88879568:100:0"
intended_follow_up: "Play Kyogre, receive the next MAIN prompt, then attack."
decision: "Use as direct evidence for FB-2026-001 and H2A; the attack remains correct after development, and the review is not a human demonstration."
evidence:
  annotations: "data/annotations/gameplay_reviews/v1/annotations.jsonl"
  replay_sha256: "f3ede5bf92cc81a91914830c6240306af22ec3248ed46f9b15fb6dd6e3077fc5"
implementation:
  annotation_commit: c16a960
  policy_commit: e268c96
  rule: "With open Bench capacity, choose any legal Pokemon PLAY before the terminal ATTACK or END fallback."
  card_specific_runtime_ids: []
replay_regression:
  "88879568:72:0": {recorded: [3], corrected_policy: [1]}
  "88879568:81:0": {recorded: [5], corrected_policy: [1]}
  "88879568:100:0": {recorded: [8], corrected_policy: [1]}
validation:
  unit_tests: "96 passed"
  cabt_operational_smoke: "40 completed, 0 failed"
  gameplay_smoke:
    matches: 20
    wins: 19
    matches_with_attack: 20
    operational_failures: 0
    productive_main_actions: 219
    end_turn_rate: 0.0837
decision: "Accept the deck-agnostic implementation and smoke evidence; require the frozen comparison gate before a new submission."
```

## Kaggle replay synchronization record

```yaml
observed_at: "2026-07-29T23:15:36Z"
submission_ids: [55093119, 55088176, 55086902]
completed_replays_downloaded: 68
raw_directory: "data/raw/kaggle/kaggle_gameplay_runs"
raw_size: "107 MiB"
schema_valid_replays: 68
invalid_replays: 0
sha256_duplicate_files: 0
decision: "Retain all 68 distinct replay files; no byte-identical duplicate was safe to remove."
limitations:
  - "The current Kaggle submission continues to receive runs, so this is a timestamped snapshot."
  - "The immutable gameplay_replays/v1 derived dataset still represents its original 31-match source set."
```

## Native ranker infrastructure smoke

```yaml
observed_at: "2026-07-30"
scope: "Infrastructure smoke with synthetic grouped rows; not promotion evidence"
feature_schema: selection-ranking-v1
xgboost:
  distribution: xgboost-cpu==3.0.2
  archive_bytes: 56652886
  extracted_validation: passed
lightgbm:
  distribution: lightgbm==4.6.0
  archive_bytes: 55281528
  extracted_validation: passed
checks:
  - backend-exclusive archive
  - native model reload
  - real in-game model decision
  - forced and counted heuristic fallback
  - CABT file-agent episode
decision: "Keep heuristic promoted; ranker infrastructure may begin real data capture and holdout studies."
limitations:
  - "Synthetic rows do not establish gameplay quality."
  - "No promotion-volume, human-agreement, holdout, or opponent-matrix gate has run."
```

## Replay termination monitoring record

```yaml
replays: 68
explicit_result_reasons: 68
terminal_state_consistency_passed: 68
reason_totals:
  all_prizes_taken: 11
  deck_out: 8
  no_pokemon_in_play: 49
owner_classified_replays: 65
owner_results:
  wins:
    all_prizes_taken: 9
    deck_out: 6
    no_pokemon_in_play: 16
  losses:
    all_prizes_taken: 2
    deck_out: 1
    no_pokemon_in_play: 31
ambiguous_validation_replays:
  count: 3
  reason_totals:
    deck_out: 1
    no_pokemon_in_play: 2
decision: "Monitor explicit Result.reason values in the investigation report and keep mirror-validation owner outcomes unknown."
evidence:
  report: "perf_reports/INVESTIGATION_REPORT_ABOMASNOW.html"
  extractor: "src/data/replay_outcomes.py"
limitations:
  - "Both sides use the same owner name in three validation episodes, so perspective W/L cannot be assigned from replay identity."
  - "Simultaneous terminal conditions may exist; the explicit CABT reason is retained as authoritative."
```

## Remote score correction

```yaml
observed_at: "2026-07-30T02:58:27Z"
corrects: EXP-20260729-004
baseline_submission_id: 55088176
baseline_public_score: 516.3
candidate_submission_id: 55093119
candidate_public_score: 503.2
score_delta_candidate_minus_baseline: -13.1
decision: "Retain 55088176 as the remote comparison reference and do not promote 55093119."
limitations:
  - "Remote evaluation variance and opponent composition are not controlled locally."
```

## Kaggle replay synchronization correction

```yaml
observed_at: "2026-07-30T02:58:27Z"
corrects: "Kaggle replay synchronization record at 2026-07-29T23:15:36Z"
raw_replays: 85
schema_valid_replays: 85
invalid_replays: 0
raw_size: "135 MiB"
attributable_matches: 82
ambiguous_mirror_validation_matches: 3
distinct_opponent_decks: 62
derived_dataset_version: gameplay_replays_v1
derived_dataset_matches: 31
decision: "Retain the raw snapshot and create a new derived dataset version; v1 remains immutable."
```

## HDI v1 experimental submission

```yaml
observed_at: "2026-07-30T21:14:25Z"
submission_id: 55119505
mode: hdi_v1
deck_id: mega_abomasnow_kyogre
archive: submissions/submission_hdi_v1.tar.gz
archive_bytes: 539099
archive_sha256: 359adce7030e6c9d3b4b97482ab7a2f90f68bec60acf8e836fae18c9372f3a36
package_payload_sha256: 1a08204a59c3c3dd82a0f722c1df121a469121d6ac3234da2f2584e3f17011c7
local_gates:
  unit_tests: "132 passed"
  cabt_operational_smoke: "40 completed, 0 failed"
  extracted_package_validation: passed
reference_submission_id: 55088176
reference_public_score: 539.2
experimental_public_score: 600.0
score_delta_experimental_minus_reference: 60.8
decision: "Retain the result as promising experimental evidence; do not promote HDI v1 until the formal local comparison and release gates pass."
limitations:
  - "The remote score does not control opponent composition or evaluation variance."
  - "The formal 200-match and frozen opponent-matrix promotion gates have not run."
  - "HDI-7-04 remains TBD and outside the implemented policy."
```

## HDI v1 remote score correction

```yaml
observed_at: "2026-07-30T21:20:12Z"
corrects: "HDI v1 experimental submission score snapshot"
submission_id: 55119505
initial_observed_public_score: 600.0
latest_public_score: 490.4
reference_submission_id: 55088176
reference_public_score: 539.2
score_delta_experimental_minus_reference: -48.8
decision: "Do not promote HDI v1; retain the submission as experimental evidence and require the frozen local comparison before further policy changes."
limitation: "Kaggle recalculated the public score after the first COMPLETE listing, so the later listing is the canonical current value."
```

## Heuristic priority-fix reproduction batch

```yaml
observed_at: "2026-08-01T00:00:00Z"
deck_id: mega_abomasnow_kyogre
deck_sha256: "0880554d3f0704f706ec4b2ff2bc7c40e91329dd700be05cfd2f1d8e4d57cf7c"
root_causes:
  - "deck_profile.json deck_sha256 was stale (3882cfbb...), so start_match discarded the configured profile and used GenericDeckProfileBuilder"
  - "generic profile lost development_priority (Snover), pokemon_search (Poké Pad), trainer_search (Petrel), hand_refresh (Lillie), secondary_attacker (Kyogre), Riptide damage_per_basic_energy_in_discard, and ordered resource_values"
  - "bench filter dropped attach-active and guaranteed-KO attack options"
  - "_attachment_score else-branch reported attach_useful_tool for unresolved/non-tool cards"
reproductions:
  - "deck-out: Riptide KO+refill 640 > bench Snover 400 after fix (was 330 < 360)"
  - "post-evolution: attach active 485 > attach bench 375 > play Kyogre 320"
  - "Poké Pad TO_HAND now picks Snover (155) over Kyogre (145)"
  - "Petrel TO_HAND no longer self-tutors (trainer_search penalty)"
decisions:
  - "conditional Bench filter: restrict to Pokémon PLAY only when no priority action is legal"
  - "EVOLVE precedes Energy; completion attach is a priority action"
  - "heuristic-only scope; HDI intentionally unchanged"
  - "default calibrations: attach completion +80, search +100, bench attach 375"
evidence:
  - "tests/test_heuristic_strategy.py (10 scenarios)"
  - "tests/test_profile.py (profile integrity)"
  - "tests/test_cabt_golden_gameplay.py (6 golden cases)"
status: implemented
```

## Heuristic turn-order and guaranteed-KO fixes

```yaml
observed_at: "2026-08-01T00:00:00Z"
deck_id: mega_abomasnow_kyogre
deck_sha256: "0880554d3f0704f706ec4b2ff2bc7c40e91329dd700be05cfd2f1d8e4d57cf7c"
root_causes:
  - "_guaranteed_attack_damage ignored deck_profile attack_plans, so Swirling Waves (130) and Frost Barrier (200) returned zero and were never recognized as guaranteed KO"
  - "_attack_score lacked a guaranteed-KO bonus, so probabilistic Hammer-lanche (500) and discard-based Riptide outranked the guaranteed-KO attack (330)"
  - "_play_score ordered Supporter search (350 + hand-size bonus) and Supporter (250) above Items, so Lillie was played before legal Items"
decisions:
  - "resolve guaranteed damage from attack_plans (and public discard-pile damage) before option/catalog metadata"
  - "apply GUARANTEED_KO_BONUS (200) only when deterministic damage reaches the opponent Active HP; never treat top-of-deck damage as guaranteed"
  - "play Items before any Supporter: Item search 340, Item 240, Supporter search 230, Supporter 210"
  - "no requires_guaranteed_ko penalty; scope kept minimal"
evidence:
  - "tests/test_heuristic_strategy.py (6 new scenarios)"
  - "tests/test_cabt_golden_gameplay.py (6 golden cases)"
  - "149 unit tests pass"
status: implemented
```

## Attacker-target gate retired

```yaml
observed_at: "2026-08-01T12:00:00Z"
deck_id: mega_abomasnow_kyogre
deck_sha256: "0880554d3f0704f706ec4b2ff2bc7c40e91329dd700be05cfd2f1d8e4d57cf7c"
root_causes:
  - "the guaranteed-KO attack was a priority action in _has_priority_action, so with a near-empty Bench and a Snover or Ultra Ball in hand the agent attacked instead of developing"
  - "board_targets.minimum_attackers (2) was declared in deck_profile.json but no code used it"
decisions:
  - "legal attacks are no longer blocked by attacker-target development; development, evolution, and attachment priorities continue through their own scores"
  - "guaranteed-KO attacks and shuffle-refill attacks keep their own bonuses"
evidence:
  - "replay scenarios C1-C6: Ultra Ball / Snover in hand before guaranteed-KO and Hammer-lanche attacks"
  - "tests/test_heuristic_strategy.py updated to remove the gate and keep weak-attack regression coverage"
  - "158 unit tests pass"
status: revised
```

## Mega Abomasnow committed-KO investigation

```yaml
observed_at: "2026-08-07T00:00:00-03:00"
submission_id: 55304212
episode_id: 90494772
opponent_target:
  card_id: 723
  name: "Mega Abomasnow ex"
  max_hp: 350
  prize_value: 3
  weakness: Fire
observed_partial_attacks:
  - "turn 7: Rocket Feathers with 4 visible Team Rocket Supporters, target HP 350, own deck 24"
  - "turn 9: Rocket Feathers with 5 visible Team Rocket Supporters, target HP 230, own deck 14"
  - "turn 11: Rocket Feathers with 4 visible Team Rocket Supporters, target HP 50, own deck 8"
root_causes:
  - "Rocket Feathers was forbidden only with zero Supporters, so any positive partial damage remained legal"
  - "R Command promotion compared relative damage instead of requiring the eighteen-Supporter 360-damage threshold"
  - "the generic all-options fallback could reintroduce a strategically forbidden partial attack"
  - "retreat protection recognized any damaging attack as productive instead of comparing immediate KO lines and retreat cost"
decisions:
  - "require 6 Supporters and an exact six-card discard for Rocket Feathers into Mega Abomasnow"
  - "require 18 discarded Supporters before selecting or promoting Porygon2 for R Command"
  - "allow retreat only when its cost is payable and the replacement has an immediate Mega Abomasnow KO"
  - "preserve two natural draws when Ariana or Factory would consume deck without a committed KO"
evidence:
  - "35 focused Honchkrow/Porygon tests pass"
  - "the replay observation at turns 7 and 9 now selects END instead of Rocket Feathers"
  - "the full suite passes: 239 tests"
  - "40-game bilateral operational smoke: 34W/0D/6L, zero execution failures"
status: "locally validated and active in the promoted development baseline"
```

## CABT 200-match telemetry audit

```yaml
observed_at: "2026-08-07T00:00:00-03:00"
report: "reports/honchkrow_porygon_cabt_200_telemetry_20260807.json"
matches: 200
results: "156W/0D/44L"
execution_failures: 0
termination_reasons: "152 no-pokemon-in-play, 40 deck-outs, 8 unresolved pre-terminal states"
partial_mega_abomasnow_attacks: 0
retreats: 106
critical_deck_end_selections: 58
resource_guards: "134 committed six-Supporter KO gates; 122 retreat-without-KO refusals"
telemetry_fields:
  - "prize_count, deck_count, hand_count, discard_count"
  - "bench_count, pokemon_in_play, active card/HP/energy"
  - "opponent deck/prizes/board counts"
  - "Rocket Supporters in hand and discard"
  - "selection, attack, retreat, END, duration, fallback, and resource guard"
limitations:
  - "CABT live observations do not expose an explicit terminal reason code"
  - "eight matches ended between the final public observation and terminal resolution"
status: "completed; deck-out prevention remains T-026 P0"
```

## CABT 1,000-match full-trace baseline

```yaml
observed_at: "2026-08-07T00:00:00-03:00"
report: "reports/honchkrow_porygon_cabt_1000_fulltrace_20260807.json"
trace: "reports/honchkrow_porygon_cabt_1000_fulltrace_20260807.jsonl.gz"
matches: 1000
results: "776W/0D/224L"
win_rate: 0.776
execution_failures: 0
losses: "166 deck-outs, 58 unresolved terminal causes"
decisions: 50688
observed_damage: 288190
observed_kos: 1520
partial_mega_abomasnow_attacks: 0
retreats: 520
retreats_without_ko_line: 665
status: "legacy baseline frozen; future CABT comparisons must use independent samples"
```

## CABT replay damage diagnostics

```yaml
observed_at: "2026-08-07T00:00:00-03:00"
report: "reports/cabt_replay_damage_diagnostics_20260807.json"
replays: 643
losses: 343
deck_out_replays: 64
damage_not_converted_losses: 111
no_observed_damage_losses: 4
status: "evidence source for KO-horizon and deck-preservation policy work"
```

## Honchkrow/Porygon committed-switch baseline promotion

```yaml
observed_at: "2026-08-07T00:00:00-03:00"
candidate_name: "ko_priority_v3_retreat_guard"
promoted_name: "baseline"
preserved_prior_name: "legacy_baseline"
evaluation_design:
  blocks_per_policy: 2
  matches_per_block: 200
  matches_per_policy: 400
  agent_sides_per_block: "100 side 0; 100 side 1"
  comparison_mode: "independent"
  pairing_limitation: "CABT 1.32.2 does not forward the configured seed to battle_start; nominal seed and side labels do not identify paired episodes"
legacy_results:
  wins: 308
  losses: 92
  win_rate: 0.77
  deck_out_losses: 64
  selected_retreats: 230
  retreats_without_same_turn_attack: 193
promoted_results:
  wins: 313
  losses: 87
  win_rate: 0.7825
  deck_out_losses: 56
  selected_retreats: 44
  retreats_without_same_turn_attack: 0
  exact_two_supporter_headset_recoveries: "106/106"
  r_command_executions: 53
  r_command_kos: 35
statistics:
  win_rate_delta_percentage_points: 1.25
  independent_two_proportion_p_two_sided: 0.671
decision:
  - "Promote the committed-switch policy as the development baseline by explicit user decision."
  - "Do not claim statistical win-rate superiority from this sample."
  - "Preserve the prior behavior as legacy_baseline and keep the existing Kaggle package unchanged until an explicit rebuild and submission."
  - "Continue T-026 against the remaining 56 deck-out losses and confirm the promoted baseline over 1,000 independent matches."
evidence:
  - "reports/honchkrow_v3_retreat_guard_audit_20260807.md"
  - "tests/test_honchkrow_porygon.py"
  - "tests/test_honchkrow_opportunity_audit.py"
status: "promoted development baseline; remote submission pending"
```

## Identical-package opponent-sample variance TODO

```yaml
observed_at: "2026-08-07T00:00:00-03:00"
submission_ids: [55320796, 55320706]
observation: "Both submissions were produced from the same package."
hypothesis: "Any score or outcome difference may be explained by remote evaluation variance and opponent composition rather than by a package change."
todo:
  - "Evaluate the result over two distinct opponent samples."
  - "Document the opponent composition and sample size for each sample."
  - "Compute win rate, variance, and confidence intervals for each sample."
  - "Do not attribute a difference to the package until the opponent-sample effect is assessed."
acceptance: "A reproducible report compares both submissions across the two opponent samples and preserves the evaluation metadata."
status: "ready"
```

## Ignition energy-type and terminal-line CABT gate

```yaml
observed_at: "2026-08-07T07:13:00-03:00"
report: "reports/honchkrow_porygon_cabt_200_ignition_terminal_20260807.json"
matches: 200
evaluation_design: "100 matches per agent side against CABT"
results: "179W/0D/21L"
win_rate: 0.895
execution_failures: 0
comparison_baseline:
  report: "reports/honchkrow_porygon_local_eval_20260806.json"
  results: "157W/0D/43L"
  win_rate: 0.785
  delta_percentage_points: 11.0
telemetry:
  ignition_attachments: 124
  ignition_attacks: 120
  ignition_without_attack: 4
  porygon_terminal_opportunities: 5
  porygon_terminal_conversions: 0
  partial_mega_abomasnow_attacks: 0
audit:
  deck_out_losses: 15
  unresolved_terminal_reasons: 8
  partial_attack_matches: 0
interpretation:
  - "The planner now validates attack costs by energy type and quantity."
  - "Rocket Energy is modeled as two independently allocatable Darkness/Psychic units."
  - "Ignition Energy is modeled as three Colorless units on Evolution Pokémon."
  - "The sample improved by 11.0 percentage points, but this is an independent CABT sample and is not a significance claim."
  - "The gate remains open because four Ignition attachments were not followed by a recorded attack and five Porygon terminal opportunities converted zero times."
status: "implemented; CABT improvement observed; residual terminal telemetry requires follow-up"
```

## Turn-planning candidate Kaggle submission

```yaml
submitted_at: "2026-08-07T11:02:09Z"
competition: "pokemon-tcg-ai-battle"
archive: "submissions/honchkrow_porygon_turn_planning_20260807.tar.gz"
archive_sha256: "762c0f524af02a8dd14dba2d404e1a069bb9d4b923bec08c5c1963ea62b66f5d"
receipt: "reports/submissions/20260807T110209Z-762c0f524af0.json"
message: "Honchkrow turn planning and tactical ledger"
status: "accepted by Kaggle; public score and replay review pending"
promotion: "blocked until T-030 deck-out and non-inferiority gates pass"
```

## 2026-08-07 production replay corrective audit

The synchronized replays for submissions `55320796` and `55322957` were
replayed against their exact archives. The decisive implementation defect was
fail-open filtering: when every candidate was marked forbidden, the ranker was
given the forbidden list again. The generic filter now chooses an available
`END` selection in that deadlock and only preserves the original list for
mandatory prompts with no end option.

The deck-out guard is now global. Elective Ariana and Factory effects must leave
one card for the natural draw, or two cards while the Mega Abomasnow KO line is
being assembled. Factory abilities are checked as well as Factory plays. The
scorer also uses typed energy units (Rocket = 2, Ignition = 3) in readiness,
attachment, and Mega-Abomasnow commitment checks. Finally, a Porygon2 promotion
is scored as terminal when visible R Command damage takes the last prizes and an
Ignition Energy in hand completes the next-turn attack.

These are policy corrections, not proof of a production win-rate increase.
The required next experiment is the bilateral CABT replay gate with explicit
counts for forbidden actions, elective deck-out attempts, typed-energy
attachments, and terminal Porygon2 conversions.

## 2026-08-07 CABT comparison baseline promotion

```yaml
baseline_name: "honchkrow_porygon_post_audit_cabt_300"
git_commit: "d5f42c5"
source_report: "reports/honchkrow_porygon_cabt_300_post_audit_clean_20260807.json"
summary_report: "reports/honchkrow_porygon_cabt_baseline_20260807.json"
matches: 300
matches_per_side: 150
opponent: "cabt.random_agent"
results: "249W/0D/51L"
win_rate: 0.83
wilson_95: [0.7834, 0.8683]
execution_failures: 0
deck_out_losses: 12
unknown_losses: 39
comparison_reference:
  report: "reports/honchkrow_porygon_cabt_200_ignition_terminal_20260807.json"
  results: "162W/0D/38L"
  win_rate: 0.81
  deck_out_losses: 26
  interpretation: "The +2.0 percentage-point win-rate difference is inconclusive; the reduction in deck-out losses is the primary operational improvement."
promotion_scope: "This is the local CABT comparison baseline. Kaggle submission and remote ranking require a separate decision."
future_gate: "Use fresh independent CABT samples, preserve side splits, and report terminal-cause attribution before changing the baseline."
```
