# Core

Implement `Selection`, `Candidate`, `GameState`, `BeliefState`, parser, catalog, and interfaces per [`docs/07_core_contracts.md`](../../docs/07_core_contracts.md) and [`docs/12_core_implementation.md`](../../docs/12_core_implementation.md).

`action.py` does not represent a singular action: the public type will be `Selection`, capable of holding zero, one, or multiple indices.
