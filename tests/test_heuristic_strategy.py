from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from src.agents.factory import load_deck_profile
from src.agents.heuristic import HeuristicAgent
from src.core import (
    Candidate,
    DeckDefinition,
    GameState,
    OptionType,
    PlayerState,
    Selection,
)

_ROOT = Path(__file__).resolve().parents[1]


def _built_agent() -> HeuristicAgent:
    agent = HeuristicAgent(deck_profile=load_deck_profile(_ROOT))
    deck = DeckDefinition.from_path(
        _ROOT / "src" / "artifacts" / "deck.csv", "mega_abomasnow_kyogre"
    )
    agent.start_match(deck)
    return agent


def _pokemon(card_id: int, hp: int, *, serial: int, energies: int = 0, area: int = 4) -> dict:
    return {
        "id": card_id,
        "serial": serial,
        "playerIndex": 0,
        "hp": hp,
        "maxHp": hp,
        "energies": [3] * energies,
        "energyCards": [],
        "tools": [],
        "preEvolution": [],
        "area": area,
    }


def _observation(
    *,
    select_type: str,
    select_context: str,
    options: list[dict],
    your_active: dict,
    your_bench: list[dict],
    your_hand: list[dict] | None,
    opponent_active_hp: int = 150,
    your_discard_energy: int = 0,
    your_deck_count: int = 30,
) -> dict:
    players = [
        {
            "active": [your_active],
            "bench": your_bench,
            "benchMax": 5,
            "deckCount": your_deck_count,
            "discard": [
                {"id": 3, "serial": 100 + index, "playerIndex": 0}
                for index in range(your_discard_energy)
            ],
            "hand": your_hand,
            "handCount": len(your_hand) if your_hand is not None else 0,
            "prize": [None] * 6,
        },
        {
            "active": [_pokemon(721, opponent_active_hp, serial=50)],
            "bench": [],
            "benchMax": 5,
            "deckCount": 10,
            "discard": [],
            "hand": None,
            "handCount": 5,
            "prize": [None] * 6,
        },
    ]
    return {
        "current": {
            "turn": 5,
            "turnActionCount": 0,
            "yourIndex": 0,
            "firstPlayer": 0,
            "supporterPlayed": False,
            "stadiumPlayed": False,
            "energyAttached": False,
            "retreated": False,
            "players": players,
        },
        "select": {
            "type": select_type,
            "context": select_context,
            "minCount": 1,
            "maxCount": 1,
            "remainEnergyCost": 0,
            "remainDamageCounter": 0,
            "option": options,
        },
        "logs": [],
    }


def test_bench_development_prefers_snover() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "PLAY", "cardId": 722, "area": 2},
            {"type": "PLAY", "cardId": 721, "area": 2},
            {"type": "END"},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=2),
        your_bench=[],
        your_hand=[
            _pokemon(722, 90, serial=1, area=2),
            _pokemon(721, 150, serial=2, area=2),
        ],
    )

    assert agent.select(observation) == [0]


def test_snover_not_discarded() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="CARD",
        select_context="DISCARD",
        options=[
            {"type": "CARD", "cardId": 722},
            {"type": "CARD", "cardId": 3},
            {"type": "CARD", "cardId": 1121},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=2),
        your_bench=[_pokemon(722, 90, serial=1, area=2)],
        your_hand=None,
    )

    assert agent.select(observation) != [0]


def test_pokepad_search_prefers_snover() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="CARD",
        select_context="TO_HAND",
        options=[
            {"type": "CARD", "cardId": 722},
            {"type": "CARD", "cardId": 721},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=2),
        your_bench=[],
        your_hand=None,
    )

    assert agent.select(observation) == [0]


def test_petrel_search_prefers_item_or_lillie() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="CARD",
        select_context="TO_HAND",
        options=[
            {"type": "CARD", "cardId": 1219},
            {"type": "CARD", "cardId": 1227},
            {"type": "CARD", "cardId": 1121},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=2),
        your_bench=[],
        your_hand=None,
    )

    assert agent.select(observation) != [0]


