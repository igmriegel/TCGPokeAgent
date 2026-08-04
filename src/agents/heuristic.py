from __future__ import annotations

import math
import time
from collections.abc import Mapping, Sequence
from dataclasses import replace
from enum import StrEnum
from typing import Any

from src.core import (
    AgentPolicy,
    AttackPlan,
    Candidate,
    CardCatalog,
    DeckDefinition,
    DeckProfile,
    DefaultParser,
    DefaultSelectionGenerator,
    GameState,
    GenericDeckProfileBuilder,
    HeuristicScorer,
    OptionType,
    PolicyDecision,
    PrizeChecker,
    PrizeCheckMode,
    PrizeCheckResult,
    PrizeMap,
    PrizeMapBuilder,
    SelectContext,
    Selection,
    SelectionRanker,
)
from src.ranking.features import SelectionFeatureExtractor
from src.ranking.rankers import HeuristicSelectionRanker

WEIGHTS: dict[str, float] = {
    "win_now": 100.0,
    "efficient_attack": 10.0,
    "useful_evolution": 8.0,
    "attack_enabling_energy": 6.0,
    "bench_development": 4.0,
    "draw_search": 5.0,
    "resource_preservation": 3.0,
    "safe_end_turn": 2.0,
    "wasted_energy": -5.0,
    "key_piece_discard": -8.0,
    "pointless_evolution": -6.0,
    "blocked_bench": -4.0,
    "premature_end": -10.0,
}

GUARANTEED_KO_BONUS = 200.0
ARTICUNO_CARD_ID = 414
FEZANDIPITI_CARD_ID = 140
ABRA_CARD_ID = 741
KADABRA_CARD_ID = 742
ALAKAZAM_CARD_ID = 743
KYOGRE_CARD_ID = 721
SNOVER_CARD_ID = 722
ABOMASNOW_CARD_ID = 723
LILLIE_CARD_ID = 1227
ULTRA_BALL_CARD_ID = 1121
MEGA_SIGNAL_CARD_ID = 1145
PETREL_CARD_ID = 1219
HAMMERLANCHE_ATTACK_ID = 1046


class DecisionPhase(StrEnum):
    """Priority phase used to sequence MAIN-turn decisions."""

    EVOLVE = "EVOLVE"
    ATTACH_PRIORITY = "ATTACH_PRIORITY"
    ATTACK_PRIORITY = "ATTACK_PRIORITY"
    PLAY_POKEMON = "PLAY_POKEMON"
    ATTACH_OPEN = "ATTACH_OPEN"
    PLAY_ITEMS = "PLAY_ITEMS"
    PLAY_SUPPORTER = "PLAY_SUPPORTER"
    ATTACK = "ATTACK"
    ATTACH_FULL = "ATTACH_FULL"
    UTILITY = "UTILITY"
    RETREAT = "RETREAT"
    END = "END"


_MAIN_PHASE_ORDER = (
    DecisionPhase.EVOLVE,
    DecisionPhase.ATTACH_PRIORITY,
    DecisionPhase.ATTACK_PRIORITY,
    DecisionPhase.PLAY_POKEMON,
    DecisionPhase.ATTACH_OPEN,
    DecisionPhase.PLAY_ITEMS,
    DecisionPhase.PLAY_SUPPORTER,
    DecisionPhase.ATTACH_FULL,
    DecisionPhase.UTILITY,
    DecisionPhase.RETREAT,
    DecisionPhase.ATTACK,
    DecisionPhase.END,
)
_MAIN_PHASE_RANK = {phase: index for index, phase in enumerate(_MAIN_PHASE_ORDER)}

FEATURE_FLAGS = {
    "use_attack_signals",
    "use_resource_signals",
    "use_setup_signals",
}

_CG_CATALOG = CardCatalog.from_cg()


def _validated_weights(weights: Mapping[str, Any] | None) -> dict[str, float]:
    """Validate and merge a caller-provided weight profile."""
    result = dict(WEIGHTS)
    for name, value in (weights or {}).items():
        if name not in WEIGHTS:
            raise ValueError(f"unknown heuristic weight: {name}")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"heuristic weight {name!r} must be numeric")
        result[name] = float(value)
    return result


def _validated_flags(flags: Mapping[str, Any] | None) -> dict[str, bool]:
    """Validate feature switches and fill enabled defaults."""
    result = {name: True for name in FEATURE_FLAGS}
    for name, value in (flags or {}).items():
        if name not in FEATURE_FLAGS:
            raise ValueError(f"unknown heuristic feature flag: {name}")
        if not isinstance(value, bool):
            raise ValueError(f"heuristic feature flag {name!r} must be boolean")
        result[name] = value
    return result


