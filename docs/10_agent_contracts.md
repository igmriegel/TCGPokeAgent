# Agent contracts

## `AgentPolicy`

All agents expose only:

```python
select(observation: Observation) -> list[int]
```

The result is validated before leaving the wrapper. Configuration, historical state, and logs are internal dependencies; they do not change the contract.

## `FallbackPolicy`

Deterministic and total policy:

1. generates all valid `Selection`;
2. dispatches by the `SelectContext`/`SelectType` pair;
3. uses a specialized rule when one exists;
4. otherwise chooses by safety and lexicographic index;
5. returns `[]` only when `minCount == 0` and the rule considers not selecting safe; if a choice is mandatory, returns the valid combination of smallest indices.

The fallback covers setup, first player, mulligan, active/bench, targets, discard, energy, attacks, counts, special conditions, and `YES_NO`.

## `HeuristicPolicy`

Sorts selections by explicable sum:

1. immediate win;
2. efficient attack;
3. useful evolution;
4. energy that enables an attack;
5. bench development;
6. draw and search;
7. resource preservation;
8. end of turn.

Penalizes wasted energy, key piece discard, evolution without benefit, blocked bench, and premature end. Each component emits an auditable reason. Tie: `Selection.indices`.

## `SearchPolicy`

Decorates the heuristic; does not replace it. Only opens when:

- `SelectType.MAIN`;
- more than one valid selection;
- at least two relevant candidates;
- `remainingOverageTime >= 30`;
- consistent belief and `search_begin_input` available.

Re-evaluates at most top 3, depth of up to 4 selections, and 100 ms total. Any error immediately returns heuristic top-1.

## `main.py`

Thin wrapper:

- initial branch returns the deck;
- remaining branches delegate to a persistent policy instance;
- resolves imports in the submission directory;
- never contains duplicate heuristics;
- on exception, logs error and returns already validated fallback.

The package can disable search by configuration without changing the policy or wrapper.
