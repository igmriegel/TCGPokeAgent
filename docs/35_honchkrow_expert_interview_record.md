# Honchkrow/Porygon expert interview record

> Append-only record of expert answers collected under
> `34_honchkrow_expert_interview.md`. Summaries are written in English to match
> the project language. Runtime behavior changes require the final approved
> implementation plan.

**Expert context:** months of direct play with the fixed deck

**Interview status:** Paused after Rounds 1–3 on 2026-08-07. Rounds 4–12 are
documented in `34_honchkrow_expert_interview.md`; resume at Round 4. Matchup-
dependent exceptions remain deferred to Round 9.

**Experimental implementation:** `expert_rounds_1_3_v1` isolates the directly
actionable rules from the first three rounds. It is an evaluation candidate,
not the promoted runtime baseline. Energy allocation, exact Porygon protection,
Supporter over-discard, matchup thresholds, and any rule scheduled for later
rounds remain unchanged.

## Round 1 — Deck identity and default win condition

### HI-001 — Dynamic six-Prize race

```yaml
question_id: "HI-001"
expert_rule: "Choose Honchkrow or Porygon2 dynamically from the current opportunity; the only universal win condition is taking all six Prizes before the opponent."
strength: "MUST"
when:
  - "At every attack-plan and development decision"
priority_above:
  - "A fixed attacker identity"
priority_below:
  - "An immediate legal game-winning line"
exceptions: []
counterexample: "Continuing to preserve Honchkrow hand damage when the discard already makes R Command the stronger Prize-taking line."
hidden_information_policy: "Use public Prize, zone, damage, and availability evidence; do not commit to one attacker for the whole match."
required_state: ["own Prizes remaining", "opponent target Prize value", "Supporters by zone", "attacker readiness"]
telemetry: ["selected game plan", "plan-switch reason", "projected Prizes over the attack horizon"]
golden_tests: ["Honchkrow is superior", "Porygon2 is superior", "both attacks take the same KO with different resource cost"]
status: "RATIFIED"
```

### HI-002 — Supporter scarcity triggers the Porygon2 pivot

```yaml
question_id: "HI-002"
expert_rule: "Shift investment toward Porygon2 as Team Rocket Supporters become scarce in the deck and accumulate in the discard pile."
strength: "MUST"
when:
  - "The remaining Supporter supply cannot reliably sustain Rocket Feathers"
  - "The discard count makes R Command competitive for current or expected targets"
priority_above:
  - "Blindly continuing the Honchkrow plan"
priority_below:
  - "An immediate superior Honchkrow Prize-taking line"
exceptions:
  - "Do not promote or expose Porygon2 before its attack horizon justifies the risk"
counterexample: "Many Supporters are already discarded and few remain searchable, but the agent spends turns rebuilding a large Honchkrow hand."
hidden_information_policy: "Track the twenty declared Supporters across hand, discard, known Prizes, and estimated deck remainder."
required_state: ["Supporters in hand", "Supporters in discard", "known or possible Supporters in Prizes", "estimated Supporters in deck"]
telemetry: ["supporter zone counts", "Honchkrow projected damage", "R Command projected damage", "pivot threshold"]
golden_tests: ["early Supporter-rich Honchkrow plan", "late Supporter-poor Porygon2 plan", "Porygon2 protected until ready"]
status: "RATIFIED"
```

### HI-003 — Maximum early Murkrow development, protected late Porygon

```yaml
question_id: "HI-003"
expert_rule: "Fill available early board space with as many Murkrow as possible, use Murkrow as replaceable attackers or sacrifices, and introduce and protect Porygon for the stronger late-game R Command line."
strength: "MUST"
when:
  - "During opening and early board development"
priority_above:
  - "Early Porygon development without a defined protection plan"
priority_below:
  - "Bench-space exceptions that the matchup or Prize race proves necessary"
exceptions:
  - "Exact reserved Bench space remains matchup-dependent and requires HI-004 clarification"
counterexample: "The agent diversifies Proton targets and leaves searchable Murkrow in deck despite open Bench space."
hidden_information_policy: "Use known Murkrow availability and Bench capacity."
required_state: ["Murkrow by zone", "Bench occupancy", "Porygon line availability", "opponent targeting and spread threats"]
telemetry: ["early Murkrow count", "turn Porygon entered play", "Porygon exposure before readiness"]
golden_tests: ["Proton may take multiple Murkrow", "Poké Pad takes fourth Murkrow", "Porygon is delayed and protected"]
status: "RATIFIED"
```

### HI-004 — Bench reservation

```yaml
question_id: "HI-004"
expert_rule: "Reserve Bench space according to the specific match rather than a universal fixed count."
strength: "SHOULD"
when:
  - "Before every Bench placement or recovery decision"
priority_above: []
priority_below: []
exceptions: []
counterexample: "A fixed reserved slot either blocks a needed Murkrow or leaves no space for a matchup-critical Porygon or Articuno."
hidden_information_policy: "Pending variables and matchup table."
required_state: ["Bench capacity", "current attackers", "matchup threats"]
telemetry: ["reserved slots", "reservation reason", "blocked development opportunities"]
golden_tests: []
status: "NEEDS_REPLAY"
```

Clarification ratified immediate game win as the absolute first objective. The
no-Pokémon survival objective applies only when no immediate game win exists.

### HI-005 — Energy is the primary scarce resource

