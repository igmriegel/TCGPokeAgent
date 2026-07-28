from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import fields, is_dataclass
from typing import Any

from .candidate import Candidate
from .catalog import CardCatalog
from .exceptions import ParseError
from .interfaces import ObservationParser as ObservationParserInterface
from .parsed_decision import ParsedDecision
from .state import GameState, PlayerState, PokemonState
from .types import OptionType, SelectContext, SelectType


class DefaultParser(ObservationParserInterface):
    """Normalize SDK observations into factual state and candidates."""

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
        return PlayerState(
            active=self._build_pokemon(data.get("active")),
            bench=[self._build_pokemon(item) for item in bench_data],
            bench_max=self._int_field(data, "benchMax") or 8,
            deck_count=self._int_field(data, "deckCount"),
            discard=deepcopy(data.get("discard") or []),
            prize=deepcopy(data.get("prize") or []),
            hand_count=self._int_field(data, "handCount"),
            hand=deepcopy(hand),
        )

    def _build_pokemon(self, data: Any) -> PokemonState | None:
        if data is None:
            return None
        if not isinstance(data, Mapping):
            raise ParseError("pokemon state must be a mapping or null")
        return PokemonState(
            card_id=data.get("cardId"),
            hp=self._int_field(data, "hp"),
            max_hp=self._int_field(data, "maxHp"),
            energies=deepcopy(data.get("energies") or []),
            energy_card_ids=deepcopy(data.get("energyCards") or []),
            tool_ids=deepcopy(data.get("tools") or []),
            pre_evolutions=deepcopy(data.get("preEvolutions") or []),
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
        for index, option in enumerate(options):
            if not isinstance(option, Mapping):
                raise ParseError("select options must be mappings")
            option_dict = dict(option)
            card_id = option_dict.get("cardId") or option_dict.get("serial")
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
                    },
                )
            )
        return candidates

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
        if not isinstance(value, str):
            return None
        try:
            return enum_type(value.upper())
        except ValueError:
            return None

    def _parse_option_type(self, value: Any) -> OptionType:
        if isinstance(value, OptionType):
            return value
        if isinstance(value, str):
            try:
                return OptionType(value.upper())
            except ValueError:
                pass
        return OptionType.CARD
