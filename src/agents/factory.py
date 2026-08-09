"""Single source of truth for agent modes, deck assets, and runtime models."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from src.agents.baseline import BaselineAgent
from src.agents.hdi import HdiAgent
from src.agents.heuristic import HeuristicAgent
from src.core import AgentPolicy, DeckProfile, SelectionRanker

SUPPORTED_AGENT_MODES = frozenset(
    {
        "baseline",
        "heuristic",
        "expert_turn_loop",
        "hdi_v1",
        "hybrid",
        "rfl",
        "xgboost_ranker",
        "lightgbm_ranker",
    }
)


def normalize_agent_mode(mode: str | None) -> str:
    """Validate and normalize one configured agent mode.

    Args:
        mode: Raw configuration or environment value.

    Returns:
        Canonical supported mode.

    Raises:
        ValueError: If the mode is not explicitly supported.
    """
    normalized = (mode or "heuristic").strip().casefold()
    aliases = {
        "xgboost": "xgboost_ranker",
        "lightgbm": "lightgbm_ranker",
        "honchkrow_porygon": "expert_turn_loop",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in SUPPORTED_AGENT_MODES:
        raise ValueError(f"unsupported agent mode: {mode}")
    return normalized


def load_deck(root: str | Path, mode: str | None = None) -> list[int]:
    """Load the canonical 60-card deck from a repository or package root.

    Args:
        root: Repository or extracted package root.
        mode: Optional policy mode used to select a mode-specific deck.

    Returns:
        Ordered positive card identifiers.
    """
    project_root = Path(root)
    normalized = (mode or "").strip().casefold() or None
    if normalized == "honchkrow_porygon":
        normalized = "expert_turn_loop"
    if normalized == "expert_turn_loop":
        deck_path = project_root / "src" / "artifacts" / "deck_team_rocket_murkrow.csv"
        if not deck_path.is_file():
            deck_path = project_root / "deck.csv"
    else:
        deck_path = project_root / "src" / "artifacts" / "deck.csv"
    if not deck_path.is_file():
        deck_path = project_root / "deck.csv"
    cards = [line.strip() for line in deck_path.read_text(encoding="utf-8").splitlines()]
    if len(cards) != 60:
        raise ValueError(f"deck has {len(cards)} cards, expected 60")
    deck = [int(card) for card in cards]
    if any(card <= 0 for card in deck):
        raise ValueError("deck card identifiers must be positive integers")
    return deck


def load_deck_profile(root: str | Path, mode: str | None = None) -> DeckProfile | None:
    """Load the optional declarative profile associated with the active deck.

    Args:
        root: Repository or extracted package root.
        mode: Optional policy mode used to select a mode-specific profile.

    Returns:
        Valid deck profile or ``None`` when no compatible asset is present.
    """
    project_root = Path(root)
    normalized = (mode or "").strip().casefold() or None
    if normalized == "honchkrow_porygon":
        normalized = "expert_turn_loop"
    profile_name = (
        "deck_profile_honchkrow_porygon.json"
        if normalized == "expert_turn_loop"
        else "deck_profile.json"
    )
    path = project_root / "src" / "artifacts" / profile_name
    if not path.is_file() and normalized == "expert_turn_loop":
        path = project_root / "src" / "artifacts" / "deck_profile.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return DeckProfile.from_dict(data) if isinstance(data, Mapping) else None
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None


def build_agent(
    mode: str | None = None,
    *,
    root: str | Path = ".",
    model_dir: str | Path | None = None,
) -> AgentPolicy:
    """Build any runtime policy from shared assets and strict mode semantics.

    Args:
        mode: Canonical mode or supported short alias.
        root: Repository or extracted package root.
        model_dir: Optional learned-model directory override.

    Returns:
        Configured policy.

    Raises:
        RuntimeError: If a learned backend or compatible model is unavailable.
        ValueError: If the requested mode is unsupported.
    """
    normalized = normalize_agent_mode(mode or os.environ.get("AGENT_MODE"))
    project_root = Path(root)
    profile = load_deck_profile(project_root, normalized)
    weights, feature_flags = _heuristic_config(project_root)
    if normalized == "baseline":
        return BaselineAgent()
    if normalized == "hdi_v1":
        return HdiAgent(profile)
    if normalized == "expert_turn_loop":
        from src.agents.honchkrow_porygon import HonchkrowPorygonAgent

        if profile is None:
            raise ValueError("expert_turn_loop requires the Honchkrow/Porygon deck profile")
        return HonchkrowPorygonAgent(profile, "expert_turn_loop")
    heuristic = HeuristicAgent(weights, feature_flags, profile)
    if normalized == "heuristic":
        return heuristic
    if normalized == "hybrid":
        from src.agents.search import HybridAgent

        return cast(AgentPolicy, HybridAgent(heuristic))
    if normalized == "rfl":
        from src.rfl.profiles import agent_from_profile

        profile_path = Path(
            os.environ.get(
                "AGENT_PROFILE",
                project_root
                / "configs"
                / "decks"
                / "mega_abomasnow_kyogre"
                / "heuristic_rfl_0001.yaml",
            )
        )
        deck_path = _deck_path(project_root)
        return agent_from_profile(
            profile_path,
            active_deck_id="mega_abomasnow_kyogre",
            active_deck_path=deck_path,
        )

    resolved_model_dir = Path(
        model_dir or os.environ.get("RANKER_MODEL_DIR", "") or project_root / "model"
    )
    if normalized == "xgboost_ranker":
        from src.ranking.rankers import XGBoostSelectionRanker

        ranker: SelectionRanker = XGBoostSelectionRanker(resolved_model_dir)
    else:
        from src.ranking.rankers import LightGBMSelectionRanker

        ranker = LightGBMSelectionRanker(resolved_model_dir)
    return HeuristicAgent(weights, feature_flags, profile, ranker=ranker)


def _deck_path(root: Path) -> Path:
    packaged = root / "deck.csv"
    return packaged if packaged.is_file() else root / "src" / "artifacts" / "deck.csv"


def _heuristic_config(root: Path) -> tuple[Mapping[str, Any] | None, Mapping[str, Any] | None]:
    config_path = root / "configs" / "agent_heuristic.yaml"
    if not config_path.is_file():
        return None, None
    try:
        from src.config.loader import ConfigLoader

        config = ConfigLoader(root / "configs").load("agent_heuristic")
    except (ImportError, OSError, TypeError, ValueError):
        return None, None
    return config.extra.get("weights"), config.extra.get("feature_flags")