```yaml
question_id: "HI-005"
expert_rule: "Treat Energy as the deck's scarcest resource because it has no direct search line and must never be wasted."
strength: "MUST"
when:
  - "Attachment, discard, retreat, and recovery decisions"
priority_above:
  - "Marginal board development or hand reduction"
priority_below:
  - "A proven game-winning expenditure"
exceptions:
  - "Exact valid expenditures and the ordering of all other resources require Round 4"
counterexample: "Attaching an Energy without a defined attack or retreat horizon."
hidden_information_policy: "Estimate remaining Energy from all public zones and possible Prizes."
required_state: ["typed Energy by zone", "searchability", "attacker cost", "turns to attack"]
telemetry: ["Energy spent without attack horizon", "last-Energy decisions", "Energy stranded at terminal state"]
golden_tests: ["protect last Energy", "spend Energy for immediate Prize", "reject speculative attachment"]
status: "RATIFIED"
```

The relative scarcity order after Energy remains unanswered.

### HI-006 — Ideal early turns and first Prize

```yaml
question_id: "HI-006"
expert_rule: "Use turn one for maximum Murkrow setup through Proton and search, then use turns two and three to reduce hand safely before Ariana, maximize Energy access, evolve, attach to a real attacker, and start the Prize race at the first legal opportunity."
strength: "MUST"
when:
  - "Opening through the first Prize-taking turn"
priority_above:
  - "Generic card-value ranking"
priority_below:
  - "An immediate game-winning or matchup-mandated exception"
exceptions:
  - "Ignition is attached only after an Active Murkrow can evolve and attack in the same turn"
counterexample: "Playing Ariana before searchable Pokémon leave the hand, reducing the probability of seeing Energy."
hidden_information_policy: "Maximize marginal draw toward unsearchable Energy while respecting known deck composition."
required_state: ["own turn number", "cards in hand", "search targets remaining", "legal evolutions", "typed Energy in hand", "marginal Ariana draw"]
telemetry: ["turn-one Murkrow count", "turn-one Proton access path", "pre-Ariana hand reduction", "Energy seen after draw sequence", "turn of first Prize"]
golden_tests:
  - "Turn-one Proton takes the required Murkrow"
  - "Turn-one Poké Pad takes fourth Murkrow or next-turn Honchkrow"
  - "Turn-one Roto keeps only Proton and/or Ariana"
  - "Turn-two search, Bench, Stadium, and evolution maximize Ariana"
  - "Ignition follows evolution and commits an immediate attack"
status: "RATIFIED"
```

Detailed timing captured from the expert:

- Turn one: use Proton for setup; use Poké Pad for the fourth Murkrow or an
  Honchkrow for next turn. If both Proton and Ariana are absent, seek a setup or
  survival Supporter with Transceiver or Roto-Stick. In this opening Roto
  context, prioritize Proton and/or Ariana rather than maximizing generic
  Supporter count.
- Turns two and three: use available search Items, play Pokémon and Stadium,
  evolve, and reduce the hand before Ariana so Ariana maximizes the chance of
  seeing Energy. Attach available Energy to an actual attacker. Ignition is
  valid only after an Active Murkrow can evolve and attack that turn.
- First Prize: the deck should initiate the Prize race as soon as Honchkrow or
  a Prize-taking Murkrow attack becomes available.

### HI-007 — Murkrow control attacks

```yaml
question_id: "HI-007"
expert_rule: "Never use Hacking; use Deceit only as a low-hand, no-Supporter survival line to find Ariana; use Torment mainly for a Knock Out or to lock the only attack of an opponent with a single Pokémon in play."
strength: "MUST"
when:
  - "Murkrow is Active and no superior Prize-taking line exists"
priority_above:
  - "Passing without progression"
priority_below:
  - "A faster primary damage or Prize line"
exceptions:
  - "Torment control is valid when the opponent has one Pokémon and only one usable attack"
counterexample: "Using Deceit as a generic search attack while Ariana or another progression Supporter is already in hand."
hidden_information_policy: "Use visible hand size, visible Supporter access, opponent board width, and legal opposing attacks."
required_state: ["own Supporters in hand", "own hand count", "opponent Pokémon count", "opponent Active attacks", "Torment KO damage"]
telemetry: ["Deceit survival opportunities", "Supporter fetched by Deceit", "Torment KO", "Torment single-attack lock", "Hacking selections"]
golden_tests: ["Hacking always rejected", "Deceit fetches Ariana with no Supporter and low hand", "Torment takes KO", "Torment locks sole opposing attack"]
status: "RATIFIED"
```

The expert confirmed that Deceit was intended. Deceit deals no damage and is
used only for its Supporter-search effect under the stated survival conditions.

### HI-008 — Fast Prize pressure with mandatory R Command tracking

```yaml
question_id: "HI-008"
expert_rule: "Pursue the fastest Prize race, but continuously evaluate R Command because two large Honchkrow attacks can leave twelve to fourteen Supporters in discard and create 240 to 280 damage."
strength: "MUST"
when:
  - "After every Supporter play, Rocket Feathers discard, recovery, and target change"
priority_above:
  - "A fixed Honchkrow-only game plan"
priority_below:
  - "An immediate faster six-Prize line"
exceptions: []
counterexample: "Ignoring a ready 280-damage R Command after two Honchkrow attacks and spending turns rebuilding hand damage."
hidden_information_policy: "Use public discard damage and known target HP; estimate future targets only as a secondary horizon."
required_state: ["discarded Team Rocket Supporters", "current and likely target HP", "Porygon2 readiness", "Prize map"]
telemetry: ["R Command damage after each Honchkrow attack", "missed R Command KO", "plan switch turn"]
golden_tests: ["12-Supporter 240-damage target", "14-Supporter 280-damage target", "Honchkrow remains faster despite available R Command"]
status: "RATIFIED"
```

Examples named by the expert for the 240–280 damage range include Ogerpon,
Latias, Meowth, and Fezandipiti variants in the observed metagame.

