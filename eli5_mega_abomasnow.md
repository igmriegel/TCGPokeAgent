# Turn Algorithm, ELI5

This is the short version of how the agent plays one `MAIN` turn.

## Big Idea

The agent does not compare all actions in one pile. It walks through a fixed
order of phases and always takes the first legal action in the earliest useful
phase.

## Turn Flow

1. If the game forces a nested choice, solve that first.
2. If there is an immediate winning action, take it.
3. In `MAIN`, check phases in order:
   - evolve
   - attach Energy that matters most, except when opening Articuno should stay sacrificial
   - play Pokemon for board development
   - play Items
   - play Supporters
   - attack
   - end only if nothing better is left
4. Inside a phase, use scoring only to pick the best target or best option.
5. If an attack is chosen, the turn ends right there.

## Simple Rules

- Evolution comes before Energy when both are legal.
- If Team Rocket's Articuno starts Active, keep it sacrificial and attach Energy
  to the rest of the board instead.
- Useful board setup comes before generic pass-like actions.
- Items come before Supporters.
- A terminal attack ends the turn.
- If a phase has no legal action, the agent skips it and checks the next one.

## One Sentence Summary

The agent tries to set up the board first, attack last, and never keeps acting
after attacking.

## Flowchart

```mermaid
flowchart TD
    A[Receive observation] --> B{select is None?}
    B -- Yes --> C[Initialize deck and stop]
    B -- No --> D[Parse observation]

    D --> E{Forced or nested choice?}
    E -- Yes --> F[Resolve the required selection legally]
    E -- No --> G{maxCount == 0 or no legal selections?}

    G -- Yes --> H[Return deterministic empty fallback]
    G -- No --> I[Generate legal selections]

    I --> J[Filter dangerous shuffle-supporter options]
    J --> K{select_context == MAIN?}

    K -- Yes --> L[Apply MAIN phase order]
    K -- No --> M[Use context-specific fallback / ranking]

    L --> N{Immediate win available?}
    N -- Yes --> O[Take the winning action]
    N -- No --> P{Earliest useful MAIN phase}

    P --> P1[Evolve]
    P1 --> P1A{Opening Articuno Active?}
    P1A -- Yes --> P1B[Skip Energy on opening Articuno and attach elsewhere]
    P1A -- No --> P2[Attach Energy]
    P1B --> P2
    P2 --> P3[Play Pokemon]
    P3 --> P4[Play Items]
    P4 --> P5[Play Supporters]
    P5 --> P6[Attack]
    P6 --> P7[End only if nothing better remains]

    M --> Q[Rank the remaining legal selections]
    O --> Q
    P7 --> Q
    F --> Q

    Q --> R[Return the chosen option indices]
    R --> S[Simulator applies the action]
    S --> T{New observation available?}
    T -- Yes --> D
    T -- No --> U[Turn or match ends in engine]

    subgraph Notes
        N1[Forced / nested choices are resolved on the current prompt only]
        N2[Choosing EVOLVE, ATTACH, PLAY, ATTACK, or END does not itself end the turn]
        N3[The next MAIN prompt is re-evaluated from the new observation]
    end
```

## Execution diagram

```mermaid
flowchart TD
    A[Start: receive observation] --> B{select is None?}
    B -- Yes --> C[Initialize deck and wait for the next prompt]
    B -- No --> D[Parse observation into state, context, and legal options]

    D --> E{Forced or nested choice?}
    E -- Yes --> F[Resolve the required selection first]
    E -- No --> G{Any legal selection available?}

    G -- No --> H[Return deterministic fallback for this SelectContext]
    G -- Yes --> I[Generate legal selections]

    I --> J[Filter dangerous shuffle-supporter options]
    J --> K{Select context}

    K -- MAIN --> L[Run MAIN phase order]
    K -- Other --> M[Use context-specific fallback or ranking]

    L --> N{Immediate win available?}
    N -- Yes --> O[Take the winning action]
    N -- No --> P[Walk MAIN phases in order]

    P --> P1{Can evolve now?}
    P1 -- Yes --> P1A[Choose evolve actions first]
    P1 -- No --> P2{Can attach meaningful Energy now?}
    P2 -- Yes --> P2A[Attach Energy that matters most]
    P2 -- No --> P3{Is opening Articuno Active?}
    P3 -- Yes --> P3A[Keep Articuno sacrificial and attach elsewhere]
    P3 -- No --> P4{Can play Pokemon for board development?}
    P4 -- Yes --> P4A[Prefer setup Pokemon that improve the board]
    P4 -- No --> P5{Can play Items that help setup?}
    P5 -- Yes --> P5A[Use Items before Supporters]
    P5 -- No --> P6{Can play Supporters that improve the line?}
    P6 -- Yes --> P6A[Use Supporters after Items]
    P6 -- No --> P7{Can attack now?}
    P7 -- Yes --> P7A[Attack and end the turn]
    P7 -- No --> P8[End only if nothing better remains]

    P1A --> Q[Score the available options inside the phase]
    P2A --> Q
    P3A --> Q
    P4A --> Q
    P5A --> Q
    P6A --> Q
    P7A --> Q
    P8 --> Q
    M --> Q
    O --> Q
    F --> Q

    Q --> R{Does the selection preserve the fixed phase order?}
    R -- Yes --> S[Keep the option that best advances the current phase]
    R -- No --> T[Reject actions that break the phase order]

    S --> U[Return the chosen option indices]
    T --> U
```
