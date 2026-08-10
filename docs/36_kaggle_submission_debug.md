# Kaggle authentication and stdout-debug submission

This document records the authentication, compact decision-audit format, and
upload procedure for the experimental package that prints decision traces to
stdout. It is not a release or performance-evaluation procedure.

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

## Build and validate the stdout-debug package

The builder starts from the dedicated `expert_turn_loop` package, injects one
JSON `debug_decision_compact` event into the extracted `main.py`, recalculates
package hashes, and writes an ignored archive:

```bash
bash scripts/build_kaggle_stdout_debug_package.sh \
  submissions/honchkrow_porygon_stdout_debug.tar.gz
.venv/bin/python -m src.eval.validation \
  --package submissions/honchkrow_porygon_stdout_debug.tar.gz
```

The event is deliberately compact so Kaggle's approximately 10,000-character
stdout limit does not cut the JSON in the middle. It contains:

- `decision_phase` and `decision_phase_reason`: the winning policy path;
- `select_context` and `bounds`: the simulator decision contract;
- `selected_indices`: the exact simulator indices returned;
- `objective`: the persistent objective before and after the decision;
- `candidates`: index, option type, card ID, and short card name;
- `stages`: candidate counts and removal reasons at each policy stage;
- `top_ranked`: the five highest-ranked selections and reason codes;
- `fallback_used`, `model_backend`, and `duration_ms`: execution health.

The schema identifier is `debug-decision-compact-v1`. No credentials or full
card text are included.

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

For legacy stdout-debug replays, inspect the captured stdout records:

```bash
rg -n 'debug_decision_compact|canonical_|fallback_used|selected_indices' \
  /path/to/replay.json
```

Prioritize records where `fallback_used` is true, where the selected index is
not the top-ranked index, where a stage removes the expected action, or where
the phase reason contradicts the intended turn sequence. Compare the exact
`selected_indices` with the candidate `index` values; indices must never be
renumbered during analysis.

## Upload

Pass the freshly generated access token to the upload process explicitly:

```bash
KAGGLE_API_TOKEN="$(cat /tmp/kaggle_access_token)" \
  kaggle competitions submit pokemon-tcg-ai-battle \
  -f submissions/honchkrow_porygon_stdout_debug.tar.gz \
  -m "experimental stdout decision trace"
```

This package is intentionally unsafe. Kaggle may treat stdout as part of the
agent protocol rather than as a replay log, causing invalid actions or a failed
submission. Never promote this package or use its result as a gameplay metric.