## Round 1 implementation deltas discovered

These are audit findings, not yet authorized changes:

| ID | Expert rule | Current behavior | Required future slice |
|---|---|---|---|
| R1-D01 | Maximize early Murkrow | Proton selection removes repeated tactical roles, which can reject multiple Murkrow | Replace role diversification with opening-board target optimization |
| R1-D02 | Roto has a setup/survival mode when both Proton and Ariana are absent; otherwise it is used with an attack-ready line and takes the maximum available Supporters | Roto is gated behind a ready Honchkrow and always selects every revealed Supporter | Add explicit Roto modes, target selection, and post-resolution damage recomputation |
| R1-D03 | Poké Pad may prepare next-turn Honchkrow | Honchkrow search usually requires a currently evolvable or ready line | Add next-turn evolution readiness and opening-hand planning |
| R1-D04 | Deceit is a no-Supporter survival search | Deceit is accepted only through damage or explicit decisive metadata | Model Supporter-search value and exact target choice |
| R1-D05 | Torment can lock a sole opposing attack | The scorer relies on coarse `preventsAttack` metadata without board-width proof | Add attack-count and opponent-board conditions |
| R1-D06 | Porygon pivot follows all Supporter zones | Zone counts estimate deck from a fixed total but do not expose a unified plan-switch threshold | Define expert thresholds and one zone-accounting feature |

## Round 1 clarification — Roto-Stick modes

```yaml
question_id: "HI-006-R1"
expert_rule: "Use Roto-Stick only when an attacker is ready to convert additional Supporters into damage or when neither Proton nor Ariana is in hand and Roto provides the required setup or survival line."
strength: "MUST"
when:
  - "Attack mode: a legal ready attacker can convert Supporters into the current attack line"
  - "Setup/survival mode: neither Proton nor Ariana is in hand and Roto-Stick is available"
priority_above:
  - "Holding Roto while the revealed Supporters change a Prize-taking attack"
priority_below:
  - "An immediate winning attack that does not need additional Supporters"
exceptions:
  - "Do not use Roto merely because it is legal"
counterexample: "Using Roto with no ready attack and while Ariana or Proton already provides progression."
hidden_information_policy: "Resolve the visible top-four selection, then recompute the factual hand Supporter count and every affected attack's damage."
required_state: ["Ariana in hand", "Proton in hand", "ready attacker", "revealed Roto cards", "Supporters selected", "post-Roto hand"]
telemetry: ["Roto mode", "Supporters revealed", "Supporters selected", "damage before Roto", "damage after Roto", "KO threshold crossed"]
golden_tests:
  - "Opening Roto without Ariana or Proton enters setup mode"
  - "Roto is preserved when progression already exists and no attacker is ready"
  - "Attack-mode Roto selects the maximum number of Supporters"
  - "Damage and KO status are recomputed after every Roto resolution"
status: "RATIFIED"
```

The exact opening selection when neither Proton nor Ariana appears among the
top four remains part of the Supporter-target interview in Round 6, with one
ratified floor: when no Supporter is already in hand, take at least Petrel if it
is revealed.

### HI-006-R2 — Opening Roto selection cardinality

```yaml
question_id: "HI-006-R2"
expert_rule: "In opening setup mode, take both Proton and Ariana when both are revealed, take only one copy when multiple Proton are revealed, and take at least Petrel when no Supporter is already in hand."
strength: "MUST"
when:
  - "Roto-Stick is used in opening setup or survival mode"
priority_above:
  - "Maximizing the raw number of revealed Supporters"
priority_below:
  - "A later attack-mode Roto, which maximizes Supporter count for damage"
exceptions:
  - "The complete Archer, Giovanni, and Petrel selection table remains for Round 6"
counterexample: "Taking two Proton while leaving Ariana after Roto, or taking no progression Supporter when Petrel is the only revealed option and the hand has none."
hidden_information_policy: "Use only the revealed top four and current visible hand."
required_state: ["Supporters in hand", "revealed Supporter IDs", "Roto mode"]
telemetry: ["opening Roto target IDs", "duplicate Proton skipped", "Petrel survival floor"]
golden_tests:
  - "Proton plus Ariana selects both"
  - "Two Proton selects one"
  - "No Supporter in hand and Petrel revealed selects Petrel"
status: "RATIFIED"
```

### HI-003-R1 — Early Murkrow board width

```yaml
question_id: "HI-003-R1"
expert_rule: "Develop at least three and preferably all four Murkrow when legal, while checking how many Pokémon remain in deck and how many are in the Prizes."
strength: "MUST"
when:
  - "Opening and early setup"
priority_above:
  - "Artificially diversifying Proton targets"
priority_below:
  - "A proven availability or matchup exception"
exceptions:
  - "Do not assume all four are searchable when deck and Prize evidence contradicts it"
counterexample: "Stopping at one or two Murkrow despite legal Bench space and known searchable copies."
hidden_information_policy: "Combine visible zones with PrizeCheck bounds before deciding whether the third or fourth Murkrow is available."
required_state: ["Murkrow in play", "Murkrow in hand", "Murkrow in discard", "Murkrow searchable range", "Murkrow Prize evidence"]
telemetry: ["Murkrow count after setup", "third-Murkrow opportunity", "fourth-Murkrow opportunity", "availability reason"]
golden_tests: ["Proton selects repeated Murkrow", "three-Murkrow minimum", "fourth Murkrow unavailable in Prizes"]
status: "RATIFIED"
```

### HI-005-R1 — Scarcity and Miracle Headset transfer