def test_lillie_is_avoided_when_hand_plus_deck_is_insecure() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="CARD",
        select_context="TO_HAND",
        options=[
            {"type": "CARD", "cardId": 1227},
            {"type": "CARD", "cardId": 1121},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=2),
        your_bench=[],
        your_hand=[_pokemon(722, 90, serial=1, area=2)],
        your_deck_count=6,
    )

    assert agent.select(observation) == [1]


def test_heuristic_evolve_priority() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "EVOLVE", "cardId": 723, "area": 2},
            {"type": "ATTACH", "cardId": 3, "inPlayArea": 4, "inPlayIndex": 0},
            {"type": "END"},
        ],
        your_active=_pokemon(722, 90, serial=11, energies=1),
        your_bench=[],
        your_hand=[_pokemon(723, 300, serial=2, area=2)],
    )

    assert agent.select(observation) == [0]


def test_heuristic_deck_out_prefers_riptide_over_bench_development() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "ATTACK", "attackId": 1042, "inPlayArea": 4},
            {"type": "PLAY", "cardId": 722, "area": 2},
            {"type": "END"},
        ],
        your_active=_pokemon(721, 150, serial=11, energies=1),
        your_bench=[_pokemon(722, 90, serial=1, area=2)],
        your_hand=[_pokemon(722, 90, serial=3, area=2)],
        your_discard_energy=18,
        your_deck_count=4,
    )

    assert agent.select(observation) == [0]


def test_evolve_precedes_energy_attachment() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "EVOLVE", "cardId": 723, "area": 2},
            {"type": "ATTACH", "cardId": 3, "inPlayArea": 4, "inPlayIndex": 0},
            {"type": "ATTACH", "cardId": 3, "inPlayArea": 2, "inPlayIndex": 0},
        ],
        your_active=_pokemon(722, 90, serial=11, energies=0),
        your_bench=[],
        your_hand=[_pokemon(723, 300, serial=2, area=2), _pokemon(3, 0, serial=3)],
    )

    assert agent.select(observation) == [0]


def test_main_turn_re_evaluates_sequential_phases_across_prompts() -> None:
    agent = _built_agent()
    first_observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "EVOLVE", "cardId": 723, "area": 2},
            {"type": "ATTACH", "cardId": 3, "inPlayArea": 4, "inPlayIndex": 0},
            {"type": "ATTACK", "attackId": 1042, "inPlayArea": 4},
        ],
        your_active=_pokemon(722, 90, serial=11, energies=0),
        your_bench=[],
        your_hand=[_pokemon(723, 300, serial=2, area=2), _pokemon(3, 0, serial=3)],
        opponent_active_hp=150,
    )
    second_observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "ATTACH", "cardId": 3, "inPlayArea": 4, "inPlayIndex": 0},
            {"type": "ATTACK", "attackId": 1042, "inPlayArea": 4},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=1),
        your_bench=[],
        your_hand=[_pokemon(3, 0, serial=3)],
        opponent_active_hp=150,
    )

    assert agent.select(first_observation) == [0]
    assert agent.select(second_observation) == [0]


def test_post_evolution_energy_completes_active_attack() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "ATTACH", "cardId": 3, "inPlayArea": 4, "inPlayIndex": 0},
            {"type": "ATTACH", "cardId": 3, "inPlayArea": 2, "inPlayIndex": 0},
            {"type": "END"},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=1),
        your_bench=[_pokemon(722, 90, serial=1, area=2)],
        your_hand=[_pokemon(3, 0, serial=3)],
    )

    assert agent.select(observation) == [0]


def test_attach_useful_tool_only_for_tools() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "ATTACH", "cardId": 1163, "inPlayArea": 4, "inPlayIndex": 0},
            {"type": "ATTACH", "cardId": 1121, "inPlayArea": 2, "inPlayIndex": 0},
            {"type": "END"},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=2),
        your_bench=[_pokemon(722, 90, serial=1, area=2)],
        your_hand=[_pokemon(1163, 0, serial=3), _pokemon(1121, 0, serial=4)],
    )

    assert agent.select(observation) == [0]


