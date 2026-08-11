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

## IMPORTANT ISSUE — Read at the start of every session

Project Owner Igor reviewed agent replays and observed that the agent is not
following the documented game plan and action sequencing. Treat this as an
unresolved P0 issue in every session until the Owner explicitly accepts closure
based on replay evidence.

Before changing gameplay behavior, read the current issue statement in
`docs/PROJECT_STATUS.md` and task `T-034` in
`docs/03_tasks/TASK_INDEX.md`. Do not assume that existing rules, focused tests,
or aggregate win rates prove strategic compliance. Preserve the distinction
between the Owner's verified observation and technical root causes, which are
still unknown and require end-to-end investigation.

---

## Architecture (vertical slices)

```
Observation
  │
  ├─ ObservationParser.parse(observation) → ParsedDecision
  │     raw, state, select_type/context, candidates
  │
  ├─ SelectionGenerator.generate(candidates, min/max, energy, damage) → list[Selection]
  │     legal combinations of options
  │
  ├─ HeuristicScorer.score(state, selection) → (float, reasons)
  │     (optional) ShortSearch.choose(observation, belief, ranked, budget)
  │
  └─ AgentPolicy.select(observation) → list[int]
        returns indices of the best Selection
```

**Separation:** `GameState` = facts only. `BeliefState` = hypotheses. Never
serialize belief as fact. Option indices belong to the simulator — never
renumber.

---

## File Map

```
Dockerfile                       # Multi-stage build (agent / dev)
docker-compose.yml               # Services: agent, experiment, download, dev
.dockerignore
kaggle OAuth credentials         # Stored outside the repository
main.py                          # Entry point: stdin → stdout JSON agent
src/
├── core/                        # Domain layer
│   ├── types.py                 # Enums: SelectType, SelectContext, OptionType,
│   │                            #   ExecutionStatus and ErrorCategory
│   ├── state.py                 # GameState, PlayerState, PokemonState
│   ├── belief.py                # BeliefState
│   ├── candidate.py             # Candidate
│   ├── selection.py             # Selection (output type)
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
├── data/                        # Data download
│   └── downloader.py            # Lazy download + SHA-256 verification vs manifest
├── config/                      # Config loader
│   └── loader.py                # ConfigLoader (include resolution, Config dataclass)
├── experiments/                 # Experiment orchestration
│   └── orchestrator.py          # run_experiment()
└── artifacts/
    ├── deck.csv                 # Active 60-card deck
    └── deck_profile.json        # Declarative deck roles
configs/                         # YAML profiles (default, agent_*, eval_*)
tests/                           # pytest fixtures + tests
scripts/                         # run_smoke, run_full, build_package, replay tools
docs/                            # Canonical status, code map, contracts, evidence
perf_reports/                    # HTML investigation reports (generated)
replays/                         # Raw Kaggle replay downloads by submission ID
```

---

## Language

The project language is **English**. All code, identifiers, docstrings,
comments, documentation, commit messages, and configuration files must be
written in English. This ensures consistency across tools (opencode, Claude
Code, Codex, Antigravity) and readers worldwide.

## Package Management

The project uses `uv` (Astral) for package and environment management. All
dependency resolution is pinned in `uv.lock` (committed to version control).
Python 3.12 is selected by `.python-version`, and `.venv` is a disposable local
artifact that must not be committed.

```bash
# Create venv and install all dependencies
uv sync

# Add a dependency
uv add <package>

# Run a command in the venv
uv run --frozen <command>

# Optional interactive activation
source .venv/bin/activate
```

`uv.lock` must be kept in sync with `pyproject.toml`. After editing
dependencies in `pyproject.toml`, run `uv lock` to update the lockfile.
CI and Docker use `uv sync --frozen` to guarantee reproducible installs.
`pyproject.toml` and `uv.lock` are the only dependency sources.

## Coding Conventions

### Style
- Python 3.12 with `from __future__ import annotations`
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

### Commits
- **Atomic commits:** each commit must represent a single logical change
  (feature, fix, refactor, docs, chore). Never mix concerns in one commit.
- **Message format:** `type: short description` — e.g. `feat: add ...`,
  `fix: correct ...`, `docs: document ...`, `chore: ...`, `refactor: ...`.
  The body explains what and why, not how.
- **Pre-commit:** all hooks must pass before committing. Use
  `pre-commit run --all-files` to verify.
