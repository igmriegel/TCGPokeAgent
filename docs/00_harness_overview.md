# Product overview

## Delivered system

The repository contains a reproducible CABT agent that:

- returns the active 60-card deck for the initial request;
- parses gameplay observations without renumbering simulator options;
- generates and validates legal `Selection` values;
- ranks decisions with explicit heuristic reasons;
- retains deterministic fallback at both policy and entry-point boundaries;
- runs local CABT evaluation, replay ingestion, reporting, packaging, and
  isolated archive validation.

Current implementation maturity is mapped in
[`CODEBASE_MAP.md`](CODEBASE_MAP.md); current release evidence is in
[`PROJECT_STATUS.md`](PROJECT_STATUS.md).

## Current release scope

The release path uses Python 3.12, `kaggle-environments==1.32.2`, the bundled
fixed deck, and the heuristic policy. Native short search exists behind an
explicitly disabled gate because its project adapter and promotion evidence
are incomplete. Learned profiles and live human gameplay capture are outside
the current release.

## Definition of promotable

A candidate is promotable only when:

- smoke and full gates use frozen seeds, both player sides, and the declared
  opponent matrix;
- all decisions have zero `INVALID`, `ERROR`, and `TIMEOUT`;
- gameplay metrics show productive actions rather than merely legal output;
- package format, size, imports, and extracted execution pass;
- the candidate is non-inferior to the stable reference under the frozen
  acceptance expression;
- the release checklist contains evidence for every applicable gate.

The current candidate is not promotable; see
[`19_final_harness_checklist.md`](19_final_harness_checklist.md).

## Sources of truth

1. Competition and CABT protocol for the external boundary.
2. Contract documents for intended internal behavior.
3. Tests and immutable run artifacts for implementation evidence.
4. `CODEBASE_MAP.md` for code ownership and maturity.
5. `PROJECT_STATUS.md` and `TASK_INDEX.md` for current decisions and work.
