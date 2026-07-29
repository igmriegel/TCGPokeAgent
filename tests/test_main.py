from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import main


def test_agent_policy_returns_canonical_deck(monkeypatch) -> None:
    monkeypatch.setattr(main, "_agent", None)
    monkeypatch.setattr(main, "_deck", None)

    result = main.agent_policy({"select": None})

    assert len(result) == 60
    assert result[:4] == [721, 721, 722, 722]


def test_public_agent_delegates_to_agent_policy(monkeypatch) -> None:
    monkeypatch.setattr(main, "agent_policy", lambda observation: [7])

    assert main.agent({"select": None}) == [7]


def test_agent_policy_delegates_legal_selection(monkeypatch, sample_observation) -> None:
    class FixedAgent:
        def select(self, observation: dict[str, Any]) -> list[int]:
            return [1]

    monkeypatch.setattr(main, "_agent", FixedAgent())
    monkeypatch.setattr(main, "_deck", [721] * 60)

    assert main.agent_policy(sample_observation) == [1]


def test_agent_policy_uses_legal_fallback_for_invalid_selection(
    monkeypatch, sample_observation
) -> None:
    class InvalidAgent:
        def select(self, observation: dict[str, Any]) -> list[int]:
            return [99]

    monkeypatch.setattr(main, "_agent", InvalidAgent())
    monkeypatch.setattr(main, "_deck", [721] * 60)

    assert main.agent_policy(sample_observation) == [0]


def test_main_stdout_contains_only_json() -> None:
    root = Path(__file__).parents[1]
    completed = subprocess.run(
        [sys.executable, "main.py"],
        cwd=root,
        input='{"select": null}',
        text=True,
        capture_output=True,
        check=True,
    )

    result = json.loads(completed.stdout)
    assert len(result) == 60
    assert completed.stderr