def test_attachment_enables_active_attack() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "ATTACH", "cardId": 3, "inPlayArea": 4, "inPlayIndex": 0},
            {"type": "ATTACH", "cardId": 3, "inPlayArea": 2, "inPlayIndex": 0},
            {"type": "PLAY", "cardId": 721, "area": 2},
            {"type": "END"},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=1),
        your_bench=[_pokemon(722, 90, serial=1, area=2)],
        your_hand=[_pokemon(721, 150, serial=5, area=2), _pokemon(3, 0, serial=6)],
    )

    assert agent.select(observation) == [0]


def test_retreat_prefers_ready_replacement_when_public_risk() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "RETREAT"},
            {"type": "ATTACK", "attackId": 1046, "inPlayArea": 4},
            {"type": "END"},
        ],
        your_active=_pokemon(723, 120, serial=11, energies=2),
        your_bench=[_pokemon(721, 150, serial=1, area=2, energies=3)],
        your_hand=[_pokemon(721, 150, serial=3, area=2)],
        opponent_active_hp=120,
    )
    observation["current"]["players"][1]["active"][0]["id"] = 723
    observation["current"]["players"][1]["active"][0]["energies"] = [3, 3, 3]

    assert agent.select(observation) == [0]


def test_retreat_is_skipped_without_ready_replacement() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "RETREAT"},
            {"type": "ATTACK", "attackId": 1046, "inPlayArea": 4},
            {"type": "END"},
        ],
        your_active=_pokemon(723, 350, serial=11, energies=2),
        your_bench=[_pokemon(721, 150, serial=1, area=2, energies=0)],
        your_hand=[_pokemon(721, 150, serial=3, area=2)],
        opponent_active_hp=120,
    )
    observation["current"]["players"][1]["active"][0]["id"] = 723
    observation["current"]["players"][1]["active"][0]["energies"] = [3, 3, 3]

    assert agent.select(observation) == [1]


def test_articuno_branch_prefers_the_visible_matchup_answer() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "PLAY", "cardId": 414, "area": 2},
            {"type": "PLAY", "cardId": 722, "area": 2},
            {"type": "END"},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=2),
        your_bench=[],
        your_hand=[_pokemon(414, 120, serial=3, area=2), _pokemon(722, 90, serial=4, area=2)],
        opponent_active_hp=50,
    )

    observation["current"]["players"][1]["active"][0]["id"] = 741
    observation["current"]["players"][1]["active"][0]["hp"] = 50

    assert agent.select(observation) == [0]


def test_articuno_branch_prefers_energy_on_active_articuno() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "ATTACH", "cardId": 3, "inPlayArea": 4, "inPlayIndex": 0},
            {"type": "ATTACH", "cardId": 3, "inPlayArea": 2, "inPlayIndex": 0},
            {"type": "END"},
        ],
        your_active=_pokemon(414, 120, serial=11, energies=2),
        your_bench=[_pokemon(722, 90, serial=1, area=2)],
        your_hand=[_pokemon(3, 0, serial=3)],
        opponent_active_hp=50,
    )

    observation["current"]["players"][1]["active"][0]["id"] = 741
    observation["current"]["players"][1]["active"][0]["hp"] = 50

    assert agent.select(observation) == [0]


def test_opening_articuno_prefers_bench_energy_over_self_attachment() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "ATTACH", "cardId": 3, "inPlayArea": 4, "inPlayIndex": 0},
            {"type": "ATTACH", "cardId": 3, "inPlayArea": 2, "inPlayIndex": 0},
            {"type": "END"},
        ],
        your_active=_pokemon(414, 120, serial=11, energies=0),
        your_bench=[_pokemon(721, 150, serial=1, area=2)],
        your_hand=[_pokemon(3, 0, serial=3)],
        opponent_active_hp=150,
    )

    observation["current"]["turn"] = 1

    assert agent.select(observation) == [1]


