# Implementation handoff

## Closed decisions

- SDK initial `kaggle-environments==1.14.10`;
- single deck from `cabt.first_agent`;
- input `Observation`, output `list[int]`;
- decision unit `Selection`;
- `GameState` factual separated from `BeliefState`;
- total deterministic fallback;
- heuristic before search/models;
- search top 3, depth 4, 100 ms, cutoff at 30 s;
- smoke 20 and full >= 200, both sides;
- zero `INVALID`, `ERROR`, `TIMEOUT`;
- package revalidated after extraction.

None of these points require a new architectural decision to start the MVP.

## First engineer delivery

Deliver F0 and F1 from [`11_implementation_order.md`](11_implementation_order.md), including:

- reproducible environment;
- validated deck;
- wrapper and minimum package;
- `Selection`, `GameState` and candidate types;
- parser with fixtures;
- fallback for all observed contexts;
- smoke of 20 matches and report.

## Required evidence in PR

- tests and command executed;
- SDK version;
- deck hash;
- results per side;
- failure counts;
- multiple selection example;
- extracted and tested package;
- `strategy_notes.md` update when there is an experimental claim.

## Available data

The eight datasets from both tracks are in `data/raw/kaggle/`, with SHA-256, schema and provenance in the manifest. There is no pending authentication block to start the inventory or implementation.

## Change rule

A behavior change updates code, test, config, experiment manifest, report and Strategy. An external contract change requires official source and date. A version only replaces the stable one after complete gate and preserved rollback.

## Acceptance

The handoff is complete when the first delivery passes all "MVP integrated" items from [`19_final_harness_checklist.md`](19_final_harness_checklist.md). The submission is only complete when it also passes the "Submission approved" block.
