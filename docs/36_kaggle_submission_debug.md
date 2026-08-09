# Kaggle authentication and stdout-debug submission

This document records the authentication and upload procedure for the
experimental package that prints decision traces to stdout. It is not a
release or performance-evaluation procedure.

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
JSON `debug_decision` event into the extracted `main.py`, recalculates package
hashes, and writes an ignored archive:

```bash
bash scripts/build_kaggle_stdout_debug_package.sh \
  submissions/honchkrow_porygon_stdout_debug.tar.gz
.venv/bin/python -m src.eval.validation \
  --package submissions/honchkrow_porygon_stdout_debug.tar.gz
```

The event contains the decision phase, reason, fallback flag, backend,
latency, and the serializable `DecisionTrace`. No credentials are included.

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
