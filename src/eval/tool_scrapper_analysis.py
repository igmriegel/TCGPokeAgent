"""Audit Tool Scrapper use against publicly visible opposing tools."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

OWNER_NAME = "mudkip_mini_chicken"
TOOL_SCRAPPER_ID = 1137
HERO_CAPE_NAME = "Hero’s Cape"


@dataclass(slots=True)
class MatchToolAudit:
    """Aggregated tool observations for one replay."""

    episode_id: str
    outcome: str
    tool_scrapper_uses: int
    opposing_tools: Counter[str] = field(default_factory=Counter)
    scrapper_in_hand_with_opposing_tool: bool = False
    hero_cape_and_scrapper_in_hand: bool = False

    @property
    def used_tool_scrapper(self) -> bool:
        """Return whether the owned agent actually played Tool Scrapper."""
        return self.tool_scrapper_uses > 0


@dataclass(slots=True)
class SubmissionToolAudit:
    """Tool Scrapper audit for one submission."""

    submission_id: str
    replay_count: int
    matches: list[MatchToolAudit]

    @property
    def tool_scrapper_uses(self) -> int:
        """Return the number of effective Tool Scrapper plays."""
        return sum(match.tool_scrapper_uses for match in self.matches)

    @property
    def scrapper_matches(self) -> set[str]:
        """Return episode IDs in which Tool Scrapper was played."""
        return {match.episode_id for match in self.matches if match.used_tool_scrapper}

    def tool_matches(self, name: str, used_scrapper: bool) -> set[str]:
        """Return matches where a named opposing tool was seen in a Scrapper cohort."""
        return {
            match.episode_id
            for match in self.matches
            if name in match.opposing_tools and match.used_tool_scrapper == used_scrapper
        }

    def tool_occurrences(self, name: str, used_scrapper: bool) -> int:
        """Return public-state observations of a named opposing tool."""
        return sum(
            match.opposing_tools[name]
            for match in self.matches
            if match.used_tool_scrapper == used_scrapper
        )


def analyze_submission(submission_id: str, replay_dir: str | Path) -> SubmissionToolAudit:
    """Analyze all local replay files for one submission.

    Args:
        submission_id: Kaggle submission identifier used as the replay directory name.
        replay_dir: Root containing ``remote/<submission_id>/episode-*-replay.json``.

    Returns:
        Submission-level audit with one record per replay.
    """
    root = Path(replay_dir) / "remote" / str(submission_id)
    paths = sorted(root.glob("episode-*-replay.json"))
    matches = [_analyze_replay(path) for path in paths]
    return SubmissionToolAudit(str(submission_id), len(paths), matches)


def analyze_submissions(
    submission_ids: Iterable[str], replay_dir: str | Path
) -> list[SubmissionToolAudit]:
    """Analyze several submissions in the supplied order."""
    return [analyze_submission(submission_id, replay_dir) for submission_id in submission_ids]


def audit_to_dict(audit: SubmissionToolAudit) -> dict[str, Any]:
    """Serialize a submission audit into JSON-compatible data."""
    scrapper_matches = audit.scrapper_matches
    tool_names = sorted({name for match in audit.matches for name in match.opposing_tools})
    return {
        "submission_id": audit.submission_id,
        "replay_count": audit.replay_count,
        "tool_scrapper_uses": audit.tool_scrapper_uses,
        "matches_with_tool_scrapper": len(scrapper_matches),
        "matches_without_tool_scrapper": audit.replay_count - len(scrapper_matches),
        "matches_with_tool_scrapper_in_hand_while_tool_visible": sum(
            match.scrapper_in_hand_with_opposing_tool for match in audit.matches
        ),
        "matches_with_hero_cape_and_tool_scrapper_in_hand": sum(
            match.hero_cape_and_scrapper_in_hand for match in audit.matches
        ),
        "tools": {
            name: {
                "seen_matches_with_scrapper": len(audit.tool_matches(name, True)),
                "seen_matches_without_scrapper": len(audit.tool_matches(name, False)),
                "seen_occurrences_with_scrapper": audit.tool_occurrences(name, True),
                "seen_occurrences_without_scrapper": audit.tool_occurrences(name, False),
            }
            for name in tool_names
        },
        "matches": [
            {
                "episode_id": match.episode_id,
                "outcome": match.outcome,
                "tool_scrapper_uses": match.tool_scrapper_uses,
                "used_tool_scrapper": match.used_tool_scrapper,
                "opposing_tools_seen": dict(sorted(match.opposing_tools.items())),
                "scrapper_in_hand_with_opposing_tool": match.scrapper_in_hand_with_opposing_tool,
                "hero_cape_and_scrapper_in_hand": match.hero_cape_and_scrapper_in_hand,
            }
            for match in audit.matches
        ],
    }


def combined_to_dict(audits: Iterable[SubmissionToolAudit]) -> dict[str, Any]:
    """Serialize aggregate counts across submissions."""
    audits = list(audits)
    matches = [match for audit in audits for match in audit.matches]
    scrapper = [match for match in matches if match.used_tool_scrapper]
    tools = sorted({name for match in matches for name in match.opposing_tools})
    return {
        "submission_count": len(audits),
        "replay_count": len(matches),
        "tool_scrapper_uses": sum(match.tool_scrapper_uses for match in matches),
        "matches_with_tool_scrapper": len(scrapper),
        "matches_without_tool_scrapper": len(matches) - len(scrapper),
        "matches_with_tool_scrapper_in_hand_while_tool_visible": sum(
            match.scrapper_in_hand_with_opposing_tool for match in matches
        ),
        "matches_with_hero_cape_and_tool_scrapper_in_hand": sum(
            match.hero_cape_and_scrapper_in_hand for match in matches
        ),
        "tools": {
            name: {
                "seen_matches_with_scrapper": sum(
                    name in match.opposing_tools and match.used_tool_scrapper for match in matches
                ),
                "seen_matches_without_scrapper": sum(
                    name in match.opposing_tools and not match.used_tool_scrapper
                    for match in matches
                ),
                "seen_occurrences_with_scrapper": sum(
                    match.opposing_tools[name] for match in scrapper if name in match.opposing_tools
                ),
                "seen_occurrences_without_scrapper": sum(
                    match.opposing_tools[name]
                    for match in matches
                    if not match.used_tool_scrapper and name in match.opposing_tools
                ),
            }
            for name in tools
        },
    }


def _analyze_replay(path: Path) -> MatchToolAudit:
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
    opposing_tools: Counter[str] = Counter()
    scrapper_events: set[tuple[Any, ...]] = set()
    scrapper_in_hand_with_opposing_tool = False
    hero_cape_and_scrapper_in_hand = False
    for step_index, step in enumerate(replay.get("steps", [])):
        for actor in step:
            for visualization in actor.get("visualize") or []:
                current = visualization.get("current") or {}
                players = current.get("players") or []
                if len(players) > 1:
                    own_hand = players[own_index].get("hand") or []
                    scrapper_in_hand = any(
                        card.get("id") == TOOL_SCRAPPER_ID or card.get("name") == "Tool Scrapper"
                        for card in own_hand
                    )
                    visible_tools: list[str] = []
                    for zone in ("active", "bench"):
                        for pokemon in players[1 - own_index].get(zone, []) or []:
                            for tool in pokemon.get("tools", []) or []:
                                name = str(tool.get("name") or tool.get("id"))
                                opposing_tools[name] += 1
                                visible_tools.append(name)
                    if scrapper_in_hand and visible_tools:
                        scrapper_in_hand_with_opposing_tool = True
                        if HERO_CAPE_NAME in visible_tools or "Hero's Cape" in visible_tools:
                            hero_cape_and_scrapper_in_hand = True
                for log in visualization.get("logs", []) or []:
                    if (
                        log.get("playerIndex") == own_index
                        and log.get("cardId") == TOOL_SCRAPPER_ID
                        and log.get("type") == "MoveCard"
                        and log.get("fromArea") == 2
                        and log.get("toArea") == 3
                    ):
                        scrapper_events.add(
                            (
                                step_index,
                                log.get("serial"),
                                log.get("fromArea"),
                                log.get("toArea"),
                            )
                        )
    return MatchToolAudit(
        episode_id,
        outcome,
        len(scrapper_events),
        opposing_tools,
        scrapper_in_hand_with_opposing_tool,
        hero_cape_and_scrapper_in_hand,
    )


def render_markdown(audits: Iterable[SubmissionToolAudit]) -> str:
    """Render the audit as a concise Portuguese handoff report."""
    audits = list(audits)
    combined = combined_to_dict(audits)
    lines = [
        "# Tool Scrapper e ferramentas visíveis — três submissões mais recentes",
        "",
        "Definição: ferramenta ‘vista’ = ferramenta anexada a Pokémon do oponente "
        "em um estado público do replay. "
        "‘Uso’ = evento efetivo de Tool Scrapper saindo da nossa mão para o descarte.",
        "",
        "## Resumo agregado",
        "",
        f"- Partidas: **{combined['replay_count']}**",
        f"- Usos de Tool Scrapper: **{combined['tool_scrapper_uses']}** em "
        f"**{combined['matches_with_tool_scrapper']}** partidas; "
        f"sem uso: **{combined['matches_without_tool_scrapper']}**",
        f"- Scrapper na nossa mão enquanto havia ferramenta adversária visível: "
        f"**{combined['matches_with_tool_scrapper_in_hand_while_tool_visible']}** partidas",
        f"- Hero’s Cape no campo e Scrapper na nossa mão: "
        f"**{combined['matches_with_hero_cape_and_tool_scrapper_in_hand']}** partidas",
        "",
        "| Ferramenta adversária | Partidas com Scrapper | Partidas sem Scrapper | "
        "Ocorrências com | Ocorrências sem |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, values in combined["tools"].items():
        lines.append(
            f"| {name} | {values['seen_matches_with_scrapper']} | "
            f"{values['seen_matches_without_scrapper']} | "
            f"{values['seen_occurrences_with_scrapper']} | "
            f"{values['seen_occurrences_without_scrapper']} |"
        )
    lines.extend(["", "## Por submissão", ""])
    for audit in audits:
        data = audit_to_dict(audit)
        lines.extend(
            [
                f"### {audit.submission_id}",
                "",
                f"Partidas: **{audit.replay_count}** · "
                f"usos de Scrapper: **{audit.tool_scrapper_uses}** · "
                f"partidas com uso: **{len(audit.scrapper_matches)}** · "
                f"sem uso: **{audit.replay_count - len(audit.scrapper_matches)}**",
                "",
                "| Ferramenta | Com Scrapper (partidas) | Sem Scrapper (partidas) |",
                "|---|---:|---:|",
            ]
        )
        for name, values in data["tools"].items():
            lines.append(
                f"| {name} | {values['seen_matches_with_scrapper']} | "
                f"{values['seen_matches_without_scrapper']} |"
            )
        lines.extend(["", "Partidas com uso do Scrapper:"])
        used = [match for match in audit.matches if match.used_tool_scrapper]
        lines.extend(
            f"- `{match.episode_id}` ({match.outcome}), {match.tool_scrapper_uses} uso(s); "
            f"ferramentas vistas: {', '.join(sorted(match.opposing_tools)) or 'nenhuma'}"
            for match in used
        )
        if not used:
            lines.append("- nenhuma")
        overlap = [match for match in audit.matches if match.hero_cape_and_scrapper_in_hand]
        lines.extend(["", "Hero’s Cape no campo com Tool Scrapper na mão:"])
        lines.extend(
            f"- `{match.episode_id}` ({match.outcome}) — Scrapper usado depois: "
            f"{'sim' if match.used_tool_scrapper else 'não'}"
            for match in overlap
        )
        if not overlap:
            lines.append("- nenhuma")
        lines.append("")
    return "\n".join(lines)
