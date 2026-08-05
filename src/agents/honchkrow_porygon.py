"""Deck-specific heuristic policy for the Honchkrow/Porygon deck."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.agents.heuristic import _CG_CATALOG, HeuristicAgent, SimpleHeuristicScorer
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
ARTICUNO_ATTACK = 583


class HonchkrowPorygonScorer(SimpleHeuristicScorer):
    """Score selections using the reviewed Honchkrow/Porygon priorities."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._proton_used_previous_turn = False

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
            return 900.0, ["ariana_hand_refresh_and_energy_access"]
        if card_id == GIOVANNI:
            if self._supporters_in_hand_after(card_id) >= self._supporters_needed_for_ko(state):
                return 760.0, ["giovanni_preserves_ko_supporters"]
            return 80.0, ["giovanni_preserves_supporters_until_ko"]
        if card_id == PROTON:
            bonus = 140.0 if self._own_bench_count(state) == 0 else 0.0
            return 650.0 + bonus, ["proton_basic_pokemon_setup"]
        if card_id == TRANSCEIVER:
            if self._proton_was_used_previous_turn(state):
                return 690.0, ["transceiver_ariana_after_proton"]
            return 720.0, ["transceiver_proton_early_game"]
        if card_id == POKE_PAD:
            if self._has_murkrow_ready_to_evolve(state):
                return 640.0, ["poke_pad_honchkrow_search"]
            return 620.0, ["poke_pad_murkrow_search"]
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
        elif target_id == ARTICUNO and self._articuno_is_needed(state):
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
            supporters = self._supporter_zone_counts(state)
            damage = supporters["hand"] * 60
            bonus = 700.0 if self._own_active_card_id(state) == HONCHKROW else 0.0
            reasons = ["honchkrow_rocket_feathers", "rocket_hand_damage"]
            if damage < self._effective_opponent_hp(state):
                reasons.append("rocket_feathers_below_ko_threshold")
                bonus -= 450.0
            if supporters["hand"] == 0:
                bonus -= 1000.0
            return 300.0 + damage + bonus, reasons
        if attack_id == R_COMMAND:
            damage = self._rocket_supporters_in_discard(state) * 20
            return 250.0 + damage, ["porygon2_r_command", "rocket_discard_damage"]
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
        if card_id == ARTICUNO and context in {
            SelectContext.SETUP_ACTIVE_POKEMON,
            SelectContext.SETUP_BENCH_POKEMON,
            SelectContext.TO_ACTIVE,
            SelectContext.TO_FIELD,
            SelectContext.TO_HAND,
        }:
            if self._articuno_is_needed(state):
                return 700.0, ["select_articuno_matchup_tech"]
            return -1500.0, ["avoid_articuno_without_matchup_need"]
        if context in {SelectContext.DISCARD, SelectContext.DISCARD_CARD_OR_ATTACHED_CARD}:
            if self._is_rocket_supporter(card_id, candidate.card):
                if card_id == ARIANA:
                    return -500.0, ["preserve_ariana_until_last"]
                if self._supporters_in_hand(state) <= 1:
                    return -1000.0, ["preserve_last_supporter"]
                return 220.0, ["discard_redundant_rocket_supporter"]
            if card_id in {MURKROW, HONCHKROW, PORYGON, PORYGON2, ARTICUNO}:
                return -150.0, ["preserve_pokemon_line"]
        if context is SelectContext.TO_HAND and card_id == ARTICUNO:
            return (260.0, ["recover_articuno_against_dragapult"])
        return super()._card_selection_score(state, candidate, context)

    def _articuno_is_needed(self, state: GameState) -> bool:
        """Return whether public matchup evidence justifies Articuno."""
        return self._visible_opponent_card_ids(state) & {121, 741, 742, 743} != set()

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

    def _supporters_in_hand_after(self, excluded_card_id: int) -> int:
        """Count supporters after hypothetically playing one supporter."""
        return max(0, self._supporters_in_hand() - int(excluded_card_id in self._supporter_ids()))

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
        if candidate.option_type is OptionType.ATTACH and card_type in {5, 6}:
            if self._scorer._feature_int(candidate, "target_energy_count") >= (
                self._scorer._attack_energy_target(target_id)
            ):
                return True
            energy_id = self._scorer._feature_int(candidate, "card_id")
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
            and self._scorer._attack_id(candidate) == ROCKET_FEATHERS
        ):
            return self._scorer._supporters_in_hand(state) == 0
        if candidate.option_type is OptionType.PLAY and card_id == ROTO_STICK:
            return not self._scorer._honchkrow_ready_to_attack(state)
        if candidate.option_type is OptionType.PLAY and card_id == ARTICUNO:
            return not (
                self._scorer._articuno_is_needed(state)
                or self._scorer._articuno_hand_reduction_needed(state, candidate)
            )
        if card_id == ARTICUNO and not self._scorer._articuno_is_needed(state):
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
                return not self._scorer._has_murkrow_ready_to_evolve(state)
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
            if self._scorer._is_rocket_supporter(card_id, candidate.card):
                if card_id == ARIANA or self._scorer._supporters_in_hand(state) <= 1:
                    return True
        return False

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
        """Return whether Ignition targets the active or explicit Giovanni target."""
        return bool(
            candidate.features.get("target_is_active", False)
            or candidate.option.get("toActive", False)
            or candidate.option.get("promote", False)
            or candidate.option.get("willBeActive", False)
        )
