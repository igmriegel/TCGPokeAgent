# Pokemon TCG Engine — AI Agent Guide

Tool-agnostic. Any AI coding tool (opencode, Claude Code, Codex, Antigravity)
can read this file to understand the project conventions.

---

## Project Overview

Kaggle agent for the **PTCG AI Battle Challenge**. Uses `kaggle-environments`
(`cabt` SDK) to play Pokemon TCG. The agent receives an `Observation`, parses
it, generates legal selections, scores them with heuristics, optionally runs
short search, and returns a `list[int]` of option indices.

**MVP scope:** fixed deck, explicit heuristics, short search (≤100ms on MAIN),
fallback for every SelectContext, 200-match evaluation gate.

---

## Architecture (vertical slices)

```
Observation
  │
  ├─ ObservationParser.parse(observation) → ParsedDecision
  │     raw, state, select_type/context, candidates
  │
  ├─ SelectionGenerator.generate(candidates, min/max, energy, damage) → list[Selection]
  │     combinações legais de opções
  │
  ├─ HeuristicScorer.score(state, selection) → (float, reasons)
  │     (opcional) ShortSearch.choose(observation, belief, ranked, budget)
  │
  └─ AgentPolicy.select(observation) → list[int]
        retorna índices da melhor Selection
```

**Separation:** `GameState` = facts only. `BeliefState` = hypotheses. Never
serialize belief as fact. Option indices belong to the simulator — never
renumber.

---

## File Map

```
main.py                          # Entry point: stdin → stdout JSON agent
src/
├── core/                        # Domain layer
│   ├── types.py                 # Enums: SelectType, SelectContext, OptionType,
│   │                            #   TurnPhase, MatchResult, AgentMode, ErrorCategory
│   ├── state.py                 # GameState, PlayerState, PokemonState
│   ├── belief.py                # BeliefState
│   ├── candidate.py             # Candidate
│   ├── selection.py             # Selection (output type)
│   ├── action.py                # Re-exports Selection (legacy compat)
│   ├── parsed_decision.py       # ParsedDecision
│   ├── selection_generator.py   # DefaultSelectionGenerator
│   ├── catalog.py               # CardCatalog
│   ├── interfaces.py            # ABCs for all pluggable components
│   ├── parser.py                # DefaultParser (dict + dataclass)
│   └── exceptions.py            # EngineError hierarchy
├── agents/                      # Agent implementations
│   ├── baseline.py              # BaselineAgent (fallback by context)
│   └── heuristic.py             # HeuristicAgent + SimpleHeuristicScorer
├── eval/                        # Evaluation harness
│   ├── runner.py                # MatchRunner, MatchRecord, RunReport
│   ├── metrics.py               # AggregateMetrics (W/D/L, Wilson CI, percentiles)
│   ├── comparison.py            # PairedComparison
│   ├── reporting.py             # JSON + Markdown serialization
│   └── validation.py            # Preflight: SDK, deck, agent output
├── config/                      # Config loader
│   └── loader.py                # ConfigLoader (include resolution, Config dataclass)
├── experiments/                 # Experiment orchestration
│   └── orchestrator.py          # run_experiment()
├── logging_setup.py             # structlog configuration
└── artifacts/
    └── deck.csv                 # 60-card deck (placeholder, replace with real deck)
configs/                         # YAML profiles (default, agent_*, eval_*)
tests/                           # pytest fixtures + tests
scripts/                         # run_smoke, run_full, build_package
docs/                            # 26 markdown files: architecture, contracts, specs
```

---

## Coding Conventions

### Style
- Python 3.11+ with `from __future__ import annotations`
- Use `@dataclass(slots=True)` for data objects, `@dataclass(frozen=True, slots=True)` for immutable
- Return types on every public function
- No comments unless explaining a non-obvious invariant
- Line length: 100

### Imports order
1. `from __future__ import annotations`
2. stdlib
3. blank
4. third-party
5. blank
6. project (`src.*`)

### Naming
- Classes: PascalCase
- Functions/variables: snake_case
- Enums: Uppercase (e.g., `SelectType.MAIN`)
- Private methods: `_leading_underscore`
- Constants: UPPER_SNAKE_CASE

### Error handling
- Custom exceptions inherit from `EngineError`
- Every exception has a `category: ErrorCategory`
- Fallback must always be available (never let a parse failure crash the agent)
- Catch and wrap external errors; don't let SDK exceptions propagate

