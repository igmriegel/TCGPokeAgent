"""Decode complete decision-ledger events captured in a Kaggle replay log."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import zlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DICTIONARY_PATH = ROOT / "src" / "artifacts" / "decision_ledger_dictionary.json"
EVENT_PATTERN = re.compile(r"audit_decision_ledger=(\{.*?\})(?:\r?\n|$)")


def load_dictionary() -> dict[str, Any]:
    """Load the versioned alias and field-description dictionary.

    Returns:
        Parsed dictionary used to encode and interpret decision-ledger records.
    """
    payload = json.loads(DICTIONARY_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("decision ledger dictionary must be a mapping")
    return payload


def _expand_keys(value: object, aliases: dict[str, str]) -> object:
    """Expand short ledger keys recursively using the bundled dictionary."""
    if isinstance(value, dict):
        return {aliases.get(key, key): _expand_keys(item, aliases) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_keys(item, aliases) for item in value]
    return value


def _captured_log_text(text: str) -> str:
    """Extract stdout and stderr from the JSON returned by the Kaggle logs CLI."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text
    if not isinstance(payload, list):
        return text

    streams: list[str] = []
    for turn in payload:
        if not isinstance(turn, list):
            continue
        for event in turn:
            if not isinstance(event, dict):
                continue
            for field in ("stdout", "stderr"):
                value = event.get(field)
                if isinstance(value, str) and value:
                    streams.append(value)
    return "\n".join(streams) if streams else text


def decode_events(text: str) -> list[dict[str, Any]]:
    """Decode all complete decision-ledger events in one captured log.

    Args:
        text: Raw replay or stderr log text.

    Returns:
        Complete public decision-ledger records in their original JSON form.
    """
    dictionary = load_dictionary()
    keys = dictionary.get("keys", {})
    aliases = {
        value: key for key, value in keys.items() if isinstance(key, str) and isinstance(value, str)
    }
    records: list[dict[str, Any]] = []
    for match in EVENT_PATTERN.finditer(_captured_log_text(text)):
        envelope = json.loads(match.group(1))
        if envelope.get("encoding") != "zlib+base64":
            continue
        encoded = envelope.get("payload")
        if not isinstance(encoded, str):
            continue
        compact = zlib.decompress(base64.b64decode(encoded)).decode("utf-8")
        if hashlib.sha256(compact.encode("utf-8")).hexdigest() != envelope.get("sha256"):
            raise ValueError("decision ledger checksum mismatch")
        record = _expand_keys(json.loads(compact), aliases)
        if isinstance(record, dict):
            records.append(record)
    return records


def annotate_record(record: dict[str, Any]) -> dict[str, Any]:
    """Attach the complete field-description dictionary to a decoded decision.

    Args:
        record: One decoded decision-ledger record.

    Returns:
        Human-readable audit record with its interpretation dictionary.
    """
    dictionary = load_dictionary()
    return {
        "schema_version": "decision-ledger-audit-view-v1",
        "decision": record,
        "field_descriptions": dictionary["field_descriptions"],
        "turn_ledger_fields": dictionary["turn_ledger_fields"],
        "match_ledger_fields": dictionary["match_ledger_fields"],
    }


def main() -> None:
    """Read a Kaggle log and write decoded decision-ledger JSONL to stdout."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Kaggle replay JSON or extracted stderr log.")
    parser.add_argument("--output", type=Path, help="Optional JSONL output path.")
    parser.add_argument(
        "--annotated",
        action="store_true",
        help="Include the complete field-description dictionary with every decoded record.",
    )
    args = parser.parse_args()
    records = decode_events(args.input.read_text(encoding="utf-8"))
    if args.annotated:
        records = [annotate_record(record) for record in records]
    payload = "".join(json.dumps(record, sort_keys=True) + "\n" for record in records)
    if args.output is None:
        print(payload, end="")
    else:
        args.output.write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