- **Granularity:** a feature may span multiple atomic commits, each
  independently reviewable and revertable.

### Error handling
- Custom exceptions inherit from `EngineError`
- Every exception has a `category: ErrorCategory`
- Fallback must always be available (never let a parse failure crash the agent)
- Catch and wrap external errors; don't let SDK exceptions propagate

### Honchkrow decision-ledger audit logging
- The official Honchkrow/Porygon package must emit one `audit_decision_ledger`
  record for every non-initial decision. This functionality is always active.
- Write audit records directly to stderr; it is the diagnostic stream, not an
  error-only stream. Stdout is reserved for the simulator's JSON action and
  must never contain a ledger.
- The complete public record uses `decision-ledger-v1`, the versioned aliases in
  `src/artifacts/decision_ledger_dictionary.json`, zlib+base64 encoding, and an
  SHA-256 integrity check. It includes candidates, stages, rankings, feature
  values, selection, trace, turn ledger, and match ledger.
- Do not remove, disable, rename, or make this audit path optional without
  updating the package harness, decoder, documentation, and smoke tests. An
  oversize record must emit `audit_decision_ledger_failed`, never a partial or
  invented audit record.

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
uv run --frozen pytest tests/ -v
```

## Delivery Evidence and Completeness

- Do not present a task as complete based only on an implementation claim.
  Complete the requested scope or state precisely what remains incomplete.
- Every material change must include proportionate, reproducible evidence that
  the requested behavior was implemented: relevant tests, extracted-package
  validation, command output, artifact hash, remote receipt, or downloaded
  remote evidence as applicable.
- State the evidence boundary explicitly. Local validation is not remote
  confirmation; a package build is not a Kaggle submission; a submission is not
  replay evidence or a strategic improvement.
- When a user asks for an improvement, report the before/after evidence or say
  that no evidence of improvement exists. Never infer strategic improvement
  from a code change, successful test, or upload alone.
- Preserve user-owned unrelated files and changes. Before a commit, identify
  the exact files included and exclude unrelated work unless the user directs
  otherwise.

---

## Config System

YAML files support `include:` for inheritance:
```yaml
# eval_full.yaml
include: default.yaml
runs: 200
```

Resolution: load included file, deep-merge current on top. See
`src/config/loader.py`.

Environment variable `AGENT_MODE`:
- `baseline` — BaselineAgent (fallback only)
- `heuristic` — HeuristicAgent (+ scorer)
- `hybrid` — heuristic pass-through; bounded search is not integrated

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

Current status is reported only in `docs/PROJECT_STATUS.md`; task status is
reported only in `docs/03_tasks/TASK_INDEX.md`. Sprint specifications define
scope and gates but do not own status. Do not mark F0-F5 complete without their
documented gates and evidence.

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

### Docker

```bash
# Build
docker compose build

# Download datasets
docker compose run download

# Run agent (stdin)
echo '{"select":...}' | docker compose run --rm agent

# Full experiment
AGENT_MODE=heuristic docker compose run experiment

# Shell dev
docker compose run --rm dev bash

# Tests
docker compose run --rm dev pytest tests/ -v
```

### Download data
```bash
# Check integrity
uv run --frozen python -m src.data.downloader --check

# Download missing datasets
uv run --frozen python -m src.data.downloader
```

### Run evaluation
```bash
# Smoke
AGENT_MODE=heuristic scripts/run_smoke.sh

# Full (200 matches)
uv run --frozen python -c "from src.experiments.orchestrator import run_experiment; from src.config.loader import load_config; run_experiment('full', load_config('eval_full'))"

# Build submission package
scripts/build_package.sh submissions/submission.tar.gz
```

---

## Key Design Decisions (locked)

- SDK pinned to `kaggle-environments==1.32.2` during MVP
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

- `docs/20_master_index.md` — canonical documentation hub
- `docs/PROJECT_STATUS.md` — current verified status and decisions
- `docs/CODEBASE_MAP.md` — code-to-consumer, test, and maturity map
- `docs/03_tasks/TASK_INDEX.md` — executable backlog and task counts
- `docs/01_architecture.md` — detailed architecture
- `docs/11_implementation_order.md` — vertical slice plan
- `docs/24_handoff_spec.md` — submission acceptance criteria
- `docs/07_core_contracts.md` — type contracts
- `src/core/interfaces.py` — ABC contracts
