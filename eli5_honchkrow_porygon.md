# Honchkrow/Porygon ELI5

This is the simple version of the Honchkrow/Porygon plan, written from the
code itself.

## What the agent is trying to do

The agent is trying to play like it has a checklist for each turn.

It does not just ask, "What is the strongest card right now?" It asks:

1. What phase am I in?
2. What line am I building?
3. What resources do I need to finish the line?
4. Can I reach a real Knock Out this turn?

The code keeps a turn ledger and a match ledger, so it can remember what it is
trying to finish instead of making each choice in isolation.

## What it looks at first

The agent reads the public board and checks:

- which Pokémon are active and on the Bench;
- how many Team Rocket Supporters are visible in hand, discard, and Prize;
- whether Honchkrow, Murkrow, Porygon, or Porygon2 are already in play;
- whether Ignition Energy, Factory, Ariana, Petrel, Transceiver, Roto-Stick,
  or Miracle Headset can actually help this turn;
- whether the opponent has a visible Mega Abomasnow ex or other matchup
  evidence that changes the line.

## What it prefers

The main idea is:

1. Build the attacker line.
2. Secure the Supporters needed for the Knock Out.
3. Only then spend extra resources.

The code prefers:

- Murkrow and Porygon setup before random side plays;
- Proton early when it keeps the line moving;
- Transceiver when it can still fetch a useful Supporter;
- Factory only when there is a real draw conversion after Supporter play;
- Petrel only when it leads to a better same-turn result;
- Roto-Stick only when revealed cards can close a Supporter gap;
- Miracle Headset only when it restores exactly the missing Supporters for a
  real KO line;
- switching or retreating only when it immediately improves the current line;
- Ignition Energy only when it completes an actual attack this turn.

## What it avoids

The agent blocks actions that look active but do not help the plan.

It avoids:

- spending the last useful Supporter too early;
- using Factory before there is a legal draw conversion;
- promoting a Pokémon that cannot attack usefully;
- retreating just to move pieces around;
- using Hacking;
- using Deceit unless the attack damage or interruption is actually decisive;
- attaching Ignition Energy if it does not lead to an attack;
- sending Articuno into the plan unless the matchup really asks for it.

## Special case: Mega Abomasnow ex

Against Mega Abomasnow ex, the code gets stricter.

It treats partial damage as not good enough. The attack or retreat has to
produce a real Knock Out path now, not just "maybe next turn."

That is why the code:

- requires enough Supporters before Rocket Feathers;
- requires a much larger Supporter count before R Command against Mega
  Abomasnow ex;
- checks exact discard counts when that is the committed KO line;
- refuses attacks that look close but do not actually finish the job;
- allows retreat only if the replacement attacker can immediately convert.

## In very simple words

The agent is a planner, not a button-masher.

It tries to:

- set up the right attacker;
- keep enough resources for the finish;
- spend search and draw cards only when they move the plan forward;
- and attack only when the attack is part of a real KO line.

So the whole idea is: "build the line, protect the resources, then cash it in."

## Execution diagram

```mermaid
flowchart TD
    A[Start: receive Observation] --> B[Read board, hand, discard, prizes, and visible matchup clues]
    B --> C[Update turn ledger and match ledger]
    C --> D[Identify the current phase and the line being built]
    D --> E[Check which resources are already available]
    E --> F[Generate every legal selection]
    F --> G{Any legal selection?}

    G -- No --> Z[Fallback selection for the current SelectContext]
    G -- Yes --> H[Score each legal selection against the plan]

    H --> I{What kind of action is this?}

    I -- Setup / evolve --> J{Does it advance the planned attacker line?}
    J -- Yes --> J1[Prefer Murkrow and Porygon setup first]
    J -- Yes --> J2[Prefer the line that gets to Honchkrow or Porygon2 efficiently]
    J -- No --> J3[Reject side plays that do not finish the line]

    I -- Supporter / search / draw --> K{Does it secure the needed KO resources?}
    K -- Yes --> K1[Reward Proton when it keeps the line moving]
    K -- Yes --> K2[Reward Transceiver when it still fetches a useful Supporter]
    K -- Yes --> K3[Reward Factory only after a legal draw conversion exists]
    K -- Yes --> K4[Reward Petrel only when it improves the same turn]
    K -- Yes --> K5[Reward Roto-Stick and Miracle Headset only when they close the exact Supporter gap]
    K -- No --> K6[Lower score for Supporters that spend resources too early]

    I -- Switch / retreat --> L{Does the move immediately improve the line?}
    L -- Yes --> L1[Allow it only if the active attacker becomes better]
    L -- No --> L2[Reject movement that only rearranges the board]

    I -- Energy attach --> M{Does Ignition Energy complete a real attack this turn?}
    M -- Yes --> M1[Reward the attach because it converts into an attack]
    M -- No --> M2[Reject Ignition Energy if it does not lead to a same-turn attack]

    I -- Attack --> N[Check whether the attack is a real KO line]
    N --> N0{Does the line depend on counted Transceiver or Miracle Headset?}
    N0 -- Yes --> N01[Force the resource play first]
    N0 -- No --> N1{Is Mega Abomasnow ex the matchup?}
    N01 --> N1
    N1 -- Yes --> O[Require stricter exact KO conditions]
    N1 -- No --> P[Use the normal KO line evaluation]
    O --> O1{Do the Supporter counts meet the exact threshold?}
    O1 -- Yes --> O2[Allow Rocket Feathers or R Command only if the KO is real now]
    O1 -- No --> O3[Reject partial damage lines]
    P --> P1{Does the attack take a real Knock Out?}
    P1 -- Yes --> P2[Boost the selection strongly]
    P1 -- No --> P3{Does it still advance the committed plan?}
    P3 -- Yes --> P4[Keep only if the damage or disruption matters]
    P3 -- No --> P5[Lower score for speculative attacks]

    I -- Other / risky option --> Q{Does it spend resources without improving the plan?}
    Q -- Yes --> Q1[Lower score for Hacking, Deceit, or early overuse of resources]
    Q -- No --> Q2[Keep if it still fits the current phase]

    H --> R{Does the choice preserve the turn plan?}
    R -- Yes --> S[Keep selections that maintain the build-then-cash-in sequence]
    R -- No --> T[Penalize actions that break the ledger or spend the finish too early]

    J1 --> U[Pick the highest-scoring selection]
    J2 --> U
    J3 --> U
    K1 --> U
    K2 --> U
    K3 --> U
    K4 --> U
    K5 --> U
    K6 --> U
    L1 --> U
    L2 --> U
    M1 --> U
    M2 --> U
    N01 --> U
    O2 --> U
    O3 --> U
    P2 --> U
    P4 --> U
    P5 --> U
    Q1 --> U
    Q2 --> U
    S --> U
    T --> U

    U --> V[Return the option indices for the best selection]
    Z --> V
```