```yaml
question_id: "HI-005-R1"
expert_rule: "Energy is the primary scarce resource; preserve the unique Miracle Headset for strategically important Supporters or two Supporters that add up to 120 Rocket Feathers damage, while accounting for the 20 R Command damage removed per recovered Supporter."
strength: "MUST"
when:
  - "Miracle Headset recovery and attack-plan comparison"
priority_above:
  - "Using the ACE SPEC for generic hand value"
priority_below:
  - "A superior immediate or terminal Prize line"
exceptions:
  - "One critical Supporter may justify Headset even without the full 120-damage gain; exact cases remain for Round 6"
counterexample: "Recovering two Supporters to add 120 Honchkrow damage when losing 40 R Command damage destroys the stronger terminal line."
hidden_information_policy: "Recalculate both hand-based Rocket Feathers and discard-based R Command after selecting recovery targets."
required_state: ["Supporters by ID in discard", "Supporters in hand", "Honchkrow damage", "R Command damage", "target HP and Prizes"]
telemetry: ["Headset targets", "Rocket Feathers delta", "R Command delta", "selected attacker after recovery"]
golden_tests:
  - "Recover two for a 120-damage Honchkrow KO"
  - "Preserve discard because Porygon2 is the stronger line"
  - "Recover one strategically critical Supporter"
status: "RATIFIED"
```

The expert also identified Factory as scarce at three copies and each Team
Rocket Supporter as present at the legal maximum of four copies. A strict total
ordering among all remaining resources is not yet required; card-specific
preservation rules will be completed in Rounds 4 and 6.

## Round 2 — Opening, turn order, and setup

### HI-010 — Always choose first

```yaml
question_id: "HI-010"
expert_rule: "Always choose to play first so Proton is legal on turn one, Evolutions come online earlier, and Rocket Feathers can begin the Prize race sooner."
strength: "MUST"
when:
  - "IS_FIRST selection in every matchup"
priority_above:
  - "Any generic advantage from going second"
priority_below: []
exceptions: []
counterexample: "Choosing second and losing the turn-one Proton and earliest evolution window."
hidden_information_policy: "No matchup inference changes this choice."
required_state: ["IS_FIRST legal options"]
telemetry: ["side choice", "turn-one Proton availability", "first evolution turn"]
golden_tests: ["Choose YES in every IS_FIRST prompt"]
status: "RATIFIED"
```

### HI-011 — Opening Active order

```yaml
question_id: "HI-011"
expert_rule: "Choose the opening Active in this order: Murkrow, Porygon, Articuno."
strength: "MUST"
when:
  - "Initial Active selection"
priority_above: []
priority_below: []
exceptions:
  - "If Articuno must start Active, either accept it as a sacrifice or use Giovanni later when a ready attacker and a valuable opposing KO target exist"
counterexample: "Starting Articuno while Murkrow is available."
hidden_information_policy: "Use the visible opening Pokémon only."
required_state: ["opening Basic options", "ready Bench attacker", "Giovanni availability", "opponent Bench targets"]
telemetry: ["opening Active card", "Articuno sacrifice", "Giovanni exit from Articuno"]
golden_tests: ["Murkrow over Porygon", "Porygon over Articuno", "Articuno Giovanni exit requires ready attacker and valuable target"]
status: "RATIFIED"
```

### HI-012 — Bench all opening Basics except conditional Articuno

```yaml
question_id: "HI-012"
expert_rule: "Place all available opening Basic Pokémon on the Bench; only Articuno may be held back when it would obstruct the board plan."
strength: "MUST"
when:
  - "Opening Bench selection and early legal Basic plays"
priority_above:
  - "Holding Basics merely to preserve hand size"
priority_below:
  - "A matchup or board-space reason to exclude Articuno"
exceptions:
  - "Articuno's exact Bench conditions are defined in Round 9"
counterexample: "Keeping Murkrow or Porygon in hand instead of developing the board and improving Ariana's marginal draw."
hidden_information_policy: "Use visible Basic options and Bench capacity."
required_state: ["opening Basics", "Bench capacity", "matchup evidence"]
telemetry: ["Basics available", "Basics Benched", "held Articuno reason"]
golden_tests: ["Bench every Murkrow and Porygon", "conditionally hold Articuno"]
status: "RATIFIED"
```

### HI-013 — Proton maximizes Murkrow and thins the deck

```yaml
question_id: "HI-013"
expert_rule: "On the first turn, Proton should take three Murkrow when available; otherwise take the remaining Murkrow and fill unused selections with other useful Basic Pokémon, preferring Porygon."
strength: "MUST"
when:
  - "First-turn Proton resolution"
priority_above:
  - "Diversifying tactical roles"
priority_below:
  - "Known availability and matchup-critical Articuno requirements"
exceptions:
  - "With two Murkrow already in play, take the remaining searchable Murkrow and as many other useful Basics as legal"
counterexample: "Rejecting three Murkrow because they share the same role."
hidden_information_policy: "Use deck and Prize availability; never assume a prized Murkrow is searchable."
required_state: ["Basic Pokémon by zone", "searchable ranges", "current field"]
telemetry: ["Proton cards selected", "deck cards removed", "post-Proton Energy density estimate"]
golden_tests:
  - "Active Murkrow plus three searchable Murkrow selects all three"
  - "Two Murkrow plus Porygon when only two Murkrow remain"
  - "Existing two Murkrow takes all remaining useful Basics"
status: "RATIFIED"
```

The expert's purpose is both board development and deck compression: removing
three Pokémon from the deck increases the probability that later Ariana and
natural draws find otherwise unsearchable Energy.

### HI-014 — Honchkrow and prized Porygon2 do not change Proton legality

