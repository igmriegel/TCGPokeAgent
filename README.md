# Pokémon TCG Engine for Kaggle

Python agent, evaluation harness, replay-learning foundation, and submission
tooling for the **PTCG AI Battle Challenge**.

> **Competition status:** The PTCG AI Battle Challenge has ended. This
> repository is now maintained as an archival and research record; evaluation,
> replay, packaging, and submission tooling is retained for reproducibility.

## Objective

The project has three tracks:

1. **Heuristic release:** fixed deck, CABT integration, legal fallback, explicit
   gameplay rules, evaluation, and isolated packaging.
2. **Evidence-driven improvement:** replay analysis, paired comparisons, and
   optional learned policies.
3. **Deferred capabilities:** native short search and live human gameplay
   capture after the release gates are green.

## External contract

- Initial compatibility: `kaggle-environments==1.32.2`.
- Input: `Observation(current, logs, select, search_begin_input)`.
- In-game output: `list[int]` with indices of legal options.
- Initial output: deck content when `select is None`.
- Submission: `.tar.gz` with `main.py` and `deck.csv` at root, valid imports from `/kaggle_simulations/agent/` and maximum size of 197.7 MiB.
- Published budget: `actTimeout=0` and `remainingOverageTime=600`.

Sources verified on **2026-07-27**: [competition Simulation](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/overview/description), [`cabt` API](https://matsuoinstitute.github.io/cabt/api.html) and [environment specification](https://raw.githubusercontent.com/Kaggle/kaggle-environments/master/kaggle_environments/envs/cabt/cabt.json).

Start with the [current status](docs/PROJECT_STATUS.md), choose work from the
[task index](docs/03_tasks/TASK_INDEX.md), and use the
[documentation hub](docs/20_master_index.md) to find contracts, gates, and
implementation guides.

## Structure

- `docs/`: canonical status, tasks, contracts, gates, and evidence.
- `src/`: agent, domain, evaluation, data, experiment, and learning code.
- `configs/`: versioned runtime and evaluation profiles.
- `scripts/`: operational, evaluation, package, and submission commands.
- `submissions/`: ignored storage for submission archives and SHA-256 sidecars; keep `.gitkeep` only.
- `data/raw/kaggle/`: authorized destination for official downloads, separated by competition.

## Docker

The project is dockerized for portability and remote execution (cloud, dedicated
servers). Uses multi-stage build to keep the image lean.

### Services

| Service | Command | Port | Usage |
|---------|---------|------|-------|
| `agent` | `python main.py` | — | Agent stdin/stdout (Kaggle submission) |
| `experiment` | `run_experiment()` | — | Full evaluation (batch of matches) |
| `download` | `src.data.downloader` | — | Lazy download of datasets |
| `dev` | bash (open stdin) | — | Development with live-mounted code |

### Commands

```bash
# Build all images
docker compose build

# Download datasets (lazy)
docker compose run download

# Build the submission package
make build-abomasnow-package

# Run gates and submit to Kaggle
make submit-kaggle

# Run experiment
AGENT_MODE=heuristic docker compose run experiment

# Run tests
docker compose run --rm dev pytest tests/ -v

# Interactive shell for development
docker compose run --rm dev bash

# Run agent (stdin)
echo '{"select": {"type": "MAIN", ...}}' | docker compose run --rm agent

# Generate a local replay with the bundled cg.game API
PYTHONPATH=. .venv/bin/python scripts/run_replay.py \
  --agent-one heuristic --agent-two random --matches 1
# Then open visualizer.html and select the generated JSON under data/derived/local_replays/
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
- `KAGGLE_API_TOKEN` — optional one-shot token passed to the container
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

## RFL experiments

The post-MVP RFL workflow is opt-in and documented in the [RFL experiment
runbook](docs/25_rfl_experiments.md). The shortest complete local sequence is:

```bash
scripts/run_smoke.sh rfl
scripts/run_full.sh rfl configs/eval_full.yaml
scripts/build_package.sh submissions/runs/rfl/latest/submission.tar.gz
```

The full run uses 200 seeds on both player sides. Do not promote a profile from
the smoke or small evaluation; use the holdout gates and extracted-package
validation described in the runbook.

## Simulation submission

Run the complete local gate and receive an interactive confirmation before any
upload:

```bash
scripts/submit_simulation.sh
```

To build and validate the same candidate without uploading:

```bash
scripts/submit_simulation.sh --dry-run
```

The script submits to `pokemon-tcg-ai-battle` through the official Kaggle CLI
only after explicit confirmation. It uses the Kaggle CLI credentials already
configured in `~/.kaggle` and does not need `KAGGLE_CONFIG_DIR` pointed at the
repository root.

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
kaggle auth login
# The current CLI stores OAuth credentials in ~/.kaggle/credentials.json.
# A one-shot access token can also be supplied as KAGGLE_API_TOKEN.
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
