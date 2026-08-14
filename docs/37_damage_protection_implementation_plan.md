# Damage Reduction and Invulnerability Implementation Plan

## Summary

Implement a declarative evaluator for active damage-reduction and damage-prevention effects in the public game state. The implementation will cover the complete inventory:

- 46 defensive Pokémon attacks;
- 7 Items/Fossils;
- 1 Supporter;
- 4 Stadiums;
- damage-counter prevention where applicable.

The same evaluator will be used by damage calculation, Knock Out checks, `PrizeMap`, and agent ranking/decision logic. Simulator option indices and unrelated gameplay rules must remain unchanged.

## Implementation Changes

### Declarative policy registry

Create an explicit registry for each approved effect. Each rule must identify:

- `card_id` and `attack_id`, when applicable;
- category: `damage_reduction`, `damage_prevention`, or `counter_prevention`;
- source type: attack, Pokémon, attached Tool/Energy, Supporter, or Stadium;
- valid zone: Active, Bench, attached Pokémon, or global field;
- affected attacker and defender scope;
- reduction amount and whether it applies before or after Weakness/Resistance;
- duration and additional conditions, including coin result, type, Ability, Rule Box, Energy, position, and HP.

The canonical SDK catalog remains the source for names and original text, while approved behavior is represented explicitly for auditability. Automatic free-form text inference is out of scope.

### Active-effect resolver

Add a central resolver that receives the public state, attacker, defender, attack, player ownership, public logs, attached cards, and Stadium in play. It returns:

- whether damage is prevented;
- total applicable reduction before Weakness/Resistance;
- total applicable reduction after Weakness/Resistance;
- whether damage counters are prevented;
- applied rules and rejected rules with reasons.

The resolver must:

- inspect both players and all applicable zones;
- support Active and Benched Pokémon, Tools/Energies, Supporters, and Stadiums;
- activate coin-based protection only when public logs confirm `heads`;
- treat missing, `tails`, or unknown coin results as unconfirmed protection;
- expire temporary effects correctly;
- distinguish incoming-damage protection from outgoing attack-damage reduction.

### Precedence

Apply effects in this logical order:

1. Any applicable total-damage prevention sets damage to zero.
2. If damage is not prevented, all applicable reductions are summed.
3. Damage is clamped at zero.
4. Weakness/Resistance ordering follows each card's original text.
5. Counter prevention is evaluated separately and does not prevent ordinary attack damage.

Attacks such as `Throh — Shoulder Throw` and `Tinkaton — Windup Swing` must be modeled as offensive damage modifiers, not as protection for the defending Pokémon.

### Engine and policy integration

Replace the current isolated special cases in `src/core/damage.py` with the declarative resolver. Use the same result in:

- `calculate_damage`;
- best-attack-damage calculations;
- Knock Out checks;
- `PrizeMap`;
- attack ranking;
- filters for attacks that cannot deal effective damage;
- switching, retreat, and attacker-preservation decisions;
- recognition of active protection on the agent's own Pokémon.

The current `has_splashing_dodge_protection` behavior should become one registered policy rather than a separate special-case path.

### State normalization

Ensure parsing consistently normalizes:

- Active and Benched Pokémon;
- Pokémon serials;
- attached Tools and Energies;
- Stadium as object, list, or ID;
- player ownership;
- public attack, effect, coin, and counter logs.

When the observation lacks enough information to confirm protection, use conservative behavior: do not assume invulnerability and do not suppress damage.

### Documentation reconciliation

Reconcile `docs/cartas_com_reducao_de_dano.md` with the canonical inventory so it contains all expected records:

- 46 Pokémon attacks;
- 7 Items/Fossils;
- 1 Supporter;
- 4 Stadiums.

Add coverage links between each documented entry and its declarative `card_id`/`attack_id` rule. Keep separate categories for total prevention, incoming-damage reduction, outgoing-damage reduction, and counter prevention.

## Tests and Acceptance Criteria

Add unit tests for:

- every total-prevention category;
- every reduction amount;
- effects before and after Weakness/Resistance;
- offensive versus defensive reductions;
- coin results `heads`, `tails`, and missing;
- Active and Bench effects;
- attached Tools/Energies;
- persistent Supporter effects;
- global Stadium effects;
- type, Rule Box, Ability, position, and HP conditions;
- multiple reductions and total-prevention precedence;
- zero-damage clamping;
- counter prevention without attack-damage prevention;
- temporary-effect expiration and replacement;
- mismatched serials and player ownership.

Add integration tests proving that one resolved effect set is used by damage, KO, `PrizeMap`, ranking, and policy decisions.

Add an inventory coverage check requiring:

- exactly 46 Pokémon attacks;
- exactly 7 Items/Fossils;
- exactly 1 Supporter;
- exactly 4 Stadiums;
- no unintended duplicate `card_id`/`attack_id` entries;
- no documented entry without a policy;
- no policy without documentation.

Run the focused damage/policy tests, the full pytest suite, `scripts/audit_documentation.py`, extracted-package validation, and a bilateral CABT smoke test. The smoke test must preserve zero `INVALID`, `ERROR`, and `TIMEOUT` outcomes. No strategic improvement claim should be made without before/after evaluation evidence.

## Assumptions

- “Invulnerability” means total damage prevention while the card's condition is satisfied.
- Unconfirmed protection is not assumed to be active.
- Effects that prevent attack effects but explicitly do not prevent damage remain outside damage prevention.
- Damage-counter prevention is evaluated independently from attack damage.
- The implementation changes the central evaluator and strategic decisions, but not simulator option numbering or unrelated gameplay behavior.
