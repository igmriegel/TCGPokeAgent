from src.agents.baseline import BaselineAgent


def test_agent_select_on_deck(select_none_observation):
    agent = BaselineAgent()
    result = agent.select(select_none_observation)
    assert isinstance(result, list)
    assert all(isinstance(i, int) for i in result if isinstance(result, list))


def test_agent_select_empty(empty_observation):
    agent = BaselineAgent()
    result = agent.select(empty_observation)
    assert isinstance(result, list)


def test_agent_select_sample(sample_observation):
    agent = BaselineAgent()
    result = agent.select(sample_observation)
    assert isinstance(result, list)


def test_agent_uses_lexicographic_fallback_for_unknown_context():
    agent = BaselineAgent()
    observation = {
        "select": {
            "context": "future_context",
            "minCount": 1,
            "maxCount": 1,
            "option": [{"type": "YES"}, {"type": "NO"}],
        }
    }
    assert agent.select(observation) == [0]


def test_agent_has_raw_fallback_when_parser_fails(monkeypatch, sample_observation):
    agent = BaselineAgent()

    def fail_parse(_observation):
        raise ValueError("malformed decision")

    monkeypatch.setattr(agent._parser, "parse", fail_parse)
    assert agent.select(sample_observation) == [0]


def test_agent_returns_empty_when_no_options_are_available():
    agent = BaselineAgent()
    assert agent.select({"select": {"minCount": 0, "maxCount": 1, "option": []}}) == []
    assert agent.select({"select": {"minCount": 1, "maxCount": 1, "option": []}}) == []