def test_opening_articuno_is_discarded_before_energy() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="CARD",
        select_context="DISCARD",
        options=[
            {"type": "CARD", "cardId": 414},
            {"type": "CARD", "cardId": 3},
            {"type": "CARD", "cardId": 1121},
        ],
        your_active=_pokemon(414, 120, serial=11, energies=0),
        your_bench=[],
        your_hand=None,
        opponent_active_hp=150,
    )

    observation["current"]["turn"] = 1

    assert agent.select(observation) == [0]


def test_second_attack_preferred_over_first_when_guaranteed_ko() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "ATTACK", "attackId": 1043, "inPlayArea": 4},
            {"type": "ATTACK", "attackId": 1042, "inPlayArea": 4},
            {"type": "END"},
        ],
        your_active=_pokemon(721, 150, serial=11, energies=3),
        your_bench=[],
        your_hand=None,
        opponent_active_hp=130,
    )

    assert agent.select(observation) == [0]


def test_guaranteed_ko_attack_preferred_over_hammerlanche() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "ATTACK", "attackId": 1047, "inPlayArea": 4},
            {"type": "ATTACK", "attackId": 1046, "inPlayArea": 4},
            {"type": "END"},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=3),
        your_bench=[],
        your_hand=None,
        opponent_active_hp=150,
    )

    assert agent.select(observation) == [0]


def test_swirling_waves_ko_preferred_over_hammerlanche() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "ATTACK", "attackId": 1043, "inPlayArea": 4},
            {"type": "ATTACK", "attackId": 1046, "inPlayArea": 4},
            {"type": "END"},
        ],
        your_active=_pokemon(721, 150, serial=11, energies=3),
        your_bench=[],
        your_hand=None,
        opponent_active_hp=130,
    )

    assert agent.select(observation) == [0]


def test_all_items_played_before_supporter() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "PLAY", "cardId": 1121, "area": 2},
            {"type": "PLAY", "cardId": 1227, "area": 2},
            {"type": "END"},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=2),
        your_bench=[],
        your_hand=[
            _pokemon(1121, 0, serial=3, area=2),
            _pokemon(1227, 0, serial=4, area=2),
        ],
    )

    assert agent.select(observation) == [0]


def test_supporter_played_when_no_items_available() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "PLAY", "cardId": 1227, "area": 2},
            {"type": "END"},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=2),
        your_bench=[],
        your_hand=[_pokemon(1227, 0, serial=3, area=2)],
    )

    assert agent.select(observation) == [0]


def test_shuffle_supporter_deck_out_accounts_for_the_played_card() -> None:
    player = SimpleNamespace(deck_count=3, hand_count=3, prize=[None] * 6)
    candidate = Candidate(
        0,
        {
            "type": "PLAY",
        },
        OptionType.PLAY,
        card={
            "cardType": 3,
            "skills": [
                {"text": "Shuffle your hand into your deck. Then draw 6 cards."},
            ],
        },
    )
    assert HeuristicAgent._shuffle_supporter_deck_out(player, candidate) is True

    safe_player = SimpleNamespace(deck_count=4, hand_count=3, prize=[None] * 6)
    assert HeuristicAgent._shuffle_supporter_deck_out(safe_player, candidate) is False


def test_dangerous_shuffle_supporter_is_filtered_before_attack() -> None:
    agent = _built_agent()
    state = GameState(
        your_index=0,
        players=[
            PlayerState(deck_count=3, hand_count=3, prize=[None] * 6),
        ],
    )
    dangerous_supporter = Candidate(
        0,
        {
            "type": "PLAY",
        },
        OptionType.PLAY,
        card={
            "cardType": 3,
            "skills": [
                {"text": "Shuffle your hand into your deck. Then draw 6 cards."},
            ],
        },
    )
    end_candidate = Candidate(1, {"type": "END"}, OptionType.END)
    selections = [
        Selection((0,), (OptionType.PLAY,)),
        Selection((1,), (OptionType.END,)),
    ]

    filtered = agent._filter_dangerous_shuffle_supporters(
        state,
        selections,
        [dangerous_supporter, end_candidate],
    )

    assert filtered == [Selection((1,), (OptionType.END,))]


