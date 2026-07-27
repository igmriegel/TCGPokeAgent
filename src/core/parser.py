from __future__ import annotations

from typing import Any

from .candidate import Candidate
from .interfaces import ObservationParser as ObservationParserInterface
from .parsed_decision import ParsedDecision
from .state import GameState, PlayerState, PokemonState
from .types import OptionType, SelectContext, SelectType


class DefaultParser(ObservationParserInterface):
    def parse(self, observation: Any) -> ParsedDecision:
        raw = self._normalize(observation)
        state = self._build_state(raw)
        candidates = self._build_candidates(raw)
        select_type, select_context = self._parse_select_info(raw)

        select_data = raw.get("select")
        if isinstance(select_data, dict):
            min_count = int(select_data.get("minCount", 0) or 0)
            max_count = int(select_data.get("maxCount", 0) or 0)
            remain_energy_cost = int(select_data.get("remainEnergyCost", 0) or 0)
            remain_damage_counter = int(select_data.get("remainDamageCounter", 0) or 0)
        else:
            min_count = max_count = remain_energy_cost = remain_damage_counter = 0

        return ParsedDecision(
            raw_observation=raw,
            state=state,
            select_type=select_type,
            select_context=select_context,
            min_count=min_count,
            max_count=max_count,
            remain_energy_cost=remain_energy_cost,
            remain_damage_counter=remain_damage_counter,
            candidates=candidates,
        )

    def _normalize(self, observation: Any) -> dict[str, Any]:
        if hasattr(observation, "__dataclass_fields__"):
            raw = {}
            for field_name in observation.__dataclass_fields__:
                raw[field_name] = getattr(observation, field_name)
            if "current" in raw and hasattr(raw["current"], "__dataclass_fields__"):
                raw["current"] = self._dataclass_to_dict(raw["current"])
            if "select" in raw and hasattr(raw["select"], "__dataclass_fields__"):
                raw["select"] = self._dataclass_to_dict(raw["select"])
            return raw
        if isinstance(observation, dict):
            return dict(observation)
        return {}

    def _dataclass_to_dict(self, obj: Any) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for field_name in obj.__dataclass_fields__:
            val = getattr(obj, field_name)
            if hasattr(val, "__dataclass_fields__"):
                result[field_name] = self._dataclass_to_dict(val)
            elif isinstance(val, list):
                result[field_name] = [
                    self._dataclass_to_dict(v) if hasattr(v, "__dataclass_fields__") else v
                    for v in val
                ]
            else:
                result[field_name] = val
        return result

    def _build_state(self, raw: dict[str, Any]) -> GameState:
        current: dict[str, Any] = raw.get("current") or {}

        players = []
        for player_key in ("you", "opponent"):
            pdata = current.get(player_key, {})
            if not pdata and player_key == "you":
                pdata = current.get("players", [{}])[0] if current.get("players") else {}
            elif not pdata and player_key == "opponent":
                pdata = (
                    current.get("players", [{}, {}])[1]
                    if len(current.get("players", [])) > 1
                    else {}
                )

            active_data = pdata.get("active") or {}
            active = PokemonState(
                card_id=active_data.get("cardId") or "",
                hp=int(active_data.get("hp", 0) or 0),
                max_hp=int(active_data.get("maxHp", 0) or 0),
                energies=active_data.get("energies") or [],
                energy_card_ids=active_data.get("energyCards") or [],
                tool_ids=active_data.get("tools") or [],
                pre_evolutions=active_data.get("preEvolutions") or [],
                appear_this_turn=bool(active_data.get("appearThisTurn", False)),
                poisoned=bool(active_data.get("poisoned", False)),
                burned=bool(active_data.get("burned", False)),
                asleep=bool(active_data.get("asleep", False)),
                paralyzed=bool(active_data.get("paralyzed", False)),
                confused=bool(active_data.get("confused", False)),
            )

            bench_data = pdata.get("bench") or []
            bench: list[PokemonState | None] = []
            for b in bench_data:
                if b is None:
                    bench.append(None)
                else:
                    bench.append(
                        PokemonState(
                            card_id=b.get("cardId") or "",
                            hp=int(b.get("hp", 0) or 0),
                            max_hp=int(b.get("maxHp", 0) or 0),
                            energies=b.get("energies") or [],
                            energy_card_ids=b.get("energyCards") or [],
                            tool_ids=b.get("tools") or [],
                            pre_evolutions=b.get("preEvolutions") or [],
                            appear_this_turn=bool(b.get("appearThisTurn", False)),
                            poisoned=bool(b.get("poisoned", False)),
                            burned=bool(b.get("burned", False)),
                            asleep=bool(b.get("asleep", False)),
                            paralyzed=bool(b.get("paralyzed", False)),
                            confused=bool(b.get("confused", False)),
                        )
                    )

            hand = pdata.get("hand")
            players.append(
                PlayerState(
                    active=active,
                    bench=bench,
                    bench_max=int(pdata.get("benchMax", 8) or 8),
                    deck_count=int(pdata.get("deckCount", 0) or 0),
                    discard=pdata.get("discard") or [],
                    prize=pdata.get("prize") or [],
                    hand_count=int(pdata.get("handCount", 0) or 0),
                    hand=hand if hand is not None else None,
                )
            )

        return GameState(
            turn=int(current.get("turn", 0) or 0),
            turn_action_count=int(current.get("turnActionCount", 0) or 0),
            your_index=int(current.get("yourIndex", 0) or 0),
            first_player=int(current.get("firstPlayer", 0) or 0),
            result=current.get("result"),
            supporter_played=bool(current.get("supporterPlayed", False)),
            stadium_played=bool(current.get("stadiumPlayed", False)),
            energy_attached=bool(current.get("energyAttached", False)),
            retreated=bool(current.get("retreated", False)),
            stadium=current.get("stadium"),
            looking=current.get("looking"),
            players=players,
            raw=current,
        )

    def _build_candidates(self, raw: dict[str, Any]) -> list[Candidate]:
        select = raw.get("select")
        if not isinstance(select, dict):
            return []
        options: list[dict[str, Any]] = select.get("option") or []
        candidates: list[Candidate] = []

        for i, opt in enumerate(options):
            opt_type = self._parse_option_type(opt.get("type"))
            card_id = opt.get("cardId") or opt.get("serial")
            card = {"id": card_id} if card_id else None
            candidates.append(
                Candidate(
                    option_index=i,
                    option=opt,
                    option_type=opt_type,
                    card=card,
                )
            )

        return candidates

    def _parse_select_info(
        self, raw: dict[str, Any]
    ) -> tuple[SelectType | None, SelectContext | None]:
        select = raw.get("select")
        if not isinstance(select, dict):
            return None, None
        st = select.get("type")
        sc = select.get("context")
        select_type = None
        select_context = None
        if isinstance(st, str):
            try:
                select_type = SelectType(st)
            except ValueError:
                pass
        if isinstance(sc, str):
            try:
                select_context = SelectContext(sc)
            except ValueError:
                pass
        return select_type, select_context

    def _parse_option_type(self, value: Any) -> OptionType:
        if isinstance(value, OptionType):
            return value
        if isinstance(value, str):
            try:
                return OptionType(value.upper())
            except ValueError:
                pass
        return OptionType.CARD
