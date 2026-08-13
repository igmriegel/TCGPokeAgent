# Honchkrow/Porygon Runtime Rules

## Purpose and evidence boundary

This document inventories the state-based rules executed by the canonical
`expert_turn_loop` Honchkrow/Porygon policy. It describes local runtime
behavior, not a claim of strategic improvement or replay-confirmed Kaggle
performance. The Owner-observed sequencing P0 remains open until replay-based
validation is accepted explicitly.

## Turn objective and order

| Rule | Runtime effect |
| --- | --- |
| Win now | A public game-winning attack takes priority over all setup, draw, and resource actions. |
| No-Pokemon protection | With one own Pokémon, play a backup Basic before optional resources unless a public terminal Porygon2 line exists. |
| Highest-value KO | A visible KO, especially one taking the remaining Prizes, outranks ordinary board development. |
| Canonical stages | The turn loop orders development, search, calculation, Supporter, Factory, Roto-Stick, Miracle Headset, and attack. Public changes replan the stage and objective. |
| END guard | END is rejected while a productive public development, recovery, protection, resource, or attack line remains. |

## Attack and promotion rules

| Rule | Runtime effect |
| --- | --- |
| No partial Rocket Feathers | Rocket Feathers is allowed only for a public KO; pressure damage is vetoed. |
| No partial R Command or Hammer In | These attacks require a committed public KO, not merely damage. |
| Rocket Feathers accounting | Damage is 60 per currently effective Rocket Supporter; discard prompts select the exact count required for the target. |
| R Command accounting | Damage is 20 per Rocket Supporter in discard and is evaluated against the selected public target. |
| Forbidden/contextual attacks | Hacking is prohibited. Dark Frost is not an Honchkrow/Porygon attack line. Deceit and Torment require their explicit decisive or survival contexts. |
| Promotion order | Immediate win, immediate KO, ready evolved attacker, then Murkrow fallback. |
| Porygon2 promotion | Ready Porygon2 with public lethal R Command is retained and prioritized, including terminal lines requiring Ignition. |
| Honchkrow promotion | Ready Honchkrow with lethal Rocket Feathers outranks Murkrow. |
| Articuno promotion | Articuno is normally preserved as a matchup defense and is avoided as an Active without a specific need. |

## Development, Energy, and search

| Rule | Runtime effect |
| --- | --- |
| Basic and evolution development | Murkrow/Porygon development builds attackers and protects against an empty-board loss. `BoardSetupPlan` requires a concrete missing attacker role; Articuno alone is protection, not completed attacker setup. Productive evolution stays available before Ariana. |
| Poké Pad commitment | Poké Pad searches Honchkrow only when Murkrow, attack cost, Supporters, and target publicly prove the KO sequence. |
| Porygon2 validity | Normal Porygon2 search/evolution requires an applicable Porygon line, while explicit terminal exceptions remain available. |
| Energy conversion | Energy is attached only when it completes or commits to a useful attack; wasteful attachments, excess energy, and Articuno energy are rejected. |
| Rocket Energy | Rocket Energy counts as two typed units and may enable a useful Murkrow attack. |
| Ignition Energy | Ignition is restricted to the Active or a committed promotion target and must enable a same-turn attack. |
| Proton | Proton is used for required early setup and prioritizes Articuno when the public matchup requires protection. |
| Transceiver | Transceiver seeks the missing Supporter for setup or a public KO; it rejects redundant Ariana and a Supporter after one was already played. |
| Roto-Stick | Roto-Stick is used only when its revealed Supporters can improve a KO, setup, or survival line. |

## Articuno matchup protection

| Rule | Runtime effect |
| --- | --- |
| Threat detection | Visible Abra, Kadabra, Alakazam, Dreepy, Drakloak, or Dragapult ex makes Articuno a protection resource. |
| Grimmsnarl/Froslass exception | When both Grimmsnarl ex and Froslass are public, Articuno is not prioritized. |
| Protection ordering | Reachable Articuno is played, searched, or recovered before non-terminal development where it is needed for the public matchup. |
| Preservation | Articuno is kept out of discard, attack, and promotion lines when it is needed as defense. |

