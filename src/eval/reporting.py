from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .metrics import AggregateMetrics
from .runner import RunReport


def serialize_report(report: RunReport, metrics: AggregateMetrics) -> dict[str, Any]:
    return {
        "config": report.config_name,
        "agent_mode": report.agent_mode,
        "total_matches": report.total_matches,
        "started_at": report.started_at,
        "finished_at": report.finished_at,
        "metrics": {
            "total": metrics.total,
            "wins": metrics.wins,
            "draws": metrics.draws,
            "losses": metrics.losses,
            "errors": metrics.errors,
            "win_rate": round(metrics.win_rate, 4),
            "wilson_ci": [round(metrics.wilson_lower, 4), round(metrics.wilson_upper, 4)],
            "avg_duration_ms": round(metrics.avg_duration_ms, 2),
            "p50_duration_ms": round(metrics.p50_duration_ms, 2),
            "p95_duration_ms": round(metrics.p95_duration_ms, 2),
            "p99_duration_ms": round(metrics.p99_duration_ms, 2),
        },
    }


def write_json(report: dict[str, Any], path: str | Path) -> None:
    with open(path, "w") as f:
        json.dump(report, f, indent=2)


def write_markdown(report: dict[str, Any], path: str | Path) -> None:
    m = report.get("metrics", {})
    lines = [
        f"# Relatório: {report['config']}",
        "",
        f"- Modo: {report['agent_mode']}",
        f"- Partidas: {report['total_matches']}",
        f"- W/D/L: {m.get('wins', 0)}/{m.get('draws', 0)}/{m.get('losses', 0)}",
        f"- Win rate: {m.get('win_rate', 0):.2%}",
        f"- Wilson 95% CI: [{m.get('wilson_ci', [0, 0])[0]:.2%}, {m.get('wilson_ci', [0, 0])[1]:.2%}]",
        f"- Erros: {m.get('errors', 0)}",
        f"- Duração média: {m.get('avg_duration_ms', 0):.1f} ms",
        f"- p50/p95/p99: {m.get('p50_duration_ms', 0):.1f} / {m.get('p95_duration_ms', 0):.1f} / {m.get('p99_duration_ms', 0):.1f} ms",
        "",
    ]
    with open(path, "w") as f:
        f.write("\n".join(lines))
