# Submission 55422182 first-divergence review

Downloaded and decoded decision ledgers for submission `55422182` on 2026-08-12.
The records identify one first actionable divergence per replay.  They are
single-decision observations, not claims about counterfactual wins.

| Replay | First observed divergence | Public evidence | Correction covered |
|---|---|---|---|
| `92410349` | Passive END retained Roto-Stick and Articuno. | Decision 26 selected END while both cards were playable candidates. | A supporterless Roto now remains productive unless the deck-reserve veto applies. |
| `92351382` | Ariana was selected before the hand had a complete auditable reduction pass. | Decision 2 selected Ariana while Giovanni and Energy candidates remained; the historical ledger had no retained-card reasons. | Stadium, development, committed Poké Pad, productive items, and productive Energy are now considered before Ariana; retained cards have a ledger field. |
| `92344156` | Passive END retained the sole Roto-Stick. | Decision 10 selected END with Roto-Stick as the only non-END candidate. | A supporterless Roto now attempts conversion rather than ending passively. |
| `92301028` | Ariana preceded a Roto-Stick held in a no-attack resource line. | Decision 20 selected Ariana while Roto-Stick and Articuno were playable candidates. | The canonical loop now allows Roto before a Supporter when no Supporter is in hand and reserve permits it. |

The archived package traces have empty package hashes and source commits in
these ledger events.  They are therefore evidence of the observed decision
path, but not sufficient by themselves to establish immutable package
provenance. Replay-based Owner acceptance remains required to close the
Owner-observed divergence.

## Additional Owner-reviewed replays

| Replay | First observed divergence | Correction scope |
|---|---|---|
| `92280407` | Petrel selected despite two playable Arianas and Proton already in hand; the following turn repeated Petrel into Proton and passed. | Petrel now rejects Proton already held and its Factory exception applies only when Ariana draws at most two cards. |
| `92269436` | A post-KO Archer displaced a public Giovanni/Roto attack line; the later low-hand Headset opportunity was not treated as Ariana recovery. | Archer is vetoed by public attack/setup/draw lines; Giovanni evaluates bench attackers; Headset accepts a small inactive hand with Ariana in discard. |

Froslass KO opportunities are tracked separately: the policy applies one
post-attack ten-HP reduction per visible opposing Froslass only to targets
whose public metadata contains an Ability.  CABT confirmation remains required
before treating this as strategic evidence.

## P0 setup and resource review

The following four local raw replays were inspected at their first causal
owner-side actions. They establish observed sequencing inputs only; they do
not establish an alternate result.

| Replay | Observed public sequence | New divergence class | Implemented guard |
|---|---|---|---|
| `92201785` | Ultra Ball search preceded Porygon2 selection during opening setup. | `setup_search_before_proton` | Proton/setup now blocks Ultra Ball, and Ultra Ball cannot select Porygon2 in that state. |
| `92191620` | Proton established the opening Bench against a public Dreepy line. | `dragapult_protection_must_persist` | Petrel/Proton search preserves the Poké Pad → Articuno protective line; Itchy Pollen still blocks Item lines. |
| `92168434` | Ultra Ball was used before later resource conversion. | `ultra_ball_supporter_preservation` | Required Supporters cannot be discarded except for a current-state, exact R Command win. |
| `92157127` | The early resource sequence exposed a setup-versus-attack choice. | `opening_partial_attack_abandons_setup` | Porygon/Porygon2 partial attacks are blocked on the first own turn; legal Roto resolves before partial damage unless deck reserve or Budew forbids it. |

The decision ledger now exposes the corresponding guard or priority reason:
`block_initial_porygon_partial_attack`, `preserve_ultra_ball_for_proton_setup`,
`free_porygon_for_ready_honchkrow`, `play_roto_before_partial_damage`, and the
selected Giovanni target's priority class and Prize value. Archer's approval is
also limited to a public dead hand: spent Energy and unpaired Evolutions are
not treated as productive resources.
