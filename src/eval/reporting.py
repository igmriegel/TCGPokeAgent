from __future__ import annotations

import json
import os
import tempfile
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

from .metrics import AggregateMetrics
from .runner import RunReport


def _json_value(value: Any) -> Any:
    """Convert enums and nested dataclasses into JSON-compatible values."""
    if hasattr(value, "value"):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if hasattr(value, "items"):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
    return value


def serialize_report(report: RunReport, metrics: AggregateMetrics) -> dict[str, Any]:
    return {
        "config": report.config_name,
        "agent_mode": report.agent_mode,
        "total_matches": report.total_matches,
        "started_at": report.started_at,
        "finished_at": report.finished_at,
        "matches": [_json_value(match) for match in report.matches],
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
            "p50_decision_ms": round(metrics.p50_decision_ms, 2),
            "p95_decision_ms": round(metrics.p95_decision_ms, 2),
            "p99_decision_ms": round(metrics.p99_decision_ms, 2),
            "invalid": metrics.invalid,
            "timeouts": metrics.timeouts,
        },
    }


def write_json(report: dict[str, Any], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, destination)
    except BaseException:
        os.unlink(temporary)
        raise


def write_markdown(report: dict[str, Any], path: str | Path) -> None:
    m = report.get("metrics", {})
    lines = [
        f"# Report: {report['config']}",
        "",
        f"- Mode: {report['agent_mode']}",
        f"- Matches: {report['total_matches']}",
        f"- W/D/L: {m.get('wins', 0)}/{m.get('draws', 0)}/{m.get('losses', 0)}",
        f"- Win rate: {m.get('win_rate', 0):.2%}",
        f"- Wilson 95% CI: [{m.get('wilson_ci', [0, 0])[0]:.2%}, "
        f"{m.get('wilson_ci', [0, 0])[1]:.2%}]",
        f"- Errors: {m.get('errors', 0)}",
        f"- Avg duration: {m.get('avg_duration_ms', 0):.1f} ms",
        f"- p50/p95/p99: {m.get('p50_duration_ms', 0):.1f} / "
        f"{m.get('p95_duration_ms', 0):.1f} / {m.get('p99_duration_ms', 0):.1f} ms",
        f"- Decision p50/p95/p99: {m.get('p50_decision_ms', 0):.1f} / "
        f"{m.get('p95_decision_ms', 0):.1f} / {m.get('p99_decision_ms', 0):.1f} ms",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
