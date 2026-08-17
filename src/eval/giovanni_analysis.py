"""Audit Giovanni promotions and post-promotion development in CABT replays."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

OWNER_NAME = "mudkip_mini_chicken"
GIOVANNI_ID = 1218
ENERGY_IDS = {6, 8, 11, 15, 17}
EVOLUTION_TARGETS = {463: 891, 473: 474}


@dataclass(slots=True)
class GiovanniEvent:
    """One effective Giovanni play and the public state after it."""

    episode_id: str
    outcome: str
    turn: int | None
    active_id: int | None
    active_serial: int | None
    active_energy_count: int
    active_is_unevolved: bool
    evolution_in_hand: bool
    evolution_card_id: int | None
    energy_in_hand: int
    same_turn_evolve: bool
    same_turn_attach: bool


@dataclass(slots=True)
class GiovanniAudit:
    """Giovanni audit for one submission."""

    submission_id: str
    events: list[GiovanniEvent] = field(default_factory=list)

    @property
    def zero_energy_unevolved(self) -> list[GiovanniEvent]:
        """Return Giovanni events that left a basic Pokémon without Energy Active."""
        return [
            event
            for event in self.events
            if event.active_is_unevolved and event.active_energy_count == 0
        ]


def analyze_submission(submission_id: str, replay_dir: str | Path) -> GiovanniAudit:
    """Analyze Giovanni plays in a local submission replay directory."""
    root = Path(replay_dir) / "remote" / str(submission_id)
    events: list[GiovanniEvent] = []
    for path in sorted(root.glob("episode-*-replay.json")):
        events.extend(_analyze_replay(path))
    return GiovanniAudit(str(submission_id), events)


def analyze_submissions(
    submission_ids: Iterable[str], replay_dir: str | Path
) -> list[GiovanniAudit]:
    """Analyze Giovanni plays for several submissions."""
    return [analyze_submission(submission_id, replay_dir) for submission_id in submission_ids]


def audit_to_dict(audit: GiovanniAudit) -> dict[str, Any]:
    """Serialize a Giovanni audit for JSON reporting."""
    events = audit.events
    zero = audit.zero_energy_unevolved
    return {
        "submission_id": audit.submission_id,
        "giovanni_uses": len(events),
        "matches_with_giovanni": len({event.episode_id for event in events}),
        "unevolved_active_uses": sum(event.active_is_unevolved for event in events),
        "unevolved_zero_energy_uses": len(zero),
        "unevolved_zero_energy_matches": len({event.episode_id for event in zero}),
        "events": [_event_to_dict(event) for event in events],
    }


def combined_to_dict(audits: Iterable[GiovanniAudit]) -> dict[str, Any]:
    """Serialize aggregate Giovanni counts."""
    audits = list(audits)
    events = [event for audit in audits for event in audit.events]
    zero = [
        event for event in events if event.active_is_unevolved and event.active_energy_count == 0
    ]
    return {
        "submission_count": len(audits),
        "giovanni_uses": len(events),
        "matches_with_giovanni": len({event.episode_id for event in events}),
        "unevolved_active_uses": sum(event.active_is_unevolved for event in events),
        "unevolved_zero_energy_uses": len(zero),
        "unevolved_zero_energy_matches": len({event.episode_id for event in zero}),
        "zero_energy_unevolved_with_evolution_in_hand": sum(
            event.evolution_in_hand for event in zero
        ),
        "zero_energy_unevolved_with_energy_in_hand": sum(
            event.energy_in_hand > 0 for event in zero
        ),
        "zero_energy_unevolved_followed_by_same_turn_evolution": sum(
            event.same_turn_evolve for event in zero
        ),
        "zero_energy_unevolved_followed_by_same_turn_attach": sum(
            event.same_turn_attach for event in zero
        ),
    }


def render_markdown(audits: Iterable[GiovanniAudit]) -> str:
    """Render a Portuguese Giovanni sequencing report."""
    audits = list(audits)
    combined = combined_to_dict(audits)
    lines = [
        "# Auditoria de Giovanni — promoção e desenvolvimento",
        "",
        "Definição: uso efetivo = Giovanni movido da nossa mão para o descarte. "
        "O estado do Ativo é o estado público imediatamente associado ao uso.",
        "",
        "## Resumo",
        "",
        f"- Usos de Giovanni: **{combined['giovanni_uses']}** em "
        f"**{combined['matches_with_giovanni']}** partidas",
        f"- Pokémon não evoluído no Ativo: **{combined['unevolved_active_uses']}** usos",
        f"- Não evoluído e sem Energia: **{combined['unevolved_zero_energy_uses']}** usos em "
        f"**{combined['unevolved_zero_energy_matches']}** partidas",
        f"- Com evolução correspondente na mão: "
        f"**{combined['zero_energy_unevolved_with_evolution_in_hand']}**",
        f"- Com Energia na mão: **{combined['zero_energy_unevolved_with_energy_in_hand']}**",
        f"- Evoluiu no mesmo turno: "
        f"**{combined['zero_energy_unevolved_followed_by_same_turn_evolution']}**",
        f"- Anexou Energia no mesmo turno: "
        f"**{combined['zero_energy_unevolved_followed_by_same_turn_attach']}**",
        "",
        "## Casos não evoluídos e sem Energia",
        "",
        "| Submissão | Partida | Resultado | Ativo | Evolução na mão | "
        "Energia na mão | Evoluiu depois | Anexou depois |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for audit in audits:
        for event in audit.zero_energy_unevolved:
            lines.append(
                f"| {audit.submission_id} | `{event.episode_id}` | {event.outcome} | "
                f"{event.active_id} | {'sim' if event.evolution_in_hand else 'não'} | "
                f"{event.energy_in_hand} | {'sim' if event.same_turn_evolve else 'não'} | "
                f"{'sim' if event.same_turn_attach else 'não'} |"
            )
    lines.extend(["", "## Por submissão", ""])
    for audit in audits:
        lines.append(
            f"- **{audit.submission_id}**: {len(audit.events)} usos; "
            f"{len(audit.zero_energy_unevolved)} não evoluídos sem Energia"
        )
    return "\n".join(lines) + "\n"


def _event_to_dict(event: GiovanniEvent) -> dict[str, Any]:
    return {
        "episode_id": event.episode_id,
        "outcome": event.outcome,
        "turn": event.turn,
        "active_id": event.active_id,
        "active_serial": event.active_serial,
        "active_energy_count": event.active_energy_count,
        "active_is_unevolved": event.active_is_unevolved,
        "evolution_in_hand": event.evolution_in_hand,
        "evolution_card_id": event.evolution_card_id,
        "energy_in_hand": event.energy_in_hand,
        "same_turn_evolve": event.same_turn_evolve,
        "same_turn_attach": event.same_turn_attach,
    }


def _analyze_replay(path: Path) -> list[GiovanniEvent]:
    replay = json.loads(path.read_text(encoding="utf-8"))
    info = replay.get("info", {})
    episode_id = str(info.get("EpisodeId", path.stem))
    agents = info.get("Agents", [])
    own_index = next(
        (index for index, agent in enumerate(agents) if agent.get("Name") == OWNER_NAME),
        0,
    )
    reward = (replay.get("rewards") or [0, 0])[own_index]
    outcome = "win" if reward == 1 else "loss" if reward == -1 else "draw"
    result: list[GiovanniEvent] = []
    seen: set[tuple[int, int | None]] = set()
    for step in replay.get("steps", []):
        for actor in step:
            visualizations = actor.get("visualize") or []
            for index, visualization in enumerate(visualizations):
                logs = visualization.get("logs") or []
                giovanni = next(
                    (
                        log
                        for log in logs
                        if log.get("cardId") == GIOVANNI_ID
                        and log.get("playerIndex") == own_index
                        and log.get("type") == "MoveCard"
                        and log.get("fromArea") == 2
                        and log.get("toArea") == 3
                    ),
                    None,
                )
                if giovanni is None:
                    continue
                key = (index, giovanni.get("serial"))
                if key in seen:
                    continue
                seen.add(key)
                current = visualization.get("current") or {}
                players = current.get("players") or []
                player = players[own_index] if len(players) > own_index else {}
                active = (player.get("active") or [None])[0] or {}
                hand = player.get("hand") or []
                active_id_value = active.get("id")
                active_id = active_id_value if isinstance(active_id_value, int) else None
                evolution_card_id = (
                    EVOLUTION_TARGETS.get(active_id) if active_id is not None else None
                )
                same_turn_evolve = False
                same_turn_attach = False
                turn = current.get("turn")
                for following in visualizations[index + 1 : index + 40]:
                    following_current = following.get("current") or {}
                    if following_current.get("turn") != turn:
                        break
                    for log in following.get("logs") or []:
                        if log.get("playerIndex") != own_index:
                            continue
                        same_turn_evolve |= log.get("type") == "Evolve"
                        same_turn_attach |= log.get("type") == "Attach"
                result.append(
                    GiovanniEvent(
                        episode_id=episode_id,
                        outcome=outcome,
                        turn=turn,
                        active_id=active_id,
                        active_serial=active.get("serial"),
                        active_energy_count=len(active.get("energyCards") or []),
                        active_is_unevolved=not bool(active.get("preEvolution")),
                        evolution_in_hand=any(card.get("id") == evolution_card_id for card in hand),
                        evolution_card_id=evolution_card_id,
                        energy_in_hand=sum(
                            card.get("id") in ENERGY_IDS
                            or "energy" in str(card.get("name", "")).casefold()
                            for card in hand
                        ),
                        same_turn_evolve=same_turn_evolve,
                        same_turn_attach=same_turn_attach,
                    )
                )
    return result
