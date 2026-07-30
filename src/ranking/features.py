"""Leakage-safe, backend-independent selection feature extraction."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from hashlib import sha256
from pathlib import Path
from typing import Any, Protocol

from src.core import (
    Candidate,
    DeckProfile,
    FeatureSchema,
    GameState,
    OptionType,
    ParsedDecision,
    PrizeCheckMode,
    PrizeCheckResult,
    Selection,
    SelectionFeatures,
)

FEATURE_SCHEMA_VERSION = "selection-ranking-v1"
_OPTION_FEATURES = tuple(f"selected_{item.value.casefold()}_count" for item in OptionType)
_REASON_FEATURES = (
    "reason_win_now",
    "reason_efficient_attack",
    "reason_ko_threat",
    "reason_useful_evolution",
    "reason_attack_enabling_energy",
    "reason_bench_development",
    "reason_draw_search",
    "reason_resource_preservation",
    "reason_wasted_energy",
    "reason_key_piece_discard",
    "reason_pointless_evolution",
    "reason_blocked_bench",
    "reason_premature_end",
)
_BASE_FEATURES = (
    "select_type_code",
    "select_context_code",
    "selection_size",
    *_OPTION_FEATURES,
    "heuristic_score",
    *_REASON_FEATURES,
    "attack_available",
    "selected_attack_damage",
    "selected_ko_signal",
    "selected_prize_swing",
    "selected_bench_development",
    "selected_evolution",
    "selected_second_attacker",
    "selected_energy_enabled",
    "selected_energy_wasted",
    "selected_energy_preserved",
    "own_hand_count",
    "own_deck_count",
    "own_bench_count",
    "own_prize_count",
    "opponent_bench_count",
    "opponent_prize_count",
    "selected_rule_box_count",
    "selected_base_prize_value",
    "prize_map_rule_box_targets",
    "deck_out_risk",
    "turn",
    "your_index",
    "is_first_player",
    "is_setup",
    "turn_action_count",
    "supporter_available",
    "energy_attachment_available",
    "selected_declared_role",
    "availability_confirmed",
    "availability_probabilistic",
    "fallback_indicator",
    "unknown_metadata_count",
    "missing_feature_count",
)

FEATURE_SCHEMA = FeatureSchema(
    version=FEATURE_SCHEMA_VERSION,
    names=_BASE_FEATURES,
    groups={
        "decision": _BASE_FEATURES[:3],
        "options": _OPTION_FEATURES,
        "heuristic": ("heuristic_score", *_REASON_FEATURES),
        "state": (
            "own_hand_count",
            "own_deck_count",
            "own_bench_count",
            "own_prize_count",
            "opponent_bench_count",
            "opponent_prize_count",
            "turn",
            "your_index",
            "is_first_player",
            "is_setup",
        ),
        "quality": (
            "fallback_indicator",
            "unknown_metadata_count",
            "missing_feature_count",
        ),
    },
)


class _Scorer(Protocol):
    def score(
        self,
        state: GameState,
        selection: Selection,
        candidates: Sequence[Candidate] | None = None,
    ) -> tuple[float, list[str]]: ...


class SelectionFeatureExtractor:
    """Create the same ordered, factual feature vector for every ranker."""

    def __init__(self, scorer: _Scorer) -> None:
        self._scorer = scorer

    def extract(
        self,
        decision: ParsedDecision,
        selections: Sequence[Selection],
        *,
        deck_profile: DeckProfile | None = None,
        prize_check: PrizeCheckResult | None = None,
    ) -> list[SelectionFeatures]:
        """Extract one immutable feature row per legal selection.

        Args:
            decision: Parsed actor-visible decision.
            selections: Legal selections with original simulator indices.
            deck_profile: Optional declarative own-deck roles.
            prize_check: Optional own-card availability inference with confidence.

        Returns:
            Feature rows in the same order as ``selections``.
        """
        return [
            self._extract_one(decision, selection, deck_profile, prize_check)
            for selection in selections
        ]

    def _extract_one(
        self,
        decision: ParsedDecision,
        selection: Selection,
        deck_profile: DeckProfile | None,
        prize_check: PrizeCheckResult | None,
    ) -> SelectionFeatures:
        state = decision.state
        candidates = {candidate.option_index: candidate for candidate in decision.candidates}
        selected = [candidates[index] for index in selection.indices if index in candidates]
        option_counts = Counter(item.option_type for item in selected)
        score, reasons = self._scorer.score(state, selection, decision.candidates)
        reason_set = set(reasons)
        own, opponent = _players(state)
        select_types = list(type(decision.select_type)) if decision.select_type is not None else []
        contexts = (
            list(type(decision.select_context)) if decision.select_context is not None else []
        )
        selected_card_ids = [
            int(item.features.get("card_id", 0))
            for item in selected
            if _numeric(item.features.get("card_id", 0)) > 0
        ]
        known_metadata = sum(
            int(bool(item.features.get("has_card_metadata")))
            + int(bool(item.features.get("has_attack_metadata")))
            for item in selected
        )
        expected_metadata = sum(
            int(item.option_type in {OptionType.PLAY, OptionType.CARD, OptionType.EVOLVE})
            + int(item.option_type is OptionType.ATTACK)
            for item in selected
        )
        availability_confirmed, availability_probabilistic = _availability(
            selected_card_ids, prize_check
        )
        values: dict[str, float] = {
            "select_type_code": float(
                select_types.index(decision.select_type) + 1
                if decision.select_type in select_types
                else 0
            ),
            "select_context_code": float(
                contexts.index(decision.select_context) + 1
                if decision.select_context in contexts
                else 0
            ),
            "selection_size": float(len(selection.indices)),
            **{
                f"selected_{option_type.value.casefold()}_count": float(option_counts[option_type])
                for option_type in OptionType
            },
            "heuristic_score": float(score),
            **{
                feature: float(feature.removeprefix("reason_") in reason_set)
                for feature in _REASON_FEATURES
            },
            "attack_available": float(
                any(item.option_type is OptionType.ATTACK for item in decision.candidates)
            ),
            "selected_attack_damage": sum(
                _first_numeric(item.option, "damage", "expectedDamage")
                or _first_numeric(item.attack or {}, "damage")
                for item in selected
            ),
            "selected_ko_signal": float(
                any(_truthy(item.option, "ko", "knockout", "isKo") for item in selected)
            ),
            "selected_prize_swing": sum(
                _numeric(item.features.get("target_base_prize_value", 0)) for item in selected
            ),
            "selected_bench_development": float(
                "develop_bench" in reason_set or "bench_development" in reason_set
            ),
            "selected_evolution": float(
                any(item.option_type is OptionType.EVOLVE for item in selected)
            ),
            "selected_second_attacker": float(
                any(
                    bool(item.features.get("target_is_active")) is False
                    and item.option_type in {OptionType.ATTACH, OptionType.EVOLVE}
                    for item in selected
                )
            ),
            "selected_energy_enabled": float("attack_enabling_energy" in reason_set),
            "selected_energy_wasted": float("wasted_energy" in reason_set),
            "selected_energy_preserved": float("resource_preservation" in reason_set),
            "own_hand_count": float(own.hand_count if own else 0),
            "own_deck_count": float(own.deck_count if own else 0),
            "own_bench_count": float(_bench_count(own)),
            "own_prize_count": float(len(own.prize) if own else 0),
            "opponent_bench_count": float(_bench_count(opponent)),
            "opponent_prize_count": float(len(opponent.prize) if opponent else 0),
            "selected_rule_box_count": sum(
                float(bool(item.features.get("card_has_rule_box"))) for item in selected
            ),
            "selected_base_prize_value": sum(
                _numeric(item.features.get("card_base_prize_value", 0)) for item in selected
            ),
            "prize_map_rule_box_targets": float(
                sum(
                    int(bool(item.features.get("target_has_rule_box")))
                    for item in decision.candidates
                )
            ),
            "deck_out_risk": float(bool(own and own.deck_count <= 3)),
            "turn": float(state.turn),
            "your_index": float(state.your_index),
            "is_first_player": float(state.your_index == state.first_player),
            "is_setup": float(
                decision.select_context is not None
                and decision.select_context.value.startswith("SETUP_")
            ),
            "turn_action_count": float(state.turn_action_count),
            "supporter_available": float(not state.supporter_played),
            "energy_attachment_available": float(not state.energy_attached),
            "selected_declared_role": float(
                _selected_has_declared_role(selected_card_ids, deck_profile)
            ),
            "availability_confirmed": availability_confirmed,
            "availability_probabilistic": availability_probabilistic,
            "fallback_indicator": 0.0,
            "unknown_metadata_count": float(max(0, expected_metadata - known_metadata)),
            "missing_feature_count": float(
                int(not state.players) + int(decision.select_type is None)
            ),
        }
        ordered = tuple(float(values[name]) for name in FEATURE_SCHEMA.names)
        return SelectionFeatures(
            selection=selection,
            schema_version=FEATURE_SCHEMA.version,
            values=ordered,
            heuristic_score=float(score),
            heuristic_reasons=tuple(reasons),
        )


def feature_schema_sha256(schema: FeatureSchema = FEATURE_SCHEMA) -> str:
    """Return the stable SHA-256 of a feature schema.

    Args:
        schema: Feature schema to hash.

    Returns:
        Lowercase hexadecimal SHA-256.
    """
    payload = json.dumps(schema.to_dict(), sort_keys=True, separators=(",", ":")).encode()
    return sha256(payload).hexdigest()


def write_feature_schema(path: str | Path, schema: FeatureSchema = FEATURE_SCHEMA) -> Path:
    """Write a canonical feature schema JSON artifact.

    Args:
        path: Destination JSON path.
        schema: Schema to serialize.

    Returns:
        Written path.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(schema.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return destination


def _players(state: GameState) -> tuple[Any, Any]:
    if not state.players:
        return None, None
    own_index = state.your_index if 0 <= state.your_index < len(state.players) else 0
    opponent_index = 1 - own_index if len(state.players) == 2 else -1
    own = state.players[own_index]
    opponent = state.players[opponent_index] if opponent_index >= 0 else None
    return own, opponent


def _bench_count(player: Any) -> int:
    return sum(item is not None for item in player.bench) if player else 0


def _numeric(value: Any) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0


def _first_numeric(mapping: Mapping[str, Any], *names: str) -> float:
    for name in names:
        value = _numeric(mapping.get(name))
        if value:
            return value
    return 0.0


def _truthy(mapping: Mapping[str, Any], *names: str) -> bool:
    return any(bool(mapping.get(name)) for name in names)


def _selected_has_declared_role(
    selected_card_ids: Sequence[int], deck_profile: DeckProfile | None
) -> bool:
    if deck_profile is None:
        return False
    role_cards = {
        int(card_id)
        for card_ids in deck_profile.roles.values()
        for card_id in card_ids
        if isinstance(card_id, int)
    }
    return bool(role_cards.intersection(selected_card_ids))


def _availability(
    selected_card_ids: Sequence[int], prize_check: PrizeCheckResult | None
) -> tuple[float, float]:
    if not selected_card_ids or prize_check is None:
        return 0.0, 0.0
    confirmed = prize_check.mode is PrizeCheckMode.EXACT
    probabilistic = prize_check.mode is PrizeCheckMode.PROBABILISTIC
    available = [
        prize_check.availability(card_id)
        for card_id in selected_card_ids
        if prize_check.availability(card_id) is not None
    ]
    return float(confirmed and bool(available)), float(probabilistic and bool(available))
