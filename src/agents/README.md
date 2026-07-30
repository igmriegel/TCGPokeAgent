# Agents

`BaselineAgent` provides deterministic fallback. `HeuristicAgent` parses,
generates, and ranks legal selections. `HybridAgent` is currently a heuristic
pass-through; `BoundedShortSearch` is tested separately and has no verified
runtime adapter.

Behavior and gates: [`docs/15_agent_implementation.md`](../../docs/15_agent_implementation.md).
