"""Deterministic ordinal policy derived from the Human Decision Index."""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from src.agents.baseline import BaselineAgent
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
    OptionType,
    ParsedDecision,
    PolicyDecision,
    PrizeChecker,
    PrizeMap,
    PrizeMapBuilder,
    RankedSelection,
    SelectContext,
    Selection,
)
from src.ranking.features import SelectionFeatureExtractor

_CATALOG = CardCatalog.from_cg()
_DISCARD_CONTEXTS = {
    SelectContext.DISCARD,
    SelectContext.DISCARD_CARD_OR_ATTACHED_CARD,
    SelectContext.DISCARD_ENERGY_CARD,
    SelectContext.DISCARD_TOOL_CARD,
    SelectContext.DISCARD_TOOL,
    SelectContext.DISCARD_ENERGY,
}
_PROMOTION_CONTEXTS = {
    SelectContext.SWITCH,
    SelectContext.TO_ACTIVE,
    SelectContext.TO_FIELD,
}
_DAMAGE_CONTEXTS = {
    SelectContext.DAMAGE,
    SelectContext.DAMAGE_COUNTER,
    SelectContext.DAMAGE_COUNTER_ANY,
    SelectContext.EFFECT_TARGET,
}


@dataclass(frozen=True, slots=True)
class OrdinalAssessment:
    """Record the lexicographic priority and reasons for one legal selection."""

    key: tuple[int, ...]
    reasons: tuple[str, ...]


