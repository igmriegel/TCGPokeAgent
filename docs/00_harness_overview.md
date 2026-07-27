# Product overview

## Expected result

Deliver a reproducible agent that:

- always returns a legal `Selection` in `list[int]` format;
- plays with a fixed 60-card deck validated by the SDK;
- uses explicit heuristics as a safe path;
- applies short search only when beneficial and within budget;
- produces sufficient evidence for technical promotion and for the Strategy writeup.

## MVP scope

The MVP uses Python 3.12 and `kaggle-environments==1.32.2`, the official agent
deck `cabt.first_agent`, a heuristic policy and search up to 100 ms on `MAIN`
decisions. `pyproject.toml` and `uv.lock` are the only dependency sources, and
all acceptance commands run through `uv`. Multi-deck support, deck
optimization, training and learned models are left for after the first valid
package.

## Definition of submittable

A candidate is submittable when:

- it passes 20 smoke matches and at least 200 of the full gate;
- it plays on both sides against `random`, `first`, heuristics without search and self-play;
- it registers zero `INVALID`, `ERROR` and `TIMEOUT`;
- it meets package format, size and imports;
- it maintains deterministic fallback for each `SelectContext`;
- it is re-validated after extracting the `.tar.gz`.

## Non-objectives of this revision

This phase does not implement Python modules, does not alter executable YAML and does not train models. The only later exception authorized by the user is the storage of official datasets in `data/raw/kaggle/`, currently blocked until acceptance of the competition rules.

## Sources of truth

1. Official `cabt` API for types and Search API.
2. `cabt.json` for budget and action shape.
3. Competition page for SDK and package.
4. These documents for architecture, gates and operation.
5. Implemented code, when it exists, accompanied by a test demonstrating compliance.
