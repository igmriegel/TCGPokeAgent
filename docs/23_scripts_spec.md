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

## Idempotence

Preflight and inventory can be repeated. Runs and freezes never overwrite existing IDs. Package can be reproduced with the same inputs and records its hash, even if tar metadata prevents byte-identity without normalization.
