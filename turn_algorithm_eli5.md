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
   - attach Energy that matters most
   - play Pokemon for board development
   - play Items
   - play Supporters
   - attack
   - end only if nothing better is left
4. Inside a phase, use scoring only to pick the best target or best option.
5. If an attack is chosen, the turn ends right there.

## Simple Rules

- Evolution comes before Energy when both are legal.
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
    A[Start MAIN turn] --> B{Forced or nested choice?}
    B -- Yes --> C[Resolve the forced choice]
    B -- No --> D{Immediate win available?}
    C --> D
    D -- Yes --> E[Take the winning action]
    D -- No --> F{Evolve legal?}
    F -- Yes --> G[Choose best Evolution]
    F -- No --> H{Priority Energy attach legal?}
    G --> Z[Turn ends after action]
    H -- Yes --> I[Choose best critical Energy attach]
    H -- No --> J{Play Pokemon for board setup?}
    I --> Z
    J -- Yes --> K[Choose the best board-development Pokemon]
    J -- No --> L{Play Item?}
    K --> Z
    L -- Yes --> M[Choose the best Item]
    L -- No --> N{Play Supporter?}
    M --> Z
    N -- Yes --> O[Choose the best Supporter]
    N -- No --> P{Attack legal?}
    O --> Z
    P -- Yes --> Q[Attack]
    P -- No --> R[End]
    Q --> Z
    R --> Z
```
