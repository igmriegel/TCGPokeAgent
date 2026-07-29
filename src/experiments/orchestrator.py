from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from src.config.loader import Config
from src.eval.metrics import aggregate
from src.eval.reporting import serialize_report, write_json, write_markdown
from src.eval.runner import MatchRunner, RunReport


@dataclass(slots=True)
class Experiment:
    name: str
    config: Config
    seeds: list[int] = field(default_factory=list)
    sides: list[int] = field(default_factory=lambda: [0, 1])
    report: RunReport | None = None
    run_dir: Path | None = None
    manifest: dict[str, object] = field(default_factory=dict)

    def run(self) -> RunReport:
        runner = MatchRunner()
        self.report = runner.run_batch(
            seeds=self.seeds,
            agent_mode=self.config.agent,
            sides=self.sides,
        )
        return self.report

    def report_path(self, output_dir: str | Path) -> Path:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path / f"{self.name}.json"


def run_experiment(
    name: str,
    config: Config,
    seeds: list[int] | None = None,
    sides: list[int] | None = None,
    output_dir: str | Path = "reports",
) -> Experiment:
    if seeds is None:
        seeds = list(range(config.seed, config.seed + config.runs))

    root = Path(output_dir)
    resolved = config.resolved()
    effective_seeds = (
        list(seeds) if seeds is not None else list(range(config.seed, config.seed + config.runs))
    )
    run_key = sha256(
        json.dumps(
            {"name": name, "config": resolved, "seeds": effective_seeds, "sides": sides or [0, 1]},
            sort_keys=True,
        ).encode()
    ).hexdigest()[:12]
    run_dir = root / "runs" / name / run_key
    if run_dir.exists():
        raise FileExistsError(f"experiment run already exists: {run_dir}")
    run_dir.mkdir(parents=True)
    manifest = {
        "run_id": run_key,
        "experiment": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": resolved,
        "seeds": effective_seeds,
        "sides": sides or [0, 1],
        "agent": config.agent,
        "sdk_version": config.sdk_version,
        "acceptance": {"minimum_matches": config.runs, "decision": "pending"},
    }
    write_json(manifest, run_dir / "manifest.json")
    exp = Experiment(
        name=name,
        config=config,
        seeds=effective_seeds,
        sides=sides or [0, 1],
        run_dir=run_dir,
        manifest=dict(manifest),
    )
    report = exp.run()
    metrics = aggregate(report.matches)
    data = serialize_report(report, metrics)

    out_path = run_dir / "report.json"
    write_json(data, out_path)
    write_markdown(data, out_path.with_suffix(".md"))

    records = run_dir / "matches.jsonl"
    with records.open("x", encoding="utf-8") as stream:
        for match in data["matches"]:
            stream.write(json.dumps(match, sort_keys=True) + "\n")
    manifest["acceptance"] = {
        "minimum_matches": config.runs,
        "decision": "pass"
        if report.total_matches >= config.runs and metrics.errors == 0
        else "fail",
        "operational_errors": metrics.errors,
    }
    write_json(manifest, run_dir / "manifest.json")

    return exp
