"""Extract explicit match termination reasons from CABT replay files."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

from src.core.archetype import resolve_deck_archetype

if TYPE_CHECKING:
    from src.core.catalog import CardCatalog

TERMINATION_REASON_BY_CODE = {
    1: "all_prizes_taken",
    2: "deck_out",
    3: "no_pokemon_in_play",
}


@dataclass(frozen=True, slots=True)
class ReplayOutcome:
    """Normalized terminal outcome and condition evidence for one replay."""

    episode_id: int
    source_path: str
    winner_index: int | None
    owner_index: int | None
    owner_outcome: str
    reason_code: int | None
    termination_reason: str
    reason_explicit: bool
    reason_consistent: bool
    terminal_turn: int
    winner_prizes_remaining: int | None
    loser_prizes_remaining: int | None
    winner_deck_remaining: int | None
    loser_deck_remaining: int | None
    winner_pokemon_in_play: int | None
    loser_pokemon_in_play: int | None
    opponent_name: str | None
    opponent_deck_cards: tuple[int, ...]
    opponent_deck_hash: str
    opponent_deck_archetype: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the normalized replay outcome."""
        return asdict(self)


def extract_replay_outcome(
    replay_path: str | Path,
    *,
    owner_name: str | None = None,
    owner_index: int | None = None,
    catalog: CardCatalog | None = None,
) -> ReplayOutcome:
    """Extract the explicit result log and terminal public state.

    Args:
        replay_path: CABT replay JSON file.
        owner_name: Optional agent name used only to classify owner outcome.
        owner_index: Explicit owner side for self-play or duplicate agent names.
        catalog: Optional card catalog for deck archetype resolution.

    Returns:
        Normalized terminal evidence.

    Raises:
        ValueError: If the replay has no usable CABT terminal state.
    """
    path = Path(replay_path)
    try:
        replay = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read replay: {path}") from error
    if not isinstance(replay, Mapping) or replay.get("name") != "cabt":
        raise ValueError(f"unsupported replay: {path}")

    terminal = _terminal_visualization(replay)
    current = terminal.get("current")
    if not isinstance(current, Mapping):
        raise ValueError(f"replay has no terminal current state: {path}")
    result_log = _result_log(terminal)
    current_result = _optional_int(current.get("result"))
    log_result = _optional_int(result_log.get("result")) if result_log else None
    winner_index = log_result if log_result is not None else current_result
    if winner_index not in {0, 1, 2}:
        raise ValueError(f"replay has no terminal result: {path}")
    winner = winner_index if winner_index in {0, 1} else None
    reason_code = _optional_int(result_log.get("reason")) if result_log else None
    reason = (
        TERMINATION_REASON_BY_CODE.get(reason_code, "unknown")
        if reason_code is not None
        else "draw"
        if winner is None
        else "unknown"
    )
    if owner_index not in {None, 0, 1}:
        raise ValueError("owner_index must be 0, 1, or None")
    resolved_owner_index = (
        owner_index if owner_index is not None else _owner_index(replay, owner_name)
    )
    owner_outcome = (
        "unknown"
        if resolved_owner_index is None
        else "draw"
        if winner is None
        else "win"
        if winner == resolved_owner_index
        else "loss"
    )

    opponent_index = 1 - resolved_owner_index if resolved_owner_index is not None else None
    agents = replay.get("info", {}).get("Agents", [])
    opponent_name = (
        agents[opponent_index].get("Name")
        if isinstance(agents, list)
        and opponent_index is not None
        and 0 <= opponent_index < len(agents)
        and isinstance(agents[opponent_index], Mapping)
        else None
    )
    opponent_deck_ids = _deck_card_ids(replay, opponent_index) if opponent_index is not None else ()
    opponent_hash = _deck_hash(opponent_deck_ids) if opponent_deck_ids else ""
    opponent_archetype = (
        _deck_archetype(opponent_deck_ids, catalog) if opponent_deck_ids else "unknown"
    )

    players = current.get("players")
    if not isinstance(players, list) or len(players) != 2:
        raise ValueError(f"replay terminal state does not contain two players: {path}")
    if winner is None:
        winner_state = loser_state = None
    else:
        winner_state = players[winner]
        loser_state = players[1 - winner]
    winner_prizes = _zone_count(winner_state, "prize")
    loser_prizes = _zone_count(loser_state, "prize")
    winner_deck = _deck_count(winner_state)
    loser_deck = _deck_count(loser_state)
    winner_pokemon = _pokemon_in_play(winner_state)
    loser_pokemon = _pokemon_in_play(loser_state)
    consistent = _reason_consistent(
        reason_code,
        winner_prizes=winner_prizes,
        loser_deck=loser_deck,
        loser_pokemon=loser_pokemon,
        is_draw=winner is None,
    )

    return ReplayOutcome(
        episode_id=int(replay.get("info", {}).get("EpisodeId", path.stem)),
        source_path=str(path),
        winner_index=winner,
        owner_index=resolved_owner_index,
        owner_outcome=owner_outcome,
        reason_code=reason_code,
        termination_reason=reason,
        reason_explicit=result_log is not None and reason_code is not None,
        reason_consistent=consistent,
        terminal_turn=int(current.get("turn", 0) or 0),
        winner_prizes_remaining=winner_prizes,
        loser_prizes_remaining=loser_prizes,
        winner_deck_remaining=winner_deck,
        loser_deck_remaining=loser_deck,
        winner_pokemon_in_play=winner_pokemon,
        loser_pokemon_in_play=loser_pokemon,
        opponent_name=opponent_name,
        opponent_deck_cards=opponent_deck_ids,
        opponent_deck_hash=opponent_hash,
        opponent_deck_archetype=opponent_archetype,
    )


