# Dragapult ELI5

This is the simple version of the Dragapult ex notebook agent, based on the
code in the kernel.

## What the agent is trying to do

This agent tries to keep a fast, aggressive tempo.

It does not think in terms of a long hidden plan. Instead, it reads the board,
checks what can be done now, scores every legal choice, and prefers the option
that moves the Dragapult line forward without wasting resources.

The basic question is:

1. Can I build the Dragapult line now?
2. Can I attack soon, or even this turn?
3. Can I use my support cards to keep the pressure going?

## What it looks at first

The code reads:

- the active and benched Pokemon on both sides;
- cards in hand, discard, stadium, and prize-relevant counts;
- how many Dreepy, Drakloak, and Dragapult ex are already in play;
- whether a Bench attacker is ready;
- whether there is enough energy for Phantom Dive;
- whether the previous turn created a real KO or item lock situation;
- how many prizes remain on each side.

## What it prefers

The agent gives higher scores to actions that keep the engine moving.

It likes:

- playing Dreepy early;
- evolving into Drakloak and then Dragapult ex;
- playing Rare Candy when it becomes a real Dragapult ex line;
- using Buddy-Buddy Poffin when it finds missing setup Pokemon;
- using Crispin when it creates a strong same-turn or next-turn line;
- using Brock Scouting or Lillie Determination when they restore useful tempo;
- attaching Fire or Psychic Energy to the Pokemon that actually matters;
- using Team Rocket Watchtower when stadium pressure matters;
- using Fezandipiti ex, Latias ex, or Meowth ex only when they help the
  current line instead of sitting there for no reason.

## How it chooses an attack

The code does not blindly attack.

It first checks whether Phantom Dive is legal, whether a Bench attacker can be
promoted, and whether the target board can actually be punished.

Then it scores possible attack lines by asking:

- does the active target give real Prize value?
- can the attack also set up bench damage counters?
- does the attack finish a knockout now?
- does the line preserve future pressure?

The agent prefers:

- Phantom Dive when it is the real main attack;
- a Bench attacker when the active attacker is not ready;
- a line that takes prizes now over a line that only looks good later;
- spreading damage when it creates a better multi-KO turn.

## What it avoids

The code tries to avoid slow or wasted turns.

It usually rejects:

- extra setup Pokemon when the line is already full;
- a Rare Candy line that does not improve the board;
- playing draw or search cards when the deck is already too thin;
- retreating when there is no better attacker to promote;
- over-attaching Energy to a Pokemon that cannot convert it;
- attacking if the attack does not really improve the prize race;
- keeping dragapult pieces in hand when they should already be on board.

## In very simple words

The agent is basically a tempo judge.

It looks at every legal move, asks "does this help me get to Dragapult ex and
real prizes faster?", gives it a score, and then picks the best score.

So the pattern is:

- set up the Dreepy/Drakloak/Dragapult line;
- use support cards only when they keep that line moving;
- attack when the attack actually matters.

## Execution diagram

```mermaid
flowchart TD
    A[Start: receive Observation] --> B[Read board state, hand, discard, logs, prizes, and stadium]
    B --> C[Update turn logs and track previous-turn effects]
    C --> D[Count Dreepy, Drakloak, Dragapult ex, and available energy]
    D --> E[Generate every legal selection]
    E --> F{Any legal selection?}

    F -- No --> Z[Fallback selection for the current SelectContext]
    F -- Yes --> G[Score each legal selection]

    G --> H{Selection type}

    H -- Setup / evolve --> I{Does this improve the Dragapult line?}
    I -- Yes --> I1[Prefer Dreepy, then Drakloak, then Dragapult ex]
    I -- Yes --> I2[Prefer Rare Candy when it enables a real Dragapult ex]
    I -- Yes --> I3[Prefer setup cards that restore tempo]
    I -- No --> I4[Reject duplicate or dead setup]

    H -- Attach energy --> J{Does this help the main attack plan?}
    J -- Yes --> J1[Attach Fire or Psychic Energy to the useful attacker]
    J -- Yes --> J2[Reward attachment more when it can convert into attack]
    J -- No --> J3[Lower score for wasted or blocked energy]

    H -- Supporter / search / draw --> K{Does it keep the line moving?}
    K -- Yes --> K1[Reward Crispin, Brock Scouting, or Lillie Determination]
    K -- Yes --> K2[Reward Buddy-Buddy Poffin, Ultra Ball, or Poke Pad when they find pieces]
    K -- Yes --> K3[Reward Watchtower when stadium pressure matters]
    K -- No --> K4[Reject support cards that do not help the turn]

    H -- Pokemon play --> L{Does the Pokemon improve the board now?}
    L -- Yes --> L1[Prefer Dreepy, Fezandipiti ex, Latias ex, or Budew only when useful]
    L -- No --> L2[Reject side plays that do not improve setup]

    H -- Switch / retreat --> M{Does it unlock a better attacker?}
    M -- Yes --> M1[Promote the attacker that can convert pressure into prizes]
    M -- No --> M2[Reject movement with no payoff]

    H -- Attack --> N{Is Phantom Dive or another real attack line available?}
    N -- Yes --> N1[Score active prizes, bench damage, and knockout value]
    N -- No --> N2[Prefer setup or other legal actions instead]
    N1 --> N3{Does the attack take a real prize or create a real follow-up?}
    N3 -- Yes --> N4[Boost the score strongly]
    N3 -- No --> N5[Lower score for speculative attacks]

    G --> O{Does the choice waste resources or break tempo?}
    O -- Yes --> P[Lower score for dead lines, overdraw, or overcommitment]
    O -- No --> Q[Keep the selection that best advances the plan]

    I1 --> R[Pick the highest-scoring selection]
    I2 --> R
    I3 --> R
    I4 --> R
    J1 --> R
    J2 --> R
    J3 --> R
    K1 --> R
    K2 --> R
    K3 --> R
    K4 --> R
    L1 --> R
    L2 --> R
    M1 --> R
    M2 --> R
    N2 --> R
    N4 --> R
    N5 --> R
    P --> R
    Q --> R

    R --> S[Return the option indices for the best selection]
    Z --> S
```
