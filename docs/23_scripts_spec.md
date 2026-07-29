# Operational commands contract

These commands are implementation targets; they are not declared available
today. Every Python entry point runs through the frozen `uv` environment.

```bash
uv run --frozen python -m scripts.preflight --config configs/default.yaml
uv run --frozen python -m scripts.run_eval --profile smoke --agent heuristic
uv run --frozen python -m scripts.run_eval --profile full --agent search
uv run --frozen python -m scripts.compare_runs --candidate RUN --baseline RUN
uv run --frozen python -m scripts.freeze_candidate --run RUN
uv run --frozen python -m scripts.package_submission --artifact ARTIFACT
uv run --frozen python -m scripts.validate_package --archive submission.tar.gz
uv run --frozen python -m scripts.export_strategy --run RUN
uv run --frozen python -m scripts.inventory_kaggle_data
uv run --frozen python -m scripts.gameplay_smoke --matches 10 --agent-mode heuristic
scripts/submit_simulation.sh
```

## Common rules

- `--help` and stable exit codes;
- config and overrides printed before mutation;
- output path printed at the end;
- stdout for summary, stderr for diagnostics;
- `0` success, `2` invalid input/config, `3` gate failed, `4` runtime failure;
- scripts call `src/`, do not duplicate game logic.

## Kaggle inventory

After accepting the rules:

```bash
kaggle competitions download pokemon-tcg-ai-battle -p data/raw/kaggle/simulation
kaggle competitions download pokemon-tcg-ai-battle-challenge-strategy -p data/raw/kaggle/strategy
uv run --frozen python -m scripts.inventory_kaggle_data
```

The inventory fails if any file lacks source, competition, version/date, size, SHA-256, format, license/status, utility and leakage risk.

## Package

`package_submission` creates an explicit staging directory, copies only the allowlist, checks root and size and generates the tar. `validate_package` rejects path traversal and runs smoke without checkout imports.

## Simulation submission

`submit_simulation.sh` runs preflight, tests, Ruff, mypy, the both-side
operational smoke gate, the observable-gameplay gate, package construction,
and isolated package validation. The gameplay gate rejects a legal agent that
never performs productive actions or attacks. The flow prints the archive size
and SHA-256, then requires explicit interactive confirmation before invoking:

```bash
kaggle competitions submit pokemon-tcg-ai-battle \
  -f submission.tar.gz \
  -m "<message>"
```

`--dry-run` executes all local gates and never uploads. `--yes` is reserved for
explicitly authorized non-interactive execution. A successful submission
writes a credential-free receipt under `reports/submissions/`.

## Idempotence

Preflight and inventory can be repeated. Runs and freezes never overwrite existing IDs. Package can be reproduced with the same inputs and records its hash, even if tar metadata prevents byte-identity without normalization.