```yaml
question_id: "HI-014"
expert_rule: "Honchkrow in hand does not change what Proton can search because Proton searches only Basic Pokémon; if Porygon2 is prized, preserve the possibility of drawing it from the Prizes rather than pretending it is searchable."
strength: "MUST"
when:
  - "Proton target selection and Porygon planning"
priority_above:
  - "Treating Evolution cards as Proton targets"
priority_below: []
exceptions:
  - "Whether to Bench Porygon when Porygon2 is known prized remains a Prize-race decision for Rounds 9 and 10"
counterexample: "Changing Proton's Basic target count because Honchkrow is already in hand."
hidden_information_policy: "Use exact Prize evidence when available and probability otherwise."
required_state: ["Porygon2 Prize status", "Honchkrow in hand", "Basic search options"]
telemetry: ["known prized Porygon2", "Porygon developed while Porygon2 unavailable"]
golden_tests: ["Honchkrow in hand does not remove Murkrow search", "known prized Porygon2 is not treated as searchable"]
status: "RATIFIED"
```

### HI-015 — Articuno setup matchups

```yaml
question_id: "HI-015"
expert_rule: "Include Articuno in the setup plan against visible Dragapult, Drakloak, Dreepy, Alakazam, Kadabra, or Abra lines."
strength: "MUST"
when:
  - "The opponent publicly reveals one of the named evolution-line cards"
priority_above:
  - "Generic Articuno avoidance"
priority_below:
  - "Exact matchup board-space and sacrifice rules to be completed in Round 9"
exceptions: []
counterexample: "Refusing Articuno after an Abra-family card is publicly visible."
hidden_information_policy: "Activate only from public card evidence."
required_state: ["visible opponent card IDs"]
telemetry: ["Articuno matchup trigger", "trigger card ID", "Articuno setup result"]
golden_tests: ["Dragapult-family trigger", "Alakazam-family trigger", "no speculative Articuno without evidence"]
status: "RATIFIED"
```

### HI-016 — Proton only outranks Ariana on turn one

```yaml
question_id: "HI-016"
expert_rule: "Proton may outrank Ariana only on the first own turn; from the second own turn onward, prefer Ariana when choosing between them."
strength: "MUST"
when:
  - "Both Proton and Ariana are legal candidates"
priority_above:
  - "Late generic Proton setup"
priority_below:
  - "A first-turn Proton board-development line"
exceptions:
  - "Immediate no-Pokémon survival through Proton is captured separately in HI-017"
counterexample: "Playing Proton on turn two instead of Ariana merely because searchable Basics remain."
hidden_information_policy: "Use own-turn number and factual Supporters in hand."
required_state: ["own turn number", "Proton in hand", "Ariana in hand"]
telemetry: ["Proton over Ariana by turn", "late Proton exception reason"]
golden_tests: ["First-turn Proton over Ariana", "Second-turn Ariana over Proton"]
status: "RATIFIED"
```

### HI-017 — Transceiver targets by immediate need

```yaml
question_id: "HI-017"
expert_rule: "Use Transceiver for Proton when setup is incomplete or no-Pokémon survival requires it and Proton is not already in hand; otherwise use Ariana for a small Energy-poor hand or a ready Rocket Feathers attacker, and consider Giovanni when Porygon2 can take a two- or three-Prize KO."
strength: "MUST"
when:
  - "Transceiver target selection"
priority_above:
  - "A static Supporter target order"
priority_below:
  - "An immediate already-available winning Supporter line"
exceptions:
  - "If Proton is already in hand during incomplete setup, fetch Ariana"
  - "Archer and the fallback when Giovanni does not produce the high-value Porygon2 KO remain for Round 6"
counterexample: "Fetching Proton while it is already in hand, or fetching generic Ariana when Giovanni produces a three-Prize R Command target."
hidden_information_policy: "Use visible hand, searchable Basic availability, attacker readiness, opponent target Prize value, and projected damage."
required_state: ["Supporters in hand", "setup completeness", "Energy need", "Rocket Feathers readiness", "Porygon2 readiness", "Giovanni target values"]
telemetry: ["Transceiver target", "target reason", "high-Prize Giovanni opportunity", "no-Pokémon survival target"]
golden_tests:
  - "Incomplete setup without Proton fetches Proton"
  - "Incomplete setup with Proton fetches Ariana"
  - "Small Energy-poor hand fetches Ariana"
  - "Ready Honchkrow fetches Ariana"
  - "Porygon2 high-Prize Giovanni line fetches Giovanni"
  - "No-Pokémon risk fetches Proton when Basics remain"
status: "RATIFIED"
```

## Round 2 implementation deltas discovered

| ID | Expert rule | Current behavior | Required future slice |
|---|---|---|---|
| R2-D01 | Proton prefers repeated Murkrow and maximum legal Basic count | Duplicate-role filtering rejects repeated Murkrow combinations | Replace role uniqueness with deck-thinning and board-target scoring |
| R2-D02 | All opening Basics are Benched except conditional Articuno | Current setup filters emphasize opening priority but do not encode the complete all-Basics rule | Add opening multi-card selection with Articuno exception |
| R2-D03 | Ariana outranks Proton after turn one | Proton remains useful later when field count is below two | Separate ordinary late setup from explicit no-Pokémon survival |
| R2-D04 | Transceiver considers a high-Prize Giovanni/Porygon2 line | Current win/high-Prize target order starts Giovanni but does not prove the coupled R Command Prize line | Add coupled own attacker, opposing target, damage, and Prize validation |
| R2-D05 | Alakazam-family evidence requires Articuno setup | Runtime IDs include the family, but documentation still calls the Alakazam branch pending or separate | Reconcile the card-trigger rule with the still-undefined matchup plan |

## Round 3 — Turn objective and replanning

