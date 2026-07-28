"""Run a local cabt battle and save a replay for the PTCG visualizer."""

from __future__ import annotations

import argparse
import contextlib
import copy
import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from src.agents.baseline import BaselineAgent
from src.agents.heuristic import HeuristicAgent
from src.eval.validation import check_deck

Agent = Callable[[dict[str, Any]], list[int]]


@contextlib.contextmanager
def _quiet_native_output():
    """Hide native OpenSpiel diagnostics while creating a replay."""
    stdout_fd = os.dup(1)
    stderr_fd = os.dup(2)
    try:
        with open(os.devnull, "w", encoding="utf-8") as sink:
            os.dup2(sink.fileno(), 1)
            os.dup2(sink.fileno(), 2)
            yield
    finally:
        os.dup2(stdout_fd, 1)
        os.dup2(stderr_fd, 2)
        os.close(stdout_fd)
        os.close(stderr_fd)


def _load_deck(path: str | Path = "src/artifacts/deck.csv") -> list[int]:
    """Load the validated 60-card deck used by the engine."""
    return [int(row[0]) for row in check_deck(path)]


def _build_agent(name: str, deck: list[int]) -> Agent:
    """Build a replay policy by name, including the initial deck response."""
    normalized = name.lower()
    if normalized == "baseline":
        policy: Any = BaselineAgent()
    elif normalized == "heuristic":
        policy = HeuristicAgent()
    elif normalized == "random":
        policy = None
    else:
        raise ValueError(f"unknown replay agent: {name}")

    def select(observation: dict[str, Any]) -> list[int]:
        if observation.get("select") is None:
            return list(deck)
        if policy is None:
            select_data = observation["select"]
            options = select_data.get("option", [])
            min_count = int(select_data.get("minCount", 0) or 0)
            max_count = int(select_data.get("maxCount", 0) or 0)
            count = min(max_count, len(options))
            if count < min_count:
                return list(range(min_count))
            return sorted(random.sample(range(len(options)), count))
        return policy.select(observation)

    return select


def _run_single_battle(
    agent_one: Agent,
    agent_two: Agent,
    deck_one: list[int],
    deck_two: list[int],
    output_path: Path,
) -> dict[str, Any]:
    """Run one direct SDK battle and write the visualizer-compatible replay."""
    with _quiet_native_output():
        from kaggle_environments.envs.cabt.cg.game import (
            battle_finish,
            battle_select,
            battle_start,
            visualize_data,
        )

    observation, start_data = battle_start(deck_one, deck_two)
    if observation is None:
        raise RuntimeError(f"cabt battle failed to start: {start_data}")

    observation_log: list[Any] = [""]
    action_log: list[list[int] | None] = [None]
    steps = 0
    try:
        while observation.get("current", {}).get("result", -1) < 0:
            player_index = int(observation["current"].get("yourIndex", 0))
            action = (agent_one if player_index == 0 else agent_two)(observation)
            saved_observation = copy.deepcopy(observation)
            saved_observation.pop("search_begin_input", None)
            observation_log.append(saved_observation)
            action_log.append(action)
            observation = battle_select(action)
            steps += 1

        visualization = json.loads(visualize_data())
        if not isinstance(visualization, list):
            raise RuntimeError("cabt visualize_data did not return a list")
        for index, frame in enumerate(visualization):
            frame["obs"] = observation_log[index] if index < len(observation_log) else ""
            action = action_log[index] if index < len(action_log) else None
            frame["action"] = [action, action]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(visualization), encoding="utf-8")
        return {
            "replay": str(output_path),
            "result": observation.get("current", {}).get("result"),
            "steps": steps,
            "frames": len(visualization),
        }
    finally:
        battle_finish()


def run_replays(
    agent_one_name: str,
    agent_two_name: str,
    matches: int,
    output_dir: str | Path,
) -> list[dict[str, Any]]:
    """Generate one visualizer replay JSON per local battle."""
    deck = _load_deck()
    results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for match_index in range(1, matches + 1):
        agent_one = _build_agent(agent_one_name, deck)
        agent_two = _build_agent(agent_two_name, deck)
        replay_path = (
            Path(output_dir)
            / datetime.now().strftime("%Y%m%d")
            / f"{timestamp}_{match_index:03d}_{agent_one_name}_vs_{agent_two_name}.json"
        )
        results.append(_run_single_battle(agent_one, agent_two, deck, deck, replay_path))
    return results


def main() -> None:
    """Parse CLI options and generate local replay files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agent-one", default="heuristic", choices=("baseline", "heuristic", "random")
    )
    parser.add_argument(
        "--agent-two", default="random", choices=("baseline", "heuristic", "random")
    )
    parser.add_argument("--matches", type=int, default=1)
    parser.add_argument("--output-dir", default="replays")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.matches < 1:
        parser.error("--matches must be positive")
    random.seed(args.seed)
    for result in run_replays(args.agent_one, args.agent_two, args.matches, args.output_dir):
        print(json.dumps(result))


if __name__ == "__main__":
    main()