---

## Testing Conventions

- Framework: pytest
- Fixtures in `tests/conftest.py`
- Test files: `tests/test_*.py`
- Golden tests for parser with real observation fixtures
- Smoke: 20 matches. Full: ≥200 matches. Both sides.
- Agents must produce zero `INVALID`, `ERROR`, `TIMEOUT` in evaluation

Run:
```bash
pytest tests/ -v
```

---

## Config System

YAML files support `include:` for inheritance:
```yaml
# eval_full.yaml
include: default.yaml
runs: 200
```

Resolution: load included file, shallow-merge current on top. See
`src/config/loader.py`.

Environment variable `AGENT_MODE`:
- `baseline` — BaselineAgent (fallback only)
- `heuristic` — HeuristicAgent (+ scorer)
- `hybrid` — HeuristicAgent + ShortSearch (planned)

---

## Implementation Order (per docs/11_implementation_order.md)

| Slice | What | Gate |
|-------|------|------|
| F0 | SDK, deck, main.py, package | Structural valid, zero failures |
| F1 | Parser, candidates, fallback | All legal decisions, no INVALID/ERROR/TIMEOUT |
| F2 | Heuristic scorer | Measurable improvement, no regression |
| F3 | Evaluation harness | Full reproducible report |
| F4 | Belief + ShortSearch | Search doesn't reduce wins, ≤100ms |
| F5 | Frozen package, final matrix | All handoff spec items |

Current status: F0-F1 core implemented, F2-F4 stubs ready.

---

## Common Tasks

### Add a new agent
1. Create `src/agents/my_agent.py` implementing `AgentPolicy`
2. Add to `src/agents/__init__.py`
3. Wire in `main.py` `_build_agent()`
4. Add config in `configs/agent_my_agent.yaml`
5. Write tests in `tests/test_my_agent.py`

### Add a new heuristic component
1. Extend `HeuristicScorer.score()` in `src/agents/heuristic.py`
2. Add weight constant to `WEIGHTS` dict
3. Update `reasons` list for traceability
4. Test with specific board states

### Run evaluation
```bash
# Smoke
AGENT_MODE=heuristic scripts/run_smoke.sh

# Full (200 matches)
python -c "from src.experiments.orchestrator import run_experiment; from src.config.loader import load_config; run_experiment('full', load_config('eval_full'))"

# Build submission package
scripts/build_package.sh submission.tar.gz
```

---

## Key Design Decisions (locked)

- SDK pinned to `kaggle-environments==1.14.10` during MVP
- Single deck from `cabt.first_agent`
- Decision unit is `Selection` (not single `Action`)
- `GameState` factual, `BeliefState` hypothetical — never mixed
- Heuristic before search before learned models
- Search: top 3 selections, depth 4, 100ms budget, off below 30s overage
- Fallback deterministic for every `SelectContext`
- Zero `INVALID`/`ERROR`/`TIMEOUT` in evaluation
- Package re-validated after extraction

### Tooling & Code Quality

- **Type hints:** every public function and method must have annotated
  parameters and return types. Use `from __future__ import annotations` at the
  top of every file to enable deferred evaluation.
- **Docstrings:** all public modules, classes, and functions must have
  Google-style docstrings (`"""Summary line.\n\nExtended description.\n\nArgs:\n    ...\nReturns:\n    ...\n"""`).
  Private members may omit docstrings when the intent is obvious from the name.
- **Formatter:** `ruff format` (equivalent to Black). No `# fmt: off` unless
  a data structure layout is semantically meaningful.
- **Static analysis:** `ruff check` with the full `E`, `F`, `I`, `N`, `W`
  rule set. All pre-existing violations must be cleared before committing new
  code in the same file.
- **Pre-commit:** a `.pre-commit-config.yaml` at the project root enforces
  `ruff format`, `ruff check --fix`, and `mypy` on every commit. The CI gate
  rejects pushes that skip or fail pre-commit.

---

## References

- `docs/20_master_index.md` — canonical doc index
- `docs/01_architecture.md` — detailed architecture
- `docs/11_implementation_order.md` — vertical slice plan
- `docs/24_handoff_spec.md` — submission acceptance criteria
- `docs/07_core_contracts.md` — type contracts
- `src/core/interfaces.py` — ABC contracts
