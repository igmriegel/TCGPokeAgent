# Pokémon TCG Engine for Kaggle

Executable plan, in English, to build, measure, and submit an agent to the **PTCG AI Battle Challenge**. API and code identifiers remain in English.

## Objective

The project evolves along three inseparable tracks:

1. **Submittable MVP:** fixed deck, real integration with `cabt`, explicit heuristics, short search and deterministic fallback.
2. **Continuous improvement:** promotion by metrics to supervised rankers, self-play, RL and search under imperfect information.
3. **Strategy:** hypothesis, ablation, result and traceable evidence from the first version.

This revision defines the implementation; the existing Python modules and YAML files do not yet implement these contracts.

## External contract

- Initial compatibility: `kaggle-environments==1.32.2`.
- Input: `Observation(current, logs, select, search_begin_input)`.
- In-game output: `list[int]` with indices of legal options.
- Initial output: deck content when `select is None`.
- Submission: `.tar.gz` with `main.py` and `deck.csv` at root, valid imports from `/kaggle_simulations/agent/` and maximum size of 197.7 MiB.
- Published budget: `actTimeout=0` and `remainingOverageTime=600`.

Sources verified on **2026-07-27**: [competition Simulation](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/overview/description), [`cabt` API](https://matsuoinstitute.github.io/cabt/api.html) and [environment specification](https://raw.githubusercontent.com/Kaggle/kaggle-environments/master/kaggle_environments/envs/cabt/cabt.json).

## Implementation order

1. Prepare SDK, official deck and minimal wrapper.
2. Preserve raw `Observation` and normalize state/options.
3. Generate all valid `Selection`, including empty or multiple.
4. Implement fallback by `SelectContext`.
5. Implement `HeuristicScorer`.
6. Build runner, metrics and smoke test of 20 matches.
7. Add `BeliefBuilder`, `StateEvaluator` and `ShortSearch`.
8. Run full gate of at least 200 matches.
9. Package, extract into temporary directory and repeat validation using only the package.

Start at the [canonical index](docs/20_master_index.md) and follow the [MVP vertical order](docs/11_implementation_order.md).

## Structure

- `docs/`: contracts, gates, roadmap and Strategy record.
- `src/`: reserved namespaces for implementation.
- `configs/`: existing profiles; the future contract is in `docs/22_config_spec.md`.
- `scripts/`: commands to be implemented as per `docs/23_scripts_spec.md`.
- `data/raw/kaggle/`: authorized destination for official downloads, separated by competition.
- `notebooks/`: exploration; never the sole source of a decision.

## Docker

The project is dockerized for portability and remote execution (cloud, dedicated
servers). Uses multi-stage build to keep the image lean.

### Services

| Service | Command | Port | Usage |
|---------|---------|------|-------|
| `agent` | `python main.py` | — | Agent stdin/stdout (Kaggle submission) |
| `marimo` | `marimo run notebooks/` | 2718 | Interactive notebooks for exploration |
| `experiment` | `run_experiment()` | — | Full evaluation (batch of matches) |
| `download` | `src.data.downloader` | — | Lazy download of datasets |
| `dev` | bash (open stdin) | — | Development with live-mounted code |

### Commands

```bash
# Build all images
docker compose build

# Download datasets (lazy)
docker compose run download

# Open Marimo in browser
docker compose up marimo

# Run experiment
AGENT_MODE=heuristic docker compose run experiment

# Run tests
docker compose run --rm dev pytest tests/ -v

# Interactive shell for development
docker compose run --rm dev bash

# Run agent (stdin)
echo '{"select": {"type": "MAIN", ...}}' | docker compose run --rm agent
```

### Remote execution

```bash
# Copy project to remote machine
rsync -avz --exclude='.venv' --exclude='data/raw' ./ user@server:~/pokemon-engine/

# Access and run
ssh user@server
cd ~/pokemon-engine
docker compose build
docker compose run download
AGENT_MODE=heuristic docker compose run experiment
```

### Volumes

- `./data:/app/data` — dataset and manifest persistence between executions
- `./kaggle.json:/root/.kaggle/kaggle.json:ro` — API credentials
- `./notebooks:/app/notebooks` — live-editable notebooks
- `./reports:/app/reports` — experiment reports accessible from host

## Quality tools

The project uses `ruff` for formatting and lint, `mypy` for type checking and
`pre-commit` to ensure everything runs before each commit.

### Initial setup

Python 3.12 is selected by `.python-version`. `uv sync` creates `.venv`
automatically and synchronizes the default development group from `uv.lock`.

```bash
uv sync
uv run --frozen pre-commit install

# Optional: activate the environment for an interactive shell
source .venv/bin/activate
```

Activation is not required. Use `uv run --frozen ...` so commands always use
the locked environment without modifying `uv.lock`.

### Manual execution

```bash
# Format all code
uv run --frozen ruff format .

# Lint (check and auto-fix)
uv run --frozen ruff check --fix .

# Type checking (src/ only)
uv run --frozen mypy --config-file=pyproject.toml src/

# Run all pre-commit hooks without committing
uv run --frozen pre-commit run --all-files

# Run a specific hook
uv run --frozen pre-commit run ruff-format --all-files

# Run tests
uv run --frozen pytest tests/ -v
```

### Pre-commit (automatic)

With `pre-commit install` executed, on each `git commit` the hooks run
automatically:

1. `ruff-format` — formats code (equivalent to Black).
2. `ruff` — lint with auto-fix (rules E, F, I, N, W).
3. `mypy` — type checking in the `src/` directory.

If any hook fails, the commit is blocked. Fix the issues and try
again.

## Data

The official Kaggle competition datasets are stored in `data/raw/kaggle/`:

```
data/raw/kaggle/
├── manifest.json            # Metadata, SHA-256 and provenance
├── simulation/              # pokemon-tcg-ai-battle
│   ├── Card_ID List_EN.pdf  (137 MB)
│   ├── Card_ID List_JP.pdf  (182 MB)
│   ├── EN_Card_Data.csv     (359 KB, 2022 records)
│   └── JP_Card_Data.csv     (442 KB, 2022 records)
├── strategy/                # pokemon-tcg-ai-battle-challenge-strategy
│   └── (same 4 files, byte-identical)
└── samples/                 # Sanitized CSV samples
```

The `data/raw/` directory is in `.gitignore` — data is not versioned.

### Kaggle API setup

```bash
cp kaggle.json.example ~/.kaggle/kaggle.json
# Edit ~/.kaggle/kaggle.json with username and key from
# https://www.kaggle.com/settings -> API -> Create New Token
chmod 600 ~/.kaggle/kaggle.json
```

### Data download

```bash
# Check if data exists (exit 0 = OK)
uv run --frozen python -m src.data.downloader --check

# Download data (lazy — only downloads what is missing)
uv run --frozen python -m src.data.downloader

# Only one competition
uv run --frozen python -m src.data.downloader --competition simulation

# Using the wrapper script
scripts/download_data.sh
scripts/download_data.sh --check
```

## Kaggle data status

The four official datasets for each competition were downloaded on 2026-07-27 to `data/raw/kaggle/`. Size, SHA-256, format, CSV schema and sanitized samples are recorded in the [`manifest.json`](data/raw/kaggle/manifest.json) and in the [data catalog](docs/21_persistence_contracts.md).
