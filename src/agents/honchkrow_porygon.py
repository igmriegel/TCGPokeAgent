"""Deck-specific heuristic policy for the Honchkrow/Porygon deck."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
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
MEGA_ABOMASNOW_EX = 723
MEGA_ABOMASNOW_ROCKET_FEATHERS_SUPPORTERS = 6
MEGA_ABOMASNOW_R_COMMAND_SUPPORTERS = 18
MEGA_ABOMASNOW_DECK_RESERVE = 2


@dataclass(slots=True)
class TurnTacticalLedger:
    """Public, turn-scoped tactical evidence for the dedicated policy.

    The engine presents one decision at a time.  This ledger therefore joins
    the public snapshots from a turn without inventing hidden cards or state.
    """

    turn: int = 0
    pre_draw_ko_candidates: tuple[int, ...] = ()
    post_draw_ko_candidates: tuple[int, ...] = ()
    potential_damage: dict[int, int] = field(default_factory=dict)
    chosen_attacker: int | None = None
    chosen_target: int | None = None
    draw_sequence: list[str] = field(default_factory=list)
    resource_guard: str = ""
    deck_risk: str = "safe"

    def reset(self, turn: int) -> None:
        """Clear evidence when the public turn changes."""
        self.turn = turn
        self.pre_draw_ko_candidates = ()
        self.post_draw_ko_candidates = ()
        self.potential_damage.clear()
        self.chosen_attacker = None
        self.chosen_target = None
        self.draw_sequence.clear()
        self.resource_guard = ""
        self.deck_risk = "safe"


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
            if not self._ariana_is_safe_and_useful(state):
                return -2600.0, ["ariana_deck_out_guard"]
            if 1 <= state.turn <= 2 and self._proton_targets_remaining(state):
                return 300.0, ["delay_ariana_for_early_proton"]
            return 1400.0, [
                "ariana_before_factory_hand_refresh",
                "ariana_hand_refresh_and_energy_access",
            ]
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
            if self._own_bench_full(state) or not self._proton_targets_exist(state):
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
            if not self._ultra_ball_is_productive(state):
                return -2200.0, ["ultra_ball_without_target_or_safe_discard"]
            return 590.0, ["ultra_ball_attacker_search_or_r_command_boost"]
        if card_id == FACTORY:
            if not self._factory_is_useful(state):
                return -1800.0, ["factory_without_post_supporter_draw"]
            return 1250.0, ["factory_after_ariana_draw_engine"]
        if card_id == PETREL:
            if self._petrel_is_emergency(state):
                return 820.0, ["petrel_emergency_ariana_search"]
            return -900.0, ["avoid_petrel_generic_supporter_search"]
        if card_id == ROTO_STICK:
            if self._roto_stick_is_needed(state):
                return 760.0, ["roto_stick_closes_ko_line"]
            return -1800.0, ["preserve_roto_stick_for_supporter_ko"]
        if card_id == MIRACLE_HEADSET:
            if not self._miracle_headset_is_useful(state):
                return -2200.0, ["reserve_miracle_headset"]
            return 700.0, ["miracle_headset_ko_or_emergency_line"]
        if card_id == NIGHT_STRETCHER:
            if not self._night_stretcher_is_productive(state):
                return -2200.0, ["night_stretcher_without_immediate_play"]
            return 1300.0, ["night_stretcher_hand_reduction_before_ariana"]
        if card_id == ARCHER:
            if not self._archer_is_safe_and_useful(state, candidate):
                return -2400.0, ["archer_without_safe_disruption"]
            return 780.0, ["archer_post_ko_disruption"]
        if card_type == 4:
            return 450.0, ["stadium_after_supporter"]
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
        opponent_hp = max(0, int(target.hp)) if target is not None else self._raw_opponent_hp(state)
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
            damage = self._attack_damage(state, candidate, supporters["hand"] * 60, target)
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
            damage = self._attack_damage(
                state, candidate, self._rocket_supporters_in_discard(state) * 20, target
            )
            score = max(score, 500.0 + damage)
            if damage >= opponent_hp > 0:
                score += 2000.0
                reasons.append("r_command_ko")
            return score, [
                "porygon2_r_command",
                "rocket_discard_damage",
                *reasons,
            ]
        if attack_id == HAMMER_IN:
            damage = self._attack_damage(state, candidate, max(100, explicit_damage), target)
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

    def _attack_damage(
        self,
        state: GameState,
        candidate: Candidate,
        base_damage: int,
        target: Any | None = None,
    ) -> int:
        """Calculate public attack damage including only applicable modifiers."""
        if base_damage <= 0:
            return 0
        target = target or self._target_opponent_pokemon(state, candidate)
        if target is None:
            return base_damage
        attack_id = self._attack_id(candidate)
        # R Command is Colorless.  The Murkrow/Honchkrow attacks are Darkness.
        if attack_id == R_COMMAND:
            return base_damage
        card = self.catalog.get_card(str(target.card_id)) or {}
        damage = base_damage
        if self._contains_type(card.get("weakness") or card.get("weaknesses"), "dark"):
            damage *= 2
        if self._contains_type(card.get("resistance") or card.get("resistances"), "dark"):
            damage = max(0, damage - 20)
        return damage

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
                if self._ariana_is_safe_and_useful(state):
                    return 1200.0, ["petrel_exact_ariana"]
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
                if self._r_command_is_best_damage_line(state):
                    return 800.0, ["defer_honchkrow_to_r_command"]
                return 1500.0, ["promote_ready_honchkrow"]
            if card_id == PORYGON2 and self._pokemon_is_ready(state, candidate):
                if (
                    self._opponent_active_card_id(state) == MEGA_ABOMASNOW_EX
                    and self._rocket_supporters_in_discard(state)
                    < MEGA_ABOMASNOW_R_COMMAND_SUPPORTERS
                ):
                    return -2400.0, ["defer_porygon2_until_mega_abomasnow_ko_ready"]
                if self._r_command_is_best_damage_line(state):
                    return 1800.0, ["promote_porygon2_best_r_command"]
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

    def _all_own_pokemon_are_rocket(self, state: GameState) -> bool:
        """Return whether Ariana draws to eight from only public card metadata."""
        player = self._own_player(state)
        if player is None:
            return False
        pokemon = [item for item in [player.active, *player.bench] if item is not None]
        if not pokemon:
            return False
        return all(
            "team rocket"
            in str((self.catalog.get_card(str(item.card_id)) or {}).get("name", "")).casefold()
            for item in pokemon
        )

    def _ariana_draw_count(self, state: GameState) -> int:
        """Return Ariana's public draw-to target for the current board."""
        return 8 if self._all_own_pokemon_are_rocket(state) else 5

    def _ariana_is_safe_and_useful(self, state: GameState) -> bool:
        """Reject Ariana when it cannot draw safely or improve the visible hand."""
        player = self._own_player(state)
        if player is None:
            return True
        if state.supporter_played:
            return False
        draws = max(0, self._ariana_draw_count(state) - max(0, player.hand_count - 1))
        reserve = self._elective_draw_reserve(state)
        return bool(draws > 0 and int(player.deck_count) - draws >= reserve)

    def _factory_is_useful(self, state: GameState) -> bool:
        """Return whether Factory has an available, non-deck-out draw trigger."""
        player = self._own_player(state)
        return bool(
            player
            and state.supporter_played
            and player.deck_count - 2 >= self._elective_draw_reserve(state)
        )

    def _elective_draw_reserve(self, state: GameState) -> int:
        """Keep natural-draw turns available while building a Mega Abomasnow KO."""
        if self._opponent_active_card_id(state) != MEGA_ABOMASNOW_EX:
            return 0
        if self._active_has_committed_mega_abomasnow_ko(state):
            return 0
        return MEGA_ABOMASNOW_DECK_RESERVE

    def _night_stretcher_is_productive(self, state: GameState) -> bool:
        """Require a recovery target that can immediately leave the hand."""
        player = self._own_player(state)
        if player is None:
            return False
        return any(
            self._night_stretcher_target_is_immediately_playable(
                state, self._card_id_from_value(card)
            )
            for card in player.discard
        )

    def _night_stretcher_target_is_immediately_playable(
        self, state: GameState, card_id: int
    ) -> bool:
        """Return whether a recovered Pokémon can Bench or evolve this turn."""
        if card_id in {MURKROW, PORYGON}:
            return not self._own_bench_full(state)
        if card_id == HONCHKROW:
            return self._has_murkrow_ready_to_evolve(state)
        if card_id == PORYGON2:
            return self._has_porygon_ready_to_evolve(state)
        return (
            card_id == ARTICUNO
            and self._articuno_is_needed(state)
            and not self._own_bench_full(state)
        )

    def _has_porygon_ready_to_evolve(self, state: GameState) -> bool:
        player = self._own_player(state)
        return bool(
            player
            and any(
                pokemon is not None and pokemon.card_id == PORYGON
                for pokemon in [player.active, *player.bench]
            )
        )

    def _ultra_ball_is_productive(self, state: GameState) -> bool:
        """Require both a useful Pokémon target and two disposable hand cards."""
        player = self._own_player(state)
        if player is None or player.deck_count == 0 or player.hand_count < 3:
            return False
        useful_target = (
            self._proton_targets_exist(state)
            or self._has_murkrow_ready_to_evolve(state)
            or self._has_porygon_ready_to_evolve(state)
        )
        disposable = sum(
            not self._is_energy_card(
                self._card_id_from_value(card),
                self.catalog.get_card(str(self._card_id_from_value(card))),
            )
            and not self._is_rocket_supporter(
                self._card_id_from_value(card),
                self.catalog.get_card(str(self._card_id_from_value(card))),
            )
            for card in self._hand_cards(state)
        )
        return useful_target and disposable >= 2

    def _miracle_headset_is_useful(self, state: GameState) -> bool:
        """Reserve the ACE SPEC for two KO supporters or an Ariana emergency."""
        player = self._own_player(state)
        if player is None or player.deck_count == 0:
            return False
        discarded = self._rocket_supporters_in_discard(state)
        needed = self._supporters_needed_for_ko(state) - self._supporters_in_hand(state)
        return (
            discarded >= 2
            and needed >= 2
            or (
                self._supporters_in_hand(state) == 0
                and any(self._card_id_from_value(card) == ARIANA for card in player.discard)
                and self._ariana_draw_count(state) > player.hand_count
            )
        )

    def _archer_is_safe_and_useful(self, state: GameState, candidate: Candidate) -> bool:
        """Use Archer only after a public KO when its redraw is safe and useful."""
        player = self._own_player(state)
        if player is None or player.deck_count + max(0, player.hand_count - 1) < 5:
            return False
        logs = state.raw.get("logs", []) if isinstance(state.raw, Mapping) else []
        prior_ko = self._truthy(candidate.option, "eligibleAfterKo", "opponentKo", "beneficial")
        if isinstance(logs, list):
            prior_ko = prior_ko or any(
                isinstance(event, Mapping)
                and int(event.get("turn", state.turn) or state.turn) == state.turn - 1
                and any(marker in str(event).casefold() for marker in ("knock", "ko"))
                for event in logs
            )
        return prior_ko and (player.hand_count <= 3 or self._opponent_hand_count(state) >= 5)

    def _opponent_hand_count(self, state: GameState) -> int:
        opponent = self._opponent_player(state)
        return opponent.hand_count if opponent is not None else 0

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
        declared_prizes = candidate.option.get(
            "prizes", candidate.option.get("prizeCount", candidate.option.get("prizeValue"))
        )
        prizes = (
            int(declared_prizes)
            if isinstance(declared_prizes, int) and not isinstance(declared_prizes, bool)
            else self.catalog.get_traits(target.card_id).base_prize_value
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

    def _r_command_is_best_damage_line(self, state: GameState) -> bool:
        """Return whether public discard makes Porygon2 the best current attacker."""
        if self._opponent_active_card_id(state) == MEGA_ABOMASNOW_EX:
            return self._rocket_supporters_in_discard(state) >= MEGA_ABOMASNOW_R_COMMAND_SUPPORTERS
        opponent_hp = self._raw_opponent_hp(state)
        r_command = self._rocket_supporters_in_discard(state) * 20
        feathers = self._supporters_in_hand(state) * 60
        hammer = 100
        if r_command >= opponent_hp > 0 and feathers < opponent_hp:
            return True
        return r_command > max(feathers, hammer)

    def _active_has_committed_mega_abomasnow_ko(self, state: GameState) -> bool:
        """Return whether the Active can take the visible Mega Abomasnow KO now."""
        if self._opponent_active_card_id(state) != MEGA_ABOMASNOW_EX:
            return False
        active = self._own_active(state)
        return bool(active and self._pokemon_has_committed_mega_abomasnow_ko(state, active))

    def _pokemon_has_committed_mega_abomasnow_ko(self, state: GameState, pokemon: Any) -> bool:
        """Evaluate a visible attacker's exact 350-HP knockout resources."""
        card_id = int(pokemon.card_id) if isinstance(pokemon.card_id, int) else 0
        energy_count = len(pokemon.energies)
        if card_id == HONCHKROW:
            feathers_ready = (
                energy_count >= self._attack_energy_target(HONCHKROW)
                and self._supporters_in_hand(state) >= MEGA_ABOMASNOW_ROCKET_FEATHERS_SUPPORTERS
            )
            hammer_ready = energy_count >= 3 and self._raw_opponent_hp(state) <= 100
            return feathers_ready or hammer_ready
        return bool(
            card_id == PORYGON2
            and energy_count >= self._attack_energy_target(PORYGON2)
            and self._rocket_supporters_in_discard(state) >= MEGA_ABOMASNOW_R_COMMAND_SUPPORTERS
        )

    def _attack_has_committed_mega_abomasnow_ko(
        self, state: GameState, candidate: Candidate
    ) -> bool:
        """Reject partial attacks into Mega Abomasnow unless they take the KO."""
        target = self._target_opponent_pokemon(state, candidate)
        if target is None or target.card_id != MEGA_ABOMASNOW_EX:
            return True
        attack_id = self._attack_id(candidate)
        if attack_id == ROCKET_FEATHERS:
            return bool(
                self._supporters_in_hand(state) >= MEGA_ABOMASNOW_ROCKET_FEATHERS_SUPPORTERS
            )
        if attack_id == R_COMMAND:
            return bool(
                self._rocket_supporters_in_discard(state) >= MEGA_ABOMASNOW_R_COMMAND_SUPPORTERS
            )
        if attack_id == HAMMER_IN:
            return self._raw_opponent_hp(state) <= 100
        return bool(self._candidate_visible_damage(candidate) >= self._raw_opponent_hp(state) > 0)

    def _candidate_visible_damage(self, candidate: Candidate) -> int:
        """Return deterministic damage declared by a legal attack candidate."""
        return max(
            self._metadata_int(candidate.attack, "damage"),
            self._metadata_int(candidate.option, "damage"),
            self._metadata_int(candidate.option, "expectedDamage"),
        )

    def _opponent_active_card_id(self, state: GameState) -> int:
        """Return the visible opposing Active card identifier."""
        opponent = self._opponent_player(state)
        if opponent is None or opponent.active is None:
            return 0
        return int(opponent.active.card_id) if isinstance(opponent.active.card_id, int) else 0

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

    def _raw_opponent_hp(self, state: GameState) -> int:
        """Return the opposing Active's remaining HP without attack-specific modifiers."""
        opponent = self._opponent_player(state)
        return max(0, int(opponent.active.hp)) if opponent and opponent.active else 0

    def _productive_line_available(self, state: GameState) -> bool:
        """Return whether ending now would abandon a visible winning line."""
        player = self._own_player(state)
        if player is None:
            return False
        useful_hand_cards = {
            MURKROW,
            PORYGON,
            HONCHKROW,
            PORYGON2,
            NIGHT_STRETCHER,
            ARIANA,
            FACTORY,
        }
        if any(
            self._card_id_from_value(card) in useful_hand_cards for card in self._hand_cards(state)
        ):
            if player.deck_count > 0 or any(
                self._card_id_from_value(card) in {MURKROW, PORYGON, HONCHKROW, PORYGON2}
                for card in self._hand_cards(state)
            ):
                return True
        if not player.hand:
            return self._night_stretcher_is_productive(state)
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
        self._turn_ledger = TurnTacticalLedger()

    @property
    def turn_ledger(self) -> TurnTacticalLedger:
        """Return the current turn's public tactical evidence."""
        return self._turn_ledger

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
        self._turn_ledger.reset(0)

    def decide(self, observation: dict[str, Any]) -> Any:
        """Decide while recording only public pre/post-draw tactical evidence."""
        parsed = self._parser.parse(observation)
        if parsed.state.turn != self._turn_ledger.turn:
            self._turn_ledger.reset(parsed.state.turn)
        attacks = [
            candidate
            for candidate in parsed.candidates
            if candidate.option_type is OptionType.ATTACK
        ]
        damage = {
            self._scorer._attack_id(candidate): self._candidate_damage(parsed.state, candidate)
            for candidate in attacks
        }
        ko_candidates = tuple(
            self._scorer._attack_id(candidate)
            for candidate in attacks
            if self._candidate_damage(parsed.state, candidate)
            >= self._target_hp(parsed.state, candidate)
            and self._target_hp(parsed.state, candidate) > 0
        )
        self._turn_ledger.potential_damage.update(damage)
        if (
            "ariana" in self._turn_ledger.draw_sequence
            or "factory" in self._turn_ledger.draw_sequence
        ):
            self._turn_ledger.post_draw_ko_candidates = ko_candidates
        else:
            self._turn_ledger.pre_draw_ko_candidates = ko_candidates
        decision = super().decide(observation)
        by_index = {candidate.option_index: candidate for candidate in parsed.candidates}
        for index in decision.selection.indices:
            candidate = by_index.get(index)
            if candidate is None:
                continue
            card_id = self._scorer._feature_int(candidate, "card_id")
            if candidate.option_type is OptionType.PLAY and card_id == ARIANA:
                self._turn_ledger.draw_sequence.append("ariana")
            elif candidate.option_type is OptionType.PLAY and card_id == FACTORY:
                self._turn_ledger.draw_sequence.append("factory")
            elif candidate.option_type is OptionType.PLAY and card_id == NIGHT_STRETCHER:
                self._turn_ledger.draw_sequence.append("night_stretcher")
            elif candidate.option_type is OptionType.ATTACK:
                self._turn_ledger.chosen_attacker = self._scorer._attack_id(candidate)
                self._turn_ledger.chosen_target = self._scorer._feature_int(
                    candidate, "target_card_id"
                )
        player = self._scorer._own_player(parsed.state)
        if player is not None and player.deck_count <= 2:
            self._turn_ledger.deck_risk = "critical"
        elif player is not None and player.deck_count <= 5:
            self._turn_ledger.deck_risk = "low"
        return decision

    def _candidate_damage(self, state: GameState, candidate: Candidate) -> int:
        """Calculate the candidate's visible tactical damage."""
        attack_id = self._scorer._attack_id(candidate)
        target = self._scorer._target_opponent_pokemon(state, candidate)
        if attack_id == ROCKET_FEATHERS:
            base = self._scorer._supporters_in_hand(state) * 60
        elif attack_id == R_COMMAND:
            base = self._scorer._rocket_supporters_in_discard(state) * 20
        elif attack_id == HAMMER_IN:
            base = 100
        else:
            base = max(
                self._scorer._metadata_int(candidate.attack, "damage"),
                self._scorer._metadata_int(candidate.option, "damage"),
                self._scorer._metadata_int(candidate.option, "expectedDamage"),
            )
        return self._scorer._attack_damage(state, candidate, base, target)

    def _target_hp(self, state: GameState, candidate: Candidate) -> int:
        """Return the raw remaining HP for the candidate's selected target."""
        target = self._scorer._target_opponent_pokemon(state, candidate)
        return max(0, int(target.hp)) if target is not None else 0

    def _filter_fezandipiti_bench_line(
        self,
        state: GameState,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
    ) -> list[Selection]:
        return list(selections)

    def _main_phase_selections(
        self,
        state: GameState,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
    ) -> tuple[str, str, list[Selection]]:
        """Apply the dedicated draw-first order to one public MAIN prompt."""
        safe = self._filter_forbidden_selections(state, selections, candidates, SelectContext.MAIN)
        by_index = {candidate.option_index: candidate for candidate in candidates}

        def matching(predicate: Any) -> list[Selection]:
            return [
                selection
                for selection in safe
                if any(
                    predicate(candidate)
                    for index in selection.indices
                    if (candidate := by_index.get(index))
                )
            ]

        game_wins = matching(
            lambda candidate: (
                candidate.option_type is OptionType.ATTACK
                and self._scorer._truthy(candidate.option, "win", "wins", "gameOver")
            )
        )
        if game_wins:
            return DecisionPhase.ATTACK_PRIORITY.value, "pre_draw_game_win", game_wins

        night_stretcher = matching(
            lambda candidate: (
                candidate.option_type is OptionType.PLAY
                and self._scorer._feature_int(candidate, "card_id") == NIGHT_STRETCHER
            )
        )
        if night_stretcher:
            return DecisionPhase.PLAY_ITEMS.value, "recover_before_ariana", night_stretcher

        hand_reduction = matching(
            lambda candidate: self._is_safe_pre_draw_hand_reduction(state, candidate)
        )
        if hand_reduction:
            return DecisionPhase.PLAY_POKEMON.value, "reduce_hand_before_ariana", hand_reduction

        ariana = matching(
            lambda candidate: (
                candidate.option_type is OptionType.PLAY
                and self._scorer._feature_int(candidate, "card_id") == ARIANA
                and self._scorer._ariana_is_safe_and_useful(state)
            )
        )
        if ariana:
            return DecisionPhase.PLAY_SUPPORTER.value, "ariana_before_factory", ariana

        factory = matching(
            lambda candidate: (
                candidate.option_type is OptionType.PLAY
                and self._scorer._feature_int(candidate, "card_id") == FACTORY
                and self._scorer._factory_is_useful(state)
            )
        )
        if factory:
            return DecisionPhase.UTILITY.value, "factory_after_ariana", factory

        attacks = matching(lambda candidate: candidate.option_type is OptionType.ATTACK)
        if attacks:
            return DecisionPhase.ATTACK.value, "post_draw_best_damage", attacks
        return super()._main_phase_selections(state, safe, candidates)

    def _is_safe_pre_draw_hand_reduction(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether a Pokémon/evolution can leave hand before Ariana safely."""
        card_id = self._scorer._feature_int(candidate, "card_id")
        if candidate.option_type is OptionType.EVOLVE:
            return card_id in {HONCHKROW, PORYGON2}
        if candidate.option_type is not OptionType.PLAY:
            return False
        if self._scorer._metadata_int(candidate.card, "cardType") != 0:
            return False
        return card_id in {MURKROW, PORYGON} and not self._scorer._own_bench_full(state)

    def _filter_forbidden_selections(
        self,
        state: GameState,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
        context: SelectContext | None,
    ) -> list[Selection]:
        """Apply Honchkrow discard cardinality without changing shared policy."""
        by_index = {candidate.option_index: candidate for candidate in candidates}
        if (
            context in {SelectContext.DISCARD, SelectContext.DISCARD_CARD_OR_ATTACHED_CARD}
            and self._scorer._opponent_active_card_id(state) == MEGA_ABOMASNOW_EX
        ):
            lethal_discard = [
                selection
                for selection in selections
                if self._rocket_supporter_count(selection, by_index)
                == MEGA_ABOMASNOW_ROCKET_FEATHERS_SUPPORTERS
            ]
            if lethal_discard:
                self._turn_ledger.resource_guard = "discard_six_for_mega_abomasnow_ko"
                return lethal_discard
        safe = super()._filter_forbidden_selections(state, selections, candidates, context)
        committed = [
            selection
            for selection in safe
            if not any(
                self._violates_mega_abomasnow_commitment(state, by_index.get(index), context)
                for index in selection.indices
            )
        ]
        safe = committed or safe
        if context not in {SelectContext.DISCARD, SelectContext.DISCARD_CARD_OR_ATTACHED_CARD}:
            diversified = self._filter_duplicate_proton_roles(safe, candidates, context)
            return diversified or safe
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
        proton_safe = self._filter_duplicate_proton_roles(capped or safe, candidates, context)
        return proton_safe or capped or safe

    def _rocket_supporter_count(
        self, selection: Selection, by_index: Mapping[int, Candidate]
    ) -> int:
        """Count Team Rocket Supporters in one legal multi-card selection."""
        return sum(
            self._scorer._is_rocket_supporter(
                self._scorer._feature_int(candidate, "card_id"), candidate.card
            )
            for index in selection.indices
            if (candidate := by_index.get(index)) is not None
        )

    def _violates_mega_abomasnow_commitment(
        self,
        state: GameState,
        candidate: Candidate | None,
        context: SelectContext | None,
    ) -> bool:
        """Return whether an optional action spends resources without a 350-HP KO."""
        if candidate is None or self._scorer._opponent_active_card_id(state) != MEGA_ABOMASNOW_EX:
            return False
        if candidate.option_type is OptionType.ATTACK:
            return not self._scorer._attack_has_committed_mega_abomasnow_ko(state, candidate)
        if candidate.option_type is OptionType.RETREAT:
            return not self._retreat_enables_committed_mega_abomasnow_ko(state)
        return bool(
            candidate.option_type is OptionType.CARD
            and self._scorer._feature_int(candidate, "card_id") == PORYGON2
            and context in {SelectContext.TO_ACTIVE, SelectContext.SWITCH}
            and self._scorer._rocket_supporters_in_discard(state)
            < MEGA_ABOMASNOW_R_COMMAND_SUPPORTERS
        )

    def _filter_duplicate_proton_roles(
        self,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
        context: SelectContext | None,
    ) -> list[Selection]:
        """Keep diversified Basic targets when Proton asks for several cards."""
        if context is not SelectContext.TO_HAND:
            return list(selections)
        by_index = {candidate.option_index: candidate for candidate in candidates}
        filtered: list[Selection] = []
        for selection in selections:
            proton_cards = [
                self._scorer._feature_int(candidate, "card_id")
                for index in selection.indices
                if (candidate := by_index.get(index)) is not None
                and candidate.option.get("sourceCardId") == PROTON
            ]
            roles = {self._proton_role(card_id) for card_id in proton_cards}
            if len(proton_cards) <= 1 or len(roles) == len(proton_cards):
                filtered.append(selection)
        return filtered

    @staticmethod
    def _proton_role(card_id: int) -> str:
        """Return the tactical role used to diversify Proton selections."""
        if card_id == MURKROW:
            return "primary"
        if card_id == PORYGON:
            return "r_command"
        if card_id == ARTICUNO:
            return "defensive"
        return str(card_id)

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
            self._turn_ledger.resource_guard = "productive_action_remains"
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
            if target_id == ARTICUNO:
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
        if candidate.option_type is OptionType.ATTACK and not (
            self._scorer._attack_has_committed_mega_abomasnow_ko(state, candidate)
        ):
            self._turn_ledger.resource_guard = "mega_abomasnow_requires_committed_ko"
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
        if candidate.option_type is OptionType.PLAY and card_id == ULTRA_BALL:
            return not self._scorer._ultra_ball_is_productive(state)
        if candidate.option_type is OptionType.PLAY and card_id == MIRACLE_HEADSET:
            return not self._scorer._miracle_headset_is_useful(state)
        if candidate.option_type is OptionType.PLAY and card_id == NIGHT_STRETCHER:
            return not self._scorer._night_stretcher_is_productive(state)
        if candidate.option_type is OptionType.PLAY and card_id == ARCHER:
            return not self._scorer._archer_is_safe_and_useful(state, candidate)
        if candidate.option_type is OptionType.PLAY and card_id == FACTORY:
            return not self._scorer._factory_is_useful(state)
        if candidate.option_type is OptionType.PLAY and card_id == GIOVANNI:
            return not self._giovanni_is_productive(state, candidate)
        if candidate.option_type is OptionType.PLAY and card_id == ARTICUNO:
            return not self._scorer._articuno_is_needed(state)
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
                    return not self._scorer._night_stretcher_target_is_immediately_playable(
                        state, card_id
                    )
                return not self._scorer._pokepad_honchkrow_is_useful(state, candidate)
        if candidate.option_type is OptionType.CARD and card_id == PORYGON2:
            if (
                context in {SelectContext.TO_ACTIVE, SelectContext.SWITCH}
                and self._scorer._opponent_active_card_id(state) == MEGA_ABOMASNOW_EX
                and self._scorer._rocket_supporters_in_discard(state)
                < MEGA_ABOMASNOW_R_COMMAND_SUPPORTERS
            ):
                return True
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
                return not self._scorer._night_stretcher_target_is_immediately_playable(
                    state, card_id
                )
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
        if context is SelectContext.TO_HAND and candidate.option.get("sourceCardId") == PETREL:
            return not self._petrel_target_is_useful(state, candidate)
        if candidate.option_type is OptionType.RETREAT:
            if self._scorer._opponent_active_card_id(state) == MEGA_ABOMASNOW_EX:
                justified = self._retreat_enables_committed_mega_abomasnow_ko(state)
                self._turn_ledger.resource_guard = (
                    "retreat_enables_mega_abomasnow_ko"
                    if justified
                    else "retreat_without_mega_abomasnow_ko"
                )
                return not justified
            if self._active_has_productive_attack(state) or self._active_has_guaranteed_ko(state):
                return True
        return False

    def _retreat_enables_committed_mega_abomasnow_ko(self, state: GameState) -> bool:
        """Require retreat to exchange a nonlethal Active for an immediate KO."""
        player = self._scorer._own_player(state)
        active = player.active if player is not None else None
        if player is None or active is None:
            return False
        active_card = self._scorer.catalog.get_card(str(active.card_id)) or {}
        retreat_cost = self._scorer._metadata_int(active_card, "retreatCost")
        if retreat_cost <= 0 or len(active.energies) < retreat_cost:
            return False
        if self._scorer._pokemon_has_committed_mega_abomasnow_ko(state, active):
            return False
        return any(
            pokemon is not None
            and self._scorer._pokemon_has_committed_mega_abomasnow_ko(state, pokemon)
            for pokemon in player.bench
        )

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
        if candidate.option_type is OptionType.RETREAT and (
            self._retreat_enables_committed_mega_abomasnow_ko(state)
        ):
            return DecisionPhase.ATTACK_PRIORITY, "retreat_enables_mega_abomasnow_ko"
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

    def _giovanni_is_productive(self, state: GameState, candidate: Candidate) -> bool:
        """Require a committed attackable switch target before playing Giovanni."""
        opponent = self._scorer._opponent_player(state)
        player = self._scorer._own_player(state)
        if opponent is None or player is None:
            return False
        ready_bench = [
            pokemon
            for pokemon in player.bench
            if pokemon is not None
            and pokemon.card_id in {HONCHKROW, PORYGON2}
            and len(pokemon.energies) >= self._scorer._attack_energy_target(int(pokemon.card_id))
        ]
        if not ready_bench:
            return False
        opponent_bench = [pokemon for pokemon in opponent.bench if pokemon is not None]
        if not opponent_bench:
            return not self._active_has_productive_attack(state)
        max_damage = max(
            self._scorer._supporters_in_hand(state) * 60 * 2,
            self._scorer._rocket_supporters_in_discard(state) * 20,
            100,
        )
        return any(
            max_damage >= int(pokemon.hp) for pokemon in opponent_bench
        ) or self._scorer._truthy(candidate.option, "enablesKo", "ko", "knockout", "isKo")

    def _petrel_target_is_useful(self, state: GameState, candidate: Candidate) -> bool:
        """Limit Petrel to exact trainer targets with immediate tactical value."""
        card_id = self._scorer._feature_int(candidate, "card_id")
        if card_id == ARIANA:
            return self._scorer._ariana_is_safe_and_useful(state)
        if card_id == FACTORY:
            return not bool(state.stadium) and self._scorer._own_player(state) is not None
        if card_id == NIGHT_STRETCHER:
            return self._scorer._night_stretcher_is_productive(state)
        if card_id == MIRACLE_HEADSET:
            return self._scorer._miracle_headset_is_useful(state)
        if card_id == ULTRA_BALL:
            return self._scorer._ultra_ball_is_productive(state)
        return False
