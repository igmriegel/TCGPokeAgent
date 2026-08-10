# Mega Lucario ELI5

This is the simple version of the Mega Lucario ex notebook agent, based on
the code in the kernel.

## What the agent is trying to do

This agent is much simpler than Honchkrow.

It does not keep a deep turn ledger or a long plan. Instead, it looks at the
current board, gives every legal choice a score, and picks the best scored
options.

The basic question is:

1. Which move helps the board most right now?
2. Which move helps Mega Lucario ex attack soonest?
3. Which move makes the current attack better?

## What it looks at first

The code reads:

- the active and benched Pokémon on both sides;
- cards in hand and discard;
- attached energy counts;
- whether it can switch, retreat, evolve, attach, or attack;
- how many Prizes are left;
- whether a Supporter has already been played this turn.

## What it prefers

The agent gives higher scores to actions that help Mega Lucario ex do work.

It likes:

- evolving Riolu into Mega Lucario ex;
- building Hariyama or Makuhita when that attacker is the better line;
- using Solrock when it is the lighter attacker that fits the board;
- attaching Fighting Energy to the Pokémon that is closest to attacking;
- playing search or draw cards when they improve the hand;
- using Switch when it unlocks the planned attacker;
- playing Boss's Orders, Carmine, Lillie's Determination, or Premium Power
  Pro when they look useful in the current state.

## How it chooses an attack

The code does not hardcode one move.

It tries to predict the best current attack for each possible attacker:

- Mega Lucario ex can attack for either a smaller or larger hit;
- Hariyama can attack as the bulkier backup;
- Makuhita can be evolved into that line if needed;
- Solrock becomes relevant when Lunatone is already in play.

Then it scores the board state after each possible attack:

- more damage is better;
- taking a Knock Out is much better;
- taking more Prize value is better;
- attacking the active Pokémon is usually better than hitting a Bench target
  unless the target switch line is better.

## What it avoids

The code tries to avoid wasting cards on dead lines.

It usually rejects:

- duplicate setup Pokémon when the line is already filled;
- a search target that does not improve the board;
- extra Energy on a Pokémon that is already above its useful attack cost;
- switching for no reason;
- retreating when it does not help the attack line;
- playing support cards that do not improve the immediate score.

## In very simple words

The agent is basically a judge with a score sheet.

It looks at every legal move, asks "how useful is this for Mega Lucario right
now?", gives it a number, and then picks the best number.

So the pattern is:

- score the legal options;
- prefer the move that builds or enables the best attacker;
- attack with the line that looks strongest on the current board.

## Execution diagram

```mermaid
flowchart TD
    A[Start: receive Observation] --> B[Read board state, hand, discard, energy, prizes, and supporter history]
    B --> C[Generate every legal selection]
    C --> D{Any legal selection?}

    D -- No --> Z[Fallback selection for the current SelectContext]
    D -- Yes --> E[Score each legal selection]

    E --> F{Selection type}

    F -- Setup / evolve --> G{Does this improve the main attacker line?}
    G -- Yes --> G1[Prefer Riolu to Mega Lucario ex]
    G -- Yes --> G2[Prefer Makuhita or Hariyama when that line is stronger]
    G -- Yes --> G3[Prefer Solrock when Lunatone already makes it relevant]
    G -- No --> G4[Reject duplicate or dead setup]

    F -- Attach energy --> H{Does this help the nearest useful attack?}
    H -- Yes --> H1[Attach to the Pokémon closest to attacking]
    H -- Yes --> H2[Increase score more if it enables a real attack this turn]
    H -- No --> H3[Lower score for over-attaching or wasting energy]

    F -- Supporter / search / draw --> I{Does it improve the immediate board?}
    I -- Yes --> I1[Reward search or draw that opens the attack line]
    I -- Yes --> I2[Reward Boss's Orders, Carmine, Lillie's Determination, or Premium Power Pro when useful]
    I -- No --> I3[Reject support cards that do not change the current turn]

    F -- Switch / retreat --> J{Does it unlock the planned attacker?}
    J -- Yes --> J1[Reward the move that enables the best attack]
    J -- No --> J2[Reject movement with no purpose]

    F -- Attack --> K[Evaluate every possible attacker]
    K --> K1[Mega Lucario ex: smaller hit or larger hit]
    K --> K2[Hariyama: backup bulky attack]
    K --> K3[Makuhita line: if that evolution path is the best line]
    K --> K4[Solrock: if Lunatone is already in play]
    K1 --> L[Score resulting damage, Knock Out value, and Prize value]
    K2 --> L
    K3 --> L
    K4 --> L

    L --> M{Does the attack take a Knock Out?}
    M -- Yes --> M1[Boost score strongly]
    M -- No --> N{Does it still improve the board?}
    N -- Yes --> N1[Keep only if the damage or setup value is still meaningful]
    N -- No --> N2[Lower score for low-impact attacks]

    E --> O{Selection wastes resources or blocks future lines?}
    O -- Yes --> P[Lower score for dead setup, unnecessary retreat, or over-commitment]
    O -- No --> Q[Keep score if the move advances the strongest line]

    G1 --> R[Pick the highest-scoring selection]
    G2 --> R
    G3 --> R
    G4 --> R
    H1 --> R
    H2 --> R
    H3 --> R
    I1 --> R
    I2 --> R
    I3 --> R
    J1 --> R
    J2 --> R
    M1 --> R
    N1 --> R
    N2 --> R
    P --> R
    Q --> R

    R --> S[Return the option indices for the best selection]
    Z --> S
```
