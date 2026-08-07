"""Deep analysis of CABT replay files — turn-by-turn state extraction."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(slots=True)
class PokemonState:
    """Snapshot of a Pokemon at a given frame."""

    name: str
    card_id: int
    hp: int
    max_hp: int
    energies: tuple[int, ...]
    tools: tuple[str, ...]
    is_active: bool


@dataclass(slots=True)
class PlayerFrameState:
    """Snapshot of one player's board at a given frame."""

    active: list[PokemonState]
    bench: list[PokemonState]
    prize_count: int
    deck_count: int
    hand_count: int
    energy_attached: bool
    supporter_played: bool
    total_hp: int = 0
    total_max_hp: int = 0

    def __post_init__(self) -> None:
        all_pokemon = self.active + self.bench
        self.total_hp = sum(p.hp for p in all_pokemon)
        self.total_max_hp = sum(p.max_hp for p in all_pokemon)


@dataclass(slots=True)
class FrameData:
    """One visualization frame — complete game state snapshot."""

    turn: int
    frame_index: int
    owner_state: PlayerFrameState
    opponent_state: PlayerFrameState
    first_player: int
    events: list[dict[str, Any]]


@dataclass(slots=True)
class GameEvent:
    """Parsed event from the visualization logs."""

    event_type: str
    player_index: int
    card_id: int | None = None
    card_name: str | None = None
    target_id: int | None = None
    target_name: str | None = None
    value: int | None = None
    area_from: str | None = None
    area_to: str | None = None
    attack_id: str | None = None


@dataclass(slots=True)
class DeepReplayAnalysis:
    """Full turn-by-turn analysis of one replay."""

    episode_id: int
    source_path: str
    owner_name: str
    opponent_name: str
    owner_index: int
    winner_index: int | None
    owner_outcome: str
    total_turns: int
    first_player: int
    frames: list[FrameData]
    events: list[GameEvent]
    owner_archetype: str
    opponent_archetype: str


def _parse_pokemon(poke: Mapping[str, Any], is_active: bool) -> PokemonState:
    """Parse a Pokemon card from the visualization state."""
    return PokemonState(
        name=str(poke.get("name", "unknown")),
        card_id=int(poke.get("id", 0)),
        hp=int(poke.get("hp", 0)),
        max_hp=int(poke.get("maxHp", 0)),
        energies=tuple(int(e) for e in poke.get("energies", [])),
        tools=tuple(
            str(t.get("name", "")) for t in poke.get("tools", []) if isinstance(t, Mapping)
        ),
        is_active=is_active,
    )


def _parse_player_state(
    player: Mapping[str, Any],
    energy_attached: bool,
    supporter_played: bool,
) -> PlayerFrameState:
    """Parse a player's full board state from a visualization frame."""
    active_raw = player.get("active", []) or []
    bench_raw = player.get("bench", []) or []

    active = [_parse_pokemon(p, True) for p in active_raw if isinstance(p, Mapping)]
    bench = [_parse_pokemon(p, False) for p in bench_raw if isinstance(p, Mapping)]

    prize_raw = player.get("prize", []) or []
    # Hidden prize cards are represented as ``None`` slots; slot count is the
    # public number of prizes remaining.
    prize_count = len(prize_raw)

    return PlayerFrameState(
        active=active,
        bench=bench,
        prize_count=prize_count,
        deck_count=int(player.get("deckCount", 0)),
        hand_count=int(player.get("handCount", 0)),
        energy_attached=energy_attached,
        supporter_played=supporter_played,
    )


def _parse_events(logs: list[dict[str, Any]]) -> list[GameEvent]:
    """Parse event logs from a visualization frame."""
    events = []
    for log in logs:
        if not isinstance(log, Mapping):
            continue
        event_type = str(log.get("type", ""))
        player_index = int(log.get("playerIndex", -1))

        event = GameEvent(event_type=event_type, player_index=player_index)

        if event_type == "Attack":
            event.attack_id = str(log.get("attackId", ""))
            event.card_id = _optional_int(log.get("cardId"))
            event.card_name = str(log.get("cardName", ""))
        elif event_type == "HpChange":
            event.card_id = _optional_int(log.get("cardId"))
            event.card_name = str(log.get("cardName", ""))
            event.value = int(log.get("value", 0))
        elif event_type == "Evolve":
            event.card_id = _optional_int(log.get("cardId"))
            event.card_name = str(log.get("cardName", ""))
            event.target_id = _optional_int(log.get("cardIdTarget"))
            event.target_name = str(log.get("cardNameTarget", ""))
        elif event_type == "Attach":
            event.card_id = _optional_int(log.get("cardId"))
            event.card_name = str(log.get("cardName", ""))
            event.target_id = _optional_int(log.get("cardIdTarget"))
            event.target_name = str(log.get("cardNameTarget", ""))
        elif event_type == "MoveCard":
            event.card_id = _optional_int(log.get("cardId"))
            event.card_name = str(log.get("cardName", ""))
            event.area_from = str(log.get("fromArea", ""))
            event.area_to = str(log.get("toArea", ""))
        elif event_type == "Draw":
            event.card_id = _optional_int(log.get("cardId"))
            event.card_name = str(log.get("cardName", ""))
        elif event_type == "Play":
            event.card_id = _optional_int(log.get("cardId"))
            event.card_name = str(log.get("cardName", ""))
        elif event_type == "Switch":
            event.card_id = _optional_int(log.get("cardIdActive"))
            event.card_name = str(log.get("cardNameActive", ""))
            event.target_id = _optional_int(log.get("cardIdBench"))
            event.target_name = str(log.get("cardNameBench", ""))

        events.append(event)
    return events