class HdiOrdinalEngine:
    """Rank selections with ordered rules instead of weighted score addition."""

    def __init__(
        self,
        deck_profile: DeckProfile | None = None,
        catalog: CardCatalog | None = None,
    ) -> None:
        self.deck_profile = deck_profile
        self.catalog = catalog or _CATALOG
        self._decision: ParsedDecision | None = None
        self._prize_map: PrizeMap | None = None
        self._deck: DeckDefinition | None = None

    def set_deck_profile(self, profile: DeckProfile) -> None:
        """Replace the declarative strategy used for subsequent decisions."""
        self.deck_profile = profile

    def set_context(
        self,
        decision: ParsedDecision,
        prize_map: PrizeMap,
        deck: DeckDefinition | None,
    ) -> None:
        """Set factual decision inputs used by ordinal assessment."""
        self._decision = decision
        self._prize_map = prize_map
        self._deck = deck

    def score(
        self,
        state: GameState,
        selection: Selection,
        candidates: Sequence[Candidate] | None = None,
    ) -> tuple[float, list[str]]:
        """Expose an ordinal trace value for the shared feature extractor."""
        if self._decision is None:
            return 0.0, ["hdi_context_unavailable"]
        assessment = self.assess(self._decision, selection, self._prize_map)
        return float(assessment.key[0]), list(assessment.reasons)

    def assess(
        self,
        decision: ParsedDecision,
        selection: Selection,
        prize_map: PrizeMap | None,
    ) -> OrdinalAssessment:
        """Return the deterministic lexicographic assessment of a selection."""
        by_index = {candidate.option_index: candidate for candidate in decision.candidates}
        selected = [by_index[index] for index in selection.indices if index in by_index]
        if len(selected) != len(selection.indices):
            return self._assessment(selection, stage=-1, reasons=("illegal_selection",))
        if not selected:
            return self._assessment(selection, stage=5, reasons=("legal_empty_selection",))

        context = decision.select_context
        if context in _DISCARD_CONTEXTS:
            return self._discard_assessment(decision, selection, selected)
        if context in _PROMOTION_CONTEXTS:
            return self._promotion_assessment(decision, selection, selected)
        if context is SelectContext.SETUP_ACTIVE_POKEMON:
            return self._setup_assessment(selection, selected, active=True)
        if context is SelectContext.SETUP_BENCH_POKEMON:
            return self._setup_assessment(selection, selected, active=False)
        if context is SelectContext.IS_FIRST:
            return self._yes_no_assessment(selection, selected, prefer_yes=True)
        if context is SelectContext.MULLIGAN:
            return self._yes_no_assessment(selection, selected, prefer_yes=False)
        if context is SelectContext.TO_HAND:
            return self._search_assessment(decision, selection, selected)

        combat = self._combat_assessment(decision, selection, selected, prize_map)
        if combat is not None:
            return combat
        return self._action_assessment(decision, selection, selected)

    def _combat_assessment(
        self,
        decision: ParsedDecision,
        selection: Selection,
        selected: Sequence[Candidate],
        prize_map: PrizeMap | None,
    ) -> OrdinalAssessment | None:
        if not (
            any(candidate.option_type is OptionType.ATTACK for candidate in selected)
            or decision.select_context in _DAMAGE_CONTEXTS
            or any(
                self._truthy(candidate.option, "ko", "knockout", "isKo") for candidate in selected
            )
        ):
            return None

        guaranteed_damage = max(
            (self._guaranteed_damage(decision, candidate) for candidate in selected), default=0
        )
        potential_damage = max(
            guaranteed_damage,
            max((self._potential_damage(candidate) for candidate in selected), default=0),
        )
        target_hp = self._target_hp(decision, selected)
        prevented = any(
            self._truthy(candidate.option, "damagePrevented", "prevented") for candidate in selected
        ) or self._active_damage_prevented(prize_map)
        proven_ko = not prevented and (
            any(self._truthy(candidate.option, "ko", "knockout", "isKo") for candidate in selected)
            or (target_hp > 0 and guaranteed_damage >= target_hp)
        )
        prize_value = self._target_prize_value(selected, prize_map)
        immediate_win = any(
            self._truthy(candidate.option, "win", "wins", "isWin", "gameOver")
            for candidate in selected
        ) or self._terminal_ko(decision.state, selected, proven_ko, prize_value)
        effort = max((self._attack_effort(candidate) for candidate in selected), default=0)
        plans = [
            plan for candidate in selected if (plan := self._attack_plan(candidate)) is not None
        ]
        unmet_previous = any(
            plan.previous_attack_id is not None
            and not self._previous_own_attack(decision, plan.previous_attack_id)
            for plan in plans
        )
        ko_required = any(plan.requires_guaranteed_ko for plan in plans)

        if immediate_win and not unmet_previous:
            return self._assessment(
                selection,
                stage=100,
                prize_value=prize_value,
                effort=effort,
                guaranteed_damage=guaranteed_damage,
                reasons=("guaranteed_win",),
            )
        if proven_ko and not unmet_previous:
            return self._assessment(
                selection,
                stage=90,
                prize_value=prize_value,
                effort=effort,
                guaranteed_damage=guaranteed_damage,
                reasons=("proven_knockout", "maximize_prize_value", "minimize_effort"),
            )
        if prevented:
            return self._assessment(
                selection, stage=0, exposure=1, reasons=("attack_damage_prevented",)
            )
        if unmet_previous:
            return self._assessment(
                selection, stage=0, exposure=1, reasons=("required_public_sequence_missing",)
            )
        if ko_required:
            return self._assessment(
                selection, stage=0, exposure=1, reasons=("guaranteed_knockout_required",)
            )
        if guaranteed_damage > 0:
            return self._assessment(
                selection,
                stage=55,
                effort=effort,
                guaranteed_damage=guaranteed_damage,
                potential_damage=potential_damage,
                reasons=("guaranteed_damage",),
            )
        if potential_damage > 0:
            return self._assessment(
                selection,
                stage=50,
                effort=effort,
                potential_damage=potential_damage,
                reasons=("potential_damage_after_guaranteed",),
            )
        if any(
            self._truthy(candidate.option, "relevantEffect", "preparesKo") for candidate in selected
        ):
            return self._assessment(selection, stage=45, reasons=("relevant_public_attack_effect",))
        return self._assessment(
            selection, stage=0, exposure=1, reasons=("attack_has_no_relevant_gain",)
        )

    def _action_assessment(
        self,
        decision: ParsedDecision,
        selection: Selection,
        selected: Sequence[Candidate],
    ) -> OrdinalAssessment:
        option_types = {candidate.option_type for candidate in selected}
        options = [candidate.option for candidate in selected]
        condition_present = self._own_active_has_condition(decision.state)
        if condition_present and any(
            self._truthy(option, "removesSpecialCondition", "recoverCondition")
            for option in options
        ):
            return self._assessment(selection, stage=85, reasons=("remove_special_condition",))
        if any(
            self._truthy(option, "freeSwitch", "avoidsKo", "preventsKnockout") for option in options
        ):
            return self._assessment(
                selection,
                stage=82,
                ko_risk=0,
                reasons=("free_switch_avoids_knockout",),
            )
        if OptionType.ATTACH in option_types:
            enables_attack = max(
                (self._attachment_enables_attack(candidate) for candidate in selected), default=0
            )
            return self._assessment(
                selection,
                stage=80,
                ready=2 if enables_attack else 1,
                attack_lines=self._ready_attacker_count(decision.state) + enables_attack,
                reasons=(
                    "attach_for_guaranteed_attack" if enables_attack else "develop_attacker_energy",
                ),
            )
        if OptionType.EVOLVE in option_types:
            return self._assessment(
                selection,
                stage=78,
                attack_lines=self._ready_attacker_count(decision.state),
                reasons=("evolve_priority_line",),
            )
        if OptionType.ABILITY in option_types:
            return self._assessment(selection, stage=76, reasons=("use_public_ability",))
        if OptionType.PLAY in option_types:
            best_role = max((self._play_priority(candidate) for candidate in selected), default=0)
            return self._assessment(
                selection,
                stage=65 + best_role,
                attack_lines=self._ready_attacker_count(decision.state),
                reasons=("develop_board_or_search",),
            )
        if OptionType.RETREAT in option_types:
            return self._assessment(
                selection,
                stage=60 if self._active_ko_risk(decision.state) else 40,
                reasons=("retreat_from_public_risk",),
            )
        if OptionType.DISCARD in option_types:
            return self._assessment(selection, stage=30, reasons=("resolve_legal_discard",))
        if OptionType.END in option_types:
            return self._assessment(selection, stage=10, reasons=("end_no_safe_improvement",))
        if decision.select_context is SelectContext.RECOVER_SPECIAL_CONDITION:
            return self._assessment(selection, stage=75, reasons=("recover_special_condition",))
        if option_types & {OptionType.YES, OptionType.NO}:
            return self._yes_no_assessment(selection, selected, prefer_yes=True)
        if OptionType.NUMBER in option_types:
            count = sum(self._number(candidate.option, "number", "count") for candidate in selected)
            return self._assessment(
                selection, stage=45, ready=count, reasons=("largest_beneficial_count",)
            )
        return self._assessment(selection, stage=20, reasons=("deterministic_legal_fallback",))

    def _discard_assessment(
        self,
        decision: ParsedDecision,
        selection: Selection,
        selected: Sequence[Candidate],
    ) -> OrdinalAssessment:
        categories = [self._discard_category(decision, candidate) for candidate in selected]
        worst = max(categories, default=5)
        total = sum(categories)
        return self._assessment(
            selection,
            stage=70,
            preservation=100 - worst * 10 - total,
            reasons=("declarative_discard_order", self._discard_reason(worst)),
        )

    def _promotion_assessment(
        self,
        decision: ParsedDecision,
        selection: Selection,
        selected: Sequence[Candidate],
    ) -> OrdinalAssessment:
        ready = max((self._candidate_ready(candidate) for candidate in selected), default=0)
        ko_risk = min(
            (self._candidate_ko_risk(decision.state, candidate) for candidate in selected),
            default=1,
        )
        prize_value = min(
            (self._candidate_prize_value(candidate) for candidate in selected), default=1
        )
        return self._assessment(
            selection,
            stage=75,
            ready=ready,
            ko_risk=ko_risk,
            prize_liability=prize_value,
            reasons=("promote_ready_attacker", "minimize_knockout_risk", "minimize_prize_value"),
        )

    def _setup_assessment(
        self,
        selection: Selection,
        selected: Sequence[Candidate],
        *,
        active: bool,
    ) -> OrdinalAssessment:
        development = max(
            (
                int(self._has_role(self._card_id(candidate), "development_priority"))
                for candidate in selected
            ),
            default=0,
        )
        secondary = max(
            (
                int(self._has_role(self._card_id(candidate), "secondary_attacker"))
                for candidate in selected
            ),
            default=0,
        )
        return self._assessment(
            selection,
            stage=70,
            ready=development * 2 + secondary,
            reasons=("setup_active" if active else "fill_bench_with_priority_line",),
        )

    def _search_assessment(
        self,
        decision: ParsedDecision,
        selection: Selection,
        selected: Sequence[Candidate],
    ) -> OrdinalAssessment:
        priorities = [self._search_priority(decision.state, candidate) for candidate in selected]
        return self._assessment(
            selection,
            stage=70,
            preservation=max(priorities, default=0),
            reasons=("search_declared_role",),
        )

    def _yes_no_assessment(
        self,
        selection: Selection,
        selected: Sequence[Candidate],
        *,
        prefer_yes: bool,
    ) -> OrdinalAssessment:
        preferred = any(
            (candidate.option_type is OptionType.YES) is prefer_yes for candidate in selected
        )
        return self._assessment(
            selection,
            stage=60,
            ready=int(preferred),
            reasons=("prefer_yes" if prefer_yes else "avoid_mulligan",),
        )

    def _assessment(
        self,
        selection: Selection,
        *,
        stage: int,
        prize_value: int = 0,
        effort: int = 0,
        guaranteed_damage: int = 0,
        potential_damage: int = 0,
        ready: int = 0,
        ko_risk: int = 0,
        prize_liability: int = 0,
        attack_lines: int = 0,
        preservation: int = 0,
        exposure: int = 0,
        reasons: tuple[str, ...],
    ) -> OrdinalAssessment:
        first_index = min(selection.indices, default=0)
        return OrdinalAssessment(
            key=(
                stage,
                prize_value,
                -effort,
                guaranteed_damage,
                potential_damage,
                ready,
                -ko_risk,
                -prize_liability,
                attack_lines,
                preservation,
                -exposure,
                -first_index,
            ),
            reasons=reasons,
        )

    def _guaranteed_damage(self, decision: ParsedDecision, candidate: Candidate) -> int:
        explicit = self._number(candidate.option, "guaranteedDamage", "damage")
        if explicit:
            return explicit
        plan = self._attack_plan(candidate)
        if plan is not None:
            if plan.damage_per_basic_energy_in_discard:
                return plan.damage_per_basic_energy_in_discard * self._discard_role_count(
                    decision.state,
                    plan.basic_energy_role,
                )
            return plan.guaranteed_damage
        return self._number(candidate.attack or {}, "damage")

    def _potential_damage(self, candidate: Candidate) -> int:
        explicit = self._number(candidate.option, "potentialDamage", "expectedDamage")
        if explicit:
            return explicit
        plan = self._attack_plan(candidate)
        if plan is not None:
            return max(plan.guaranteed_damage, plan.potential_damage)
        return self._number(candidate.attack or {}, "damage")

    def _target_hp(self, decision: ParsedDecision, selected: Sequence[Candidate]) -> int:
        explicit = max(
            (
                self._number(candidate.option, "targetHp")
                or self._feature_int(candidate, "target_hp")
                for candidate in selected
            ),
            default=0,
        )
        if explicit:
            return explicit
        opponent = self._opponent(decision.state)
        return opponent.active.hp if opponent and opponent.active else 0

    def _target_prize_value(self, selected: Sequence[Candidate], prize_map: PrizeMap | None) -> int:
        explicit = max(
            (
                self._number(candidate.option, "prizeValue", "prizes")
                or self._feature_int(candidate, "target_base_prize_value")
                for candidate in selected
            ),
            default=0,
        )
        if explicit:
            return explicit
        active = (
            next(
                (target for target in prize_map.targets if target.zone == "active"),
                None,
            )
            if prize_map
            else None
        )
        return active.effective_prize_value if active else 0

    def _terminal_ko(
        self,
        state: GameState,
        selected: Sequence[Candidate],
        proven_ko: bool,
        prize_value: int,
    ) -> bool:
        if not proven_ko:
            return False
        own = self._own(state)
        opponent = self._opponent(state)
        last_prize = bool(own and own.prize and prize_value >= len(own.prize))
        targets_active = all(
            self._truthy(candidate.option, "targetIsActive")
            or bool(candidate.features.get("target_is_active"))
            or candidate.option_type is OptionType.ATTACK
            for candidate in selected
        )
        no_other_pokemon = bool(
            opponent
            and opponent.active
            and targets_active
            and not any(item is not None for item in opponent.bench)
        )
        return last_prize or no_other_pokemon

    def _active_damage_prevented(self, prize_map: PrizeMap | None) -> bool:
        return bool(
            prize_map
            and any(
                target.zone == "active" and target.damage_prevented for target in prize_map.targets
            )
        )

    def _attack_plan(self, candidate: Candidate) -> AttackPlan | None:
        attack_id = candidate.option.get("attackId")
        if isinstance(attack_id, str) and attack_id.isdigit():
            attack_id = int(attack_id)
        if isinstance(attack_id, int) and self.deck_profile:
            return self.deck_profile.attack_plans.get(attack_id)
        return None

    def _attack_effort(self, candidate: Candidate) -> int:
        explicit = self._number(candidate.option, "energyCost", "cost")
        if explicit:
            return explicit
        plan = self._attack_plan(candidate)
        if plan is not None:
            return plan.energy_cost
        energies = (candidate.attack or {}).get("energies", [])
        return len(energies) if isinstance(energies, list) else 0

    def _previous_own_attack(self, decision: ParsedDecision, attack_id: int) -> bool:
        own_index = decision.state.your_index
        own_attacks = [
            log
            for log in decision.logs
            if isinstance(log, Mapping)
            and log.get("playerIndex") == own_index
            and isinstance(log.get("attackId"), int)
        ]
        return bool(own_attacks and own_attacks[-1].get("attackId") == attack_id)

    def _discard_category(self, decision: ParsedDecision, candidate: Candidate) -> int:
        card_id = self._card_id(candidate)
        card_type = self._card_type(candidate)
        if self._has_role(card_id, "basic_energy"):
            return 0
        if self._has_role(card_id, "powerglass"):
            return 1
        if card_type == 3 and (
            decision.state.supporter_played or self._visible_count(decision.state, card_id) > 1
        ):
            return 2
        if card_type == 0 and self._visible_count(decision.state, card_id) > 1:
            return 3
        if card_type == 0 or self._is_unique_resource(card_id):
            return 5
        return 4

    def _discard_reason(self, category: int) -> str:
        return {
            0: "discard_basic_energy",
            1: "discard_unneeded_powerglass",
            2: "discard_redundant_supporter",
            3: "discard_duplicate_pokemon",
            4: "discard_replaceable_resource",
            5: "preserve_last_or_unique_resource",
        }.get(category, "discard_replaceable_resource")

    def _attachment_enables_attack(self, candidate: Candidate) -> int:
        if self._truthy(candidate.option, "enablesAttack", "enables"):
            return 1
        card_id = self._feature_int(candidate, "target_card_id")
        energy_count = self._feature_int(candidate, "target_energy_count")
        target = self._attack_energy_target(card_id)
        return int(target > 0 and energy_count < target <= energy_count + 1)

    def _candidate_ready(self, candidate: Candidate) -> int:
        if self._truthy(candidate.option, "readyAttacker", "canAttack"):
            return 1
        card_id = self._card_id(candidate) or self._feature_int(candidate, "target_card_id")
        energy_count = max(
            self._feature_int(candidate, "card_energy_count"),
            self._feature_int(candidate, "target_energy_count"),
        )
        target = self._attack_energy_target(card_id)
        return int(target > 0 and energy_count >= target)

    def _candidate_ko_risk(self, state: GameState, candidate: Candidate) -> int:
        explicit = self._number(candidate.option, "koRisk", "knockoutRisk")
        if explicit:
            return explicit
        hp = max(
            self._feature_int(candidate, "card_hp"),
            self._feature_int(candidate, "target_hp"),
        )
        if hp <= 0:
            hp = self._number(candidate.option, "hp")
        return int(hp > 0 and self._opponent_guaranteed_damage(state) >= hp)

    def _candidate_prize_value(self, candidate: Candidate) -> int:
        explicit = self._number(candidate.option, "prizeValue", "prizes")
        if explicit:
            return explicit
        card_id = self._card_id(candidate) or self._feature_int(candidate, "target_card_id")
        if self.deck_profile and card_id in self.deck_profile.prize_values:
            return self.deck_profile.prize_values[card_id]
        return self.catalog.get_traits(str(card_id)).base_prize_value

    def _play_priority(self, candidate: Candidate) -> int:
        card_id = self._card_id(candidate)
        if self._has_role(card_id, "development_priority"):
            return 9
        if self._has_role(card_id, "ace_spec"):
            return 8
        if self._has_role(card_id, "evolution_search"):
            return 7
        if self._has_role(card_id, "general_search"):
            return 6
        if self._has_role(card_id, "free_switch"):
            return 5
        if self._card_type(candidate) == 0:
            return 4
        return 1

    def _search_priority(self, state: GameState, candidate: Candidate) -> int:
        card_id = self._card_id(candidate)
        if self._has_role(card_id, "ace_spec"):
            return 100
        if self._has_role(card_id, "development_priority"):
            return 90
        if self._has_role(card_id, "primary_attacker"):
            return 80
        if self._has_role(card_id, "evolution_search"):
            return 70
        if self._has_role(card_id, "general_search"):
            return 60
        if self._has_role(card_id, "free_switch") and self._active_ko_risk(state):
            return 85
        if self.deck_profile:
            return int(self.deck_profile.resource_values.get(card_id, 0))
        return 0

    def _attack_energy_target(self, card_id: int) -> int:
        if self.deck_profile:
            return max(0, self.deck_profile.attack_energy_targets.get(card_id, 0))
        return 0

    def _ready_attacker_count(self, state: GameState) -> int:
        own = self._own(state)
        if own is None:
            return 0
        pokemon = [own.active, *own.bench]
        return sum(
            1
            for item in pokemon
            if item is not None
            and isinstance(item.card_id, int)
            and len(item.energies) >= self._attack_energy_target(item.card_id) > 0
        )

    def _active_ko_risk(self, state: GameState) -> bool:
        own = self._own(state)
        return bool(
            own
            and own.active
            and own.active.hp > 0
            and self._opponent_guaranteed_damage(state) >= own.active.hp
        )

    def _opponent_guaranteed_damage(self, state: GameState) -> int:
        opponent = self._opponent(state)
        if opponent is None or opponent.active is None:
            return 0
        card = self.catalog.get_card(str(opponent.active.card_id)) or {}
        damage = 0
        for attack_id in card.get("attacks", []):
            attack = self.catalog.get_attack(str(attack_id)) or {}
            value = attack.get("damage", 0)
            if isinstance(value, int) and not isinstance(value, bool):
                damage = max(damage, value)
        return damage

    def _own_active_has_condition(self, state: GameState) -> bool:
        own = self._own(state)
        active = own.active if own else None
        return bool(
            active
            and (
                active.poisoned
                or active.burned
                or active.asleep
                or active.paralyzed
                or active.confused
            )
        )

    def _discard_role_count(self, state: GameState, role: str) -> int:
        own = self._own(state)
        if own is None:
            return 0
        return sum(1 for card in own.discard if self._has_role(self._raw_card_id(card), role))

    def _visible_count(self, state: GameState, card_id: int) -> int:
        if card_id <= 0:
            return 0
        own = self._own(state)
        if own is None:
            return 0
        cards: list[Any] = [*(own.hand or []), *own.discard, own.active, *own.bench]
        return sum(self._raw_card_id(card) == card_id for card in cards)

    def _is_unique_resource(self, card_id: int) -> bool:
        return bool(
            card_id > 0 and self._deck is not None and self._deck.counts.get(card_id, 0) == 1
        )

    def _has_role(self, card_id: int, role: str) -> bool:
        return bool(self.deck_profile and self.deck_profile.has_role(card_id, role))

    def _card_id(self, candidate: Candidate) -> int:
        value = candidate.features.get("card_id") or candidate.option.get("cardId")
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return 0

    def _raw_card_id(self, card: Any) -> int:
        if isinstance(card, int) and not isinstance(card, bool):
            return card
        if isinstance(card, Mapping):
            value = card.get("id", card.get("cardId"))
            if isinstance(value, int) and not isinstance(value, bool):
                return value
        return 0

    def _card_type(self, candidate: Candidate) -> int:
        value = (candidate.card or {}).get("cardType")
        return value if isinstance(value, int) and not isinstance(value, bool) else -1

    def _feature_int(self, candidate: Candidate, name: str) -> int:
        value = candidate.features.get(name, 0)
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

    def _number(self, mapping: Mapping[str, Any], *names: str) -> int:
        for name in names:
            value = mapping.get(name)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return int(value)
        return 0

    def _truthy(self, mapping: Mapping[str, Any], *names: str) -> bool:
        return any(bool(mapping.get(name, False)) for name in names)

    def _own(self, state: GameState) -> Any:
        return (
            state.players[state.your_index] if 0 <= state.your_index < len(state.players) else None
        )

    def _opponent(self, state: GameState) -> Any:
        index = 1 - state.your_index
        return state.players[index] if 0 <= index < len(state.players) else None


