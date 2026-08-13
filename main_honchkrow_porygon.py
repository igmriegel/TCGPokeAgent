"""Standalone Kaggle entrypoint for the Honchkrow/Porygon heuristic deck."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import sys
import zlib
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Mapping, cast

from src.agents.honchkrow_porygon import HonchkrowPorygonAgent
from src.core import AgentPolicy, DeckDefinition, DeckProfile

logger = logging.getLogger(__name__)
_SOURCE_PATH = globals().get("__file__")


def _discover_root() -> Path:
    """Find the repository or extracted package root used by the entrypoint."""
    if isinstance(_SOURCE_PATH, str):
        return Path(_SOURCE_PATH).resolve().parent
    for entry in reversed(sys.path):
        if not entry:
            continue
        candidate = Path(entry).resolve()
        if (candidate / "src" / "artifacts" / "deck_profile_honchkrow_porygon.json").is_file():
            return candidate
    return Path.cwd()


_ROOT = _discover_root()
_DECK_PATH = _ROOT / "src" / "artifacts" / "deck_team_rocket_murkrow.csv"
if not _DECK_PATH.is_file():
    _DECK_PATH = _ROOT / "deck.csv"
_PROFILE_PATH = _ROOT / "src" / "artifacts" / "deck_profile_honchkrow_porygon.json"
POLICY_VARIANT = "expert_turn_loop"
_agent: AgentPolicy | None = None
_deck: list[int] | None = None
_LEDGER_DICTIONARY_PATH = _ROOT / "src" / "artifacts" / "decision_ledger_dictionary.json"
_LEDGER_KEY_MAP: dict[str, str] | None = None


def _package_provenance() -> dict[str, str]:
    """Load immutable build provenance when running from an extracted package."""
    manifest_path = _ROOT / "package_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"source_commit": "", "package_sha256": ""}
    return {
        "source_commit": str(manifest.get("source_commit", "")),
        "package_sha256": str(manifest.get("package_payload_sha256", "")),
    }


def _ledger_key_map() -> dict[str, str]:
    """Load the versioned audit-key dictionary bundled with the package."""
    global _LEDGER_KEY_MAP
    if _LEDGER_KEY_MAP is None:
        payload = json.loads(_LEDGER_DICTIONARY_PATH.read_text(encoding="utf-8"))
        keys = payload.get("keys", {}) if isinstance(payload, Mapping) else {}
        _LEDGER_KEY_MAP = {
            key: value
            for key, value in keys.items()
            if isinstance(key, str) and isinstance(value, str)
        }
    return _LEDGER_KEY_MAP


def _compact_ledger_keys(value: object) -> object:
    """Replace audit-record keys with their stable short aliases recursively."""
    if isinstance(value, dict):
        key_map = _ledger_key_map()
        return {
            key_map.get(str(key), str(key)): _compact_ledger_keys(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_compact_ledger_keys(item) for item in value]
    if isinstance(value, tuple):
        return [_compact_ledger_keys(item) for item in value]
    return value


def _public_ledger(ledger: object) -> dict[str, object]:
    """Return JSON-safe public ledger fields without exposing private state."""
    return cast(dict[str, object], asdict(cast(Any, ledger))) if is_dataclass(ledger) else {}


def _decision_ledger(decision: object) -> dict[str, object]:
    """Serialize every calculated public value used for one policy decision."""
    trace = getattr(decision, "trace", None)
    ranked = [
        {
            "indices": row.selection.indices,
            "score": row.score,
            "rank": row.rank,
            "reasons": row.reasons,
            "margin_to_next": row.margin_to_next,
        }
        for row in getattr(decision, "ranked", ())
    ]
    features = [
        {
            "indices": row.selection.indices,
            "schema_version": row.schema_version,
            "values": row.values,
            "heuristic_score": row.heuristic_score,
            "heuristic_reasons": row.heuristic_reasons,
        }
        for row in getattr(decision, "features", ())
    ]
    return {
        "event": "audit_decision_ledger",
        "schema_version": "decision-ledger-v1",
        "selection": getattr(getattr(decision, "selection", None), "indices", ()),
        "decision_phase": getattr(decision, "decision_phase", ""),
        "decision_phase_reason": getattr(decision, "decision_phase_reason", ""),
        "fallback_used": getattr(decision, "fallback_used", False),
        "model_backend": getattr(decision, "model_backend", ""),
        "model_version": getattr(decision, "model_version", ""),
        "duration_ms": getattr(decision, "duration_ms", 0.0),
        "trace": cast(dict[str, object], asdict(cast(Any, trace))) if is_dataclass(trace) else {},
        "ranked": ranked,
        "features": features,
        "turn_ledger": _public_ledger(getattr(_agent, "turn_ledger", None)),
        "match_ledger": _public_ledger(getattr(_agent, "match_ledger", None)),
        **_package_provenance(),
    }


def _emit_decision_ledger() -> None:
    """Write the complete public decision audit record to the Kaggle log."""
    decision = getattr(_agent, "last_decision", None)
    if decision is None:
        return
    try:
        raw = json.dumps(
            _compact_ledger_keys(_decision_ledger(decision)), separators=(",", ":"), default=str
        )
        payload = json.dumps(
            {
                "event": "audit_decision_ledger",
                "schema_version": "decision-ledger-v1",
                "dictionary": "decision-ledger-keys-v1",
                "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                "encoding": "zlib+base64",
                "payload": base64.b64encode(zlib.compress(raw.encode("utf-8"), level=9)).decode(
                    "ascii"
                ),
            },
            separators=(",", ":"),
        )
        if len(payload) > 9_000:
            raise ValueError("encoded decision ledger exceeds the Kaggle log budget")
        print(f"audit_decision_ledger={payload}", file=sys.stderr, flush=True)
    except Exception:
        logger.exception("audit_decision_ledger_failed")


def _emit_fallback_ledger(observation: Mapping[str, Any], result: list[int]) -> None:
    """Record deterministic fallback use without changing the simulator response."""
    select = observation.get("select")
    context = select.get("type", "") if isinstance(select, Mapping) else ""
    payload = json.dumps(
        {
            "event": "audit_decision_ledger",
            "schema_version": "decision-ledger-v1",
            "selection": result,
            "select_context": context,
            "fallback_used": True,
            "reason": "policy_exception",
        },
        separators=(",", ":"),
    )
    try:
        print(f"audit_decision_ledger={payload}", file=sys.stderr, flush=True)
    except Exception:
        logger.exception("audit_decision_ledger_failed")


def _load_deck() -> list[int]:
    """Load the dedicated 60-card Honchkrow/Porygon deck."""
    deck = DeckDefinition.from_path(_DECK_PATH, "honchkrow_porygon")
    return list(deck.card_ids)


def _load_profile() -> DeckProfile:
    """Load and validate the dedicated declarative deck profile."""
    data = json.loads(_PROFILE_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("Honchkrow/Porygon profile must be a mapping")
    profile = DeckProfile.from_dict(data)
    deck = DeckDefinition.from_path(_DECK_PATH, "honchkrow_porygon")
    if profile.deck_sha256 != deck.sha256:
        raise ValueError("Honchkrow/Porygon profile does not match its deck")
    return profile


def _build_agent() -> HonchkrowPorygonAgent:
    """Build the isolated Honchkrow/Porygon policy."""
    return HonchkrowPorygonAgent(_load_profile(), POLICY_VARIANT)


def agent_policy(observation: dict[str, Any]) -> list[int]:
    """Return one legal CABT action for the dedicated deck."""
    global _agent, _deck
    if _agent is None:
        _agent = _build_agent()
    if _deck is None:
        _deck = _load_deck()
    if observation.get("select") is None:
        _agent.start_match(DeckDefinition.from_cards(_deck, "honchkrow_porygon"))
        return list(_deck)
    try:
        result = _agent.select(observation)
        _emit_decision_ledger()
        _validate_selection(observation, result)
        return result
    except Exception:
        fallback = _fallback_selection(observation)
        _emit_fallback_ledger(observation, fallback)
        return fallback


def _validate_selection(observation: Mapping[str, Any], output: list[int]) -> None:
    """Validate indices against the current CABT selection contract."""
    select = observation.get("select")
    if not isinstance(select, Mapping):
        raise ValueError("select must be a mapping")
    options = select.get("option")
    if not isinstance(options, list):
        raise ValueError("select.option must be a list")
    if len(output) != len(set(output)) or any(
        isinstance(index, bool) or not isinstance(index, int) or index < 0 or index >= len(options)
        for index in output
    ):
        raise ValueError("selection contains invalid indices")
    minimum = int(select.get("minCount", 0) or 0)
    maximum = int(select.get("maxCount", 0) or 0)
    if not minimum <= len(output) <= maximum:
        raise ValueError("selection violates cardinality")


def _fallback_selection(observation: Mapping[str, Any]) -> list[int]:
    """Return the first deterministic selection satisfying cardinality."""
    select = observation.get("select")
    if not isinstance(select, Mapping) or not isinstance(select.get("option"), list):
        return []
    options = select["option"]
    minimum = max(0, int(select.get("minCount", 0) or 0))
    result = list(range(minimum))
    return result if len(result) <= len(options) else []


def main() -> None:
    """Read one JSON observation and write one JSON selection."""
    logging.basicConfig(level="INFO")
    raw = sys.stdin.read()
    try:
        observation = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        observation = {}
    result = agent_policy(observation if isinstance(observation, dict) else {})
    json.dump(result, sys.stdout)


def agent(observation: dict[str, Any]) -> list[int]:
    """Expose the Kaggle callable entrypoint."""
    return agent_policy(observation)


if __name__ == "__main__":
    main()
