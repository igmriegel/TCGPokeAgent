"""Deck-specific heuristic policy for the Honchkrow/Porygon deck."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.agents.heuristic import _CG_CATALOG, HeuristicAgent, SimpleHeuristicScorer
from src.core import Candidate, DeckProfile, GameState, OptionType, SelectContext
from src.ranking.features import SelectionFeatureExtractor

MURKROW = 463
HONCHKROW = 891
PORYGON = 473
PORYGON2 = 474
ARTICUNO = 414
ARIANA = 1216
ARCHER = 1217
GIOVANNI = 1218
PETREL = 1219
PROTON = 1220
POKE_PAD = 1152
TRANSCEIVER = 1134
ROTO_STICK = 1077
NIGHT_STRETCHER = 1097
ULTRA_BALL = 1121
MIRACLE_HEADSET = 1109
FACTORY = 1257
ROCKET_ENERGY = 15
IGNITION_ENERGY = 17
ROCKET_FEATHERS = 1285
R_COMMAND = 670
ARTICUNO_ATTACK = 583


class HonchkrowPorygonScorer(SimpleHeuristicScorer):
    """Score selections using the reviewed Honchkrow/Porygon priorities."""

    def _sdk_score(
        self,
        state: GameState,
        candidate: Candidate,
        context: SelectContext | None,
    ) -> tuple[float, list[str]]:
        if context is SelectContext.IS_FIRST:
            if candidate.option_type is OptionType.YES:
                return 1000.0, ["choose_first_for_proton_setup"]
            if candidate.option_type is OptionType.NO:
                return -1000.0, ["decline_second_turn"]
        return super()._sdk_score(state, candidate, context)

    def _play_score(self, state: GameState, candidate: Candidate) -> tuple[float, list[str]]:
        card_id = self._feature_int(candidate, "card_id")
        card_type = self._metadata_int(candidate.card, "cardType")
        if card_type == 0:
            if card_id == ARTICUNO:
                if self._opponent_has_effect_threat(state):
                    return 920.0, ["play_articuno_tech"]
                return -1500.0, ["preserve_articuno_until_effect_threat"]
            if card_id == HONCHKROW:
                return 620.0, ["develop_primary_honchkrow"]
            if card_id == PORYGON2:
                return 480.0, ["develop_secondary_porygon"]
            return 430.0, ["develop_attacker_line"]
        if card_id == ARIANA:
            return 900.0, ["ariana_hand_refresh_and_energy_access"]
        if card_id == PROTON:
            return 650.0, ["proton_basic_pokemon_setup"]
        if card_id == TRANSCEIVER:
            return 610.0, ["transceiver_supporter_access"]
        if card_id == POKE_PAD:
            return 575.0, ["poke_pad_attacker_search"]
        if card_id == ULTRA_BALL:
            return 590.0, ["ultra_ball_attacker_search_or_r_command_boost"]
        if card_id == FACTORY:
            return 560.0, ["establish_factory_draw_engine"]
        if card_id == PETREL:
            return 430.0, ["petrel_specific_trainer_search"]
        if card_id in {ROTO_STICK, MIRACLE_HEADSET, NIGHT_STRETCHER}:
            return 380.0, ["play_resource_utility"]
        if card_type == 3:
            return 340.0, ["play_supporter_for_factory"]
        return super()._play_score(state, candidate)

    def _attachment_score(self, state: GameState, candidate: Candidate) -> tuple[float, list[str]]:
        card_type = self._metadata_int(candidate.card, "cardType")
        target_id = self._feature_int(candidate, "target_card_id")
        energy_count = self._feature_int(candidate, "target_energy_count")
        if card_type not in {5, 6}:
            return super()._attachment_score(state, candidate)
        target = 0
        if target_id == HONCHKROW:
            target = 260
        elif target_id == PORYGON2:
            target = 190
        elif target_id == MURKROW:
            target = 120
        elif target_id == ARTICUNO and self._opponent_has_effect_threat(state):
            target = 170
        if energy_count >= self._attack_energy_target(target_id):
            return -500.0, ["avoid_energy_above_attack_plan"]
        if card_type == 6 and self._feature_int(candidate, "card_id") == IGNITION_ENERGY:
            target += 45
        if self._feature_int(candidate, "card_id") == ROCKET_ENERGY:
            target += 25
        return 300.0 + target, ["attach_energy_to_attack_line"]

    def _attack_score(self, state: GameState, candidate: Candidate) -> tuple[float, list[str]]:
        attack_id = self._attack_id(candidate)
        if attack_id == ROCKET_FEATHERS:
            damage = self._rocket_supporters_in_discard(state) * 60
            bonus = 700.0 if self._own_active_card_id(state) == HONCHKROW else 0.0
            return 300.0 + damage + bonus, ["honchkrow_rocket_feathers", "rocket_discard_damage"]
        if attack_id == R_COMMAND:
            damage = self._rocket_supporters_in_discard(state) * 20
            return 250.0 + damage, ["porygon2_r_command", "rocket_discard_damage"]
        if attack_id == ARTICUNO_ATTACK:
            damage = 60 + (60 if self._active_has_rocket_energy(state) else 0)
            return 260.0 + damage, ["articuno_dark_frost"]
        return super()._attack_score(state, candidate)

    def _card_selection_score(
        self,
        state: GameState,
        candidate: Candidate,
        context: SelectContext | None,
    ) -> tuple[float, list[str]]:
        card_id = self._feature_int(candidate, "card_id")
        if card_id == ARTICUNO and context in {
            SelectContext.SETUP_ACTIVE_POKEMON,
            SelectContext.SETUP_BENCH_POKEMON,
            SelectContext.TO_ACTIVE,
            SelectContext.TO_FIELD,
            SelectContext.TO_HAND,
        }:
            if self._opponent_has_effect_threat(state):
                return 700.0, ["select_articuno_tech"]
            return -1500.0, ["avoid_articuno_without_effect_threat"]
        if context in {SelectContext.DISCARD, SelectContext.DISCARD_CARD_OR_ATTACHED_CARD}:
            if self._is_rocket_supporter(card_id, candidate.card):
                return 220.0, ["discard_redundant_rocket_supporter"]
            if card_id in {MURKROW, HONCHKROW, PORYGON, PORYGON2, ARTICUNO}:
                return -150.0, ["preserve_pokemon_line"]
        return super()._card_selection_score(state, candidate, context)

    def _opponent_has_effect_threat(self, state: GameState) -> bool:
        opponent = self._opponent_player(state)
        if opponent is None:
            return False
        for pokemon in [opponent.active, *opponent.bench]:
            if pokemon is None or not isinstance(pokemon.card_id, int):
                continue
            card = self.catalog.get_card(str(pokemon.card_id)) or {}
            for attack_id in card.get("attacks", []):
                attack = self.catalog.get_attack(str(attack_id)) or {}
                text = str(attack.get("text", "")).casefold()
                if any(
                    marker in text
                    for marker in (
                        "prevent",
                        "can't use",
                        "cant use",
                        "discard",
                        "poison",
                        "paraly",
                        "confus",
                        "asleep",
                        "damage counter",
                        "switch",
                    )
                ):
                    return True
        return False

    def _rocket_supporters_in_discard(self, state: GameState) -> int:
        player = self._own_player(state)
        if player is None:
            return 0
        return sum(
            1
            for card in player.discard
            if isinstance(card, Mapping)
            and self._is_rocket_supporter(
                int(card.get("id", card.get("cardId", 0)) or 0),
                self.catalog.get_card(str(card.get("id", card.get("cardId", 0)))) or {},
            )
        )

    def _active_has_rocket_energy(self, state: GameState) -> bool:
        active = self._own_active(state)
        return bool(
            active
            and any(
                isinstance(energy, Mapping)
                and int(energy.get("id", energy.get("cardId", 0)) or 0) == ROCKET_ENERGY
                for energy in active.energies
            )
        )

    @staticmethod
    def _is_rocket_supporter(card_id: int, card: Mapping[str, Any] | None) -> bool:
        return card_id in {ARIANA, ARCHER, GIOVANNI, PETREL, PROTON} or (
            isinstance(card, Mapping)
            and int(card.get("cardType", -1)) == 3
            and "team rocket" in str(card.get("name", "")).casefold()
        )

    @staticmethod
    def _attack_id(candidate: Candidate) -> int:
        value = candidate.option.get("attackId")
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value if isinstance(value, int) and not isinstance(value, bool) else 0


class HonchkrowPorygonAgent(HeuristicAgent):
    """Run the isolated Honchkrow/Porygon heuristic with shared legal plumbing."""

    def __init__(self, profile: DeckProfile) -> None:
        super().__init__(deck_profile=profile)
        self._scorer = HonchkrowPorygonScorer(deck_profile=profile, catalog=_CG_CATALOG)
        self._feature_extractor = SelectionFeatureExtractor(self._scorer)
        self._configured_profile = profile
        self._active_deck_profile = profile

    def _update_alakazam_matchup(self, observation: Mapping[str, Any], state: GameState) -> None:
        return None

    def _filter_fezandipiti_bench_line(
        self,
        state: GameState,
        selections: list[Any],
        candidates: list[Candidate],
    ) -> list[Any]:
        return list(selections)

    def _candidate_is_forbidden(
        self,
        state: GameState,
        candidate: Candidate | None,
        context: SelectContext | None,
    ) -> bool:
        if candidate is None:
            return False
        card_type = self._scorer._metadata_int(candidate.card, "cardType")
        target_id = self._scorer._feature_int(candidate, "target_card_id")
        card_id = self._scorer._feature_int(candidate, "card_id")
        if candidate.option_type is OptionType.ATTACH and card_type in {5, 6}:
            return self._scorer._feature_int(
                candidate, "target_energy_count"
            ) >= self._scorer._attack_energy_target(target_id)
        if card_id == ARTICUNO and not self._scorer._opponent_has_effect_threat(state):
            return candidate.option_type is OptionType.PLAY or (
                candidate.option_type is OptionType.CARD
                and context
                in {
                    SelectContext.SETUP_ACTIVE_POKEMON,
                    SelectContext.SETUP_BENCH_POKEMON,
                    SelectContext.TO_ACTIVE,
                    SelectContext.TO_FIELD,
                    SelectContext.TO_HAND,
                }
            )
        return False
