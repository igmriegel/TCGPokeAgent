"""Export local, package-provenant decision traces from CABT replay files."""

from __future__ import annotations

import argparse
import json
import tarfile
import tempfile
from pathlib import Path

try:
    from scripts.audit_submission_55333874 import _run_worker
except ModuleNotFoundError:
    from audit_submission_55333874 import _run_worker


def _extract_archive(archive: Path, destination: Path) -> Path:
    """Extract one validated package archive into a temporary directory."""
    with tarfile.open(archive, "r:gz") as handle:
        handle.extractall(destination, filter="data")
    return destination


def main() -> int:
    """Run a local replay audit and write JSONL traces plus a summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--package", type=Path)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="decision-trace-") as temporary:
        package_root = None
        if args.package is not None:
            package_root = _extract_archive(args.package, Path(temporary))
        worker_output = Path(temporary) / "worker.json"
        _run_worker(args.replay_dir, worker_output, "submitted_package", package_root)
        payload = json.loads(worker_output.read_text(encoding="utf-8"))
        decisions = payload.get("decisions", [])
        trace_path = args.output_dir / "decision_traces.jsonl"
        with trace_path.open("w", encoding="utf-8") as stream:
            for decision in decisions:
                record = {
                    "episode_id": decision.get("episode_id"),
                    "step": decision.get("step"),
                    "turn": decision.get("turn"),
                    "executed_action": decision.get("executed_action"),
                    "generated_action": decision.get("generated_action"),
                    "result_matches_replay": decision.get("result_matches_submission"),
                    "decision_trace": decision.get("decision_trace"),
                }
                stream.write(json.dumps(record, sort_keys=True) + "\n")
        summary = dict(payload.get("summary", {}))
        summary["trace_file"] = str(trace_path)
        (args.output_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
