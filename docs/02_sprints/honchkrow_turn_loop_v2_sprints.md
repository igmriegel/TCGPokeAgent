# Honchkrow/Porygon Expert Turn Loop v2

> Dedicated implementation and promotion track. Detailed status is owned by
> [`HONCHKROW_TURN_LOOP_V2_TASK_INDEX.md`](../03_tasks/HONCHKROW_TURN_LOOP_V2_TASK_INDEX.md).

## Frozen contract

- Baseline: `supporter_resource_v2`; its behavior is immutable in this track.
- Candidate: `expert_turn_loop_v2`; it must always be selected explicitly.
- Deck and card profile are shared byte-for-byte by both policies.
- Historical replay evidence is restricted to the 26 frozen replays from
  submission `55333874`.
- Beliefs, opposing hand contents, and post-divergence outcomes are never facts.
- Local CABT gates decide promotion. Remote Kaggle upload is outside scope unless
  explicitly authorized; this run has an explicit user override recorded in the
  status index despite the screening `HOLD`.

The reproducible foundation manifest is generated with:

```bash
uv run --frozen python scripts/create_honchkrow_turn_loop_v2_manifest.py
```

## Expert annotation matrix

`IMPLEMENTED` means the candidate has an executable rule and focused evidence.
`PARTIAL` means a rule exists but its full fixture or evaluation gate remains
open. `MISSING` means no candidate behavior exists. `REJECTED` means the rule
would require hidden information or conflicts with a stronger verified rule.

| Annotation | Verifiable rule and precondition | Current method | Public information | Exception | Telemetry / fixture | Status |
|---|---|---|---|---|---|---|
| Develop Basics first | Fill legal Bench space during setup before resource-only actions | `_main_phase_selections`, scorer board rules | Own hand, field, Bench capacity, legal options | Immediate win, forced prompt, committed KO | Board width; empty/one/developed field | `PARTIAL` |
| Evolve available Pokémon | Prefer productive Honchkrow/Porygon2 evolution | `_main_phase_selections` | Own field, hand, legal evolution option | Immediate terminal line has priority | Stage and evolution replan | `IMPLEMENTED` |
| Proton repairs the board | Use only on opening/setup with fewer than two Pokémon and useful visible targets | `_proton_setup_is_useful`, `_filter_duplicate_proton_roles` | Own field, turn, visible candidates | Do not break a terminal line | Proton target and late-use counters | `IMPLEMENTED` |
| Poké Pad finds Honchkrow | Search when a current or next-turn evolution line is public | `_refresh_evolution_ko_commitment`, `_pokepad_honchkrow_is_useful` | Murkrow age, Energy, deck copies, target HP | No useful Honchkrow target | Evolution-KO golden | `PARTIAL` |
| Ultra Ball has a purpose | Require a useful target and two acceptable legal discards | `_ultra_ball_is_productive`, discard filters | Public hand, deck counts, legal targets | Exact KO discard may spend a Supporter | Discard fixtures | `PARTIAL` |
| Night Stretcher is immediate | Recover only a Pokémon that can enter the current line | `_night_stretcher_is_productive` | Public discard, field and hand | None | Immediate bench/evolution fixtures | `IMPLEMENTED` |
| Petrel is exact | Select only the item tied to the recorded objective | `_petrel_target_is_useful` | Public hand/deck estimates and candidates | No generic target | Target/reason telemetry | `PARTIAL` |
| Supporter KO priority | Prefer demonstrable Giovanni terminal line, otherwise draw/search/recovery/setup | objective and switch commitments | Target HP/Prizes, attackers, Energy, hand | Survival and forced prompts | KO candidates and objective | `PARTIAL` |
| Factory already in hand | Play Factory before Ariana to reduce hand size and maximize Ariana draw | `_factory_play_is_useful`, `_main_phase_selections` | Own hand, stadium state, deck reserve | Immediate win | `stadium_before_ariana` golden | `IMPLEMENTED` |
| Factory drawn by Ariana | After Ariana resolves, play the newly drawn Factory, activate it only if useful, then replan | `_factory_play_is_useful`, `_factory_is_useful`, `_replan_reason` | Current public hand, Supporter flag, deck reserve | Reject unsafe/unproductive draw | Post-Ariana Factory golden | `PARTIAL` |
| Archer after KO | Require a public previous-turn KO and a safe replacement hand | `_archer_is_safe_and_useful` | Public log, hand, Active Energy, deck | Preserve an already productive hand | Archer fixtures | `PARTIAL` |
| Roto has two modes | Setup only without Proton/Ariana; attack mode maximizes useful Supporters | `_roto_setup_mode`, `_roto_recovery_selections` | Hand, ready attacker, revealed cards | Preserve redundant Supporters/Ariana when required | Roto counts and damage delta | `IMPLEMENTED` |
| Headset recovers two | Require exactly two useful Supporters and a KO/draw conversion | `_v3_miracle_headset_is_useful`, Headset selection filter | Public discard, target, hand, deck | Deck-out guard | Recovery/opportunity counters | `IMPLEMENTED` |
| Rocket Feathers is committed | Attack only for KO or an explicitly productive horizon | `_variant_attack_is_lethal`, `_rocket_feathers_has_horizon` | Hand Supporters, target HP, Energy | Prevent immediate loss | Required/available/damage ledger | `IMPLEMENTED` |
| Porygon2 closes Prizes | Promote and attach Ignition only for a same-turn terminal R Command | switch and Ignition commitments | Discard Supporters, Energy, target HP/Prizes | None | Ignition-without-attack counter | `IMPLEMENTED` |
| Retreat converts now | Giovanni first; paid retreat only into a proven immediate attack | `_giovanni_switch_plan`, `_paid_retreat_plan` | Visible Active/Bench, costs, Energy, target | Forced selection | Resource guard and conversion | `IMPLEMENTED` |
| Confusion is factual | Use only `PokemonState.confused`, public retreat cost and visible attackers | retreat commitment helpers | Explicit status, Energy, legal options | No inference from prose/log fragments | Confusion golden | `PARTIAL` |
| Opponent hidden hand tactics | Do not infer disruption or a KO line from unseen cards | N/A | Not public | Always rejected | Hidden-information audit | `REJECTED` |

