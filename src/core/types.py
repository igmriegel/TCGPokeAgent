from __future__ import annotations

from enum import Enum
from typing import NewType


MatchupLabel = NewType("MatchupLabel", str)


class TurnPhase(str, Enum):
    UNKNOWN = "unknown"
    START = "start"
    DRAW = "draw"
    MAIN = "main"
    ATTACK = "attack"
    END = "end"


class MatchResult(str, Enum):
    WIN = "win"
    DRAW = "draw"
    LOSS = "loss"
    UNKNOWN = "unknown"


class ExecutionStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    INVALID = "invalid"


class ErrorCategory(str, Enum):
    NONE = "none"
    PARSE = "parse"
    POLICY = "policy"
    LEGALITY = "legality"
    TIMEOUT = "timeout"
    RUNTIME = "runtime"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class AgentMode(str, Enum):
    BASELINE = "baseline"
    HEURISTIC = "heuristic"
    HYBRID = "hybrid"


class SelectType(str, Enum):
    MAIN = "MAIN"
    CARD = "CARD"
    ATTACHED_CARD = "ATTACHED_CARD"
    CARD_OR_ATTACHED_CARD = "CARD_OR_ATTACHED_CARD"
    ENERGY = "ENERGY"
    SKILL = "SKILL"
    ATTACK = "ATTACK"
    EVOLVE = "EVOLVE"
    COUNT = "COUNT"
    YES_NO = "YES_NO"
    SPECIAL_CONDITION = "SPECIAL_CONDITION"


class SelectContext(str, Enum):
    SETUP_ACTIVE_POKEMON = "SETUP_ACTIVE_POKEMON"
    SETUP_BENCH_POKEMON = "SETUP_BENCH_POKEMON"
    IS_FIRST = "IS_FIRST"
    MULLIGAN = "MULLIGAN"
    SWITCH = "SWITCH"
    TO_ACTIVE = "TO_ACTIVE"
    TO_BENCH = "TO_BENCH"
    TO_FIELD = "TO_FIELD"
    TO_HAND = "TO_HAND"
    TO_DECK = "TO_DECK"
    TO_DECK_BOTTOM = "TO_DECK_BOTTOM"
    TO_PRIZE = "TO_PRIZE"
    NOT_MOVE = "NOT_MOVE"
    DISCARD = "DISCARD"
    DAMAGE = "DAMAGE"
    DAMAGE_COUNTER = "DAMAGE_COUNTER"
    DAMAGE_COUNTER_ANY = "DAMAGE_COUNTER_ANY"
    HEAL = "HEAL"
    REMOVE_DAMAGE_COUNTER = "REMOVE_DAMAGE_COUNTER"
    EFFECT_TARGET = "EFFECT_TARGET"
    EVOLVES_FROM = "EVOLVES_FROM"
    EVOLVES_TO = "EVOLVES_TO"
    DEVOLVE = "DEVOLVE"
    EVOLVE = "EVOLVE"
    ATTACH_ENERGY = "ATTACH_ENERGY"
    ATTACH_TOOL = "ATTACH_TOOL"
    DETACH_FROM = "DETACH_FROM"
    DISCARD_ENERGY = "DISCARD_ENERGY"
    DISCARD_TOOL = "DISCARD_TOOL"
    SWITCH_ENERGY = "SWITCH_ENERGY"
    SKILL_ORDER = "SKILL_ORDER"
    ATTACK = "ATTACK"
    DISABLE_ATTACK = "DISABLE_ATTACK"
    DRAW_COUNT = "DRAW_COUNT"
    DAMAGE_COUNTER_COUNT = "DAMAGE_COUNTER_COUNT"
    REMOVE_DAMAGE_COUNTER_COUNT = "REMOVE_DAMAGE_COUNTER_COUNT"
    ACTIVATE = "ACTIVATE"
    FIRST_EFFECT = "FIRST_EFFECT"
    MORE_DEVOLVE = "MORE_DEVOLVE"
    COIN_HEAD = "COIN_HEAD"
    AFFECT_SPECIAL_CONDITION = "AFFECT_SPECIAL_CONDITION"
    RECOVER_SPECIAL_CONDITION = "RECOVER_SPECIAL_CONDITION"


class OptionType(str, Enum):
    PLAY = "PLAY"
    ATTACH = "ATTACH"
    EVOLVE = "EVOLVE"
    ABILITY = "ABILITY"
    DISCARD = "DISCARD"
    RETREAT = "RETREAT"
    ATTACK = "ATTACK"
    END = "END"
    CARD = "CARD"
    TOOL_CARD = "TOOL_CARD"
    ENERGY_CARD = "ENERGY_CARD"
    ENERGY = "ENERGY"
    SKILL = "SKILL"
    NUMBER = "NUMBER"
    YES = "YES"
    NO = "NO"
    SPECIAL_CONDITION = "SPECIAL_CONDITION"
