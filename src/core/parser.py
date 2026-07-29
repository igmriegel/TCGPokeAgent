from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import fields, is_dataclass
from typing import Any, cast

from .candidate import Candidate
from .catalog import CardCatalog
from .exceptions import ParseError
from .interfaces import ObservationParser as ObservationParserInterface
from .parsed_decision import ParsedDecision
from .state import GameState, PlayerState, PokemonState
from .types import OptionType, SelectContext, SelectType


class DefaultParser(ObservationParserInterface):
    """Normalize SDK observations into factual state and candidates."""

    _SDK_SELECT_TYPES = {
        0: SelectType.MAIN,
        1: SelectType.CARD,
        2: SelectType.ATTACHED_CARD,
        3: SelectType.CARD_OR_ATTACHED_CARD,
        4: SelectType.ENERGY,
        5: SelectType.SKILL,
        6: SelectType.ATTACK,
        7: SelectType.EVOLVE,
        8: SelectType.COUNT,
        9: SelectType.YES_NO,
        10: SelectType.SPECIAL_CONDITION,
    }
    _SDK_SELECT_CONTEXTS = {
        0: SelectContext.MAIN,
        1: SelectContext.SETUP_ACTIVE_POKEMON,
        2: SelectContext.SETUP_BENCH_POKEMON,
        3: SelectContext.SWITCH,
        4: SelectContext.TO_ACTIVE,
        5: SelectContext.TO_BENCH,
        6: SelectContext.TO_FIELD,
        7: SelectContext.TO_HAND,
        8: SelectContext.DISCARD,
        9: SelectContext.TO_DECK,
        10: SelectContext.TO_DECK_BOTTOM,
        11: SelectContext.TO_PRIZE,
        12: SelectContext.NOT_MOVE,
        13: SelectContext.DAMAGE_COUNTER,
        14: SelectContext.DAMAGE_COUNTER_ANY,
        15: SelectContext.DAMAGE,
        16: SelectContext.REMOVE_DAMAGE_COUNTER,
        17: SelectContext.HEAL,
        18: SelectContext.EVOLVES_FROM,
        19: SelectContext.EVOLVES_TO,
        20: SelectContext.DEVOLVE,
        21: SelectContext.ATTACH_FROM,
        22: SelectContext.ATTACH_TO,
        23: SelectContext.DETACH_FROM,
        24: SelectContext.LOOK,
        25: SelectContext.EFFECT_TARGET,
        26: SelectContext.DISCARD_ENERGY_CARD,
        27: SelectContext.DISCARD_TOOL_CARD,
        28: SelectContext.SWITCH_ENERGY,
        29: SelectContext.DISCARD_CARD_OR_ATTACHED_CARD,
        30: SelectContext.DISCARD_ENERGY,
        31: SelectContext.TO_HAND_ENERGY,
        32: SelectContext.TO_DECK_ENERGY,
        33: SelectContext.SWITCH_ENERGY,
        34: SelectContext.SKILL_ORDER,
        35: SelectContext.ATTACK,
        36: SelectContext.DISABLE_ATTACK,
        37: SelectContext.EVOLVE,
        38: SelectContext.DRAW_COUNT,
        39: SelectContext.DAMAGE_COUNTER_COUNT,
        40: SelectContext.REMOVE_DAMAGE_COUNTER_COUNT,
        41: SelectContext.IS_FIRST,
        42: SelectContext.MULLIGAN,
        43: SelectContext.ACTIVATE,
        44: SelectContext.FIRST_EFFECT,
        45: SelectContext.MORE_DEVOLVE,
        46: SelectContext.COIN_HEAD,
        47: SelectContext.AFFECT_SPECIAL_CONDITION,
        48: SelectContext.RECOVER_SPECIAL_CONDITION,
    }
    _SDK_OPTION_TYPES = {
        0: OptionType.NUMBER,
        1: OptionType.YES,
        2: OptionType.NO,
        3: OptionType.CARD,
        4: OptionType.TOOL_CARD,
        5: OptionType.ENERGY_CARD,
        6: OptionType.ENERGY,
        7: OptionType.PLAY,
        8: OptionType.ATTACH,
        9: OptionType.EVOLVE,
        10: OptionType.ABILITY,
        11: OptionType.DISCARD,
        12: OptionType.RETREAT,
        13: OptionType.ATTACK,
        14: OptionType.END,
        15: OptionType.SKILL,
        16: OptionType.SPECIAL_CONDITION,
    }

    def __init__(self, catalog: CardCatalog | None = None) -> None:
        self._catalog = catalog

    def parse(self, observation: Any) -> ParsedDecision:
        """Parse a dictionary or dataclass observation without mutating it."""
        normalized = self._normalize(observation)
        logs = normalized.get("logs", [])
        if logs is None:
            logs = []
        if not isinstance(logs, list):
            raise ParseError("observation logs must be a list")

        current = normalized.get("current")
        if current is not None and not isinstance(current, Mapping):
            raise ParseError("observation current must be a mapping or null")
        select = normalized.get("select")
        if select is not None and not isinstance(select, Mapping):
            raise ParseError("observation select must be a mapping or null")

        state = self._build_state(normalized)
        candidates = self._build_candidates(normalized)
        select_type, select_context = self._parse_select_info(normalized)
        min_count, max_count, energy_cost, damage_counter = self._selection_fields(select)

        return ParsedDecision(
            raw_observation=observation,
            state=state,
            select_type=select_type,
            select_context=select_context,
            min_count=min_count,
            max_count=max_count,
            remain_energy_cost=energy_cost,
            remain_damage_counter=damage_counter,
            candidates=candidates,
            logs=deepcopy(logs),
            search_begin_input=deepcopy(normalized.get("search_begin_input")),
            normalized_observation=normalized,
        )

    def _normalize(self, observation: Any) -> dict[str, Any]:
        if isinstance(observation, Mapping):
            return deepcopy(dict(observation))
        if is_dataclass(observation) and not isinstance(observation, type):
            return self._convert_dataclass(observation)
        raise ParseError("observation must be a mapping or dataclass")

    def _convert_dataclass(self, value: Any) -> dict[str, Any]:
        return {
            field.name: self._convert_value(getattr(value, field.name)) for field in fields(value)
        }

    def _convert_value(self, value: Any) -> Any:
        if is_dataclass(value) and not isinstance(value, type):
            return self._convert_dataclass(value)
        if isinstance(value, Mapping):
            return {key: self._convert_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._convert_value(item) for item in value]
        return deepcopy(value)

    def _selection_fields(self, select: Mapping[str, Any] | None) -> tuple[int, int, int, int]:
        if select is None:
            return 0, 0, 0, 0
        return (
            self._int_field(select, "minCount"),
            self._int_field(select, "maxCount"),
            self._int_field(select, "remainEnergyCost"),
            self._int_field(select, "remainDamageCounter"),
        )

    def _int_field(self, data: Mapping[str, Any], name: str) -> int:
        try:
            return int(data.get(name, 0) or 0)
        except (TypeError, ValueError) as error:
            raise ParseError(f"observation field {name!r} must be an integer") from error

    def _build_state(self, raw: dict[str, Any]) -> GameState:
        current = raw.get("current") or {}
        if not isinstance(current, Mapping):
            raise ParseError("observation current must be a mapping or null")

        players_data = current.get("players")
        players: list[PlayerState] = []
        for player_key, index in (("you", 0), ("opponent", 1)):
            pdata = current.get(player_key)
            if pdata is None and isinstance(players_data, list) and len(players_data) > index:
                pdata = players_data[index]
            players.append(self._build_player(pdata or {}))

        return GameState(
            turn=self._int_field(current, "turn"),
            turn_action_count=self._int_field(current, "turnActionCount"),
            your_index=self._int_field(current, "yourIndex"),
            first_player=self._int_field(current, "firstPlayer"),
            result=current.get("result"),
            supporter_played=bool(current.get("supporterPlayed", False)),
            stadium_played=bool(current.get("stadiumPlayed", False)),
            energy_attached=bool(current.get("energyAttached", False)),
            retreated=bool(current.get("retreated", False)),
            stadium=current.get("stadium"),
            looking=current.get("looking"),
            players=players,
            raw=deepcopy(dict(current)),
        )

    def _build_player(self, data: Any) -> PlayerState:
        if not isinstance(data, Mapping):
            raise ParseError("player state must be a mapping")
        bench_data = data.get("bench") or []
        if not isinstance(bench_data, list):
            raise ParseError("player bench must be a list")
        hand = data.get("hand")
        if hand is not None and not isinstance(hand, list):
            raise ParseError("player hand must be a list or null")
        active = self._build_pokemon(data.get("active"))
        if active is not None:
            active.poisoned = bool(data.get("poisoned", False))
            active.burned = bool(data.get("burned", False))
            active.asleep = bool(data.get("asleep", False))
            active.paralyzed = bool(data.get("paralyzed", False))
            active.confused = bool(data.get("confused", False))
        deck = data.get("deck")
        return PlayerState(
            active=active,
            bench=[self._build_pokemon(item) for item in bench_data],
            bench_max=self._int_field(data, "benchMax") or 8,
            deck_count=(
                self._int_field(data, "deckCount")
                if data.get("deckCount") is not None
                else len(deck)
                if isinstance(deck, list)
                else 0
            ),
            discard=deepcopy(data.get("discard") or []),
            prize=deepcopy(data.get("prize") or []),
            hand_count=(
                self._int_field(data, "handCount")
                if data.get("handCount") is not None
                else len(hand)
                if isinstance(hand, list)
                else 0
            ),
            hand=deepcopy(hand),
        )

    def _build_pokemon(self, data: Any) -> PokemonState | None:
        if isinstance(data, list):
            data = data[0] if data else None
        if data is None:
            return None
        if not isinstance(data, Mapping):
            raise ParseError("pokemon state must be a mapping or null")
        return PokemonState(
            card_id=self._card_id(data),
            hp=self._int_field(data, "hp"),
            max_hp=self._int_field(data, "maxHp"),
            energies=deepcopy(data.get("energies") or []),
            energy_card_ids=deepcopy(data.get("energyCards") or []),
            tool_ids=deepcopy(data.get("tools") or []),
            pre_evolutions=deepcopy(data.get("preEvolutions") or data.get("preEvolution") or []),
            appear_this_turn=bool(data.get("appearThisTurn", False)),
            poisoned=bool(data.get("poisoned", False)),
            burned=bool(data.get("burned", False)),
            asleep=bool(data.get("asleep", False)),
            paralyzed=bool(data.get("paralyzed", False)),
            confused=bool(data.get("confused", False)),
        )

    def _build_candidates(self, raw: dict[str, Any]) -> list[Candidate]:
        select = raw.get("select")
        if not isinstance(select, Mapping):
            return []
        options = select.get("option") or []
        if not isinstance(options, list):
            raise ParseError("select option must be a list")
        candidates: list[Candidate] = []
        current = raw.get("current")
        parsed_your_index = (
            self._mapping_int(current, "yourIndex") if isinstance(current, Mapping) else 0
        )
        for index, option in enumerate(options):
            if not isinstance(option, Mapping):
                raise ParseError("select options must be mappings")
            option_dict = dict(option)
            resolved_card = self._resolve_option_card(normalized=raw, option=option_dict)
            target = self._resolve_in_play_target(raw, option_dict)
            card_id = option_dict.get("cardId") or self._card_id(resolved_card)
            resolved_target_id = self._card_id(target)
            target_card_id = resolved_target_id if isinstance(resolved_target_id, int) else 0
            attack_id = option_dict.get("attackId")
            card = self._catalog.get_card(str(card_id)) if self._catalog and card_id else None
            attack = (
                self._catalog.get_attack(str(attack_id)) if self._catalog and attack_id else None
            )
            candidates.append(
                Candidate(
                    option_index=index,
                    option=option_dict,
                    option_type=self._parse_option_type(option_dict.get("type")),
                    card=card,
                    attack=attack,
                    features={
                        "has_card_metadata": card is not None,
                        "has_attack_metadata": attack is not None,
                        "card_id": int(card_id) if isinstance(card_id, int) else 0,
                        "card_hp": self._mapping_int(resolved_card, "hp"),
                        "card_max_hp": self._mapping_int(resolved_card, "maxHp"),
                        "card_energy_count": self._mapping_length(resolved_card, "energies"),
                        "card_owner_is_self": (
                            self._mapping_int(resolved_card, "playerIndex") == parsed_your_index
                        )
                        if resolved_card
                        else False,
                        "target_card_id": target_card_id,
                        "target_hp": self._mapping_int(target, "hp"),
                        "target_max_hp": self._mapping_int(target, "maxHp"),
                        "target_energy_count": self._mapping_length(target, "energies"),
                        "target_is_active": self._enum_code(option_dict.get("inPlayArea")) == 4,
                    },
                )
            )
        return candidates

    def _resolve_option_card(
        self, normalized: Mapping[str, Any], option: Mapping[str, Any]
    ) -> Mapping[str, Any] | None:
        option_type = self._enum_code(option.get("type"))
        area = self._enum_code(option.get("area"))
        if option_type in {7, 8, 9}:
            area = 2
        if option_type == 13:
            area = 4
        index = option.get("index", 0 if option_type == 13 else None)
        return self._resolve_area_card(
            normalized,
            area,
            index,
            option.get("playerIndex"),
        )

    def _resolve_in_play_target(
        self, normalized: Mapping[str, Any], option: Mapping[str, Any]
    ) -> Mapping[str, Any] | None:
        return self._resolve_area_card(
            normalized,
            self._enum_code(option.get("inPlayArea")),
            option.get("inPlayIndex"),
            option.get("playerIndex"),
        )

    def _resolve_area_card(
        self,
        normalized: Mapping[str, Any],
        area: int | None,
        index: Any,
        player_index: Any,
    ) -> Mapping[str, Any] | None:
        if area is None or isinstance(index, bool) or not isinstance(index, int):
            return None
        current = normalized.get("current")
        if not isinstance(current, Mapping):
            return None
        your_index = self._mapping_int(current, "yourIndex")
        owner = player_index if isinstance(player_index, int) else your_index
        player = self._player_mapping(current, owner)
        select = normalized.get("select")
        zones: dict[int, Any] = {
            1: select.get("deck") if isinstance(select, Mapping) else None,
            2: player.get("hand") if player else None,
            3: player.get("discard") if player else None,
            4: player.get("active") if player else None,
            5: player.get("bench") if player else None,
            6: player.get("prize") if player else None,
            7: current.get("stadium"),
            12: current.get("looking"),
        }
        zone = zones.get(area)
        if not isinstance(zone, list) or not 0 <= index < len(zone):
            return None
        card = zone[index]
        return card if isinstance(card, Mapping) else None

    def _player_mapping(
        self, current: Mapping[str, Any], player_index: int
    ) -> Mapping[str, Any] | None:
        players = current.get("players")
        if isinstance(players, list) and 0 <= player_index < len(players):
            player = players[player_index]
            return player if isinstance(player, Mapping) else None
        your_index = self._mapping_int(current, "yourIndex")
        key = "you" if player_index == your_index else "opponent"
        player = current.get(key)
        return player if isinstance(player, Mapping) else None

    def _card_id(self, card: Any) -> int | str | None:
        if not isinstance(card, Mapping):
            return None
        return card.get("cardId") or card.get("id")

    def _mapping_int(self, data: Any, name: str) -> int:
        if not isinstance(data, Mapping):
            return 0
        value = data.get(name)
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

    def _mapping_length(self, data: Any, name: str) -> int:
        if not isinstance(data, Mapping):
            return 0
        value = data.get(name)
        return len(value) if isinstance(value, list) else 0

    def _enum_code(self, value: Any) -> int | None:
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        return None

    def _parse_select_info(
        self, raw: dict[str, Any]
    ) -> tuple[SelectType | None, SelectContext | None]:
        select = raw.get("select")
        if not isinstance(select, Mapping):
            return None, None
        select_type = self._enum_value(SelectType, select.get("type"))
        select_context = self._enum_value(SelectContext, select.get("context"))
        return select_type, select_context

    def _enum_value(self, enum_type: Any, value: Any) -> Any:
        if isinstance(value, int) and not isinstance(value, bool):
            mapping = cast(
                dict[int, Any],
                {
                    SelectType: self._SDK_SELECT_TYPES,
                    SelectContext: self._SDK_SELECT_CONTEXTS,
                    OptionType: self._SDK_OPTION_TYPES,
                }.get(enum_type, {}),
            )
            return mapping.get(value)
        if not isinstance(value, str):
            return None
        try:
            return enum_type(value.upper())
        except ValueError:
            return None

    def _parse_option_type(self, value: Any) -> OptionType:
        if isinstance(value, OptionType):
            return value
        if isinstance(value, int) and not isinstance(value, bool):
            return self._SDK_OPTION_TYPES.get(value, OptionType.CARD)
        if isinstance(value, str):
            try:
                return OptionType(value.upper())
            except ValueError:
                pass
        return OptionType.CARD
