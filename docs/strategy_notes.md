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
  archive: "reports/submissions/candidate-16f1e8b.tar.gz"
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
  rule: "With open Bench capacity, choose any legal Pokemon PLAY before ATTACK or END."
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
decision: "Monitor explicit Result.reason values in the Marimo dashboard and keep mirror-validation owner outcomes unknown."
evidence:
  notebook: "notebooks/03_run_results_dashboard.py"
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
archive: submission_hdi_v1.tar.gz
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