### HI-020 — Expert objective order

```yaml
question_id: "HI-020"
expert_rule: "Order turn objectives as: prevent immediate no-Pokémon loss, win the game now, maximize Prizes taken, maximize the chance of finding Energy, prepare an attacker, deal non-KO damage, preserve resources and end, then use Torment or Deceit control."
strength: "MUST"
when:
  - "At every full turn-plan evaluation"
priority_above: []
priority_below: []
exceptions:
  - "Whether an immediate game win logically supersedes no-Pokémon prevention requires clarification"
counterexample: "Choosing a low-value control attack while a board-development or Prize-taking line exists."
hidden_information_policy: "Evaluate only reachable actions and public Prize, board, hand, discard, and deck facts."
required_state: ["no-Pokémon loss risk", "winning attacks", "Prizes by target", "Energy access probability", "attacker readiness", "resource horizon"]
telemetry: ["objective before action", "objective after action", "objective precedence reason"]
golden_tests: ["survival priority", "win-now priority", "higher-Prize KO", "Energy-access priority", "control as last resort"]
status: "NEEDS_REPLAY"
```

### HI-021 — Replan after information-changing actions

```yaml
question_id: "HI-021"
expert_rule: "Recalculate the complete turn plan after Ariana, Factory, Roto-Stick, Ultra Ball, Transceiver, Miracle Headset, and every Prize draw."
strength: "MUST"
when:
  - "After each listed action resolves and a new observation is received"
priority_above:
  - "Continuing a stale turn objective or attacker commitment"
priority_below:
  - "A mandatory nested selection or already-paid attack cost that must resolve legally"
exceptions:
  - "Poké Pad and Proton replanning remain to be confirmed"
counterexample: "Continuing resource setup after Ariana reveals a winning attack."
hidden_information_policy: "Use the new public observation; never assume the searched or drawn result before resolution."
required_state: ["action just resolved", "new hand", "new deck count", "new zones", "legal options", "updated damage"]
telemetry: ["replan checkpoint", "old objective", "new objective", "plan-switch reason"]
golden_tests: ["Ariana creates KO", "Roto crosses KO threshold", "Headset changes Honchkrow/Porygon choice", "Prize draw changes next plan"]
status: "RATIFIED"
```

### HI-022 — Evaluate all Prize-taking lines before draw or search

```yaml
question_id: "HI-022"
expert_rule: "Before drawing or searching, enumerate immediate game wins, every current KO, two- or three-Prize targets, Giovanni-plus-KO lines, and ready R Command, then choose the reachable line that takes the most Prizes."
strength: "MUST"
when:
  - "Before every optional draw or search sequence"
priority_above:
  - "Generic resource improvement"
priority_below:
  - "Immediate survival if the expert survival-first precedence remains ratified"
exceptions:
  - "Tie-breakers between equal Prize lines remain for Round 7"
counterexample: "Using Ariana before noticing a ready three-Prize Giovanni R Command line."
hidden_information_policy: "Use visible targets and exact current damage; prospective draws are a separate branch."
required_state: ["all legal attacks", "all Giovanni targets", "target Prize values", "damage by attacker", "own Prizes remaining"]
telemetry: ["pre-draw Prize lines", "selected Prize line", "superior line declined reason"]
golden_tests: ["game win", "three-Prize over one-Prize KO", "Giovanni target", "ready R Command"]
status: "RATIFIED"
```

### HI-023 — Productive setup remains legal before a guaranteed KO

```yaml
question_id: "HI-023"
expert_rule: "Before executing a guaranteed KO, the agent may Bench Pokémon, evolve, attach non-Ignition Energy, use Ariana, Roto-Stick, Factory, Poké Pad, or strategically recover a next-turn Supporter with Miracle Headset."
strength: "MAY"
when:
  - "The current KO remains legal and guaranteed after the optional action"
priority_above:
  - "Attacking immediately when free setup improves the following Prize turn"
priority_below:
  - "Preserving the guaranteed KO and avoiding deck-out or resource loss"
exceptions:
  - "Ignition belongs on the Pokémon attacking this turn because it is discarded at end of turn"
  - "Miracle Headset requires a strategic next-turn target such as Ariana or Giovanni"
counterexample: "Attaching Ignition to a Bench Pokémon before a different attacker takes the KO."
hidden_information_policy: "Do not assume optional draws preserve the KO; recalculate after each action."
required_state: ["locked KO requirements", "post-action attack legality", "Energy type", "next-turn Supporter need", "deck reserve"]
telemetry: ["pre-KO setup action", "KO preserved", "KO lost after setup", "next-turn value"]
golden_tests: ["Bench before KO", "evolve before KO", "Rocket Energy before KO", "Ignition only on current attacker", "Headset for next-turn Giovanni"]
status: "NEEDS_REPLAY"
```

The expert allowed every listed action, but the exact condition under which an
optional draw is worth risking a currently guaranteed KO requires a boundary
question before implementation.

### HI-024 — Two-turn Prize horizon and deliberate over-discard

