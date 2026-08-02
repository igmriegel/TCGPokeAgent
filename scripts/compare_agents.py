"""Compare policy outcomes against the SDK random baseline only.

This script measures win/draw/loss counts for the local ``baseline`` and
``heuristic`` agents against the CABT ``random`` opponent on both sides. It
does not compute aggregate metrics, decision latency, or gameplay quality
beyond final match outcomes and execution errors.
"""

from __future__ import annotations

import argparse
import contextlib
import os
from collections import Counter
from typing import Any


@contextlib.contextmanager
def _quiet_native_output():
    """Hide native SDK diagnostics during comparison runs."""
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


def _outcome(reward: Any) -> str:
    """Map an SDK reward to a stable W/D/L label."""
    if isinstance(reward, (int, float)):
        return "W" if reward > 0 else "L" if reward < 0 else "D"
    return "ERROR"


def compare(matches: int) -> dict[str, Counter[str]]:
    """Run each policy on both sides against random and return outcome counts.

    Args:
        matches: Number of runs per side and per agent mode.

    Returns:
        Outcome counters keyed by agent mode.
    """
    with _quiet_native_output():
        from kaggle_environments import make
        from kaggle_environments.envs.cabt.cabt import random_agent

        import main

    report: dict[str, Counter[str]] = {}
    for mode in ("baseline", "heuristic"):
        outcomes: Counter[str] = Counter()
        os.environ["AGENT_MODE"] = mode
        for side in (0, 1):
            for _ in range(matches):
                main._agent = None
                main._deck = None
                agents = [main.agent_policy, random_agent]
                if side == 1:
                    agents.reverse()
                with _quiet_native_output():
                    environment = make("cabt", debug=False)
                    environment.run(agents)
                player = environment.state[side]
                if all(getattr(item, "status", None) == "DONE" for item in environment.state):
                    outcomes[_outcome(getattr(player, "reward", None))] += 1
                else:
                    outcomes["ERROR"] += 1
        report[mode] = outcomes
    return report


def main() -> None:
    """Run the comparison and print a machine-readable summary."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--matches", type=int, default=10)
    args = parser.parse_args()
    report = compare(args.matches)
    for mode, outcomes in report.items():
        total = sum(outcomes.values())
        print(f"{mode}: {dict(sorted(outcomes.items()))} total={total}")
    if any(outcomes.get("ERROR", 0) for outcomes in report.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
