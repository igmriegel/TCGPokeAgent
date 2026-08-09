from __future__ import annotations

from src.agents.heuristic import HeuristicAgent
from src.core import DecisionTrace, DeckDefinition


def test_heuristic_decision_exposes_stage_trace_without_renumbering_indices() -> None:
    agent = HeuristicAgent()
    deck = DeckDefinition.from_cards([463] * 60, "trace-test")
    agent.start_match(deck)
    observation = {
        "current": {
            "yourIndex": 0,
            "turn": 1,
            "turnActionCount": 1,
            "players": [
                {
                    "active": [{"id": 463, "serial": 1}],
                    "bench": [],
                    "hand": [{"id": 17, "serial": 2}],
                    "handCount": 1,
                    "deckCount": 50,
                    "discard": [],
                    "prize": [],
                },
                {
                    "active": [{"id": 463, "serial": 3}],
                    "bench": [],
                    "hand": None,
                    "handCount": 0,
                    "deckCount": 50,
                    "discard": [],
                    "prize": [],
                },
            ],
        },
        "select": {
            "type": 0,
            "context": 0,
            "minCount": 1,
            "maxCount": 1,
            "option": [{"type": 14}],
        },
    }

    decision = agent.decide(observation)

    assert isinstance(decision.trace, DecisionTrace)
    assert decision.trace.schema_version == "decision-trace-v1"
    assert decision.trace.candidates[0].option_index == 0
    assert decision.trace.selected_indices == decision.selection.indices
    assert [stage.name for stage in decision.trace.stages] == [
        "generate",
        "filter_dangerous_shuffle_supporters",
        "filter_forbidden",
        "main_phase",
        "rank",
    ]
