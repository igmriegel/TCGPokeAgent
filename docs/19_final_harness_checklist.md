# Release acceptance checklist

> Canonical release gate. `PASS` requires linked evidence from the candidate
> being promoted. `PARTIAL` blocks promotion. `N/A` requires an explicit scope
> decision.

**Last audited:** 2026-07-29

**Release scope:** heuristic-only; native search disabled

## Gate summary

| Gate | State | Evidence or gap |
|---|---|---|
| Documentation and contracts | `PASS` | Protocol, vocabulary, metrics, persistence, and handoff contracts exist |
| Reproducible environment | `PASS` | Python 3.12, frozen `uv.lock`, SDK 1.32.2, preflight |
| Legal runtime behavior | `PASS` | Parser/fallback tests and zero operational failures in recorded smoke |
| Package isolation and safety | `PASS` | Root files, size, traversal checks, extracted-content smoke |
| Full local evaluation | `PARTIAL` | 400 matches exist, but only against `random`; report metadata needs reconciliation |
| Gameplay behavior | `PARTIAL` | Productive play recovered; full development and gameplay metrics remain open |
| Feedback validation | `PARTIAL` | FB-2026-001–009 implemented but not frozen-gate validated |
| Search | `N/A` | Disabled because no verified project Python adapter exists |
| Learned policy | `N/A` | No model is proposed for this release |
| Remote promotion | `PARTIAL` | `55093119` scores below stable reference `55088176` |

## Blocking items

- [ ] T-001–T-003: complete board-development behavior and metrics.
- [ ] T-004: run the frozen four-opponent, both-side comparison.
- [ ] T-005–T-006: validate Rule Box/PrizeMap and PrizeCheck transitions.
- [ ] Resolve local report `agent_mode` metadata.
- [ ] Rebuild and validate the final artifact after the promoted policy is frozen.
- [ ] Confirm the remote candidate is non-inferior to the stable reference.

## Already satisfied

- [x] `Observation` to legal `list[int]` contract.
- [x] Factual `GameState` and separate `BeliefState`.
- [x] Official 60-card deck and exact SDK version.
- [x] Deterministic fallback and original option indices.
- [x] Zero `INVALID`, `ERROR`, and `TIMEOUT` in recorded full local evaluation.
- [x] Package below 197.7 MiB with no unsafe archive paths.
- [x] Isolated package execution and remote-compatible root layout.
- [x] Release hashes, manifest, rollback artifact, and evidence log.
- [x] Search explicitly disabled for the heuristic-only scope.

## Decision rule

The next candidate may be promoted only when every applicable gate is `PASS`.
A prior release may remain usable while a new candidate is blocked. Current
headline status belongs in [`PROJECT_STATUS.md`](PROJECT_STATUS.md).
