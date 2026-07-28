# Runner and evaluation implementation

## Layers

1. `validation.py`: preflight of SDK, deck, agent, and package.
2. `runner.py`: execution of a match and a batch.
3. `metrics.py`: aggregation without I/O.
4. `comparison.py`: paired comparison and gates.
5. `reporting.py`: serialization of computed objects.

## Preflight

- confirm exact SDK version;
- validate 60 cards and deck rules accepted by the engine;
- instantiate `cabt` with official agents;
- call the candidate on empty, simple, and multiple selection fixtures;
- reject output that is not `list[int]`;
- confirm writable run directories.

## Execution

Each match receives an explicit evaluation case identifier and internal deadline. The runner passes the identifier through the supported environment configuration and captures observation, selection, monotonic duration, overage balance, scorer reasons, and the status returned by the environment. Since `cabt` native randomness is not seedable, the identifier is used for matrix accounting and captured traces are the audit/replay source. A failure ends the match, but the batch continues to produce a complete diagnosis.

Game order is predefined in the manifest. When parallelism is introduced, results remain ordered by `match_id`.

## Metrics

Keep raw and aggregated records separate. Calculate percentiles from raw durations, Wilson by matchup and side, and failure counts. Do not round values in JSON; round only for Markdown/CSV presentation.

## Smoke and full

Smoke: 20 balanced matches, intended for integration. Full: minimum 200, with matrix declared before the run. Both execute both sides. Full only starts after smoke is green.

## Package validation

1. list tar contents and reject absolute paths or `..`;
2. extract into temporary directory;
3. confirm `main.py` and `deck.csv` at the root;
4. measure size;
5. run smoke with cwd and imports restricted to the extracted content;
6. compute SHA-256 of the approved package.

## Tests

- runner preserves case identifiers and produces complete audit traces;
- failure of one match does not erase previous ones;
- Wilson at 0%, 50%, and 100%;
- percentiles for small batch;
- separation by side;
- gate fails with one operational occurrence;
- nested package or one with external import is rejected.
