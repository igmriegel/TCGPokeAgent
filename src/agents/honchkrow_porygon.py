"""Deck-specific heuristic policy for the Honchkrow/Porygon deck."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.agents.heuristic import (
    _CG_CATALOG,
    DecisionPhase,
    HeuristicAgent,
    SimpleHeuristicScorer,
)
from src.core import (
    Candidate,
    DeckDefinition,
    DeckProfile,
    GameState,
    OptionType,
    SelectContext,
    Selection,
)
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
HACKING = 669
DECEIT = 652
TORMENT = 653
HAMMER_IN = 1286
ARTICUNO_ATTACK = 583
DREEPY = 119
DRAKLOAK = 120
DRAGAPULT_EX = 121


class HonchkrowPorygonScorer(SimpleHeuristicScorer):
    """Score selections using the reviewed Honchkrow/Porygon priorities."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._proton_used_previous_turn = False

    @property
    def _strategy(self) -> Mapping[str, Any]:
        """Return the immutable strategic data declared by this deck profile."""
        return self.deck_profile.strategic_context if self.deck_profile else {}

    def set_proton_used_previous_turn(self, used: bool) -> None:
        """Set the public early-game Proton history for the current decision."""
        self._proton_used_previous_turn = used

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
            if self._own_field_count(state) < 2 and card_id in {MURKROW, PORYGON}:
                return 1800.0, ["opening_backup_pokemon"]
            if card_id == ARTICUNO:
                if self._articuno_is_needed(state):
                    return 920.0, ["play_articuno_matchup_tech"]
                if self._articuno_hand_reduction_needed(state, candidate):
                    return 260.0, ["play_articuno_to_reduce_hand"]
                return -1500.0, ["preserve_articuno_until_needed"]
            if card_id == HONCHKROW:
                return 620.0, ["develop_primary_honchkrow"]
            if card_id == PORYGON2:
                return 480.0, ["develop_secondary_porygon"]
            return 430.0, ["develop_attacker_line"]
        if card_id == ARIANA:
            if 1 <= state.turn <= 2 and self._proton_targets_remaining(state):
                return 300.0, ["delay_ariana_for_early_proton"]
            return 900.0, ["ariana_hand_refresh_and_energy_access"]
        if card_id == GIOVANNI:
            if self._giovanni_is_lethal_or_promoting(state, candidate):
                return 1600.0, ["giovanni_immediate_ko_line"]
            if self._supporters_in_hand_after(card_id, state) >= self._supporters_needed_for_ko(
                state
            ):
                return 760.0, ["giovanni_preserves_ko_supporters"]
            return 80.0, ["giovanni_preserves_supporters_until_ko"]
        if card_id == PROTON:
            targets = self._proton_targets_remaining(state)
            if self._own_bench_full(state):
                return -2400.0, ["proton_bench_full"]
            priority = self._proton_priority_score(state, targets)
            reasons = ["proton_targets_remaining"]
            if targets.get(MURKROW, 0) > 0:
                reasons.append("proton_murkrow_priority")
            if self._articuno_is_needed(state) and targets.get(ARTICUNO, 0) > 0:
                reasons.append("proton_matchup_articuno")
            return 420.0 + priority, reasons
        if card_id == TRANSCEIVER:
            if self._early_proton_window(state) and self._proton_targets_exist(state):
                return 1200.0, ["transceiver_proton_early_game"]
            if self._proton_was_used_previous_turn(state):
                return 690.0, ["transceiver_ariana_after_proton"]
            return 720.0, ["transceiver_proton_early_game"]
        if card_id == POKE_PAD:
            if self._pokepad_honchkrow_is_useful(state, candidate):
                return 860.0, ["poke_pad_honchkrow_search"]
            return 620.0, ["poke_pad_murkrow_search"]
        if card_id == ULTRA_BALL:
            return 590.0, ["ultra_ball_attacker_search_or_r_command_boost"]
        if card_id == FACTORY:
            return 560.0, ["establish_factory_draw_engine"]
        if card_id == PETREL:
            if self._petrel_is_emergency(state):
                return 820.0, ["petrel_emergency_ariana_search"]
            return -900.0, ["avoid_petrel_generic_supporter_search"]
        if card_id == ROTO_STICK:
            if self._roto_stick_is_needed(state):
                return 760.0, ["roto_stick_closes_ko_line"]
            return -1800.0, ["preserve_roto_stick_for_supporter_ko"]
        if card_id in {MIRACLE_HEADSET, NIGHT_STRETCHER}:
            return 380.0, ["play_resource_utility"]
        if card_type == 4:
            return 700.0, ["stadium_before_supporter"]
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
        elif target_id == ARTICUNO and self._articuno_is_needed(state):
            target = 170
        if energy_count >= self._attack_energy_target(target_id):
            return -500.0, ["avoid_energy_above_attack_plan"]
        if card_type == 6 and self._feature_int(candidate, "card_id") == IGNITION_ENERGY:
            if not self._ignition_attachment_is_productive(state, candidate):
                return -2400.0, ["ignition_energy_without_attack_line"]
            target += 180
        if self._feature_int(candidate, "card_id") == ROCKET_ENERGY:
            target += 25
        return 300.0 + target, ["attach_energy_to_attack_line"]

    def _attack_score(self, state: GameState, candidate: Candidate) -> tuple[float, list[str]]:
        attack_id = self._attack_id(candidate)
        target = self._target_opponent_pokemon(state, candidate)
        opponent_hp = (
            self._effective_target_hp(state, target)
            if target is not None
            else self._effective_opponent_hp(state)
        )
        explicit_damage = max(
            self._metadata_int(candidate.attack, "damage"),
            self._metadata_int(candidate.option, "damage"),
            self._metadata_int(candidate.option, "expectedDamage"),
        )
        if self._truthy(candidate.option, "win", "wins", "gameOver"):
            return 5000.0, ["honchkrow_win_now"]
        reasons: list[str] = ["honchkrow_attack_for_prize_progress"]
        score = 260.0 + explicit_damage
        if self._truthy(candidate.option, "ko", "knockout", "isKo") or (
            explicit_damage > 0 and opponent_hp > 0 and explicit_damage >= opponent_hp
        ):
            score += 1500.0
            reasons.append("honchkrow_guaranteed_ko")
        if attack_id == ROCKET_FEATHERS:
            supporters = self._supporter_zone_counts(state)
            damage = supporters["hand"] * 60
            bonus = 700.0 if self._own_active_card_id(state) == HONCHKROW else 0.0
            reasons = ["honchkrow_rocket_feathers", "rocket_hand_damage"]
            if damage < self._effective_opponent_hp(state):
                reasons.append("rocket_feathers_below_ko_threshold")
                bonus -= 450.0
            if supporters["hand"] == 0:
                bonus -= 1000.0
            score = max(score, 300.0 + damage + bonus)
            if damage >= opponent_hp > 0:
                score += 1100.0
                reasons.append("rocket_feathers_ko")
            return score, reasons
        if attack_id == R_COMMAND:
            damage = self._rocket_supporters_in_discard(state) * 20
            if damage >= opponent_hp > 0:
                score += 900.0
                reasons.append("r_command_ko")
            return max(score, 250.0 + damage), [
                "porygon2_r_command",
                "rocket_discard_damage",
                *reasons,
            ]
        if attack_id == HAMMER_IN:
            damage = max(100, explicit_damage)
            if damage >= opponent_hp > 0:
                score += 1200.0
                reasons.append("hammer_in_ko")
            return score + damage, ["hammer_in_fixed_damage", *reasons]
        if attack_id == HACKING:
            return -5000.0, ["hacking_forbidden", "hacking_without_decisive_interrupt"]
        if attack_id == DECEIT:
            if not self._deceit_is_decisive(state, candidate, explicit_damage):
                return -2200.0, ["deceit_without_decisive_damage_or_interrupt"]
            return 420.0 + explicit_damage, ["deceit_contextual_tempo"]
        if attack_id == TORMENT:
            if self._truthy(candidate.option, "preventsAttack", "disablesAttack"):
                return 560.0 + explicit_damage, ["torment_blocks_next_attack"]
            return 300.0 + explicit_damage, ["torment_damage_only"]
        if attack_id == ARTICUNO_ATTACK:
            return -3000.0, ["articuno_never_attacks_in_honchkrow"]
        return super()._attack_score(state, candidate)

    def _card_selection_score(
        self,
        state: GameState,
        candidate: Candidate,
        context: SelectContext | None,
    ) -> tuple[float, list[str]]:
        card_id = self._feature_int(candidate, "card_id")
        if context is SelectContext.TO_HAND and card_id == PROTON:
            if self._early_proton_window(state) and self._proton_targets_exist(state):
                return 1800.0, ["select_proton_for_early_setup"]
        if context is SelectContext.TO_HAND and card_id == HONCHKROW:
            if self._pokepad_honchkrow_is_useful(state, candidate):
                return 1750.0, ["select_honchkrow_for_attack_or_hand_refresh"]
        if context is SelectContext.TO_HAND and card_id == ARIANA:
            if candidate.option.get("sourceCardId") == PETREL and self._petrel_is_emergency(state):
                return 1650.0, ["petrel_emergency_ariana"]
            if candidate.option.get("sourceCardId") == PETREL:
                return -1800.0, ["avoid_petrel_generic_ariana"]
        is_effect_target = context is not None and context.value == "EFFECT_TARGET"
        if context in {SelectContext.TO_ACTIVE, SelectContext.SWITCH} or is_effect_target:
            if is_effect_target and card_id not in {
                HONCHKROW,
                PORYGON2,
                MURKROW,
                ARTICUNO,
            }:
                return super()._card_selection_score(state, candidate, context)
            if is_effect_target:
                return self._giovanni_target_score(state, candidate)
            if card_id == HONCHKROW and self._pokemon_is_ready(state, candidate):
                return 1500.0, ["promote_ready_honchkrow"]
            if card_id == PORYGON2 and self._pokemon_is_ready(state, candidate):
                return 1250.0, ["promote_ready_porygon2"]
            if card_id == MURKROW:
                return 100.0, ["promote_murkrow_only_without_evolved_attacker"]
            if card_id == ARTICUNO and not self._articuno_is_needed(state):
                return -1800.0, ["avoid_articuno_promotion_without_matchup"]
        if context is SelectContext.EFFECT_TARGET and self._contains_type(
            (candidate.card or {}).get("weakness") or (candidate.card or {}).get("weaknesses"),
            "dark",
        ):
            return 1400.0, ["giovanni_dark_weakness_target"]
        if card_id == ARTICUNO and context in {
            SelectContext.SETUP_ACTIVE_POKEMON,
            SelectContext.SETUP_BENCH_POKEMON,
            SelectContext.TO_ACTIVE,
            SelectContext.TO_FIELD,
            SelectContext.TO_HAND,
        }:
            if self._articuno_is_needed(state) or self._own_field_count(state) < 2:
                return 700.0, ["select_articuno_matchup_tech"]
            return -1500.0, ["avoid_articuno_without_matchup_need"]
        if context in {SelectContext.DISCARD, SelectContext.DISCARD_CARD_OR_ATTACHED_CARD}:
            if self._is_energy_card(card_id, candidate.card):
                return -2500.0, ["protect_energy_from_discard"]
            if self._is_rocket_supporter(card_id, candidate.card):
                if card_id == ARIANA:
                    if self._discard_is_required_for_ko(state, candidate):
                        return 1550.0, ["discard_ariana_to_close_ko"]
                    return -500.0, ["preserve_ariana_until_last"]
                if self._supporters_in_hand(state) <= 1:
                    return -1000.0, ["preserve_last_supporter"]
                return 220.0, ["discard_redundant_rocket_supporter"]
            if card_id in {MURKROW, HONCHKROW, PORYGON, PORYGON2, ARTICUNO}:
                return -150.0, ["preserve_pokemon_line"]
        if context is SelectContext.TO_HAND and card_id == ARTICUNO:
            return (260.0, ["recover_articuno_against_dragapult"])
        return super()._card_selection_score(state, candidate, context)

    def _own_field_count(self, state: GameState) -> int:
        """Count own Active and Bench Pokémon visible to the policy."""
        player = self._own_player(state)
        if player is None:
            return 0
        return int(player.active is not None) + sum(pokemon is not None for pokemon in player.bench)

    def _articuno_is_needed(self, state: GameState) -> bool:
        """Return whether public matchup evidence justifies Articuno."""
        return (
            self._visible_opponent_card_ids(state) & {DREEPY, DRAKLOAK, DRAGAPULT_EX, 741, 742, 743}
            != set()
        )

    def _own_bench_full(self, state: GameState) -> bool:
        player = self._own_player(state)
        return bool(player and self._own_bench_count(state) >= player.bench_max)

    def _declared_count(self, card_id: int) -> int:
        counts = self._strategy.get("pokemon_counts", {})
        value = (
            counts.get(str(card_id), counts.get(card_id, 0)) if isinstance(counts, Mapping) else 0
        )
        return int(value) if isinstance(value, (int, float)) else 0

    def _proton_targets_remaining(self, state: GameState) -> dict[int, int]:
        """Count visible-deck Proton targets after known cards are removed."""
        player = self._own_player(state)
        if player is None:
            return {}
        result: dict[int, int] = {}
        field = [player.active, *player.bench]
        for card_id in (MURKROW, PORYGON, PORYGON2, ARTICUNO):
            known = sum(
                1 for pokemon in field if pokemon is not None and pokemon.card_id == card_id
            )
            known += sum(
                1
                for card in list(player.hand or ()) + list(player.discard) + list(player.prize)
                if self._card_id_from_value(card) == card_id
            )
            result[card_id] = max(0, self._declared_count(card_id) - known)
        return result

    def _proton_priority_score(self, state: GameState, targets: Mapping[int, int]) -> float:
        values = {
            MURKROW: 520.0,
            PORYGON: 330.0,
            PORYGON2: 260.0,
            ARTICUNO: 520.0 if self._articuno_is_needed(state) else 60.0,
        }
        raw = max((values[key] for key, count in targets.items() if count > 0), default=-500.0)
        return raw - max(0, self._own_bench_count(state) - 1) * 100.0

    def _proton_targets_exist(self, state: GameState) -> bool:
        """Return whether Proton has at least one visible-deck target left."""
        return any(count > 0 for count in self._proton_targets_remaining(state).values())

    def _petrel_is_emergency(self, state: GameState) -> bool:
        """Return whether Petrel is the only available Rocket Supporter."""
        supporters = [
            self._card_id_from_value(card)
            for card in self._hand_cards(state)
            if self._card_id_from_value(card) in self._supporter_ids()
        ]
        return supporters == [PETREL]

    def _early_proton_window(self, state: GameState) -> bool:
        return 1 <= state.turn <= 2

    def _card_in_hand(self, state: GameState, card_id: int) -> bool:
        return any(self._card_id_from_value(card) == card_id for card in self._hand_cards(state))

    def _roto_stick_is_needed(self, state: GameState) -> bool:
        return self._supporters_needed_for_ko(state) > self._supporters_in_hand(state)

    @staticmethod
    def _is_energy_card(card_id: int, card: Mapping[str, Any] | None) -> bool:
        return card_id in {ROCKET_ENERGY, IGNITION_ENERGY} or (
            isinstance(card, Mapping) and int(card.get("cardType", -1)) in {5, 6}
        )

    def _target_opponent_pokemon(self, state: GameState, candidate: Candidate) -> Any:
        opponent = self._opponent_player(state)
        if opponent is None:
            return None
        target_id = self._feature_int(candidate, "target_card_id") or int(
            candidate.option.get("targetCardId", 0) or 0
        )
        return next(
            (
                p
                for p in [opponent.active, *opponent.bench]
                if p is not None and (not target_id or p.card_id == target_id)
            ),
            opponent.active,
        )

    def _effective_target_hp(self, state: GameState, target: Any) -> int:
        if target is None:
            return 0
        card = self.catalog.get_card(str(target.card_id)) or {}
        weakness = card.get("weakness") or card.get("weaknesses")
        if self._contains_type(weakness, "dark"):
            return (max(0, int(target.hp)) + 1) // 2
        return max(0, int(target.hp))

    def _ignition_attachment_is_productive(self, state: GameState, candidate: Candidate) -> bool:
        target_id = self._feature_int(candidate, "target_card_id")
        target_energy = self._feature_int(candidate, "target_energy_count")
        completes = target_energy + 1 >= self._attack_energy_target(target_id)
        explicit_damage = max(
            self._metadata_int(candidate.attack, "damage"),
            self._metadata_int(candidate.option, "damage"),
            self._metadata_int(candidate.option, "expectedDamage"),
        )
        return (
            completes
            and (
                explicit_damage > 0
                or bool(
                    candidate.option.get("enablesAttack", candidate.option.get("enables", False))
                )
            )
            and target_id in {HONCHKROW, PORYGON2, MURKROW}
        )

    def _deceit_is_decisive(self, state: GameState, candidate: Candidate, damage: int) -> bool:
        target = self._target_opponent_pokemon(state, candidate)
        return (
            damage > 0
            or (target is not None and damage >= self._effective_target_hp(state, target))
            or self._truthy(candidate.option, "decisive", "win", "gameOver")
        )

    def _has_murkrow_ready_to_evolve(self, state: GameState) -> bool:
        """Return whether a visible Murkrow can support Honchkrow search."""
        player = self._own_player(state)
        return bool(
            player
            and any(
                pokemon is not None and pokemon.card_id == MURKROW
                for pokemon in [player.active, *player.bench]
            )
        )

    def _pokepad_honchkrow_is_useful(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether Poké Pad fetching Honchkrow has an immediate purpose."""
        if self._has_murkrow_ready_to_evolve(state) or self._honchkrow_ready_to_attack(state):
            return True
        return self._articuno_hand_reduction_needed(state, candidate)

    def _giovanni_target_score(
        self, state: GameState, candidate: Candidate
    ) -> tuple[float, list[str]]:
        """Rank Giovanni targets by prize value, then lowest remaining HP."""
        target = self._target_opponent_pokemon(state, candidate)
        if target is None:
            return 0.0, ["giovanni_no_target_data"]
        prizes = int(
            candidate.option.get(
                "prizes", candidate.option.get("prizeCount", candidate.option.get("prizeValue", 1))
            )
            or 1
        )
        hp = max(0, int(getattr(target, "hp", 0)))
        guaranteed = self._truthy(candidate.option, "ko", "knockout", "isKo")
        return 900.0 + prizes * 500.0 + max(0, 300 - hp) + (500.0 if guaranteed else 0.0), [
            "giovanni_highest_prize_target",
            "giovanni_lowest_hp_tiebreak",
            *(["giovanni_guaranteed_ko_target"] if guaranteed else []),
        ]

    def _discard_is_required_for_ko(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether the SDK explicitly marks this discard as KO-enabling."""
        return self._truthy(
            candidate.option,
            "requiredForKo",
            "enablesKo",
            "enablesKO",
            "koLine",
            "lethal",
        ) or bool(candidate.features.get("required_for_ko", False))

    def _honchkrow_ready_to_attack(self, state: GameState) -> bool:
        """Return whether a visible Honchkrow has its declared attack cost."""
        player = self._own_player(state)
        if player is None:
            return False
        return any(
            pokemon is not None
            and pokemon.card_id == HONCHKROW
            and len(pokemon.energies) >= self._attack_energy_target(HONCHKROW)
            for pokemon in [player.active, *player.bench]
        )

    @staticmethod
    def _card_selected_from_night_stretcher(candidate: Candidate) -> bool:
        """Return whether a card option is the payload of Night Stretcher."""
        source = candidate.option.get("sourceCardId", candidate.option.get("sourceId", 0))
        return bool(source == NIGHT_STRETCHER)

    def _visible_opponent_card_ids(self, state: GameState) -> set[int]:
        """Return Pokémon identifiers visible on the opposing field."""
        opponent = self._opponent_player(state)
        if opponent is None:
            return set()
        return {
            int(pokemon.card_id)
            for pokemon in [opponent.active, *opponent.bench]
            if pokemon is not None and isinstance(pokemon.card_id, int)
        }

    def _articuno_hand_reduction_needed(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether Articuno is a useful hand-size reduction play."""
        return bool(
            candidate.option.get("reducesHand", False)
            or candidate.option.get("handReduction", False)
            or (self._own_player(state) is not None and self._own_player(state).hand_count >= 8)
        )

    def _supporter_ids(self) -> set[int]:
        """Return all Team Rocket supporter identifiers in this deck."""
        return {ARIANA, ARCHER, GIOVANNI, PETREL, PROTON}

    def _hand_cards(self, state: GameState) -> list[Any]:
        """Return the visible own hand, or an empty list when it is hidden."""
        player = self._own_player(state)
        return list(player.hand or ()) if player is not None and player.hand is not None else []

    def _supporters_in_hand(self, state: GameState | None = None) -> int:
        """Count visible Team Rocket supporters in hand."""
        if state is None:
            state = self._energy_context_state
        if state is None:
            return 0
        return sum(
            1
            for card in self._hand_cards(state)
            if self._is_rocket_supporter(
                self._card_id_from_value(card),
                self.catalog.get_card(str(self._card_id_from_value(card))) or {},
            )
        )

    def _supporters_in_hand_after(
        self, excluded_card_id: int, state: GameState | None = None
    ) -> int:
        """Count supporters after hypothetically playing one supporter."""
        return max(
            0, self._supporters_in_hand(state) - int(excluded_card_id in self._supporter_ids())
        )

    def _pokemon_is_ready(self, state: GameState, candidate: Candidate) -> bool:
        energy_count = int(
            candidate.features.get("target_energy_count", candidate.features.get("energy_count", 0))
        )
        if energy_count:
            return energy_count >= self._attack_energy_target(
                self._feature_int(candidate, "card_id")
            )
        player = self._own_player(state)
        return bool(
            player
            and any(
                pokemon is not None
                and pokemon.card_id == self._feature_int(candidate, "card_id")
                and len(pokemon.energies) >= self._attack_energy_target(int(pokemon.card_id))
                for pokemon in player.bench
            )
        ) or bool(candidate.option.get("ready", candidate.option.get("energized", False)))

    def _giovanni_is_lethal_or_promoting(self, state: GameState, candidate: Candidate) -> bool:
        if self._truthy(candidate.option, "win", "gameOver", "ko", "knockout"):
            return True
        player = self._own_player(state)
        if player is None:
            return False
        return (
            any(
                pokemon is not None
                and pokemon.card_id == HONCHKROW
                and len(pokemon.energies) >= self._attack_energy_target(HONCHKROW)
                for pokemon in player.bench
            )
            and self._effective_opponent_hp(state) <= 100
        )

    def _supporter_zone_counts(self, state: GameState) -> dict[str, int]:
        """Count known supporters by zone using conservative hidden-Prize handling."""
        player = self._own_player(state)
        if player is None:
            return {"hand": 0, "deck": 0, "discard": 0, "prize": 0, "hidden_prize": 0}
        hand = self._count_supporters(player.hand or ())
        discard = self._count_supporters(player.discard)
        prize = self._count_supporters(player.prize)
        hidden_prize = sum(1 for card in player.prize if self._card_id_from_value(card) == 0)
        known_total = hand + discard + prize + hidden_prize
        total = 20
        deck = max(0, total - known_total)
        return {
            "hand": hand,
            "deck": deck,
            "discard": discard,
            "prize": prize,
            "hidden_prize": hidden_prize,
        }

    def _count_supporters(self, cards: Sequence[Any]) -> int:
        """Count Team Rocket supporters in a visible card zone."""
        return sum(
            1
            for card in cards
            if self._is_rocket_supporter(
                self._card_id_from_value(card),
                self.catalog.get_card(str(self._card_id_from_value(card))) or {},
            )
        )

    def _own_bench_count(self, state: GameState) -> int:
        """Count occupied own Bench positions."""
        player = self._own_player(state)
        return sum(pokemon is not None for pokemon in player.bench) if player else 0

    def _supporters_needed_for_ko(self, state: GameState) -> int:
        """Return the minimum 60-damage supporter count for the active target."""
        hp = self._effective_opponent_hp(state)
        return (hp + 59) // 60 if hp > 0 else 0

    def _effective_opponent_hp(self, state: GameState) -> int:
        """Estimate active HP after public weakness and resistance metadata."""
        opponent = self._opponent_player(state)
        if opponent is None or opponent.active is None:
            return 0
        hp = max(0, int(opponent.active.hp))
        card = self.catalog.get_card(str(opponent.active.card_id)) or {}
        weakness = card.get("weakness") or card.get("weaknesses")
        resistance = card.get("resistance") or card.get("resistances")
        if self._contains_type(weakness, "dark"):
            hp = (hp + 1) // 2
        if self._contains_type(resistance, "dark"):
            hp += 20
        return hp

    def _productive_line_available(self, state: GameState) -> bool:
        """Return whether ending now would abandon a visible winning line."""
        player = self._own_player(state)
        if player is None or not player.hand:
            return False
        has_energy = any(
            self._is_energy_card(
                self._card_id_from_value(card),
                self.catalog.get_card(str(self._card_id_from_value(card))),
            )
            for card in player.hand
        )
        if not has_energy:
            return False
        supporters = self._supporter_zone_counts(state)["hand"]
        if self._own_active_card_id(state) in {HONCHKROW, PORYGON2} and supporters > 0:
            return self._supporters_needed_for_ko(state) <= supporters
        return (
            any(
                pokemon is not None
                and pokemon.card_id in {HONCHKROW, PORYGON2}
                and len(pokemon.energies) + 1 >= self._attack_energy_target(int(pokemon.card_id))
                for pokemon in player.bench
            )
            and supporters > 0
        )

    @staticmethod
    def _contains_type(value: Any, expected: str) -> bool:
        """Match SDK weakness/resistance representations by normalized text."""
        if isinstance(value, Mapping):
            return expected in str(value.get("type", value.get("name", ""))).casefold()
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return any(HonchkrowPorygonScorer._contains_type(item, expected) for item in value)
        return expected in str(value).casefold()

    @staticmethod
    def _card_id_from_value(card: Any) -> int:
        """Extract a numeric card identifier from a visible card value."""
        if isinstance(card, Mapping):
            value = card.get("id", card.get("cardId", 0))
            return int(value) if isinstance(value, int) and not isinstance(value, bool) else 0
        return 0

    def _proton_was_used_previous_turn(self, state: GameState) -> bool:
        """Return whether public current-state history records prior Proton use."""
        if self._proton_used_previous_turn:
            return True
        logs = state.raw.get("logs", []) if isinstance(state.raw, Mapping) else []
        if not isinstance(logs, list):
            return False
        return any(
            isinstance(event, Mapping)
            and self._card_id_from_value(event) == PROTON
            and int(event.get("turn", state.turn)) < state.turn
            for event in logs
        )

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
        self._scorer: HonchkrowPorygonScorer = HonchkrowPorygonScorer(
            deck_profile=profile, catalog=_CG_CATALOG
        )
        self._feature_extractor = SelectionFeatureExtractor(self._scorer)
        self._configured_profile = profile
        self._active_deck_profile = profile

    def _update_alakazam_matchup(self, observation: Mapping[str, Any], state: GameState) -> None:
        logs = observation.get("logs", [])
        used_previous_turn = False
        if isinstance(logs, list):
            used_previous_turn = any(
                isinstance(event, Mapping)
                and self._event_card_id(event) == PROTON
                and int(event.get("turn", state.turn)) < state.turn
                for event in logs
            )
        self._scorer.set_proton_used_previous_turn(used_previous_turn)

    @staticmethod
    def _event_card_id(event: Mapping[str, Any]) -> int:
        """Extract a card identifier from a public event record."""
        value = event.get("cardId", event.get("card_id", event.get("id", 0)))
        return int(value) if isinstance(value, int) and not isinstance(value, bool) else 0

    def start_match(self, deck: DeckDefinition) -> None:
        """Reset Honchkrow-only public history at the start of a match."""
        super().start_match(deck)
        self._scorer.set_proton_used_previous_turn(False)

    def _filter_fezandipiti_bench_line(
        self,
        state: GameState,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
    ) -> list[Selection]:
        return list(selections)

    def _filter_forbidden_selections(
        self,
        state: GameState,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
        context: SelectContext | None,
    ) -> list[Selection]:
        """Apply Honchkrow discard cardinality without changing shared policy."""
        safe = super()._filter_forbidden_selections(state, selections, candidates, context)
        if context not in {SelectContext.DISCARD, SelectContext.DISCARD_CARD_OR_ATTACHED_CARD}:
            return safe
        by_index = {candidate.option_index: candidate for candidate in candidates}
        required = self._scorer._supporters_needed_for_ko(state)
        capped = [
            selection
            for selection in safe
            if sum(
                self._scorer._is_rocket_supporter(
                    self._scorer._feature_int(candidate, "card_id"), candidate.card
                )
                for index in selection.indices
                if (candidate := by_index.get(index)) is not None
            )
            <= required
        ]
        return capped or safe

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
        if candidate.option_type is OptionType.END and self._scorer._productive_line_available(
            state
        ):
            return True
        if candidate.option_type is OptionType.ATTACH and card_type in {5, 6}:
            if self._scorer._feature_int(candidate, "target_energy_count") >= (
                self._scorer._attack_energy_target(target_id)
            ):
                return True
            energy_id = self._scorer._feature_int(candidate, "card_id")
            if energy_id == ROCKET_ENERGY and target_id == PORYGON2:
                return True
            if energy_id == IGNITION_ENERGY and not bool(
                candidate.features.get("target_is_active", False)
            ):
                return True
            if target_id == ARTICUNO and not self._scorer._articuno_is_needed(state):
                return True
            if energy_id == IGNITION_ENERGY and not self._ignition_target_is_valid(
                state, candidate
            ):
                return True
            if target_id == MURKROW and bool(
                candidate.option.get("enablesAttack", candidate.option.get("enables", False))
            ):
                return True
            if self._only_energy_in_hand(state):
                return True
            return False
        if (
            candidate.option_type is OptionType.ATTACK
            and self._scorer._attack_id(candidate) == ARTICUNO_ATTACK
        ):
            return True
        if (
            candidate.option_type is OptionType.ATTACK
            and self._scorer._attack_id(candidate) == HACKING
        ):
            return True
        if (
            candidate.option_type is OptionType.ATTACK
            and self._scorer._attack_id(candidate) == DECEIT
        ):
            damage = max(
                self._scorer._metadata_int(candidate.attack, "damage"),
                self._scorer._metadata_int(candidate.option, "damage"),
                self._scorer._metadata_int(candidate.option, "expectedDamage"),
            )
            if not self._scorer._deceit_is_decisive(state, candidate, damage):
                return True
        if (
            candidate.option_type is OptionType.ATTACK
            and self._scorer._attack_id(candidate) == ROCKET_FEATHERS
        ):
            return self._scorer._supporters_in_hand(state) == 0
        if candidate.option_type is OptionType.PLAY and card_id == ROTO_STICK:
            return not self._scorer._roto_stick_is_needed(state)
        if candidate.option_type is OptionType.PLAY and card_id == ARTICUNO:
            return not (
                self._scorer._articuno_is_needed(state)
                or self._scorer._own_field_count(state) < 2
                or self._scorer._articuno_hand_reduction_needed(state, candidate)
            )
        if (
            card_id == ARTICUNO
            and not self._scorer._articuno_is_needed(state)
            and self._scorer._own_field_count(state) >= 2
        ):
            if candidate.option_type is OptionType.ATTACH:
                return True
            if candidate.option_type is OptionType.CARD and context in {
                SelectContext.SETUP_ACTIVE_POKEMON,
                SelectContext.SETUP_BENCH_POKEMON,
                SelectContext.TO_ACTIVE,
                SelectContext.TO_FIELD,
            }:
                return True
        if candidate.option_type is OptionType.CARD and card_id == HONCHKROW:
            if context in {SelectContext.TO_HAND, SelectContext.LOOK}:
                if self._scorer._card_selected_from_night_stretcher(candidate):
                    return False
                return not self._scorer._pokepad_honchkrow_is_useful(state, candidate)
        if candidate.option_type is OptionType.CARD and card_id == PORYGON2:
            if (
                context
                in {
                    SelectContext.SETUP_BENCH_POKEMON,
                    SelectContext.TO_BENCH,
                    SelectContext.TO_FIELD,
                }
                and self._scorer._own_field_count(state) == 0
            ):
                return True
            if (
                context in {SelectContext.SETUP_BENCH_POKEMON, SelectContext.TO_BENCH}
                and self._scorer._proton_targets_remaining(state).get(MURKROW, 0) > 0
            ):
                return True
        if candidate.option_type is OptionType.CARD and context is SelectContext.TO_HAND:
            if self._scorer._card_selected_from_night_stretcher(candidate):
                return card_type in {5, 6, 2}
            if card_id in {ROCKET_ENERGY, IGNITION_ENERGY}:
                return False
            if card_id == ARTICUNO:
                return not self._scorer._visible_opponent_card_ids(state) & {121}
        if (
            candidate.option_type is OptionType.CARD
            and context
            in {
                SelectContext.TO_HAND,
                SelectContext.TO_FIELD,
            }
            and card_id == NIGHT_STRETCHER
        ):
            return False
        if (
            candidate.option_type is OptionType.CARD
            and context
            in {
                SelectContext.TO_HAND,
                SelectContext.TO_FIELD,
            }
            and card_type in {5, 6, 2}
        ):
            if self._scorer._card_selected_from_night_stretcher(candidate):
                return True
        if context in {SelectContext.DISCARD, SelectContext.DISCARD_CARD_OR_ATTACHED_CARD}:
            if self._scorer._is_energy_card(card_id, candidate.card):
                return True
            if self._scorer._is_rocket_supporter(card_id, candidate.card):
                if card_id == ARIANA and not self._scorer._discard_is_required_for_ko(
                    state, candidate
                ):
                    return True
                if self._scorer._supporters_in_hand(state) <= 1:
                    return True
        if candidate.option_type is OptionType.RETREAT:
            if self._active_has_productive_attack(state) or self._active_has_guaranteed_ko(state):
                return True
        return False

    def _active_has_productive_attack(self, state: GameState) -> bool:
        """Return whether the Active has an energized, damaging public attack."""
        active = self._scorer._own_active(state)
        if active is None or not isinstance(active.card_id, int):
            return False
        card = self._scorer.catalog.get_card(str(active.card_id)) or {}
        for attack_id in card.get("attacks", []):
            attack = self._scorer.catalog.get_attack(str(attack_id)) or {}
            energies = attack.get("energies", [])
            if not isinstance(energies, list) or len(energies) > len(active.energies):
                continue
            if self._scorer._metadata_int(attack, "damage") > 0:
                return True
        return False

    def _active_has_guaranteed_ko(self, state: GameState) -> bool:
        """Return whether any legal Active attack deterministically takes a KO."""
        active = self._scorer._own_active(state)
        if active is None:
            return False
        card = self._scorer.catalog.get_card(str(active.card_id)) or {}
        opponent_hp = self._scorer._effective_opponent_hp(state)
        return any(
            isinstance(attack_id, int)
            and len((self._scorer.catalog.get_attack(str(attack_id)) or {}).get("energies", []))
            <= len(active.energies)
            and self._scorer._metadata_int(
                self._scorer.catalog.get_attack(str(attack_id)) or {}, "damage"
            )
            >= opponent_hp
            for attack_id in card.get("attacks", [])
        )

    def _candidate_phase(self, state: GameState, candidate: Candidate) -> tuple[DecisionPhase, str]:
        """Put lethal and KO-enabling actions before ordinary development."""
        if candidate.option_type is OptionType.ATTACK:
            if self._scorer._truthy(candidate.option, "win", "wins", "ko", "knockout", "isKo"):
                return DecisionPhase.ATTACK_PRIORITY, "guaranteed_ko"
        if candidate.option_type is OptionType.DISCARD and self._scorer._discard_is_required_for_ko(
            state, candidate
        ):
            return DecisionPhase.ATTACK_PRIORITY, "discard_enables_ko"
        return super()._candidate_phase(state, candidate)

    def _only_energy_in_hand(self, state: GameState) -> bool:
        """Return whether the visible hand contains exactly one Energy card."""
        player = self._scorer._own_player(state)
        if player is None or player.hand is None:
            return False
        energies = 0
        for card in player.hand:
            card_id = self._scorer._card_id_from_value(card)
            metadata = self._scorer.catalog.get_card(str(card_id)) or {}
            energies += int(self._scorer._metadata_int(metadata, "cardType") in {5, 6})
        return energies == 1

    def _ignition_target_is_valid(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether Ignition completes a damaging attack this turn."""
        return self._scorer._ignition_attachment_is_productive(state, candidate)