def load_replay_outcomes(
    replay_dir: str | Path,
    *,
    owner_name: str | None = None,
    catalog: CardCatalog | None = None,
) -> tuple[list[ReplayOutcome], list[dict[str, str]]]:
    """Load every replay while retaining per-file extraction failures.

    Args:
        replay_dir: Directory containing CABT replay JSON files.
        owner_name: Optional owner agent name for W/D/L classification.
        catalog: Optional card catalog for deck archetype resolution.

    Returns:
        Successfully normalized outcomes and structured errors.
    """
    outcomes: list[ReplayOutcome] = []
    errors: list[dict[str, str]] = []
    for path in sorted(Path(replay_dir).glob("*.json")):
        try:
            outcomes.append(extract_replay_outcome(path, owner_name=owner_name, catalog=catalog))
        except ValueError as error:
            errors.append({"path": str(path), "error": str(error)})
    return outcomes, errors


def _deck_card_ids(replay: Mapping[str, Any], player_index: int) -> tuple[int, ...]:
    """Extract the 60-card deck from the initial visualization frame."""
    try:
        action = replay["steps"][0][0]["visualize"][0]["action"]
        return tuple(int(c) for c in action[player_index])
    except (KeyError, IndexError, TypeError):
        return ()


def _deck_hash(card_ids: tuple[int, ...]) -> str:
    """SHA-256 hex digest of sorted card IDs (first 16 chars)."""
    canonical = ",".join(str(c) for c in sorted(card_ids))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _deck_archetype(
    card_ids: tuple[int, ...],
    catalog: CardCatalog | None = None,
) -> str:
    """Resolve deck archetype from card IDs using the card catalog.

    Strategy: group all Pokémon copies by exact evolution line and use the
    terminal Pokémon name for each of the two most represented lines.
    """
    if not card_ids or catalog is None:
        return "unknown"
    return resolve_deck_archetype(card_ids, lambda card_id: catalog.get_card(str(card_id)))


def _terminal_visualization(replay: Mapping[str, Any]) -> Mapping[str, Any]:
    try:
        visualization = replay["steps"][0][0]["visualize"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("replay has no visualization timeline") from error
    if not isinstance(visualization, list) or not visualization:
        raise ValueError("replay has an empty visualization timeline")
    for item in reversed(visualization):
        if isinstance(item, Mapping):
            current = item.get("current")
            if isinstance(current, Mapping) and _optional_int(current.get("result")) in {
                0,
                1,
                2,
            }:
                return item
    raise ValueError("replay visualization has no terminal result")


def _result_log(terminal: Mapping[str, Any]) -> Mapping[str, Any] | None:
    logs = terminal.get("logs")
    if not isinstance(logs, list):
        return None
    return next(
        (
            item
            for item in reversed(logs)
            if isinstance(item, Mapping) and item.get("type") == "Result"
        ),
        None,
    )


def _owner_index(replay: Mapping[str, Any], owner_name: str | None) -> int | None:
    if not owner_name:
        return None
    agents = replay.get("info", {}).get("Agents", [])
    matches = [
        index
        for index, agent in enumerate(agents)
        if isinstance(agent, Mapping) and agent.get("Name") == owner_name
    ]
    return matches[0] if len(matches) == 1 else None


def _zone_count(player: Any, name: str) -> int | None:
    if not isinstance(player, Mapping):
        return None
    zone = player.get(name)
    return len(zone) if isinstance(zone, list) else None


def _deck_count(player: Any) -> int | None:
    if not isinstance(player, Mapping):
        return None
    count = _optional_int(player.get("deckCount"))
    return count if count is not None else _zone_count(player, "deck")


def _pokemon_in_play(player: Any) -> int | None:
    active = _zone_count(player, "active")
    bench = _zone_count(player, "bench")
    return active + bench if active is not None and bench is not None else None


def _reason_consistent(
    reason_code: int | None,
    *,
    winner_prizes: int | None,
    loser_deck: int | None,
    loser_pokemon: int | None,
    is_draw: bool,
) -> bool:
    if is_draw:
        return reason_code is None
    if reason_code == 1:
        return winner_prizes == 0
    if reason_code == 2:
        return loser_deck == 0
    if reason_code == 3:
        return loser_pokemon == 0
    return False


def _optional_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