## Sprint gates

### HLV2-S0 — Evidence, scope and freezing

HLV2-001 freezes policy names, deck/profile/lock hashes, source revision, SDK
pin and replay corpus. HLV2-002 owns the rule matrix above. Exit requires a
regenerable manifest and no runtime dependence on an implicit environment
variable when selecting the candidate.

### HLV2-S1 — Persistent turn planning

HLV2-003 adds the public turn ledger. HLV2-004 invalidates the objective after
draw/search/recovery, Pokémon placement, evolution, Supporter, Stadium, Item,
discard, Energy attachment and retreat, recording previous/new stages.

### HLV2-S2 — Setup, board and search

HLV2-005 through HLV2-007 cover Basic placement, Proton, Poké Pad, Ultra Ball,
Night Stretcher and exact Petrel targets. Exit requires precedence, no-target,
discard, deck-reserve and terminal-line fixtures.

### HLV2-S3 — Supporters and draw engine

HLV2-008 through HLV2-012 cover KO arithmetic, Supporter priority, both valid
Factory/Ariana orders, Archer, Roto-Stick and Miracle Headset. Every draw or
zone change must refresh damage and reserve telemetry.

### HLV2-S4 — Attack, retreat and Confusion

HLV2-013 through HLV2-016 cover Rocket Feathers, terminal R Command, Ignition,
Giovanni, paid retreat and explicit Confusion. Exit requires zero qualified
`torment_with_superior_line`, `ignition_without_attack`, and unconverted paid
retreat events in focused fixtures.

### HLV2-S5 — Integration and telemetry

HLV2-017 integrates only `expert_turn_loop_v2`; HLV2-018 emits decision JSONL
with variant, stage, objective, public resource arithmetic, reasons, fallback,
latency and tactical counters. Simulator option indices remain unchanged.

### HLV2-S6 — Tests and replay audit

HLV2-019 runs unit, golden, full pytest, Ruff, formatter, mypy and pre-commit.
HLV2-020 reproduces all 26 frozen replays for baseline and candidate. A
divergence is a single-decision counterfactual; no alternate match outcome may
be claimed after it.

### HLV2-S7 — CABT comparison

HLV2-021 runs 300 bilateral matches per policy. Only after all operational and
tactical gates pass may HLV2-022 run independent 1,000-match blocks per policy.
HLV2-023 writes the required JSON, JSONL, Markdown and HTML artifacts under
`reports/honchkrow_turn_loop_v2/<run_id>/`. Promotion requires a positive
candidate win-rate difference whose 95% lower bound exceeds zero, zero
operational failures and no deck-out or material tactical regression.

### HLV2-S8 — Closure and release

HLV2-024 builds and validates a package only after every promotion gate passes,
or after an explicitly recorded user override such as this operational release.
HLV2-025 updates release status only after that decision. Failure retains
`supporter_resource_v2` and must not create or upload a submission.
