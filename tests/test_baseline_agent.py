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
