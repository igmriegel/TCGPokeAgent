"""Deck archetype resolution from canonical Pokémon card metadata."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Callable, Iterable, Mapping


def resolve_deck_archetype(
    card_ids: Iterable[int],
    card_lookup: Callable[[int], Any | None],
) -> str:
    """Resolve a deck label from Pokémon evolution-line counts.

    All copies in an evolution line are counted together and the terminal
    Pokémon name is used as the label. Card names are matched exactly, so a
    regular card and its ``ex`` counterpart remain separate lines.

    Args:
        card_ids: Card IDs from the complete deck list.
        card_lookup: Function returning SDK objects or mapping records by ID.

    Returns:
        The two most represented terminal evolution lines, or ``"unknown"``.
    """
    lines = resolve_deck_archetype_lines(card_ids, card_lookup)
    return " / ".join(line[0] for line in lines) or "unknown"


def resolve_deck_archetype_lines(
    card_ids: Iterable[int],
    card_lookup: Callable[[int], Any | None],
) -> list[tuple[str, int, int]]:
    """Resolve the two dominant evolution lines with their energy types.

    Args:
        card_ids: Card IDs from the complete deck list.
        card_lookup: Function returning SDK objects or mapping records by ID.

    Returns:
        ``(terminal_name, copy_count, energy_type)`` tuples for the two
        dominant Pokémon lines. The list is empty when no Pokémon are found.
    """
    counts = Counter(int(card_id) for card_id in card_ids)
    records: dict[int, Any] = {}
    children: defaultdict[str, list[Any]] = defaultdict(list)
    for card_id in counts:
        card = card_lookup(card_id)
        if card is None or int(_value(card, "cardType", -1)) != 0:
            continue
        records[card_id] = card
        parent = _value(card, "evolvesFrom")
        if parent:
            children[str(parent)].append(card)

    if not records:
        return []

    line_counts: Counter[str] = Counter()
    line_priority: dict[str, tuple[int, int]] = {}
    for card_id, card in records.items():
        terminal = _terminal_name(card, children)
        line_counts[terminal] += counts[card_id]
        line_priority[terminal] = max(
            line_priority.get(terminal, (0, 0)),
            (_stage_rank(card), int(_value(card, "hp", 0) or 0)),
        )

    ranked = sorted(
        line_counts,
        key=lambda name: (
            -line_counts[name],
            -line_priority[name][0],
            -line_priority[name][1],
            name,
        ),
    )
    result = []
    for name in ranked[:2]:
        terminal = next(
            card for card in records.values() if str(_value(card, "name", "unknown")) == name
        )
        result.append((name, line_counts[name], int(_value(terminal, "energyType", -1) or -1)))
    return result


def _terminal_name(card: Any, children: Mapping[str, list[Any]]) -> str:
    """Follow an exact-name evolution chain to its terminal card."""
    name = str(_value(card, "name", "unknown"))
    visited: set[str] = set()
    while name not in visited and children.get(name):
        visited.add(name)
        child = max(children[name], key=lambda item: (_stage_rank(item), _hp(item)))
        name = str(_value(child, "name", name))
    return name


def _stage_rank(card: Any) -> int:
    """Return the evolution stage rank used for deterministic tie-breaking."""
    if _as_bool(_value(card, "stage2", False)):
        return 2
    return 1 if _as_bool(_value(card, "stage1", False)) else 0


def _hp(card: Any) -> int:
    """Return a card HP as an integer for deterministic ordering."""
    try:
        return int(_value(card, "hp", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _as_bool(value: Any) -> bool:
    """Interpret SDK booleans and CSV boolean strings consistently."""
    if isinstance(value, str):
        return value.casefold() in {"1", "true", "yes"}
    return bool(value)


def _value(card: Any, key: str, default: Any = None) -> Any:
    """Read a field from either an SDK object or a mapping record."""
    if isinstance(card, Mapping):
        return card.get(key, default)
    return getattr(card, key, default)
