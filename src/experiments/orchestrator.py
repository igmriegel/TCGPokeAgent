from __future__ import annotations

from dataclasses import dataclass, field
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

    exp = Experiment(
        name=name,
        config=config,
        seeds=seeds,
        sides=sides or [0, 1],
    )
    report = exp.run()
    metrics = aggregate(report.matches)
    data = serialize_report(report, metrics)

    out_path = exp.report_path(output_dir)
    write_json(data, out_path)
    write_markdown(data, out_path.with_suffix(".md"))

    return exp
