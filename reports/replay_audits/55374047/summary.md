# Submission 55374047 replay audit

## Scope and provenance

- Submission: `55374047` (`v13 modular damage reduction`).
- Remote episode window: 28 completed episodes downloaded on 2026-08-09.
- Package: `submissions/honchkrow_porygon_submission_4e35976.tar.gz`.
- Source revision: `4e359763429a0031c6f743fbf0601db2fc2d608b`.
- Package SHA-256:
  `973b34ca61e63c6b04e67705961b403b6376b154fa0e831efc57522aaf460183`.

The extracted package reproduced all 1,614 recorded decisions: every returned
selection matched the replay, with zero invalid indices, exceptions, or
fallbacks. This proves package provenance and operational replay fidelity; it
does not prove that the policy followed the Owner's intended game plan.

## Replay outcome

| Result | Replays |
|---|---:|
| Wins | 14 |
| Losses | 14 |
| Draws | 0 |
| Explicit, reconciled terminal reasons | 28 / 28 |

| Loss category | Replays |
|---|---:|
| Prize-race loss | 8 |
| Deck-out | 3 |
| Board collapse | 3 |

The owner made 95 attacks and 59 observed KOs; opponents made 129 attacks and
99 observed KOs. The three deck-out losses are now suitable inputs to the
resource/objective review in T-026. The aggregate categories alone do not
identify a causal policy defect or justify a gameplay rule.

## Next-submission gate

| Requirement | Status | Evidence or next action |
|---|---|---|
| Exact remote package and replay provenance | Complete | Package replay trace: 1,614 / 1,614 exact decisions |
| Terminal outcome telemetry | Complete | 28 / 28 explicit and reconciled outcomes |
| Owner P0 sequencing review (T-034) | Open | Review representative failing decisions against the documented game plan; only Owner replay-based acceptance can close it |
| Isolated, replay-supported policy correction | Open | Derive one first causal objective/resource defect from the v13 and current baseline replay evidence; do not infer one from loss totals |
| Focused regression fixtures | Open | Encode the accepted defect and its legal alternatives |
| CABT qualification | Open | Run smoke, then 200 bilateral matches against the official policy with zero invalid/error/timeout and no material regression |
| Frozen package qualification | Open | Build, extract, validate, checksum, and retain a submission receipt |

## Decision

Submission `55374047` is a diagnostic reference, not a resubmission candidate.
The next upload may proceed only after the open rows above are satisfied. The
first implementation target remains a replay-supported T-026 resource or
objective correction; T-034 remains a release blocker because the Owner's
observed sequencing divergence has not been accepted as resolved.
