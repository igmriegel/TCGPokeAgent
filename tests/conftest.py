from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def sample_observation() -> dict[str, Any]:
    return {
        "current": {
            "turn": 1,
            "turnActionCount": 0,
            "yourIndex": 0,
            "firstPlayer": 0,
            "supporterPlayed": False,
            "stadiumPlayed": False,
            "energyAttached": False,
            "retreated": False,
            "you": {
                "active": {
                    "cardId": "base1-4",
                    "hp": 120,
                    "maxHp": 120,
                    "energies": [],
                    "energyCards": [],
                    "tools": [],
                    "preEvolutions": [],
                    "appearThisTurn": True,
                },
                "bench": [],
                "benchMax": 8,
                "deckCount": 54,
                "discard": [],
                "prize": [None, None, None, None, None, None],
                "handCount": 6,
                "hand": ["base1-1", "base1-2", "base1-3", "base1-4", "base1-5", "base1-6"],
            },
            "opponent": {
                "active": {
                    "cardId": "base1-7",
                    "hp": 60,
                    "maxHp": 60,
                    "energies": [],
                    "energyCards": [],
                    "tools": [],
                    "preEvolutions": [],
                    "appearThisTurn": True,
                },
                "bench": [],
                "benchMax": 8,
                "deckCount": 54,
                "discard": [],
                "prize": [None, None, None, None, None, None],
                "handCount": 6,
                "hand": None,
            },
        },
        "select": {
            "type": "MAIN",
            "context": "ATTACK",
            "minCount": 1,
            "maxCount": 1,
            "remainEnergyCost": 0,
            "remainDamageCounter": 0,
            "option": [
                {"type": "ATTACK", "attackId": "attack-1", "cardId": "base1-4"},
                {"type": "ATTACK", "attackId": "attack-2", "cardId": "base1-4"},
                {"type": "END"},
            ],
        },
        "logs": [],
        "search_begin_input": None,
    }


@pytest.fixture
def empty_observation() -> dict[str, Any]:
    return {}


@pytest.fixture
def select_none_observation() -> dict[str, Any]:
    return {"current": None, "select": None, "logs": [], "search_begin_input": None}


@pytest.fixture
def multi_select_observation() -> dict[str, Any]:
    return {
        "current": {
            "turn": 3,
            "turnActionCount": 2,
            "yourIndex": 0,
            "firstPlayer": 0,
            "you": {
                "active": {"cardId": "base1-4", "hp": 120, "maxHp": 120},
                "bench": [],
                "deckCount": 50,
                "discard": [],
                "prize": [None] * 6,
                "handCount": 5,
                "hand": ["e1", "e2", "e3"],
            },
            "opponent": {
                "active": {"cardId": "base1-7", "hp": 60, "maxHp": 60},
                "bench": [],
                "deckCount": 52,
                "discard": [],
                "prize": [None] * 6,
                "handCount": 5,
                "hand": None,
            },
        },
        "select": {
            "type": "ENERGY",
            "context": "ATTACH_ENERGY",
            "minCount": 1,
            "maxCount": 2,
            "remainEnergyCost": 2,
            "remainDamageCounter": 0,
            "option": [
                {"type": "ENERGY", "count": 1, "cardId": "e1"},
                {"type": "ENERGY", "count": 1, "cardId": "e2"},
                {"type": "ENERGY", "count": 1, "cardId": "e3"},
            ],
        },
        "logs": [],
        "search_begin_input": None,
    }


@pytest.fixture
def min_count_zero_observation() -> dict[str, Any]:
    return {
        "current": {
            "turn": 2,
            "turnActionCount": 1,
            "yourIndex": 0,
            "firstPlayer": 0,
            "you": {"active": {"cardId": "b1", "hp": 60, "maxHp": 60}, "bench": [], "deckCount": 55},
            "opponent": {"active": {"cardId": "b2", "hp": 50, "maxHp": 50}, "bench": [], "deckCount": 56},
        },
        "select": {
            "type": "YES_NO",
            "context": "ACTIVATE",
            "minCount": 0,
            "maxCount": 1,
            "remainEnergyCost": 0,
            "remainDamageCounter": 0,
            "option": [{"type": "YES"}, {"type": "NO"}],
        },
        "logs": [],
        "search_begin_input": None,
    }
