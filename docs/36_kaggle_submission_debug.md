# Kaggle authentication and decision-ledger audit

This document records authentication, complete decision-ledger capture, and
upload procedure for the auditable official package. It is not a release or
performance-evaluation procedure.

## Authentication formats

The current Kaggle CLI uses OAuth credentials stored in
`~/.kaggle/credentials.json`. That file contains an access token and a refresh
token.

Check only credential presence, never print token contents:

```bash
test -s ~/.kaggle/credentials.json && echo "OAuth credentials present"
```

For OAuth login or token refresh:

```bash
kaggle auth login
kaggle auth print-access-token >/tmp/kaggle_access_token
```

The second command may need network access to `api.kaggle.com`. It prints a
short-lived access token; do not commit or share `/tmp/kaggle_access_token`.

## Build and validate the auditable package

The dedicated `expert_turn_loop` builder includes the ledger in every official
archive. The historical `stdout-debug` builder is now a compatibility alias for
the same archive. The ledger is written to stderr; stdout contains only the
JSON action required by the simulator:

```bash
bash scripts/build_kaggle_stdout_debug_package.sh \
  submissions/honchkrow_porygon_stdout_debug.tar.gz
.venv/bin/python -m src.eval.validation \
  --package submissions/honchkrow_porygon_stdout_debug.tar.gz
```

Kaggle captures stdout and stderr separately and limits each to roughly 10,000
characters per decision. The full audit record uses dictionary aliases,
zlib compression, base64 encoding, and an uncompressed SHA-256. Decoding it
contains:

- `decision_phase` and `decision_phase_reason`: the winning policy path;
- `select_context` and `bounds`: the simulator decision contract;
- `selected_indices`: the exact simulator indices returned;
- `objective`: the persistent objective before and after the decision;
- all candidates, filter stages, and exact simulator indices;
- every ranked selection, score, margin, and reason code;
- every feature vector and heuristic value calculated for a legal selection;
- the complete public `turn_ledger` and match-scoped `match_ledger`;
- `fallback_used`, model metadata, and duration: execution health.

The schema identifier is `decision-ledger-v1`; aliases are specified in
`src/artifacts/decision_ledger_dictionary.json`. No credentials or hidden state
are included. An oversize record emits `audit_decision_ledger_failed`, never a
partial ledger masquerading as complete evidence.

Decode downloaded replays or extracted stderr logs before reviewing decisions:

```bash
uv run --frozen python scripts/decode_kaggle_decision_ledger.py REPLAY_OR_LOG \
  --output decisions.jsonl
```

### Reading a replay decision

For a replay JSON downloaded from Kaggle, prefer the replay inspector helper
before falling back to raw JSON tools:

```bash
PYTHONPATH=. .venv/bin/python scripts/inspect_replay.py \
  replays/remote/55392121/episode-91484013-replay.json \
  --turn 11 --player-index 0 \
  --card-id 1216 --card-id 1257 --card-id 15
```

The helper prints the decision frame, visible logs, legal options, and the
recorded action in one place. Use `--format json` when you need a structured
payload for a report or a quick downstream filter.

For current auditable packages, locate the captured stderr envelope first:

```bash
rg -n 'audit_decision_ledger|audit_decision_ledger_failed' \
  /path/to/replay.json
```

Prioritize fallback or audit-failure events, then compare decoded selected
indices with the candidate indices. Indices must never be renumbered during
analysis.

## Upload

Pass the freshly generated access token to the upload process explicitly:

```bash
KAGGLE_API_TOKEN="$(cat /tmp/kaggle_access_token)" \
  kaggle competitions submit pokemon-tcg-ai-battle \
  -f submissions/honchkrow_porygon_submission.tar.gz \
  -m "auditable decision ledger"
```

The ledger does not change the returned action: stdout remains reserved for the
agent protocol. Verify a fresh remote replay contains and decodes the stderr
event before relying on a submission as strategic evidence.

## Download and decode remote agent logs

Kaggle exposes the two agent streams for each completed simulation episode.
List the episodes belonging to the submission first:

```bash
kaggle competitions episodes SUBMISSION_ID --format json
```

Then download the log for the submission agent. `AGENT_INDEX` is the zero-based
player position shown by the episode/replay; download both `0` and `1` when the
submission was evaluated on both sides:

```bash
mkdir -p logs/kaggle/SUBMISSION_ID/EPISODE_ID
kaggle competitions logs EPISODE_ID AGENT_INDEX \
  -p logs/kaggle/SUBMISSION_ID/EPISODE_ID -q
```

Locate and decode the complete stderr decision-ledger events:

```bash
rg -n 'audit_decision_ledger|audit_decision_ledger_failed' \
  logs/kaggle/SUBMISSION_ID/EPISODE_ID
uv run --frozen python scripts/decode_kaggle_decision_ledger.py \
  LOG_FILE --output decisions.jsonl
```

Keep the downloaded log with its submission ID, episode ID, agent index, and
decoded JSONL. An `audit_decision_ledger_failed` event or missing envelope means
the episode cannot be claimed as a complete decision audit.