```yaml
question_id: "HI-024"
expert_rule: "When Honchkrow can take a KO and leave two or three Prizes, deliberately discard additional Team Rocket Supporters if doing so enables Porygon2 to take the remaining two- or three-Prize KO with R Command on the next turn."
strength: "MUST"
when:
  - "Honchkrow takes the current KO"
  - "The resulting Prize count can be closed by one high-value opposing KO"
  - "Porygon2 has a credible next-turn promotion, Energy, and survival path"
priority_above:
  - "Always discarding the minimum Supporters required for the current KO"
priority_below:
  - "A current immediate game win or a line with a higher verified win probability"
exceptions:
  - "Do not over-discard without a credible Porygon2 attack and target horizon"
counterexample: "Discarding only the minimum for a Honchkrow KO and leaving R Command 20 or 40 damage short of the final multi-Prize KO."
hidden_information_policy: "Use current discard, hand, remaining Prizes, visible opponent targets, Porygon2 availability, and Energy access."
required_state: ["supporters selected for discard", "post-attack discard damage", "next own Prizes", "next target Prize value", "Porygon2 readiness and survival"]
telemetry: ["minimum current-KO discard", "planned extra discard", "projected R Command damage", "two-turn terminal plan", "plan conversion"]
golden_tests:
  - "Over-discard one Supporter to enable final two-Prize R Command"
  - "Over-discard two Supporters to enable final three-Prize R Command"
  - "Reject over-discard without ready Porygon2 horizon"
status: "RATIFIED"
```

### HI-025 — No-KO action order

```yaml
question_id: "HI-025"
expert_rule: "When no KO exists, develop the Bench, maximize Ariana, prepare Team Rocket's Energy, deal partial damage, use Torment, use Deceit, then end the turn."
strength: "SHOULD"
when:
  - "No current legal KO or game-winning line exists"
priority_above: []
priority_below:
  - "Matchup and survival exceptions"
exceptions:
  - "Ignition is not a preparation attachment because it leaves play at end of turn; it requires a same-turn attack"
counterexample: "Attach Ignition as next-turn preparation and lose it at end of turn."
hidden_information_policy: "Use visible development, hand-refresh, attack, and control lines."
required_state: ["KO availability", "Bench development options", "Ariana marginal draw", "Energy type", "partial damage horizon", "Torment lock value", "Deceit survival need"]
telemetry: ["no-KO phase chosen", "partial-damage horizon", "control reason", "end reason"]
golden_tests: ["Bench before Ariana", "Rocket Energy preparation", "partial damage before generic control", "Deceit before END only as survival"]
status: "RATIFIED"
```

### HI-026 — Resource and survival awareness

The expert ranked taking a smaller KO now above preparing a larger KO next
turn, then preserving Energy and protecting Porygon, while requiring continuous
deck-out awareness. Exact exceptions and thresholds remain for Rounds 4, 7,
and 10 rather than being converted into a premature universal rule.

## Round 3 implementation deltas discovered

| ID | Expert rule | Current behavior | Required future slice |
|---|---|---|---|
| R3-D01 | Replan after every information-changing action | The turn objective is selected once and persisted for the whole turn | Introduce explicit replanning checkpoints and commitment exceptions |
| R3-D02 | Enumerate every Prize-taking line before optional draw/search | Current MAIN ordering recognizes selected lethal lines but does not build one complete cross-attacker Prize plan | Add a Prize-horizon evaluator before resource actions |
| R3-D03 | Productive development may occur before a guaranteed KO | Current lethal attack ordering normally attacks before the allowed setup actions | Add a locked-KO invariant and safe pre-KO action set |
| R3-D04 | Honchkrow may over-discard to enable next-turn terminal R Command | Current commitment minimizes Supporter discard, including exact-count logic | Optimize discard across a two-turn Prize horizon |
| R3-D05 | Only Team Rocket's Energy is a preparation attachment | Generic typed scoring can value attachments without encoding the expert's current-turn Ignition invariant in every branch | Centralize permanent versus expiring Energy plans |

## Round 3 clarifications

### HI-020-R1 — Immediate game win is absolute

```yaml
question_id: "HI-020-R1"
expert_rule: "When a legal action wins the game immediately, execute it as fast as possible before survival, setup, draw, or resource actions."
strength: "MUST"
when:
  - "A legal current action takes the remaining Prizes or otherwise wins"
priority_above:
  - "Every other objective"
priority_below: []
exceptions: []
counterexample: "Benching a Pokémon to prevent a hypothetical next-turn loss instead of taking the final Prizes now."
hidden_information_policy: "Require a factual legal win, not a projected draw."
required_state: ["legal action", "current damage", "remaining Prizes", "target Prize value"]
telemetry: ["win-now opportunity", "win-now conversion", "actions taken before win"]
golden_tests: ["Immediate win bypasses all setup"]
status: "RATIFIED"
```

The final objective order therefore begins with immediate game win, followed
by preventing immediate no-Pokémon loss when no win exists. The remaining
Round 3 order is unchanged.

### HI-021-R1 — Replanning checkpoint taxonomy

```yaml
question_id: "HI-021-R1"
expert_rule: "Replan after actions that reveal new information or enable an attacker: Ariana, Factory, Roto-Stick, Ultra Ball, Transceiver, Miracle Headset, Prize draws, Evolution, and Energy attachment. Do not replan merely after Proton, Poké Pad, or placing a Pokémon on the Bench."
strength: "MUST"
when:
  - "A listed action resolves"
priority_above:
  - "Persisting a stale objective"
priority_below:
  - "Mandatory nested resolution"
exceptions:
  - "If CABT reveals unexpected information during Proton or Poké Pad, the implementation must record the simulator divergence before adding a checkpoint"
counterexample: "Failing to notice that Evolution or Energy attachment enabled a KO."
hidden_information_policy: "Proton, Poké Pad, and Bench placement are deterministic components of the existing plan; random or newly revealed results trigger replanning."
required_state: ["last resolved action", "new observation", "attacker readiness", "updated damage"]
telemetry: ["checkpoint type", "objective before", "objective after", "new KO enabled"]
golden_tests:
  - "Evolution triggers replan"
  - "Energy attachment triggers replan"
  - "Proton resolution preserves plan"
  - "Poké Pad resolution preserves plan"
  - "Bench placement preserves plan"
status: "RATIFIED"
```