def _optional_int(value: Any) -> int | None:
    """Safely convert a value to int."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _get_visualization(replay: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Extract the visualization timeline from a replay."""
    try:
        visualize = replay["steps"][0][0]["visualize"]
        return visualize if isinstance(visualize, list) else []
    except (KeyError, IndexError, TypeError):
        return []


def _resolve_owner(replay: Mapping[str, Any], owner_name: str) -> int | None:
    """Resolve owner player index from agent names."""
    agents = replay.get("info", {}).get("Agents", [])
    for i, agent in enumerate(agents):
        if isinstance(agent, Mapping) and agent.get("Name") == owner_name:
            return i
    return None


def extract_deep_analysis(
    replay_path: str | Path,
    *,
    owner_name: str = "Igor Riegel",
) -> DeepReplayAnalysis:
    """Extract full turn-by-turn analysis from a CABT replay.

    Args:
        replay_path: Path to the CABT replay JSON file.
        owner_name: Name of the owner agent for W/L classification.

    Returns:
        Complete turn-by-turn analysis.

    Raises:
        ValueError: If the replay cannot be parsed.
    """
    path = Path(replay_path)
    replay = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(replay, Mapping) or replay.get("name") != "cabt":
        raise ValueError(f"unsupported replay: {path}")

    owner_index = _resolve_owner(replay, owner_name)
    if owner_index is None:
        raise ValueError(f"owner '{owner_name}' not found in replay: {path}")

    visualization = _get_visualization(replay)
    if not visualization:
        raise ValueError(f"no visualization timeline: {path}")

    agents = replay.get("info", {}).get("Agents", [])
    opponent_index = 1 - owner_index
    opponent_name = ""
    if isinstance(agents, list) and 0 <= opponent_index < len(agents):
        opponent_name = str(agents[opponent_index].get("Name", ""))

    frames: list[FrameData] = []
    all_events: list[GameEvent] = []
    terminal_turn = 0
    winner_index = None
    first_player = 0

    for frame_idx, frame in enumerate(visualization):
        if not isinstance(frame, Mapping):
            continue

        current = frame.get("current")
        if not isinstance(current, Mapping):
            continue

        turn = int(current.get("turn", 0) or 0)
        terminal_turn = max(terminal_turn, turn)
        first_player = int(current.get("firstPlayer", 0) or 0)

        result = current.get("result")
        if result in (0, 1):
            winner_index = result

        players = current.get("players", [])
        if not isinstance(players, list) or len(players) != 2:
            continue

        energy_attached = bool(current.get("energyAttached", False))
        supporter_played = bool(current.get("supporterPlayed", False))

        owner_state = _parse_player_state(players[owner_index], energy_attached, supporter_played)
        opponent_state = _parse_player_state(
            players[opponent_index], energy_attached, supporter_played
        )

        frame_events_raw = frame.get("logs", []) or []
        frame_events = _parse_events(frame_events_raw)
        all_events.extend(frame_events)

        frames.append(
            FrameData(
                turn=turn,
                frame_index=frame_idx,
                owner_state=owner_state,
                opponent_state=opponent_state,
                first_player=first_player,
                events=[{"type": e.event_type, "player": e.player_index} for e in frame_events],
            )
        )

    owner_outcome = (
        "draw" if winner_index is None else "win" if winner_index == owner_index else "loss"
    )

    # Resolve archetypes from deck cards
    owner_archetype = _resolve_archetype(replay, owner_index)
    opponent_archetype = _resolve_archetype(replay, opponent_index)

    return DeepReplayAnalysis(
        episode_id=int(replay.get("info", {}).get("EpisodeId", 0)),
        source_path=str(path),
        owner_name=owner_name,
        opponent_name=opponent_name,
        owner_index=owner_index,
        winner_index=winner_index,
        owner_outcome=owner_outcome,
        total_turns=terminal_turn,
        first_player=first_player,
        frames=frames,
        events=all_events,
        owner_archetype=owner_archetype,
        opponent_archetype=opponent_archetype,
    )


def _resolve_archetype(replay: Mapping[str, Any], player_index: int) -> str:
    """Best-effort archetype from deck card IDs (first 5 Pokemon names)."""
    try:
        action = replay["steps"][0][0]["visualize"][0]["action"]
        deck_ids = [int(c) for c in action[player_index]]
    except (KeyError, IndexError, TypeError):
        return "unknown"

    # Just return card ID count for now — catalog lookup not available here
    from collections import Counter

    counts = Counter(deck_ids)
    top_cards = [str(cid) for cid, _ in counts.most_common(5)]
    return f"cards:{','.join(top_cards)}"


def load_all_deep_analyses(
    replay_dir: str | Path,
    *,
    owner_name: str = "Igor Riegel",
) -> list[DeepReplayAnalysis]:
    """Load deep analysis for all replays in a directory.

    Args:
        replay_dir: Directory containing CABT replay JSON files.
        owner_name: Owner agent name for classification.

    Returns:
        List of successful deep analyses (failures silently skipped).
    """
    results = []
    for path in sorted(Path(replay_dir).rglob("episode-*.json")):
        try:
            results.append(extract_deep_analysis(path, owner_name=owner_name))
        except ValueError:
            continue
    return results
