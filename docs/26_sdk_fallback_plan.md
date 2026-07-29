# SDK Capability Fallback Plan

This plan defines how the agent remains executable when a capability required
by S8 or S9 is unbound, opaque, or unreliable in the installed `cabt` Python
wrapper.
Fallbacks preserve legal output and reproducibility; they do not silently claim
that the unavailable capability was evaluated.

## Principles

1. The heuristic policy is the stable production path.
2. Every optional capability has a capability probe before it is opened.
3. A failed probe or runtime exception returns the last legal deterministic
   choice and records a typed reason.
4. Facts from the SDK remain facts; fallback hypotheses never enter
   `GameState`.
5. A fallback run can pass the operational gate, but cannot promote search.

## Capability matrix

| Missing or unsafe capability | Detection | Runtime fallback | Evidence | Promotion impact |
|---|---|---|---|---|
| Search lifecycle (`search_begin`, `search_step`, `search_release`, `search_end`) | Probe the project adapter and require all four callable operations | Heuristic top-1 legal `Selection` | `search.disabled` with reason `adapter_unavailable` | S8 remains pending |
| Opaque or missing `search_begin_input` | Require a non-null input on a gated `MAIN` decision | Heuristic ranking; do not synthesize search state | Decision trace records `missing_search_input` | No search claim |
| Overage below 30 seconds | Read the SDK overage field; reject invalid values | Heuristic top-1 | `overage_below_threshold` | Search coverage excludes decision |
| Inconsistent hidden state | `BeliefState.consistent == false` | Heuristic policy; no search | Belief violations and `belief_inconsistent` | Search gate fails safely |
| Search timeout or exception | Wall-clock deadline and `try/finally` lifecycle | Exact heuristic top-1 selection | Typed `search_timeout` or `search_api_error` | Candidate is not promoted |
| SDK does not expose all required opponents | Probe opponent factory before matrix execution | Run available opponents and mark missing entries | Matrix manifest lists unavailable opponents | S9 remains pending |
| Native SDK diagnostics on stdout/stderr | Isolate SDK calls behind quiet context | Preserve agent JSON stdout contract | Captured diagnostics in run log | Operational gate may pass |
| SDK observation dataclass/`Struct` serialization | Normalize mappings and scalar values recursively | Store JSON-safe factual trace; omit opaque objects | Serialization error count must be zero | Run fails if traces cannot be persisted |
| Extracted package lacks repository imports | Run from temporary directory with checkout unavailable | Fail package validation; do not fall back to checkout | Isolated package result | S9 fails |

## S8 execution plan

### S8.1 Documented contract and local capability evidence

The official API documents all four lifecycle functions and the complete
`search_begin` inputs. The installed `kaggle-environments==1.32.2` package has
no Python-level search bindings in `cg/sim.py`, but its Linux native library
exports all four `Search*` symbols. This is an adapter integration gap, not
evidence that search is absent from the engine.

Before calling native symbols, obtain a matching header/source or wrapper
implementation and verify every ctypes structure, argument type, return type,
ownership rule, and error code. Exported symbol names alone are not sufficient
ABI evidence.

Sources verified on 2026-07-29:
[cabt API](https://matsuoinstitute.github.io/cabt/api.html) and
[cabt sim module](https://matsuoinstitute.github.io/cabt/sim.html).

### S8.2 Capability probe

Add a startup/self-test probe that reports:

- SDK version and adapter identity;
- availability and signatures of the four search operations;
- observation support for `search_begin_input` and overage;
- configured search limits.

The probe must be read-only and cached for the process lifetime. An unverified
or absent adapter disables search for the process instead of raising through
`main.py`.

### S8.3 Project-owned adapter

- Do not patch `.venv` or installed `site-packages`.
- Prefer an official matching Python wrapper when available.
- Otherwise bind the native ABI in a project module only after verifying the
  corresponding source/header.
- Convert the raw observation exactly as required by the official API.
- Validate every hidden-zone list against observed cardinality before begin.
- Normalize native errors into project `SearchAPIError` categories.

### S8.4 Safe decorator

Keep `BoundedShortSearch` around the heuristic policy with these invariants:

- open only on `MAIN`, at least two ranked legal selections, consistent belief,
  usable search input, and overage of at least 30 seconds;
- inspect at most three selections and depth four;
- stop at 100 ms, including cleanup;
- call release and end in `finally` blocks whenever begin succeeds;
- return exactly the heuristic top-1 on every failure;
- expose `considered`, `opened`, `fallbacks`, `failures`, and latency counters.

### S8.5 Required test matrix

Test each of the following with a fake SDK adapter:

1. all methods available and successful;
2. begin unavailable;
3. step raises;
4. release raises;
5. end raises;
6. deadline exceeded;
7. inconsistent belief;
8. missing input;
9. low overage;
10. one legal option and zero legal options.

The expected result for every failure case is legal heuristic output and no
uncaught exception. Search approval requires a real adapter run; fake-adapter
tests prove safety only.

## S9 execution plan

S9 can proceed with search disabled as a frozen heuristic submission only after
the release manifest explicitly states `search.enabled: false` and records the
reason `python_search_adapter_not_integrated`. The final matrix must then:

1. run both sides against every opponent actually exposed by the SDK;
2. record unavailable required opponents as a gate failure, not as a skipped
   success;
3. validate zero `INVALID`, `ERROR`, and `TIMEOUT`;
4. build and hash the archive;
5. extract it into a clean directory without checkout imports;
6. run initial-deck and in-game smoke from extracted contents;
7. link manifest, report, archive hash, and strategy record.

If the competition requires the missing SDK capability, stop at the heuristic
release and mark S9 `BLOCKED` with the exact SDK/version evidence. If it does
not, S9 may be approved for the heuristic-only release while S8 remains
unapproved.

## Current decision

The current repository follows the safe heuristic fallback while the Python
search adapter is unintegrated. The next implementation task is ABI/source
verification, followed by the project-owned adapter, capability probe, and
fake-adapter test matrix. Until that evidence exists, search must remain
disabled and no search win-rate claim may be made.
