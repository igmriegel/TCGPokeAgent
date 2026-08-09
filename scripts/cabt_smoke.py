"""Run a bounded cabt smoke matrix against the packaged agent."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@contextlib.contextmanager
def _quiet_native_output():
    """Hide native SDK diagnostics while preserving the smoke summary."""
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


def _run_match(agent: Callable[[dict[str, Any]], list[int]], opponent: Any) -> bool:
    """Run one match and return whether both players completed normally."""
    from kaggle_environments import make

    with _quiet_native_output():
        environment = make("cabt", debug=False)
        environment.run([agent, opponent])
    return all(getattr(player, "status", None) == "DONE" for player in environment.state)


def _run_match_result(players: list[Any], tracked_side: int) -> str:
    """Run one match and return the tracked agent's terminal result."""
    from kaggle_environments import make

    with _quiet_native_output():
        environment = make("cabt", debug=False)
        environment.run(players)
    if not all(getattr(player, "status", None) == "DONE" for player in environment.state):
        return "errors"
    own_reward = float(getattr(environment.state[tracked_side], "reward", 0) or 0)
    opponent_reward = float(getattr(environment.state[1 - tracked_side], "reward", 0) or 0)
    if own_reward > opponent_reward:
        return "wins"
    if own_reward < opponent_reward:
        return "losses"
    return "draws"


def run_smoke(matches: int, agent_mode: str) -> tuple[int, int]:
    """Run the agent on both sides for a fixed number of cabt matches."""
    with _quiet_native_output():
        from kaggle_environments.envs.cabt.cabt import random_agent

        import main

    os.environ["AGENT_MODE"] = agent_mode
    completed = 0
    failures = 0
    for _ in range(matches):
        main._agent = None
        main._deck = None
        for opponent in (random_agent,):
            if _run_match(main.agent_policy, opponent):
                completed += 1
            else:
                failures += 1
        main._agent = None
        main._deck = None
        with _quiet_native_output():
            from kaggle_environments import make

            environment = make("cabt", debug=False)
            environment.run([random_agent, main.agent_policy])
        if all(getattr(player, "status", None) == "DONE" for player in environment.state):
            completed += 1
        else:
            failures += 1
    return completed, failures


def run_performance(matches: int, agent_mode: str) -> dict[str, int]:
    """Run balanced CABT matches and aggregate outcomes for the configured agent."""
    with _quiet_native_output():
        from kaggle_environments.envs.cabt.cabt import random_agent

        import main

    os.environ["AGENT_MODE"] = agent_mode
    outcomes = {"wins": 0, "losses": 0, "draws": 0, "errors": 0}
    for _ in range(matches):
        for tracked_side in (0, 1):
            main._agent = None
            main._deck = None
            players = (
                [main.agent_policy, random_agent]
                if tracked_side == 0
                else [random_agent, main.agent_policy]
            )
            outcomes[_run_match_result(players, tracked_side)] += 1
    return outcomes


def main() -> None:
    """Parse arguments, run smoke matches, and fail on any engine failure."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--matches", type=int, default=20)
    parser.add_argument("--agent-mode", default="expert_turn_loop")
    parser.add_argument("--performance", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.performance:
        output_fd = os.dup(1)
        try:
            outcomes = run_performance(args.matches, args.agent_mode)
            total = sum(outcomes.values())
            if args.output is not None:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(
                    json.dumps(
                        {
                            "agent_mode": args.agent_mode,
                            "iterations_per_side": args.matches,
                            "total_matches": total,
                            "outcomes": outcomes,
                        },
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
            os.write(output_fd, f"cabt performance: {outcomes}, total={total}\n".encode())
        finally:
            os.close(output_fd)
        if outcomes["errors"]:
            raise SystemExit(1)
        return
    completed, failures = run_smoke(args.matches, args.agent_mode)
    print(f"cabt smoke: {completed} completed, {failures} failed")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
