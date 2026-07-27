from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class Config:
    project: str = ""
    seed: int = 42
    agent: str = "baseline"
    runs: int = 200
    extra: dict[str, Any] = field(default_factory=dict)


class ConfigLoader:
    def __init__(self, config_dir: str | Path) -> None:
        self._config_dir = Path(config_dir)

    def load(self, name: str) -> Config:
        path = self._resolve_path(name)
        raw = self._load_yaml_with_includes(path)
        return self._to_config(raw)

    def _resolve_path(self, name: str) -> Path:
        path = Path(name)
        if not path.is_absolute():
            path = self._config_dir / name
        if not path.suffix:
            path = path.with_suffix(".yaml")
        return path.resolve()

    def _load_yaml_with_includes(self, path: Path) -> dict[str, Any]:
        raw = self._read_yaml(path)
        include = raw.pop("include", None)
        if include:
            include_path = self._resolve_path(str(include))
            base = self._load_yaml_with_includes(include_path)
            base.update(raw)
            return base
        return raw

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        with open(path) as f:
            return dict(yaml.safe_load(f) or {})

    def _to_config(self, raw: dict[str, Any]) -> Config:
        extra = {k: v for k, v in raw.items() if k not in Config.__dataclass_fields__}
        return Config(
            project=str(raw.get("project", "")),
            seed=int(raw.get("seed", 42)),
            agent=str(raw.get("agent", "baseline")),
            runs=int(raw.get("runs", 200)),
            extra=extra,
        )


def load_config(name: str, config_dir: str | Path = "configs") -> Config:
    return ConfigLoader(config_dir).load(name)