class HdiAgent(AgentPolicy):
    """Select legal CABT indices with the deterministic HDI v1 rule order."""

    def __init__(
        self,
        deck_profile: DeckProfile | None = None,
        catalog: CardCatalog | None = None,
    ) -> None:
        active_catalog = catalog or _CATALOG
        self._parser = DefaultParser(active_catalog)
        self._generator = DefaultSelectionGenerator()
        self._baseline = BaselineAgent()
        self._configured_profile = deck_profile
        self._active_deck_profile = deck_profile
        self._deck: DeckDefinition | None = None
        self._prize_checker: PrizeChecker | None = None
        self._prize_map_builder = PrizeMapBuilder(active_catalog)
        self._engine = HdiOrdinalEngine(deck_profile, active_catalog)
        self._feature_extractor = SelectionFeatureExtractor(self._engine)
        self._last_decision: PolicyDecision | None = None

    def start_match(self, deck: DeckDefinition) -> None:
        """Reset match-scoped public state and resolve the active deck profile."""
        self._deck = deck
        self._prize_checker = PrizeChecker(deck)
        profile = (
            self._configured_profile
            if self._configured_profile and self._configured_profile.deck_sha256 == deck.sha256
            else GenericDeckProfileBuilder(self._engine.catalog).build(deck)
        )
        evolution_basics = tuple(sorted({line[0] for line in profile.evolution_lines if line}))
        roles = dict(profile.roles)
        roles["evolution_basic"] = evolution_basics
        self._active_deck_profile = replace(profile, roles=roles)
        self._engine.set_deck_profile(self._active_deck_profile)

    @property
    def last_decision(self) -> PolicyDecision | None:
        """Return the latest auditable HDI decision."""
        return self._last_decision

    def select(self, observation: dict[str, Any]) -> list[int]:
        """Return original simulator indices for the best legal selection."""
        try:
            return list(self.decide(observation).selection.indices)
        except Exception:
            return self._baseline.select(observation)

    def decide(self, observation: dict[str, Any]) -> PolicyDecision:
        """Return the complete ordinal ranking for one actor-visible observation."""
        started = time.perf_counter()
        parsed = self._parser.parse(observation)
        if parsed.max_count == 0:
            return self._empty_decision(started)
        selections = self._generator.generate(
            parsed.candidates,
            parsed.min_count,
            parsed.max_count,
            parsed.remain_energy_cost,
            parsed.remain_damage_counter,
        )
        if not selections:
            return self._empty_decision(started)
        contextualized = [
            replace(selection, context=parsed.select_context) for selection in selections
        ]
        prize_map = self._prize_map_builder.build(parsed.state)
        prize_check = self._prize_checker.check(observation) if self._prize_checker else None
        self._engine.set_context(parsed, prize_map, self._deck)
        assessed = [
            (selection, self._engine.assess(parsed, selection, prize_map))
            for selection in contextualized
        ]
        assessed.sort(key=lambda item: item[1].key, reverse=True)
        ranked = tuple(
            RankedSelection(
                selection=selection,
                score=float(assessment.key[0]),
                rank=rank,
                reasons=assessment.reasons,
            )
            for rank, (selection, assessment) in enumerate(assessed, start=1)
        )
        features = self._feature_extractor.extract(
            parsed,
            contextualized,
            deck_profile=self._active_deck_profile,
            prize_check=prize_check,
        )
        result = PolicyDecision(
            selection=ranked[0].selection,
            ranked=ranked,
            features=tuple(features),
            fallback_used=False,
            model_backend="hdi_v1",
            model_version="hdi-v1",
            duration_ms=(time.perf_counter() - started) * 1000.0,
        )
        self._last_decision = result
        return result

    def _empty_decision(self, started: float) -> PolicyDecision:
        result = PolicyDecision(
            selection=Selection(indices=(), option_types=()),
            ranked=(),
            features=(),
            fallback_used=True,
            model_backend="hdi_v1",
            model_version="hdi-v1",
            duration_ms=(time.perf_counter() - started) * 1000.0,
        )
        self._last_decision = result
        return result
