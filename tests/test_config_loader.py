import tempfile
from pathlib import Path

import yaml

from src.config.loader import ConfigLoader


def test_load_default():
    loader = ConfigLoader("configs")
    config = loader.load("default.yaml")

    assert config.project == "Pokemon_TCG_engine_Kaggle"
    assert config.seed == 42
    assert config.agent == "baseline"


def test_load_eval_small():
    loader = ConfigLoader("configs")
    config = loader.load("eval_small.yaml")

    assert config.project == "Pokemon_TCG_engine_Kaggle"
    assert config.seed == 42
    assert config.runs == 10


def test_load_agent_config():
    loader = ConfigLoader("configs")
    config = loader.load("agent_heuristic.yaml")

    assert config.agent == "heuristic"


def test_load_without_suffix():
    loader = ConfigLoader("configs")
    config = loader.load("default")
    assert config.seed == 42
