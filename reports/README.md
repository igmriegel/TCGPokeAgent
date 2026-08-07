# Evaluation report storage

This directory keeps compact, reviewable evidence in Git. Full CABT traces,
per-match dumps, and progress checkpoints are generated artifacts and are
ignored by `.gitignore`:

- `*.jsonl.gz` full traces;
- `*.progress.json` interrupted-run checkpoints;
- full-trace, telemetry, diagnostic, ignition-terminal, and clean per-match
  JSON dumps.

Run the relevant evaluation script to regenerate ignored artifacts. Commit a
small summary JSON or Markdown report containing the sample size, W/D/L,
execution status, confidence interval, hashes, and the command used. Do not
use generated traces as the only source of a promotion decision.

Historical large artifacts may still exist in a developer's working tree, but
they are intentionally not required for a fresh checkout.
