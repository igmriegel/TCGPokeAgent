"""Inspect Kaggle CABT replay frames without ad-hoc ``jq`` filters.

The helper loads a replay JSON file, extracts each decision frame, and
summarizes the visible action log, legal options, and chosen action in a
stable text or JSON form. It is intended for replay debugging and evidence
collection, not as a gameplay gate.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class ReplayFrame:
    """Summarize one visible replay decision frame."""

    step_index: int
    entry_index: int
    turn: int | None
    your_index: int | None
    select_type: int | None
    select_context: int | None
    action: tuple[int, ...]
    card_ids: tuple[int, ...]
    attack_ids: tuple[int, ...]
    log_lines: tuple[str, ...]
    option_lines: tuple[str, ...]


def _int_or_none(value: Any) -> int | None:
    """Return an integer value when the input is an int, otherwise ``None``."""

    return value if isinstance(value, int) else None


def _card_label(card_id: int | None) -> str:
    """Format a card identifier for debug output."""

    if card_id is None:
        return "-"
    return f"cardId={card_id}"


def _attack_label(attack_id: int | None) -> str:
    """Format an attack identifier for debug output."""

    if attack_id is None:
        return "-"
    return f"attackId={attack_id}"


def _describe_log_item(item: Mapping[str, Any]) -> str:
    """Render one replay log item into a compact human-readable string."""

    parts = [f"type={item.get('type')}"]
    if "playerIndex" in item:
        parts.append(f"player={item.get('playerIndex')}")
    if "cardId" in item:
        parts.append(_card_label(_int_or_none(item.get("cardId"))))
    if "cardIdTarget" in item:
        parts.append(f"target={_card_label(_int_or_none(item.get('cardIdTarget')))}")
    if "attackId" in item:
        parts.append(_attack_label(_int_or_none(item.get("attackId"))))
    if "fromArea" in item:
        parts.append(f"from={item.get('fromArea')}")
    if "toArea" in item:
        parts.append(f"to={item.get('toArea')}")
    if "value" in item:
        parts.append(f"value={item.get('value')}")
    return " ".join(parts)


def _lookup_hand_card(current: Mapping[str, Any], option: Mapping[str, Any]) -> int | None:
    """Resolve a play/attach/evolve option to the card currently referenced in hand."""

    index = option.get("index")
    if not isinstance(index, int):
        return None
    players = current.get("players")
    your_index = current.get("yourIndex")
    if not isinstance(players, list) or not isinstance(your_index, int):
        return None
    if your_index < 0 or your_index >= len(players):
        return None
    player = players[your_index]
    if not isinstance(player, Mapping):
        return None
    hand = player.get("hand")
    if not isinstance(hand, list) or index < 0 or index >= len(hand):
        return None
    card = hand[index]
    if not isinstance(card, Mapping):
        return None
    return _int_or_none(card.get("id"))


def _describe_option(current: Mapping[str, Any], option: Mapping[str, Any]) -> str:
    """Render one legal option into a compact human-readable string."""

    parts = [f"type={option.get('type')}"]
    if "index" in option:
        parts.append(f"index={option.get('index')}")
    if "area" in option:
        parts.append(f"area={option.get('area')}")
    if "inPlayArea" in option:
        parts.append(f"inPlayArea={option.get('inPlayArea')}")
    if "inPlayIndex" in option:
        parts.append(f"inPlayIndex={option.get('inPlayIndex')}")
    if "attackId" in option:
        parts.append(_attack_label(_int_or_none(option.get("attackId"))))
    card_id = _lookup_hand_card(current, option)
    if card_id is not None:
        parts.append(_card_label(card_id))
    return " ".join(parts)


def load_replay_frames(path: Path) -> list[ReplayFrame]:
    """Load and summarize every visible decision frame in a replay.

    Args:
        path: Path to a Kaggle replay JSON file.

    Returns:
        One summary per replay frame and per player entry.

    Raises:
        ValueError: If the replay structure is not the expected Kaggle layout.
    """

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError(f"expected replay JSON object: {path}")
    steps = data.get("steps")
    if not isinstance(steps, list):
        raise ValueError(f"expected replay steps array: {path}")

    frames: list[ReplayFrame] = []
    for step_index, step in enumerate(steps):
        if not isinstance(step, list):
            continue
        for entry_index, entry in enumerate(step):
            if not isinstance(entry, Mapping):
                continue
            observation = entry.get("observation")
            if not isinstance(observation, Mapping):
                continue
            current = observation.get("current")
            if not isinstance(current, Mapping):
                continue
            select = observation.get("select")
            if not isinstance(select, Mapping):
                select = {}
            logs = observation.get("logs")
            if not isinstance(logs, list):
                logs = []
            turn = _int_or_none(current.get("turn"))
            your_index = _int_or_none(current.get("yourIndex"))
            select_type = _int_or_none(select.get("type"))
            select_context = _int_or_none(select.get("context"))
            action = tuple(
                item for item in entry.get("action", []) if isinstance(item, int)
            )
            log_lines: list[str] = []
            card_ids: list[int] = []
            attack_ids: list[int] = []
            for log in logs:
                if not isinstance(log, Mapping):
                    continue
                log_lines.append(_describe_log_item(log))
                card_id = _int_or_none(log.get("cardId"))
                if card_id is not None:
                    card_ids.append(card_id)
                attack_id = _int_or_none(log.get("attackId"))
                if attack_id is not None:
                    attack_ids.append(attack_id)
            options = select.get("option")
            if not isinstance(options, list):
                options = []
            option_lines = tuple(
                _describe_option(current, option)
                for option in options
                if isinstance(option, Mapping)
            )
            frames.append(
                ReplayFrame(
                    step_index=step_index,
                    entry_index=entry_index,
                    turn=turn,
                    your_index=your_index,
                    select_type=select_type,
                    select_context=select_context,
                    action=action,
                    card_ids=tuple(dict.fromkeys(card_ids)),
                    attack_ids=tuple(dict.fromkeys(attack_ids)),
                    log_lines=tuple(log_lines),
                    option_lines=option_lines,
                )
            )
    return frames


def filter_replay_frames(
    frames: Sequence[ReplayFrame],
    *,
    step_indices: set[int] | None = None,
    turn: int | None = None,
    your_index: int | None = None,
    card_ids: set[int] | None = None,
    attack_ids: set[int] | None = None,
) -> list[ReplayFrame]:
    """Filter replay frames by stable replay coordinates or observed IDs."""

    filtered: list[ReplayFrame] = []
    for frame in frames:
        if step_indices is not None and frame.step_index not in step_indices:
            continue
        if turn is not None and frame.turn != turn:
            continue
        if your_index is not None and frame.your_index != your_index:
            continue
        if card_ids is not None and not card_ids.intersection(frame.card_ids):
            continue
        if attack_ids is not None and not attack_ids.intersection(frame.attack_ids):
            continue
        filtered.append(frame)
    return filtered


def frame_as_text(frame: ReplayFrame) -> str:
    """Render one replay frame as a multi-line debug string."""

    lines = [
        (
            f"step={frame.step_index} entry={frame.entry_index} turn={frame.turn} "
            f"player={frame.your_index} select_type={frame.select_type} "
            f"select_context={frame.select_context} action={list(frame.action)}"
        )
    ]
    if frame.option_lines:
        lines.append("options:")
        lines.extend(f"  - {line}" for line in frame.option_lines)
    if frame.log_lines:
        lines.append("logs:")
        lines.extend(f"  - {line}" for line in frame.log_lines)
    return "\n".join(lines)


def frames_as_json(frames: Sequence[ReplayFrame]) -> list[dict[str, Any]]:
    """Render replay frames as JSON-serializable dictionaries."""

    return [
        {
            "step_index": frame.step_index,
            "entry_index": frame.entry_index,
            "turn": frame.turn,
            "your_index": frame.your_index,
            "select_type": frame.select_type,
            "select_context": frame.select_context,
            "action": list(frame.action),
            "card_ids": list(frame.card_ids),
            "attack_ids": list(frame.attack_ids),
            "options": list(frame.option_lines),
            "logs": list(frame.log_lines),
        }
        for frame in frames
    ]


def parse_int_list(values: Iterable[str]) -> set[int]:
    """Parse repeated CLI integers into a stable set."""

    return {int(value) for value in values}