def test_guaranteed_attack_damage_uses_profile_plans() -> None:
    agent = _built_agent()
    candidates = [
        Candidate(0, {"type": "ATTACK", "attackId": 1043}, OptionType.ATTACK),
        Candidate(1, {"type": "ATTACK", "attackId": 1047}, OptionType.ATTACK),
        Candidate(2, {"type": "ATTACK", "attackId": 1046}, OptionType.ATTACK),
        Candidate(3, {"type": "ATTACK", "attackId": 1042}, OptionType.ATTACK),
    ]
    state = GameState()

    damages = [
        agent._scorer._guaranteed_attack_damage(state, candidate) for candidate in candidates
    ]

    assert damages == [130, 200, 0, 0]


def test_guaranteed_ko_attack_waits_for_ultra_ball() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "ATTACK", "attackId": 1047, "inPlayArea": 4},
            {"type": "PLAY", "cardId": 1121, "area": 2},
            {"type": "END"},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=3),
        your_bench=[],
        your_hand=[_pokemon(1121, 0, serial=3, area=2)],
        opponent_active_hp=150,
    )

    assert agent.select(observation) == [1]


def test_guaranteed_ko_attack_waits_for_available_snover() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "ATTACK", "attackId": 1047, "inPlayArea": 4},
            {"type": "PLAY", "cardId": 722, "area": 2},
            {"type": "END"},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=3),
        your_bench=[],
        your_hand=[_pokemon(722, 90, serial=1, area=2)],
        opponent_active_hp=150,
    )

    assert agent.select(observation) == [1]


def test_snover_preferred_over_ultra_ball_when_developing_bench() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "PLAY", "cardId": 1121, "area": 2},
            {"type": "PLAY", "cardId": 722, "area": 2},
            {"type": "END"},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=3),
        your_bench=[],
        your_hand=[_pokemon(722, 90, serial=1, area=2), _pokemon(1121, 0, serial=3, area=2)],
    )

    assert agent.select(observation) == [1]


def test_ultra_ball_played_when_attack_is_absent() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "PLAY", "cardId": 1121, "area": 2},
            {"type": "END"},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=2),
        your_bench=[],
        your_hand=[_pokemon(1121, 0, serial=3, area=2)],
    )

    assert agent.select(observation) == [0]


def test_snover_played_before_hammerlanche_when_attack_is_weaker() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "ATTACK", "attackId": 1046, "inPlayArea": 4},
            {"type": "PLAY", "cardId": 722, "area": 2},
            {"type": "END"},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=3),
        your_bench=[],
        your_hand=[_pokemon(722, 90, serial=1, area=2)],
        opponent_active_hp=150,
    )

    assert agent.select(observation) == [1]


def test_attack_waits_until_the_board_is_fully_developed() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "ATTACK", "attackId": 1047, "inPlayArea": 4},
            {"type": "PLAY", "cardId": 722, "area": 2},
            {"type": "END"},
        ],
        your_active=_pokemon(723, 300, serial=11, energies=3),
        your_bench=[_pokemon(722, 90, serial=1, area=2)],
        your_hand=[_pokemon(722, 90, serial=2, area=2)],
        opponent_active_hp=150,
    )

    assert agent.select(observation) == [1]


def test_evolve_still_precedes_a_weaker_attack() -> None:
    agent = _built_agent()
    observation = _observation(
        select_type="MAIN",
        select_context="MAIN",
        options=[
            {"type": "EVOLVE", "cardId": 723, "area": 2},
            {"type": "ATTACK", "attackId": 1044, "inPlayArea": 4},
            {"type": "END"},
        ],
        your_active=_pokemon(722, 90, serial=11, energies=1),
        your_bench=[],
        your_hand=[_pokemon(723, 300, serial=2, area=2)],
        opponent_active_hp=150,
    )

    assert agent.select(observation) == [0]
