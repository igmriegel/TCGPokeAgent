"""Run CABT matches and enforce the observable-gameplay smoke gate.

The gate consumes decision traces from ``MatchRunner`` and checks that the
candidate produces visible main-turn actions, including attacks, instead of
only ending turns or failing execution.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os

from src.eval.gameplay import GameplayMetrics
from src.eval.runner import MatchRunner


@contextlib.contextmanager
def _quiet_native_output():
    """Hide native SDK diagnostics while preserving the gameplay summary."""
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


def main() -> None:
    """Run the gameplay smoke matrix and print aggregate action metrics."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matches", type=int, default=10)
    parser.add_argument("--agent-mode", default="heuristic")
    parser.add_argument("--opponent", default="random")
    args = parser.parse_args()
    if args.matches < 1:
        parser.error("--matches must be positive")

    with _quiet_native_output():
        report = MatchRunner(opponent=args.opponent).run_batch(
            list(range(args.matches)),
            args.agent_mode,
        )
    metrics = GameplayMetrics.from_report(report)
    print(json.dumps(metrics.to_dict(), sort_keys=True))
    try:
        metrics.assert_minimum_gameplay()
    except ValueError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