### HI-023-R1 — Actions before a nonterminal guaranteed KO

```yaml
question_id: "HI-023-R1"
expert_rule: "When a guaranteed KO does not end the game, Ariana and Factory may still be used as bonus progression, while Roto-Stick should be preserved for a later larger KO."
strength: "SHOULD"
when:
  - "The current hand already supports the nonterminal KO"
priority_above:
  - "Attacking immediately without useful Ariana or Factory progression"
priority_below:
  - "An immediate game win, which attacks immediately"
exceptions:
  - "Recalculate after Ariana or Factory resolves; do not assume the old hand remains unchanged"
counterexample: "Spend Roto-Stick for surplus current damage instead of preserving it for the larger following KO."
hidden_information_policy: "Treat Ariana and Factory results as new observations and replan."
required_state: ["current KO line", "Ariana value", "Factory legality", "Roto future value", "remaining Prize horizon"]
telemetry: ["pre-KO Ariana", "pre-KO Factory", "Roto preserved reason", "KO retained after replan"]
golden_tests: ["Ariana before nonterminal KO", "Factory before nonterminal KO", "preserve Roto", "immediate game win skips all setup"]
status: "RATIFIED"
```

### HI-024-R1 — High-confidence Honchkrow-to-Porygon commitment

```yaml
question_id: "HI-024-R1"
expert_rule: "Commit extra Honchkrow discard to a next-turn terminal R Command only with high certainty: the game is expected to end next turn, the Porygon2 line is guaranteed and protected, and Ignition is already in hand for the attack turn."
strength: "MUST"
when:
  - "Planning deliberate Supporter over-discard on Rocket Feathers"
priority_above:
  - "Minimum-only discard when the terminal line is reliable"
priority_below:
  - "Preserving resources when Porygon can be removed or the attack is uncertain"
exceptions:
  - "Porygon2 need not have been on the Bench before the earlier Honchkrow attack, but its development and evolution path must become guaranteed before resources are committed"
  - "Attach Ignition only on the turn R Command is used"
counterexample: "Over-discarding while the opponent can Knock Out the exposed Porygon before the next attack."
hidden_information_policy: "High certainty requires public availability, legal development, Ignition in hand, a protected attacker, a visible terminal target, and sufficient projected discard damage."
required_state: ["Porygon and Porygon2 availability", "legal evolution timing", "Ignition in hand", "opponent removal threat", "next target Prizes and HP", "projected R Command damage"]
telemetry: ["terminal commitment confidence", "Porygon protection proof", "Ignition proof", "extra Supporters discarded", "next-turn conversion"]
golden_tests:
  - "Commit with guaranteed protected Porygon and Ignition"
  - "Reject when Porygon is vulnerable"
  - "Reject without Ignition in hand"
  - "Attach Ignition only on attack turn"
status: "RATIFIED"
```

The exact definition of a guaranteed and protected Porygon is deferred to the
promotion and switching matrix in Round 8.

## Rounds 1–3 experimental implementation checkpoint

The `expert_rounds_1_3_v1` candidate implements the following bounded changes:

- recognize an arithmetic last-Prize KO as an immediate win even when the SDK
  option does not carry an explicit `win` annotation;
- prefer Murkrow, then Porygon, then Articuno as the opening Active;
- make Proton maximize Murkrow count before total Basic count and Porygon;
- let first-turn Poké Pad take Honchkrow for a Murkrow that evolves next turn;
- add first-turn Roto setup/survival mode when neither Proton nor Ariana is in
  hand, taking at most one Proton, all revealed Ariana, and Petrel only as the
  ratified no-Supporter fallback;
- preserve Roto when the existing hand already guarantees the current KO;
- recompute the turn objective after Ariana, Factory, Roto-Stick, Ultra Ball,
  Transceiver, Miracle Headset, a Prize selection, Evolution, or Energy
  attachment, while preserving it after Proton, Poké Pad, and Bench placement;
- allow Deceit as a conservative Ariana survival line only with no Supporter
  and at most two cards in hand; the numerical low-hand boundary is an
  experimental interpretation and remains subject to Round 7 ratification;
- permit the Torment control bonus only when the opponent has one Pokémon, its
  catalog entry has one attack, and the legal option confirms that attack is
  disabled;
- allow Ariana and Factory progression before a nonterminal guaranteed KO,
  while terminal KOs remain immediate.

The candidate deliberately does not implement the high-confidence
Honchkrow-to-Porygon over-discard commitment because "guaranteed and protected"
does not yet have an executable threshold. It also does not change any typed-
Energy allocation rule before Round 4.

### First 300-match CABT result

The clean bilateral evaluation completed 300/300 matches with zero execution
failures. Against the promoted 300-match independent baseline, the candidate
improved from 249W/51L (83.0%) to 264W/36L (88.0%), a nominal gain of 5.0
percentage points. The independent 95% difference interval is -0.62 to +10.62
points and the two-sided two-proportion p-value is 0.082, so the sample is
promising but not statistically conclusive.

Operational signals moved in the intended direction: deck-out losses declined
from 12 to 9, unresolved terminal snapshots from 50 to 39, median terminal turn
from 12.5 to 9, and median decisions per match from 41 to 35. The candidate
recorded 24 immediate arithmetic game-win selections and 60 opening Roto
setup/survival selections. The Deceit survival branch did not activate and is
therefore fixture-tested but not CABT-observed.

The comparison is independent rather than paired because CABT 1.32.2 does not
forward the configured seed into `battle_start`. The candidate remains
experimental; the detailed evidence is in
`reports/honchkrow_porygon_expert_rounds_1_3_comparison_20260807.json`.