class SimpleHeuristicScorer(HeuristicScorer):
    """Score legal selections using deterministic, auditable option signals."""

    def __init__(
        self,
        weights: Mapping[str, Any] | None = None,
        feature_flags: Mapping[str, Any] | None = None,
        deck_profile: DeckProfile | None = None,
        catalog: CardCatalog | None = None,
    ) -> None:
        self.weights = _validated_weights(weights)
        self.feature_flags = _validated_flags(feature_flags)
        self.deck_profile = deck_profile
        self.catalog = catalog or _CG_CATALOG
        self.prize_check: PrizeCheckResult | None = None
        self.prize_map: PrizeMap | None = None
        self.alakazam_matchup_confirmed = False
        self._energy_context_state: GameState | None = None
        self.water_energy_in_discard = 0

    def set_deck_profile(self, profile: DeckProfile) -> None:
        """Replace the declarative deck strategy for a new match."""
        self.deck_profile = profile

    def set_strategic_context(
        self,
        prize_check: PrizeCheckResult | None,
        prize_map: PrizeMap | None,
    ) -> None:
        """Set match-scoped Prize knowledge used for the current decision."""
        self.prize_check = prize_check
        self.prize_map = prize_map

    def set_alakazam_matchup_confirmed(self, confirmed: bool = True) -> None:
        """Persist public confirmation of the Alakazam matchup."""
        self.alakazam_matchup_confirmed = confirmed

    def set_energy_context(self, state: GameState) -> None:
        """Cache visible Energy resources for the current decision cycle."""
        self._energy_context_state = state
        self.water_energy_in_discard = self._count_basic_energy_cards(
            self._own_player(state).discard if self._own_player(state) else None
        )

    def _alakazam_matchup_active(self, state: GameState) -> bool:
        """Return whether the matchup is confirmed now or in an earlier prompt."""
        return self.alakazam_matchup_confirmed or self._opponent_visible_alakazam_line(state)

    def _fezandipiti_line_active(self, state: GameState) -> bool:
        """Return whether an Alakazam matchup has exposed an energized Fezandipiti."""
        if not self._alakazam_matchup_active(state):
            return False
        opponent = self._opponent_player(state)
        if opponent is None:
            return False
        return any(
            pokemon is not None
            and pokemon.card_id == FEZANDIPITI_CARD_ID
            and bool(pokemon.energies)
            for pokemon in [opponent.active, *opponent.bench]
        )

    def _fezandipiti_active_hp(self, state: GameState) -> int:
        """Return the remaining HP of the opposing Active Fezandipiti."""
        opponent = self._opponent_player(state)
        active = opponent.active if opponent is not None else None
        if active is None or active.card_id != FEZANDIPITI_CARD_ID:
            return 0
        return max(0, int(active.hp))

    def _kyogre_riptide_guarantees_fezandipiti_ko(self, state: GameState) -> bool:
        """Return whether discarded Water Energy makes Riptide lethal now."""
        hp = self._fezandipiti_active_hp(state)
        return hp > 0 and self.water_energy_in_discard * 20 >= hp

    def _special_evolution_allowed(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether the special matchup permits a Snover evolution."""
        if not self._fezandipiti_line_active(state):
            return True
        target_id = self._feature_int(candidate, "target_card_id")
        if (
            target_id != SNOVER_CARD_ID
            and self._feature_int(candidate, "card_id") != ABOMASNOW_CARD_ID
        ):
            return True
        active = self._own_active(state)
        if active is None or active.card_id != SNOVER_CARD_ID:
            return False
        energy_count = len(active.energies)
        if energy_count >= 2:
            return True
        if state.energy_attached:
            return False
        return bool(self._can_attach_to_active(state, SNOVER_CARD_ID))

    def _can_attach_to_active(self, state: GameState, card_id: int) -> bool:
        """Return whether the current state can complete Hammer-lanche setup."""
        active = self._own_active(state)
        return bool(active and active.card_id == card_id and len(active.energies) + 1 >= 2)

    def score(
        self,
        state: GameState,
        selection: Selection,
        candidates: Sequence[Candidate] | None = None,
    ) -> tuple[float, list[str]]:
        """Return a weighted score and stable reason codes for a selection."""
        by_index = {candidate.option_index: candidate for candidate in candidates or ()}
        selected = [by_index[index] for index in selection.indices if index in by_index]
        if not selected:
            return 0.0, ["no_signal"]

        score = 0.0
        reasons: list[str] = []
        for candidate in selected:
            option = candidate.option
            context = selection.context.value if selection.context else ""
            is_attack = candidate.option_type.value == "ATTACK" or "ATTACK" in context
            is_energy = candidate.option_type.value in {"ENERGY", "ENERGY_CARD"}
            is_end = candidate.option_type.value == "END"
            sdk_score, sdk_reasons = self._sdk_score(state, candidate, selection.context)
            score += sdk_score
            reasons.extend(sdk_reasons)

            if self._truthy(option, "win", "wins", "isWin", "gameOver"):
                score += self.weights["win_now"] * 100.0
                reasons.append("win_now")
            if self.feature_flags["use_attack_signals"] and is_attack:
                damage = self._number(option, "damage", "expectedDamage", "value")
                cost = max(1.0, self._number(option, "cost", "energyCost"))
                if damage > 0:
                    score += self.weights["efficient_attack"] * min(1.0, damage / cost)
                    reasons.append("efficient_attack")
                if self._truthy(option, "ko", "knockout", "isKo"):
                    score += self.weights["win_now"] * 0.5
                    reasons.append("ko_threat")
            if self._truthy(option, "evolve", "isEvolution") or "EVOLVE" in context:
                if self._truthy(option, "useful", "enablesAttack", "survivalGain"):
                    score += self.weights["useful_evolution"]
                    reasons.append("useful_evolution")
                else:
                    score += self.weights["pointless_evolution"]
                    reasons.append("pointless_evolution")
            if self.feature_flags["use_attack_signals"] and is_energy:
                count = self._number(option, "count", "energyCount")
                if self._truthy(option, "enablesAttack", "enables"):
                    score += self.weights["attack_enabling_energy"]
                    reasons.append("attack_enabling_energy")
                elif count > 1 or self._truthy(option, "wasted", "waste"):
                    score += self.weights["wasted_energy"]
                    reasons.append("wasted_energy")
            if self.feature_flags["use_setup_signals"] and self._truthy(
                option, "bench", "developBench", "setup"
            ):
                score += self.weights["bench_development"]
                reasons.append("bench_development")
            if self._truthy(option, "draw", "search", "drawSearch"):
                score += self.weights["draw_search"]
                reasons.append("draw_search")
            if self.feature_flags["use_resource_signals"]:
                if self._truthy(option, "preserve", "preservesKeyPiece"):
                    score += self.weights["resource_preservation"]
                    reasons.append("resource_preservation")
                if self._truthy(option, "keyPiece", "keyCard") or (
                    candidate.option_type.value == "DISCARD" and self._truthy(option, "rare")
                ):
                    score += self.weights["key_piece_discard"]
                    reasons.append("key_piece_discard")
            if is_end:
                if state.turn_action_count == 0 or self._truthy(option, "premature"):
                    score += self.weights["premature_end"]
                    reasons.append("premature_end")
                else:
                    score += self.weights["safe_end_turn"]
                    reasons.append("safe_end_turn")
            if self._truthy(option, "blockedBench", "benchFull"):
                score += self.weights["blocked_bench"]
                reasons.append("blocked_bench")

        return score, list(dict.fromkeys(reasons)) or ["no_signal"]

    def _sdk_score(
        self,
        state: GameState,
        candidate: Candidate,
        context: SelectContext | None,
    ) -> tuple[float, list[str]]:
        option_type = candidate.option_type
        if context is SelectContext.MAIN:
            return self._main_action_score(state, candidate)
        if option_type is OptionType.NUMBER:
            number = self._number(candidate.option, "number")
            return number * 10.0, ["prefer_larger_count"]
        if option_type in {OptionType.YES, OptionType.NO}:
            prefer_yes = context is not SelectContext.MULLIGAN
            preferred = (
                option_type is OptionType.YES if prefer_yes else option_type is OptionType.NO
            )
            return (20.0 if preferred else 0.0), ["prefer_yes" if prefer_yes else "avoid_mulligan"]
        if option_type is OptionType.CARD:
            return self._card_selection_score(state, candidate, context)
        if option_type is OptionType.ATTACK:
            return self._attack_score(state, candidate)
        if option_type is OptionType.RETREAT:
            return self._retreat_score(state, candidate)
        if option_type in {OptionType.ENERGY, OptionType.ENERGY_CARD}:
            if context is None:
                return 0.0, []
            count = max(1.0, self._number(candidate.option, "count"))
            return count * 10.0, ["satisfy_energy_cost"]
        return 0.0, []

    def _main_action_score(self, state: GameState, candidate: Candidate) -> tuple[float, list[str]]:
        option_type = candidate.option_type
        if option_type is OptionType.END:
            return -1000.0, ["end_only_after_productive_actions"]
        if option_type is OptionType.EVOLVE:
            energy = self._feature_int(candidate, "target_energy_count")
            return 500.0 + energy * 10.0, ["evolve_attacker"]
        if option_type is OptionType.ABILITY:
            return 450.0, ["use_available_ability"]
        if option_type is OptionType.ATTACH:
            return self._attachment_score(state, candidate)
        if option_type is OptionType.PLAY:
            return self._play_score(state, candidate)
        if option_type is OptionType.ATTACK:
            return self._attack_score(state, candidate)
        if option_type is OptionType.RETREAT:
            return self._retreat_score(state, candidate)
        if option_type is OptionType.DISCARD:
            return 20.0, ["resolve_discard_action"]
        return 1.0, ["productive_legal_action"]

    def _attachment_score(self, state: GameState, candidate: Candidate) -> tuple[float, list[str]]:
        card_type = self._metadata_int(candidate.card, "cardType")
        target_id = self._feature_int(candidate, "target_card_id")
        energy_count = self._feature_int(candidate, "target_energy_count")
        if card_type == 2:
            return 300.0, ["attach_useful_tool"]
        if card_type in {5, 6}:
            if energy_count >= self._attack_energy_target(target_id):
                return -1500.0, ["energy_above_attack_cost"]
            if (
                bool(candidate.features.get("target_is_active", False))
                and self._own_active_card_id(state) == ARTICUNO_CARD_ID
                and not self._alakazam_matchup_active(state)
            ):
                return -2000.0, ["sacrificial_articuno"]
            target_goal = self._attack_energy_target(target_id)
            deficit = max(0, target_goal - energy_count)
            active_bonus = 30.0 if bool(candidate.features.get("target_is_active", False)) else 0.0
            if active_bonus and energy_count + 1 >= target_goal:
                active_bonus += 80.0
            if bool(candidate.features.get("target_is_active", False)):
                active_card_id = self._own_active_card_id(state)
                if active_card_id == KYOGRE_CARD_ID and self._kyogre_riptide_line_ready(state):
                    active_bonus -= 40.0
                if active_card_id == ARTICUNO_CARD_ID and self._opponent_visible_abra(state):
                    active_bonus += 80.0
            if self._alakazam_matchup_active(state) and target_id == ARTICUNO_CARD_ID:
                active_bonus += 300.0
            return 350.0 + deficit * 25.0 + active_bonus, ["develop_attacker_energy"]
        return 100.0, ["attach_unrecognized_card"]

    def _play_score(self, state: GameState, candidate: Candidate) -> tuple[float, list[str]]:
        card_id = self._feature_int(candidate, "card_id")
        card_type = self._metadata_int(candidate.card, "cardType")
        if card_type == 0:
            if self._fezandipiti_line_active(state):
                if card_id == KYOGRE_CARD_ID:
                    return 620.0, ["fezandipiti_threat", "bench_kyogre_first"]
                if card_id == SNOVER_CARD_ID:
                    return 180.0, ["fezandipiti_threat", "hold_snover_until_needed"]
            if card_id == ARTICUNO_CARD_ID and not self._alakazam_matchup_active(state):
                return -2000.0, ["avoid_articuno_without_matchup_evidence"]
            if card_id == ARTICUNO_CARD_ID and self._alakazam_matchup_active(state):
                return 520.0, ["tech_matchup_articuno"]
            if card_id == KYOGRE_CARD_ID and self._kyogre_is_valuable(state):
                return 480.0, ["sacrificial_kyogre"]
            if self._has_role(card_id, "development_priority"):
                bonus = 100.0
            elif self._has_role(card_id, "evolution_basic"):
                bonus = 30.0
            else:
                bonus = 20.0
            return 300.0 + bonus, [
                "develop_bench",
                "play_available_pokemon_before_attack",
            ]
        if card_type == 1 and self._has_search_role(card_id):
            if card_id == MEGA_SIGNAL_CARD_ID:
                bonus = 120.0 if self._needs_evolution_search(state) else -20.0
                return 340.0 + bonus, ["play_search_card", "search_evolution_line"]
            if card_id == ULTRA_BALL_CARD_ID:
                bonus = 90.0 if self._needs_pokemon_search(state) else 0.0
                return 340.0 + bonus, ["play_search_card", "search_pokemon_line"]
            return 320.0, ["play_search_card"]
        if card_type == 1:
            return 240.0, ["play_item"]
        if card_type == 2:
            return 280.0, ["attach_tool"]
        if card_type == 3 and self._has_search_role(card_id):
            if card_id == PETREL_CARD_ID:
                if self._lillie_is_useful(state) and self._card_in_hand(state, LILLIE_CARD_ID):
                    return -1500.0, ["play_lillie_before_redundant_petrel"]
                bonus = 90.0 if self._needs_evolution_search(state) else 35.0
                if self._needs_pokemon_search(state):
                    bonus += 35.0
                if self._lillie_is_useful(state):
                    bonus -= 50.0
                return 220.0 + bonus, ["play_supporter_search"]
            if card_id == LILLIE_CARD_ID:
                bonus = 90.0 if self._lillie_is_useful(state) else -60.0
                return 220.0 + bonus, ["play_supporter_search"]
            return 230.0, ["play_supporter_search"]
        if card_type == 3:
            return 210.0, ["play_supporter"]
        if card_type == 4:
            return 180.0, ["play_stadium"]
        return 150.0, ["play_known_legal_card"]

    def _has_search_role(self, card_id: int) -> bool:
        return any(
            self._has_role(card_id, role)
            for role in (
                "evolution_search",
                "general_search",
                "trainer_search",
                "hand_refresh",
                "pokemon_search",
            )
        )

    def _attack_score(self, state: GameState, candidate: Candidate) -> tuple[float, list[str]]:
        active_target = next(
            (
                target
                for target in (self.prize_map.targets if self.prize_map else ())
                if target.zone == "active"
            ),
            None,
        )
        if active_target and active_target.damage_prevented:
            return -1000.0, ["attack_damage_prevented"]
        damage = float(self._metadata_int(candidate.attack, "damage"))
        text = str((candidate.attack or {}).get("text", "")).casefold()
        if "damage for each basic" in text and "discard pile" in text:
            energy_type = self._attack_energy_type(candidate)
            multiplier = self._leading_damage_multiplier(text)
            damage = multiplier * self._discard_basic_energy_count(state, energy_type)
        elif "discard the top 6 cards" in text and "100 damage for each basic" in text:
            damage = self._hammerlanche_assessment(state, candidate)["expected_damage"]
        score = 200.0 + max(0, damage)
        if damage <= 0:
            score -= 80.0
        reasons = ["attack_for_damage"]
        guaranteed = self._guaranteed_attack_damage(state, candidate)
        opponent_hp = self._opponent_active_hp(state)
        if opponent_hp > 0 and guaranteed >= opponent_hp:
            score += GUARANTEED_KO_BONUS
            reasons.append("guaranteed_ko")
        if self._is_hammerlanche(candidate):
            assessment = self._hammerlanche_assessment(state, candidate)
            score += GUARANTEED_KO_BONUS * assessment["ko_probability"]
            reasons.extend(["hammerlanche_expected_damage", "hammerlanche_energy_probability"])
            if assessment["ko_probability"] > 0:
                reasons.append("hammerlanche_ko_probability")
            if self._active_can_guaranteed_ko(state):
                score -= GUARANTEED_KO_BONUS * 3.0
                reasons.append("probabilistic_attack_behind_guaranteed_ko")
        if self._own_deck_count(state) < 15 and "shuffle" in text:
            energy_type = self._attack_energy_type(candidate)
            returned = self._discard_basic_energy_count(state, energy_type)
            score += min(80.0, returned * 5.0)
            reasons.append("deck_refill")
        return score, reasons

    def _retreat_score(self, state: GameState, candidate: Candidate) -> tuple[float, list[str]]:
        if not self._retreat_is_priority(state, candidate):
            return -2000.0, ["legal_retreat"]
        return 260.0, ["retreat_from_public_risk"]

    def _retreat_is_priority(self, state: GameState, candidate: Candidate) -> bool:
        player = self._own_player(state)
        if player is None:
            return False
        active = player.active
        if active is None or active.card_id is None:
            return False
        if active.card_id == ARTICUNO_CARD_ID and not self._alakazam_matchup_active(state):
            return self._bench_has_ready_evolved_replacement(state)
        if not self._active_is_publicly_threatened(state):
            return False
        if active.card_id == KYOGRE_CARD_ID and self._kyogre_riptide_line_ready(state):
            return False
        return self._bench_has_ready_replacement(state)

    def _bench_has_ready_replacement(self, state: GameState) -> bool:
        player = self._own_player(state)
        if player is None:
            return False
        for pokemon in player.bench:
            if pokemon is None or pokemon.card_id is None:
                continue
            if self._pokemon_can_attack_next_turn(pokemon):
                return True
        return False

    def _bench_has_ready_evolved_replacement(self, state: GameState) -> bool:
        """Return whether an evolved, energized attacker is ready on the Bench."""
        player = self._own_player(state)
        if player is None:
            return False
        return any(
            pokemon is not None
            and self._has_role(int(pokemon.card_id), "primary_attacker")
            and self._pokemon_can_attack_next_turn(pokemon)
            for pokemon in player.bench
            if pokemon is not None and isinstance(pokemon.card_id, int)
        )

    def _pokemon_can_attack_next_turn(self, pokemon: Any) -> bool:
        card_id = pokemon.card_id if pokemon is not None else None
        if not isinstance(card_id, int) or card_id <= 0:
            return False
        energy_count = len(getattr(pokemon, "energies", ()))
        return energy_count >= self._attack_energy_target(card_id)

    def _active_is_publicly_threatened(self, state: GameState) -> bool:
        own_active = self._own_active(state)
        if own_active is None or own_active.hp <= 0:
            return False
        opponent = self._opponent_player(state)
        if opponent is None or opponent.active is None or opponent.active.card_id is None:
            return False
        return bool(self._public_attack_damage(state, opponent.active) >= own_active.hp)

    def _public_attack_damage(self, state: GameState, pokemon: Any) -> int:
        card_id = pokemon.card_id if pokemon is not None else None
        if not isinstance(card_id, int) or card_id <= 0:
            return 0
        energy_count = len(getattr(pokemon, "energies", ()))
        card = self.catalog.get_card(str(card_id)) or {}
        best = 0
        for attack_id in card.get("attacks", []):
            attack = self.catalog.get_attack(str(attack_id)) or {}
            energies = attack.get("energies", [])
            if not isinstance(energies, list) or len(energies) > energy_count:
                continue
            damage = self._public_attack_damage_for_attack(state, attack, pokemon)
            if damage > best:
                best = damage
        return best

    def _public_attack_damage_for_attack(
        self,
        state: GameState,
        attack: Mapping[str, Any],
        pokemon: Any,
    ) -> int:
        text = str(attack.get("text", "")).casefold()
        if "damage for each basic" in text and "discard pile" in text:
            energy_type = self._metadata_int(
                self.catalog.get_card(str(pokemon.card_id)) or {}, "energyType"
            )
            multiplier = self._leading_damage_multiplier(text)
            return multiplier * self._discard_basic_energy_count_for_player(
                self._opponent_player(state),
                energy_type,
            )
        return max(0, self._metadata_int(attack, "damage"))

    def _own_active(self, state: GameState) -> Any:
        player = self._own_player(state)
        return player.active if player is not None else None

    def _opponent_player(self, state: GameState) -> Any:
        players = state.players
        if len(players) < 2:
            return None
        your_index = state.your_index if 0 <= state.your_index < len(players) else 0
        return players[1 - your_index]

    def _own_active_card_id(self, state: GameState) -> int:
        active = self._own_active(state)
        if active is None or active.card_id is None:
            return 0
        return active.card_id if isinstance(active.card_id, int) else 0

    def _opponent_visible_alakazam_line(self, state: GameState) -> bool:
        opponent = self._opponent_player(state)
        if opponent is None:
            return False
        visible = [opponent.active, *opponent.bench]
        return any(
            pokemon is not None
            and pokemon.card_id in {ABRA_CARD_ID, KADABRA_CARD_ID, ALAKAZAM_CARD_ID}
            for pokemon in visible
        )

    def _opponent_visible_abra(self, state: GameState) -> bool:
        """Return whether the opponent exposes any card in the Alakazam line."""
        return self._alakazam_matchup_active(state)

    def _opponent_active_prevents_ex(self, state: GameState) -> bool:
        opponent = self._opponent_player(state)
        if opponent is None or opponent.active is None or opponent.active.card_id is None:
            return False
        traits = self.catalog.get_traits(str(opponent.active.card_id))
        return traits.prevents_damage_from_ex

    def _kyogre_riptide_line_ready(self, state: GameState) -> bool:
        return (
            self._own_active_card_id(state) == KYOGRE_CARD_ID
            and self._own_deck_count(state) < 15
            and self._discard_basic_energy_count(state, 3) > 0
        )

    def _kyogre_is_valuable(self, state: GameState) -> bool:
        return self._kyogre_riptide_line_ready(state) or self._opponent_active_prevents_ex(state)

    def _needs_evolution_search(self, state: GameState) -> bool:
        player = self._own_player(state)
        if player is None:
            return False
        return (
            any(
                pokemon is not None and pokemon.card_id == SNOVER_CARD_ID
                for pokemon in player.bench
            )
            or self._own_active_card_id(state) == SNOVER_CARD_ID
        )

    def _has_bench_snover(self, state: GameState) -> bool:
        """Return whether Snover is currently available on the own Bench."""
        player = self._own_player(state)
        return bool(
            player
            and any(
                pokemon is not None and pokemon.card_id == SNOVER_CARD_ID
                for pokemon in player.bench
            )
        )

    def _needs_pokemon_search(self, state: GameState) -> bool:
        player = self._own_player(state)
        if player is None:
            return False
        if (
            self._opponent_visible_abra(state)
            and self._own_active_card_id(state) != ARTICUNO_CARD_ID
        ):
            return True
        return (
            self._bench_has_space(state)
            and not self._bench_has_ready_replacement(state)
            and not self._card_in_hand(state, SNOVER_CARD_ID)
        )

    def _lillie_is_useful(self, state: GameState) -> bool:
        player = self._own_player(state)
        if player is None:
            return False
        total = player.deck_count + player.hand_count
        if total <= 6:
            return False
        if total == 7 and not (
            self._kyogre_riptide_line_ready(state) or self._active_can_guaranteed_ko(state)
        ):
            return False
        return player.hand_count <= 4 or not self._needs_pokemon_search(state)

    def _card_in_hand(self, state: GameState, card_id: int) -> bool:
        """Return whether the visible own hand contains a card identifier."""
        player = self._own_player(state)
        if player is None or player.hand is None:
            return False
        return any(
            isinstance(card, Mapping)
            and (card.get("id") == card_id or card.get("cardId") == card_id)
            for card in player.hand
        )

    def _petrel_is_useful(self, state: GameState) -> bool:
        player = self._own_player(state)
        if player is None:
            return False
        if self._needs_evolution_search(state):
            return True
        if self._needs_pokemon_search(state):
            return True
        return self._lillie_is_useful(state)

    def _active_can_guaranteed_ko(self, state: GameState) -> bool:
        active = self._own_active(state)
        if active is None or active.card_id is None:
            return False
        opponent = self._opponent_player(state)
        if opponent is None or opponent.active is None:
            return False
        energy_count = len(active.energies)
        card = self.catalog.get_card(str(active.card_id)) or {}
        for attack_id in card.get("attacks", []):
            attack = self.catalog.get_attack(str(attack_id)) or {}
            energies = attack.get("energies", [])
            if not isinstance(energies, list) or len(energies) > energy_count:
                continue
            if self._public_attack_damage_for_attack(state, attack, active) >= opponent.active.hp:
                return True
        return False

    def _guaranteed_attack_damage(self, state: GameState, candidate: Candidate) -> int:
        """Return the deterministic part of an attack's damage.

        Discard-pile based damage is public information; top-of-deck based
        damage is probabilistic and therefore excluded. Fixed-damage attacks
        fall back to the deck profile's ``attack_plans`` and then to the
        catalog attack metadata.
        """
        explicit = self._number(candidate.option, "guaranteedDamage", "damage")
        if explicit:
            return int(max(0, explicit))
        plan = self._attack_plan(candidate)
        if plan is not None:
            if plan.damage_per_basic_energy_in_discard:
                return plan.damage_per_basic_energy_in_discard * self._discard_basic_energy_count(
                    state, self._attack_energy_type(candidate)
                )
            return plan.guaranteed_damage
        text = str((candidate.attack or {}).get("text", "")).casefold()
        if "damage for each basic" in text and "discard pile" in text:
            energy_type = self._attack_energy_type(candidate)
            multiplier = self._leading_damage_multiplier(text)
            return multiplier * self._discard_basic_energy_count(state, energy_type)
        return int(max(0, self._number(candidate.attack or {}, "damage")))

    def _attack_plan(self, candidate: Candidate) -> AttackPlan | None:
        attack_id = candidate.option.get("attackId")
        if isinstance(attack_id, str) and attack_id.isdigit():
            attack_id = int(attack_id)
        if isinstance(attack_id, int) and self.deck_profile:
            return self.deck_profile.attack_plans.get(attack_id)
        return None

    def _is_hammerlanche(self, candidate: Candidate) -> bool:
        """Return whether a candidate represents the Hammer-lanche attack."""
        attack_id = candidate.option.get("attackId")
        if isinstance(attack_id, str) and attack_id.isdigit():
            attack_id = int(attack_id)
        return attack_id == HAMMERLANCHE_ATTACK_ID

    def _hammerlanche_assessment(self, state: GameState, candidate: Candidate) -> dict[str, float]:
        """Estimate Hammer-lanche damage from the visible Energy distribution."""
        energy = self._energy_distribution(state)
        deck_count = max(0, int(energy["deck_count"]))
        energy_in_deck = min(deck_count, max(0, round(energy["deck_energy"])))
        draws = min(6, deck_count)
        if deck_count == 0 or draws == 0:
            return {
                "total_energy": energy["total_energy"],
                "hand_energy": energy["hand_energy"],
                "deck_energy": float(energy_in_deck),
                "prize_energy": energy["prize_energy"],
                "discard_energy": energy["discard_energy"],
                "attached_energy": energy["attached_energy"],
                "deck_count": float(deck_count),
                "probability_hit": 0.0,
                "expected_hits": 0.0,
                "expected_damage": 0.0,
                "ko_probability": 0.0,
            }
        expected_hits = draws * energy_in_deck / deck_count
        probability_hit = self._hypergeometric_at_least(deck_count, energy_in_deck, draws, 1)
        required_hits = max(1, math.ceil(self._opponent_active_hp(state) / 100))
        ko_probability = self._hypergeometric_at_least(
            deck_count, energy_in_deck, draws, required_hits
        )
        return {
            "total_energy": energy["total_energy"],
            "hand_energy": energy["hand_energy"],
            "deck_energy": float(energy_in_deck),
            "prize_energy": energy["prize_energy"],
            "discard_energy": energy["discard_energy"],
            "attached_energy": energy["attached_energy"],
            "deck_count": float(deck_count),
            "probability_hit": probability_hit,
            "expected_hits": expected_hits,
            "expected_damage": expected_hits * 100.0,
            "ko_probability": ko_probability,
        }

    def _energy_distribution(self, state: GameState) -> dict[str, float]:
        """Return visible and inferred counts of Basic {W} Energy by zone."""
        player = self._own_player(state)
        if player is None:
            return {
                "total_energy": 0.0,
                "hand_energy": 0.0,
                "deck_energy": 0.0,
                "prize_energy": 0.0,
                "discard_energy": 0.0,
                "attached_energy": 0.0,
                "deck_count": 0.0,
            }
        total = self._total_basic_energy_count()
        hand_energy = self._count_basic_energy_cards(player.hand)
        discard_energy = self._count_basic_energy_cards(player.discard)
        attached_energy = sum(
            len(pokemon.energies)
            for pokemon in [player.active, *player.bench]
            if pokemon is not None
        )
        availability = self.prize_check.availability(3) if self.prize_check else None
        if availability is not None:
            prize_energy = availability.prized_expected
            deck_energy = availability.searchable_expected
        else:
            prize_energy = float(self._count_basic_energy_cards(player.prize))
            deck_energy = max(
                0.0,
                float(total - hand_energy - discard_energy - attached_energy - prize_energy),
            )
        return {
            "total_energy": float(total),
            "hand_energy": float(hand_energy),
            "deck_energy": deck_energy,
            "prize_energy": float(prize_energy),
            "discard_energy": float(discard_energy),
            "attached_energy": float(attached_energy),
            "deck_count": float(player.deck_count),
        }

    def _total_basic_energy_count(self) -> int:
        """Return the deck's declared Basic {W} Energy count."""
        return self.deck_profile.basic_energy_count if self.deck_profile else 0

    @staticmethod
    def _count_basic_energy_cards(cards: Any) -> int:
        """Count Basic {W} Energy card objects in a visible zone."""
        if not isinstance(cards, list):
            return 0
        return sum(
            1
            for card in cards
            if isinstance(card, Mapping) and (card.get("id") == 3 or card.get("cardId") == 3)
        )

    @staticmethod
    def _hypergeometric_at_least(
        population: int, successes: int, draws: int, minimum: int
    ) -> float:
        """Return the chance of at least ``minimum`` successes without replacement."""
        if minimum <= 0:
            return 1.0
        if population <= 0 or successes <= 0 or draws <= 0 or minimum > draws:
            return 0.0
        successes = min(successes, population)
        draws = min(draws, population)
        denominator = math.comb(population, draws)
        lower = max(minimum, draws - (population - successes))
        upper = min(draws, successes)
        return (
            sum(
                math.comb(successes, hits) * math.comb(population - successes, draws - hits)
                for hits in range(lower, upper + 1)
            )
            / denominator
        )

    def _opponent_active_hp(self, state: GameState) -> int:
        players = state.players
        if len(players) < 2:
            return 0
        your_index = state.your_index if 0 <= state.your_index < len(players) else 0
        opponent = players[1 - your_index]
        if opponent.active is None:
            return 0
        return max(0, opponent.active.hp)

    def _card_selection_score(
        self,
        state: GameState,
        candidate: Candidate,
        context: SelectContext | None,
    ) -> tuple[float, list[str]]:
        card_id = self._feature_int(candidate, "card_id")
        card_type = self._metadata_int(candidate.card, "cardType")
        energy_count = self._feature_int(candidate, "card_energy_count")
        hp = self._feature_int(candidate, "card_hp")
        if context is SelectContext.SETUP_ACTIVE_POKEMON:
            if self._alakazam_matchup_active(state):
                if self._fezandipiti_line_active(state) and card_id in {
                    KYOGRE_CARD_ID,
                    SNOVER_CARD_ID,
                }:
                    return (320.0 if card_id == KYOGRE_CARD_ID else 180.0), [
                        "setup_fezandipiti_response"
                    ]
                if card_id == ARTICUNO_CARD_ID:
                    return 320.0, ["setup_matchup_articuno"]
                return -2000.0, ["avoid_non_articuno_matchup_setup"]
            score = 120.0 if self._has_role(card_id, "evolution_basic") else 110.0
            return score, ["setup_active_attacker"]
        if context is SelectContext.SETUP_BENCH_POKEMON:
            if card_id == ARTICUNO_CARD_ID and not self._alakazam_matchup_active(state):
                return -2000.0, ["avoid_articuno_without_matchup_evidence"]
            if self._alakazam_matchup_active(state):
                if self._fezandipiti_line_active(state) and card_id in {
                    KYOGRE_CARD_ID,
                    SNOVER_CARD_ID,
                }:
                    return (300.0 if card_id == KYOGRE_CARD_ID else 160.0), [
                        "setup_fezandipiti_response"
                    ]
                if card_id == ARTICUNO_CARD_ID:
                    return 300.0, ["setup_matchup_articuno"]
                return -2000.0, ["avoid_non_articuno_matchup_setup"]
            score = 100.0 if card_type == 0 else -100.0
            return score, ["setup_bench"]
        if context in {
            SelectContext.SWITCH,
            SelectContext.TO_ACTIVE,
            SelectContext.TO_FIELD,
        }:
            score = hp + energy_count * 100.0
            if card_id == ARTICUNO_CARD_ID and not self._alakazam_matchup_active(state):
                return -2000.0, ["avoid_articuno_without_matchup_evidence"]
            if card_id == ARTICUNO_CARD_ID and self._alakazam_matchup_active(state):
                score += 120.0
                return score, ["promote_tech_attacker"]
            if card_id == KYOGRE_CARD_ID and self._kyogre_is_valuable(state):
                score += 80.0
                return score, ["promote_sacrificial_attacker"]
            return score, ["promote_prepared_attacker"]
        if context is SelectContext.TO_HAND:
            if self.prize_check and self.prize_check.mode is PrizeCheckMode.EXACT:
                availability = self.prize_check.availability(card_id)
                if availability and availability.searchable_exact == 0:
                    return -1000.0, ["confirmed_prized_unsearchable"]
            value = self._card_resource_value(card_id, card_type)
            if card_id == ABOMASNOW_CARD_ID and not self._has_bench_snover(state):
                return -2000.0, ["avoid_abomasnow_without_bench_snover"]
            if card_id == ARTICUNO_CARD_ID and not self._alakazam_matchup_active(state):
                return -2000.0, ["avoid_articuno_without_matchup_evidence"]
            if card_id == ARTICUNO_CARD_ID and self._alakazam_matchup_active(state):
                value += 120.0
            elif card_id == KYOGRE_CARD_ID and self._kyogre_is_valuable(state):
                value += 90.0
            elif card_id == MEGA_SIGNAL_CARD_ID:
                value += 90.0 if self._needs_evolution_search(state) else -30.0
            elif card_id == ULTRA_BALL_CARD_ID:
                value += 70.0 if self._needs_pokemon_search(state) else -10.0
            elif card_id == LILLIE_CARD_ID:
                if self._card_in_hand(state, LILLIE_CARD_ID):
                    return -2000.0, ["avoid_duplicate_lillie_search"]
                value += 90.0 if self._lillie_is_useful(state) else -70.0
            elif card_id == PETREL_CARD_ID:
                value += 40.0 if self._petrel_is_useful(state) else -80.0
            if self._has_role(card_id, "trainer_search"):
                value -= 200.0
                return value, ["avoid_redundant_supporter_search"]
            return value, ["search_useful_card"]
        if context in {
            SelectContext.DISCARD,
            SelectContext.DISCARD_CARD_OR_ATTACHED_CARD,
        }:
            if card_id == ARTICUNO_CARD_ID and not self._alakazam_matchup_active(state):
                return 130.0, ["discard_sacrificial_articuno"]
            if self._has_role(card_id, "development_priority"):
                return -1000.0, ["preserve_development_pokemon"]
            if card_type in {5, 6}:
                return 120.0, ["discard_energy_for_synergy"]
            if card_type == 0:
                return -100.0, ["preserve_pokemon"]
            return 20.0, ["discard_replaceable_card"]
        if context in {
            SelectContext.DAMAGE,
            SelectContext.DAMAGE_COUNTER,
            SelectContext.DAMAGE_COUNTER_ANY,
            SelectContext.EFFECT_TARGET,
        }:
            owner_is_self = bool(candidate.features.get("card_owner_is_self", False))
            return (-hp if owner_is_self else 1000.0 - hp), ["target_vulnerable_pokemon"]
        if context in {
            SelectContext.HEAL,
            SelectContext.REMOVE_DAMAGE_COUNTER,
        }:
            max_hp = self._feature_int(candidate, "card_max_hp")
            return max_hp - hp, ["heal_most_damaged"]
        return self._card_resource_value(card_id, card_type), ["card_resource_value"]

    def _card_resource_value(self, card_id: int, card_type: int) -> float:
        if self.deck_profile and card_id in self.deck_profile.resource_values:
            return self.deck_profile.resource_values[card_id]
        if self._has_role(card_id, "primary_attacker"):
            return 160.0
        if self._has_role(card_id, "evolution_basic"):
            return 150.0
        if self._has_role(card_id, "attacker"):
            return 140.0
        return {0: 120.0, 1: 100.0, 2: 90.0, 3: 100.0, 4: 70.0}.get(card_type, 10.0)

    def _has_role(self, card_id: int, role: str) -> bool:
        return bool(self.deck_profile and self.deck_profile.has_role(card_id, role))

    def _bench_has_space(self, state: GameState) -> bool:
        player = self._own_player(state)
        if player is None:
            return False
        occupied = sum(pokemon is not None for pokemon in player.bench)
        return bool(occupied < player.bench_max)

    def _attack_energy_target(self, card_id: int) -> int:
        if self.deck_profile and card_id in self.deck_profile.attack_energy_targets:
            return max(1, self.deck_profile.attack_energy_targets[card_id])
        card = self.catalog.get_card(str(card_id)) or {}
        costs = []
        for attack_id in card.get("attacks", []):
            attack = self.catalog.get_attack(str(attack_id)) or {}
            energies = attack.get("energies", [])
            if isinstance(energies, list):
                costs.append(len(energies))
        return max(costs, default=1)

    def _attack_energy_type(self, candidate: Candidate) -> int:
        energies = (candidate.attack or {}).get("energies", [])
        if not isinstance(energies, list) or not energies:
            return -1
        value = energies[0]
        return value if isinstance(value, int) and not isinstance(value, bool) else -1

    def _discard_basic_energy_count(self, state: GameState, energy_type: int) -> int:
        if energy_type == 3 and self._energy_context_state is state:
            return self.water_energy_in_discard
        player = self._own_player(state)
        if player is None:
            return 0
        count = 0
        for card in player.discard:
            if not isinstance(card, Mapping):
                continue
            card_id = card.get("id", card.get("cardId"))
            metadata = self.catalog.get_card(str(card_id)) or {}
            if (
                self._metadata_int(metadata, "cardType") == 5
                and self._metadata_int(metadata, "energyType") == energy_type
            ):
                count += 1
        return count

    def _discard_basic_energy_count_for_player(
        self,
        player: Any,
        energy_type: int,
    ) -> int:
        if player is None:
            return 0
        count = 0
        for card in getattr(player, "discard", ()):
            if not isinstance(card, Mapping):
                continue
            card_id = card.get("id", card.get("cardId"))
            metadata = self.catalog.get_card(str(card_id)) or {}
            if (
                self._metadata_int(metadata, "cardType") == 5
                and self._metadata_int(metadata, "energyType") == energy_type
            ):
                count += 1
        return count

    def _leading_damage_multiplier(self, text: str) -> int:
        words = text.split()
        for index, word in enumerate(words):
            if word == "damage" and index:
                try:
                    return int(words[index - 1])
                except ValueError:
                    return 0
        return 0

    def _own_player(self, state: GameState) -> Any:
        if 0 <= state.your_index < len(state.players):
            return state.players[state.your_index]
        return None

    def _own_deck_count(self, state: GameState) -> int:
        player = self._own_player(state)
        return player.deck_count if player is not None else 0

    def _discard_count(self, state: GameState, card_id: int) -> int:
        player = self._own_player(state)
        if player is None:
            return 0
        return sum(
            1
            for card in player.discard
            if isinstance(card, Mapping)
            and (card.get("id") == card_id or card.get("cardId") == card_id)
        )

    def _feature_int(self, candidate: Candidate, name: str) -> int:
        value = candidate.features.get(name, 0)
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

    def _metadata_int(self, metadata: Mapping[str, Any] | None, name: str) -> int:
        if metadata is None:
            return 0
        value = metadata.get(name)
        return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0

    def _mapping_int(self, mapping: Mapping[str, Any], name: str) -> int:
        value = mapping.get(name)
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

    def _truthy(self, option: Mapping[str, Any], *names: str) -> bool:
        return any(bool(option.get(name, False)) for name in names)

    def _number(self, option: Mapping[str, Any], *names: str) -> float:
        for name in names:
            value = option.get(name)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
        return 0.0


class HeuristicAgent(AgentPolicy):
    """Select the highest-scoring legal option with deterministic tie-breaking."""

    def __init__(
        self,
        weights: Mapping[str, Any] | None = None,
        feature_flags: Mapping[str, Any] | None = None,
        deck_profile: DeckProfile | None = None,
        ranker: SelectionRanker | None = None,
    ) -> None:
        self._parser = DefaultParser(_CG_CATALOG)
        self._generator = DefaultSelectionGenerator()
        self._scorer = SimpleHeuristicScorer(
            weights, feature_flags, deck_profile=deck_profile, catalog=_CG_CATALOG
        )
        self._configured_profile = deck_profile
        self._active_deck_profile = deck_profile
        self._deck: DeckDefinition | None = None
        self._prize_checker: PrizeChecker | None = None
        self._prize_map_builder = PrizeMapBuilder(_CG_CATALOG)
        self._feature_extractor = SelectionFeatureExtractor(self._scorer)
        self._heuristic_ranker = HeuristicSelectionRanker()
        self._ranker = ranker or self._heuristic_ranker
        self._fallback_count = 0
        self._last_decision: PolicyDecision | None = None
        self.alakazam_matchup_confirmed = False

    def start_match(self, deck: DeckDefinition) -> None:
        """Reset the deck strategy without changing generic policy code."""
        self.alakazam_matchup_confirmed = False
        self._scorer.set_alakazam_matchup_confirmed(False)
        self._deck = deck
        self._prize_checker = PrizeChecker(deck)
        profile = (
            self._configured_profile
            if self._configured_profile and self._configured_profile.deck_sha256 == deck.sha256
            else GenericDeckProfileBuilder(_CG_CATALOG).build(deck)
        )
        evolution_basics = tuple(sorted({line[0] for line in profile.evolution_lines if line}))
        roles = dict(profile.roles)
        roles["evolution_basic"] = evolution_basics
        active_profile = replace(profile, roles=roles)
        self._active_deck_profile = active_profile
        self._scorer.set_deck_profile(active_profile)

    @property
    def weights(self) -> dict[str, float]:
        """Return a copy of the active heuristic weights."""
        return dict(self._scorer.weights)

    @property
    def fallback_count(self) -> int:
        """Return the number of learned inference failures in this process."""
        return self._fallback_count

    @property
    def last_decision(self) -> PolicyDecision | None:
        """Return the latest auditable decision, if a decision has run."""
        return self._last_decision

    @classmethod
    def from_profile(cls, profile_path: str, *, deck_id: str, deck_path: str) -> HeuristicAgent:
        """Load a validated RFL profile, falling back to baseline weights."""
        from src.rfl.profiles import agent_from_profile

        return agent_from_profile(profile_path, active_deck_id=deck_id, active_deck_path=deck_path)

    def select(self, observation: dict[str, Any]) -> list[int]:
        """Return the best legal selection while preserving the public contract."""
        return list(self.decide(observation).selection.indices)

    def decide(self, observation: dict[str, Any]) -> PolicyDecision:
        """Return an auditable ranking decision for one observation.

        Args:
            observation: Raw actor-visible CABT observation.

        Returns:
            Complete policy decision including alternatives, features, and latency.
        """
        started = time.perf_counter()
        parsed = self._parser.parse(observation)
        self._update_alakazam_matchup(observation, parsed.state)
        self._scorer.set_energy_context(parsed.state)
        prize_check = self._prize_checker.check(observation) if self._prize_checker else None
        prize_map = self._prize_map_builder.build(parsed.state)
        self._scorer.set_strategic_context(prize_check, prize_map)
        if parsed.max_count == 0:
            return self._record_empty_decision(started)
        selections = self._generator.generate(
            parsed.candidates,
            parsed.min_count,
            parsed.max_count,
            parsed.remain_energy_cost,
            parsed.remain_damage_counter,
        )
        if not selections:
            return self._record_empty_decision(started)
        selections = self._filter_dangerous_shuffle_supporters(
            parsed.state, selections, parsed.candidates
        )
        selections = self._filter_forbidden_selections(
            parsed.state, selections, parsed.candidates, parsed.select_context
        )
        decision_phase = ""
        decision_phase_reason = ""
        if parsed.select_context is SelectContext.MAIN:
            decision_phase, decision_phase_reason, selections = self._main_phase_selections(
                parsed.state, selections, parsed.candidates
            )
        contextualized = [
            Selection(
                indices=selection.indices,
                option_types=selection.option_types,
                context=parsed.select_context,
            )
            for selection in selections
        ]
        features = self._feature_extractor.extract(
            parsed,
            contextualized,
            deck_profile=self._active_deck_profile,
            prize_check=prize_check,
        )
        fallback_used = False
        ranker = self._ranker
        try:
            ranked = ranker.rank(parsed, contextualized, features)
            self._validate_ranking(contextualized, ranked)
        except Exception:
            if ranker is self._heuristic_ranker:
                raise
            self._fallback_count += 1
            fallback_used = True
            ranker = self._heuristic_ranker
            ranked = ranker.rank(parsed, contextualized, features)
        if ranked:
            winning_phase, winning_phase_reason = self._selection_phase(
                parsed.state, ranked[0].selection, parsed.candidates
            )
            if not decision_phase:
                decision_phase = winning_phase.value
            decision_phase_reason = winning_phase_reason
        result = PolicyDecision(
            selection=ranked[0].selection,
            ranked=tuple(ranked),
            features=tuple(features),
            decision_phase=decision_phase,
            decision_phase_reason=decision_phase_reason,
            fallback_used=fallback_used,
            model_backend=str(getattr(ranker, "backend", "heuristic")),
            model_version=str(getattr(ranker, "model_version", "heuristic-v1")),
            duration_ms=(time.perf_counter() - started) * 1000.0,
        )
        self._last_decision = result
        return result

    def _update_alakazam_matchup(self, observation: Mapping[str, Any], state: GameState) -> None:
        """Persist only actor-visible evidence for the Alakazam matchup."""
        if self.alakazam_matchup_confirmed:
            return
        if self._scorer._opponent_visible_alakazam_line(state) or self._public_alakazam_evidence(
            observation, state
        ):
            self.alakazam_matchup_confirmed = True
            self._scorer.set_alakazam_matchup_confirmed()

    @staticmethod
    def _public_alakazam_evidence(observation: Mapping[str, Any], state: GameState) -> bool:
        """Return whether public hand or event data exposes the Alakazam line."""
        opponent_index = 1 - state.your_index if len(state.players) >= 2 else 1
        current = observation.get("current")
        if isinstance(current, Mapping):
            players = current.get("players")
            if isinstance(players, list) and 0 <= opponent_index < len(players):
                opponent = players[opponent_index]
                if isinstance(opponent, Mapping) and HeuristicAgent._contains_alakazam_card(
                    opponent.get("hand")
                ):
                    return True
        logs = observation.get("logs")
        if not isinstance(logs, list):
            return False
        return any(
            isinstance(event, Mapping)
            and event.get("playerIndex") == opponent_index
            and HeuristicAgent._contains_alakazam_card(event)
            for event in logs
        )

    @staticmethod
    def _contains_alakazam_card(value: Any) -> bool:
        """Find an explicitly identified Alakazam-line card in public data."""
        if isinstance(value, Mapping):
            for key in ("cardId", "card_id", "cardIdActive", "cardIdBench", "cardIdTarget"):
                if value.get(key) in {ABRA_CARD_ID, KADABRA_CARD_ID, ALAKAZAM_CARD_ID}:
                    return True
            if value.get("id") in {ABRA_CARD_ID, KADABRA_CARD_ID, ALAKAZAM_CARD_ID}:
                return True
            return any(
                HeuristicAgent._contains_alakazam_card(item)
                for key in ("hand", "cards", "revealed", "mulligan", "active", "bench")
                for item in (value.get(key),)
            )
        if isinstance(value, list):
            return any(HeuristicAgent._contains_alakazam_card(item) for item in value)
        return False

    def _record_empty_decision(self, started: float) -> PolicyDecision:
        selection = Selection(indices=(), option_types=())
        result = PolicyDecision(
            selection=selection,
            ranked=(),
            features=(),
            decision_phase="",
            decision_phase_reason="",
            fallback_used=False,
            model_backend=str(getattr(self._ranker, "backend", "heuristic")),
            model_version=str(getattr(self._ranker, "model_version", "heuristic-v1")),
            duration_ms=(time.perf_counter() - started) * 1000.0,
        )
        self._last_decision = result
        return result

    def _main_phase_selections(
        self,
        state: GameState,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
    ) -> tuple[str, str, list[Selection]]:
        """Return the earliest MAIN phase and the selections that match it."""
        safe_selections = self._filter_forbidden_selections(
            state, selections, candidates, SelectContext.MAIN
        )
        safe_selections = self._filter_fezandipiti_bench_line(state, safe_selections, candidates)
        by_phase: dict[DecisionPhase, list[Selection]] = {phase: [] for phase in _MAIN_PHASE_ORDER}
        reason_by_phase: dict[DecisionPhase, str] = {}
        for selection in safe_selections:
            phase, reason = self._selection_phase(state, selection, candidates)
            by_phase.setdefault(phase, []).append(selection)
            reason_by_phase.setdefault(phase, reason)
        for phase in _MAIN_PHASE_ORDER:
            if by_phase.get(phase):
                return (
                    phase.value,
                    reason_by_phase.get(phase, phase.value.casefold()),
                    by_phase[phase],
                )
        return DecisionPhase.END.value, "no_signal", list(safe_selections)

    def _filter_fezandipiti_bench_line(
        self,
        state: GameState,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
    ) -> list[Selection]:
        """Stage Kyogre before exposing Snover to an energized Fezandipiti."""
        if not self._scorer._fezandipiti_line_active(state):
            return list(selections)
        by_index = {candidate.option_index: candidate for candidate in candidates}

        def pokemon_ids(selection: Selection) -> list[int]:
            return [
                self._scorer._feature_int(candidate, "card_id")
                for index in selection.indices
                if (candidate := by_index.get(index)) is not None
                and candidate.option_type is OptionType.PLAY
                and self._scorer._metadata_int(candidate.card, "cardType") == 0
            ]

        player = self._scorer._own_player(state)
        kyogre_benched = any(
            pokemon is not None and pokemon.card_id == KYOGRE_CARD_ID
            for pokemon in (player.bench if player else ())
        )
        ids_by_selection = [(selection, pokemon_ids(selection)) for selection in selections]
        if self._scorer._kyogre_riptide_guarantees_fezandipiti_ko(state):
            kyogre_only = [
                selection
                for selection, ids in ids_by_selection
                if KYOGRE_CARD_ID in ids and SNOVER_CARD_ID not in ids
            ]
            if kyogre_only:
                return kyogre_only
        if not kyogre_benched:
            kyogre_first = [
                selection
                for selection, ids in ids_by_selection
                if KYOGRE_CARD_ID in ids and SNOVER_CARD_ID not in ids
            ]
            if kyogre_first:
                return kyogre_first
        if kyogre_benched:
            without_snover = [
                selection for selection, ids in ids_by_selection if SNOVER_CARD_ID not in ids
            ]
            if without_snover and not self._snover_is_needed_now(state):
                return without_snover
        return list(selections)

    def _snover_is_needed_now(self, state: GameState) -> bool:
        """Return whether delaying Snover would miss the next attacker window."""
        player = self._own_player_state(state)
        if player is None:
            return True
        if any(
            pokemon is not None and self._scorer._pokemon_can_attack_next_turn(pokemon)
            for pokemon in player.bench
        ):
            return False
        if self._scorer._own_active_card_id(state) == KYOGRE_CARD_ID:
            return not self._scorer._pokemon_can_attack_next_turn(player.active)
        return True

    def _filter_forbidden_selections(
        self,
        state: GameState,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
        context: SelectContext | None,
    ) -> list[Selection]:
        """Remove strategically forbidden actions when another legal choice exists."""
        by_index = {candidate.option_index: candidate for candidate in candidates}
        safe = [
            selection
            for selection in selections
            if not any(
                self._candidate_is_forbidden(state, by_index.get(index), context)
                for index in selection.indices
            )
        ]
        return safe if safe else list(selections)

    def _candidate_is_forbidden(
        self,
        state: GameState,
        candidate: Candidate | None,
        context: SelectContext | None,
    ) -> bool:
        """Return whether a candidate violates a hard resource-preservation rule."""
        if candidate is None:
            return False
        card_id = self._scorer._feature_int(candidate, "card_id")
        matchup_confirmed = self._scorer._alakazam_matchup_active(state)
        no_matchup = not matchup_confirmed
        card_type = self._scorer._metadata_int(candidate.card, "cardType")
        target_id = self._scorer._feature_int(candidate, "target_card_id")
        if matchup_confirmed:
            special_feza = self._scorer._fezandipiti_line_active(state)
            if candidate.option_type is OptionType.EVOLVE and (
                card_id == ABOMASNOW_CARD_ID or target_id == ABOMASNOW_CARD_ID
            ):
                return not special_feza or not self._scorer._special_evolution_allowed(
                    state, candidate
                )
            if candidate.option_type is OptionType.CARD and card_id in {
                SNOVER_CARD_ID,
                ABOMASNOW_CARD_ID,
            }:
                return not special_feza or card_id == ABOMASNOW_CARD_ID
            if candidate.option_type is OptionType.PLAY and card_type == 0:
                if special_feza and card_id in {KYOGRE_CARD_ID, SNOVER_CARD_ID}:
                    return False
                return card_id != ARTICUNO_CARD_ID
            if candidate.option_type is OptionType.CARD and card_type == 0:
                if context in {
                    SelectContext.SETUP_ACTIVE_POKEMON,
                    SelectContext.SETUP_BENCH_POKEMON,
                    SelectContext.TO_BENCH,
                    SelectContext.TO_FIELD,
                    SelectContext.TO_HAND,
                }:
                    if special_feza and card_id in {KYOGRE_CARD_ID, SNOVER_CARD_ID}:
                        return False
                    return card_id != ARTICUNO_CARD_ID
            if candidate.option_type is OptionType.ATTACH and target_id == ABOMASNOW_CARD_ID:
                return True
            if candidate.option_type is OptionType.ATTACK and (
                self._scorer._own_active_card_id(state) == ABOMASNOW_CARD_ID
                or target_id == ABOMASNOW_CARD_ID
            ):
                return True
        if candidate.option_type is OptionType.ATTACH:
            target_energy_count = self._scorer._feature_int(candidate, "target_energy_count")
            if card_type in {5, 6} and target_energy_count >= self._scorer._attack_energy_target(
                target_id
            ):
                return True
        if card_id == ARTICUNO_CARD_ID and no_matchup:
            if candidate.option_type is OptionType.PLAY:
                return True
            if candidate.option_type is OptionType.ATTACH:
                card_type = self._scorer._metadata_int(candidate.card, "cardType")
                if card_type in {5, 6}:
                    return True
            if candidate.option_type is OptionType.CARD and context in {
                SelectContext.SETUP_BENCH_POKEMON,
                SelectContext.TO_ACTIVE,
                SelectContext.TO_FIELD,
                SelectContext.TO_HAND,
            }:
                return True
        if (
            candidate.option_type is OptionType.CARD
            and context is SelectContext.TO_HAND
            and card_id == LILLIE_CARD_ID
            and self._scorer._card_in_hand(state, LILLIE_CARD_ID)
        ):
            return True
        if (
            candidate.option_type is OptionType.RETREAT
            and self._scorer._own_active_card_id(state) == ARTICUNO_CARD_ID
            and no_matchup
            and not self._scorer._bench_has_ready_evolved_replacement(state)
        ):
            return True
        return False

    def _selection_phase(
        self,
        state: GameState,
        selection: Selection,
        candidates: Sequence[Candidate],
    ) -> tuple[DecisionPhase, str]:
        """Classify a selection by its highest-priority MAIN phase."""
        by_index = {candidate.option_index: candidate for candidate in candidates}
        phase = DecisionPhase.END
        reason = "end"
        for index in selection.indices:
            candidate = by_index.get(index)
            if candidate is None:
                continue
            candidate_phase, candidate_reason = self._candidate_phase(state, candidate)
            if _MAIN_PHASE_RANK[candidate_phase] < _MAIN_PHASE_RANK[phase]:
                phase = candidate_phase
                reason = candidate_reason
        return phase, reason

    def _candidate_phase(self, state: GameState, candidate: Candidate) -> tuple[DecisionPhase, str]:
        """Classify one legal option into the deterministic MAIN sequencing order."""
        option_type = candidate.option_type
        if option_type is OptionType.EVOLVE:
            return DecisionPhase.EVOLVE, "evolve"
        if option_type is OptionType.ATTACH:
            if self._attach_completes_active_attack(candidate):
                return DecisionPhase.ATTACH_PRIORITY, "attach_completes_active_attack"
            if self._bench_has_space(state):
                return DecisionPhase.ATTACH_OPEN, "attach_energy"
            return DecisionPhase.ATTACH_FULL, "attach_energy"
        if option_type is OptionType.PLAY:
            card_type = self._scorer._metadata_int(candidate.card, "cardType")
            card_id = self._scorer._feature_int(candidate, "card_id")
            if card_type == 0:
                if not self._bench_has_space(state):
                    return DecisionPhase.UTILITY, "bench_full"
                if self._scorer._has_role(card_id, "development_priority"):
                    return DecisionPhase.PLAY_POKEMON, "develop_priority_pokemon"
                return DecisionPhase.PLAY_POKEMON, "develop_bench_pokemon"
            if card_type == 1:
                if self._scorer._has_search_role(card_id):
                    return DecisionPhase.PLAY_ITEMS, "play_search_item"
                return DecisionPhase.PLAY_ITEMS, "play_item"
            if card_type == 3:
                if self._scorer._has_search_role(card_id):
                    return DecisionPhase.PLAY_SUPPORTER, "play_search_supporter"
                return DecisionPhase.PLAY_SUPPORTER, "play_supporter"
            return DecisionPhase.UTILITY, "play_utility_card"
        if option_type is OptionType.ATTACK:
            if self._attack_is_priority(state, candidate):
                return DecisionPhase.ATTACK_PRIORITY, "priority_attack"
            return DecisionPhase.ATTACK, "attack"
        if option_type is OptionType.RETREAT:
            if self._scorer._retreat_is_priority(state, candidate):
                return DecisionPhase.RETREAT, "retreat_from_public_risk"
            return DecisionPhase.END, "retreat"
        if option_type in {OptionType.ABILITY, OptionType.DISCARD}:
            return DecisionPhase.UTILITY, option_type.value.casefold()
        if option_type is OptionType.END:
            return DecisionPhase.END, "end"
        return DecisionPhase.UTILITY, option_type.value.casefold()

    def _bench_has_space(self, state: GameState) -> bool:
        """Return True when the own Bench can still accept a Pokémon."""
        player = self._own_player_state(state)
        if player is None:
            return False
        occupied = sum(pokemon is not None for pokemon in player.bench)
        return bool(occupied < player.bench_max)

    def _attack_is_priority(self, state: GameState, candidate: Candidate) -> bool:
        """Return True when an attack should preempt later development phases."""
        text = str((candidate.attack or {}).get("text", "")).casefold()
        player = self._own_player_state(state)
        return bool(player and player.deck_count < 15 and "shuffle" in text)

    @staticmethod
    def _validate_ranking(selections: Sequence[Selection], ranked: Sequence[Any]) -> None:
        expected = {selection.indices for selection in selections}
        actual = {item.selection.indices for item in ranked}
        if not ranked or expected != actual or len(ranked) != len(selections):
            raise RuntimeError("ranker did not return every legal selection exactly once")

    def _filter_dangerous_shuffle_supporters(
        self,
        state: GameState,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
    ) -> list[Selection]:
        """Drop plays of hand-shuffle supporters that would deck us out.

        A supporter that shuffles the hand into the deck and draws (for
        example Lillie) is only safe when the reshuffled total (deck plus hand)
        covers the draw. Otherwise playing it loses the game instantly; skip it
        so an attack, or END when no attack is legal, is chosen instead.
        """
        if not state.players:
            return list(selections)
        player = self._own_player_state(state)
        if player is None:
            return list(selections)
        by_index = {candidate.option_index: candidate for candidate in candidates}
        kept = [
            selection
            for selection in selections
            if not any(
                self._shuffle_supporter_deck_out(player, by_index.get(index))
                for index in selection.indices
            )
        ]
        return kept if kept else list(selections)

    @staticmethod
    def _shuffle_supporter_deck_out(player: Any, candidate: Candidate | None) -> bool:
        """True when playing this shuffle supporter would deck us out."""
        draw = HeuristicAgent._shuffle_supporter_draw(player, candidate)
        if draw is None:
            return False
        return bool(player.deck_count + player.hand_count - 1 < draw)

    @staticmethod
    def _shuffle_supporter_draw(player: Any, candidate: Candidate | None) -> int | None:
        """Draw size of a hand-shuffle supporter play, or None otherwise.

        Detects supporter cards whose skill shuffles the hand into the deck
        before drawing, and returns the number of cards drawn (6, or 8 while
        exactly 6 Prize cards remain).
        """
        if candidate is None or candidate.option_type is not OptionType.PLAY:
            return None
        card = candidate.card if isinstance(candidate.card, Mapping) else None
        if card is None:
            return None
        card_type = card.get("cardType")
        if not isinstance(card_type, int) or card_type != 3:
            return None
        texts = [
            str(skill.get("text", "")).casefold()
            for skill in card.get("skills", [])
            if isinstance(skill, Mapping)
        ]
        if not texts or not any("shuffle your hand" in text for text in texts):
            return None
        return 8 if len(player.prize) == 6 and any("8 cards" in text for text in texts) else 6

    def _own_player_state(self, state: GameState) -> Any:
        if 0 <= state.your_index < len(state.players):
            return state.players[state.your_index]
        return None

    def _has_priority_action(
        self,
        state: GameState,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
    ) -> bool:
        """Return True when a legal selection contains an action that must not
        be deferred for bench development.

        Evolution, Abilities, search/Trainer plays, and guaranteed Knock Outs
        all precede filling the Bench in the declared play order.
        """
        by_index = {candidate.option_index: candidate for candidate in candidates}
        for selection in selections:
            for index in selection.indices:
                candidate = by_index.get(index)
                if candidate is None:
                    continue
                if candidate.option_type in {OptionType.EVOLVE, OptionType.ABILITY}:
                    return True
                if candidate.option_type is OptionType.PLAY and self._is_priority_play(candidate):
                    return True
                if (
                    candidate.option_type is OptionType.ATTACH
                    and self._attach_completes_active_attack(candidate)
                ):
                    return True
                if candidate.option_type is OptionType.ATTACK and self._attack_is_guaranteed_ko(
                    state, candidate
                ):
                    return True
        return False

    def _attach_completes_active_attack(self, candidate: Candidate) -> bool:
        """True when attaching an energy to the Active Pokémon enables its
        required attack, which takes priority over bench development.
        """
        if not bool(candidate.features.get("target_is_active", False)):
            return False
        target_id = self._scorer._feature_int(candidate, "target_card_id")
        energy_count = self._scorer._feature_int(candidate, "target_energy_count")
        return energy_count + 1 >= self._scorer._attack_energy_target(target_id)

    def _is_priority_play(self, candidate: Candidate) -> bool:
        card_type = self._scorer._metadata_int(candidate.card, "cardType")
        if card_type != 0:
            return True
        card_id = self._scorer._feature_int(candidate, "card_id")
        search_roles = (
            "evolution_search",
            "general_search",
            "trainer_search",
            "hand_refresh",
            "pokemon_search",
        )
        return any(self._scorer._has_role(card_id, role) for role in search_roles)

    def _attack_is_guaranteed_ko(self, state: GameState, candidate: Candidate) -> bool:
        damage = self._scorer._guaranteed_attack_damage(state, candidate)
        return damage > 0 and damage >= self._opponent_active_hp(state)

    @staticmethod
    def _opponent_active_hp(state: GameState) -> int:
        players = state.players
        if len(players) < 2:
            return 0
        your_index = state.your_index if 0 <= state.your_index < len(players) else 0
        opponent = players[1 - your_index]
        if opponent.active is None:
            return 0
        return max(0, opponent.active.hp)