## Supporters, switching, and recovery

| Rule | Runtime effect |
| --- | --- |
| Ariana | Ariana is played only when safe and useful; it waits for concrete development, recovery, protection, and energy obligations. It may legally use the final deck card. |
| Petrel | Petrel searches only targets with a current conversion. A Petrel that can only fetch Proton is deferred setup, because Proton cannot be played after Petrel in the same turn. |
| Factory | Factory is played or activated only for useful draw and may replace visible Spikemuth Gym. |
| Archer | Archer requires a public own-KO transition, a safe draw-five, and no superior visible line. |
| Giovanni pivot | Giovanni outranks paid retreat when it promotes a ready attacker for an immediate productive attack. |
| Giovanni Bench KO | Giovanni may bind both a ready Benched Porygon2 and a public opposing Bench target by serial when post-Giovanni R Command KOs and closes the Prize race. |
| Giovanni target selection | Targets prefer immediate win, high-Prize guaranteed KO, Darkness weakness, and energized Bench value; unready or insufficient-damage lines are rejected. |
| Paid retreat | Paid retreat is permitted only if it exchanges a nonlethal Active for an immediate KO; Giovanni has precedence. |
| Night Stretcher | Recovery requires an immediately playable Basic/evolution/attacker or required Articuno. Rocket Energy is the sole Energy exception: it must be legally attachable immediately and advance the active or committed attacker before Ariana; Tool payloads are not selected. |

## Miracle Headset plans

| Plan | Runtime effect |
| --- | --- |
| `headset_rocket_feathers_ko` | Recover up to two Supporters when they close the current public Rocket Feathers KO. |
| `headset_rocket_feathers_plus_ariana` | Recover Ariana and another Supporter when the line gains at least 60 Rocket Feathers damage; Ariana is preserved for the next turn rather than counted as current damage. |
| `headset_supporter_recovery` | With no playable Supporter, recover one or two Supporters that create a public action now. |
| `headset_giovanni_porygon2_bench_ko` | Recover Giovanni for a ready Benched Porygon2 to KO a public opposing Bench target. |
| Current-state calculation | Every plan recalculates target, energy, damage, and Supporter requirement from current public state; historical ledger counts do not authorize a KO. |
| Shared recovery plan | `RecoveryPlan` is used for Headset, Night Stretcher, deferred-Petrel comparison, obligations, and END filtering; it records the recovered public cards and conversion reason. |
| Committed selection | The recovery prompt is narrowed to Supporters authorized by the selected plan and avoids duplicate Ariana already in hand. |

## Resource protection, public damage, and audit

| Rule | Runtime effect |
| --- | --- |
| Item lock | Items are rejected after public Budew Itchy Pollen. |
| Tool Scrapper | A visible removable opponent Tool is prioritized, with Hero's Cape and Cynthia's Power Weight handled first. |
| Discard protection | Preserve Energy, Ariana, the final Supporter, Pokémon lines, and protected Headset resources unless a public KO explicitly consumes them. |
| Public damage | Damage accounts for weakness, resistance, and public prevention such as Splashing Dodge. |
| Serial commitments | Promotion, Ignition, Giovanni, and opponent targets use public serials when available, preventing a duplicate-card substitution. |
| Public-line evaluator | Porygon2/Headset/Giovanni terminal calculations record attacker, target, attack, before/after damage, Supporters, Prizes, verdict, and veto reason. |
| Decision ledger | Non-initial decisions emit the compressed `decision-ledger-v1` record to stderr; stdout remains simulator JSON only. |
| Deterministic fallback | Parsing or policy failure falls back to a legal deterministic selection without renumbering simulator option indices. |

## Interpretation notes

- `expert_turn_loop` is the active dedicated runtime policy. Historical names
  and helper methods are not independent runtime modes.
- A local test, package validation, or CABT smoke run proves operational
  behavior only. It does not prove strategic improvement on Kaggle.
- Replay identifiers are evidence/provenance only and must never be inputs to
  runtime policy conditions.
