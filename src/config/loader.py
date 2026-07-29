from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class Config:
    project: str = ""
    sdk_version: str = "1.32.2"
    seed: int = 42
    agent: str = "baseline"
    runs: int = 200
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def evaluation(self) -> dict[str, Any]:
        """Return the resolved evaluation section."""
        value = self.extra.get("evaluation", {})
        return dict(value) if isinstance(value, dict) else {}

    @property
    def search(self) -> dict[str, Any]:
        """Return the resolved search section."""
        value = self.extra.get("search", {})
        return dict(value) if isinstance(value, dict) else {}

    def resolved(self) -> dict[str, Any]:
        """Return a JSON-safe resolved configuration."""
        return {
            "project": self.project,
            "sdk_version": self.sdk_version,
            "seed": self.seed,
            "agent": self.agent,
            "runs": self.runs,
            **deepcopy(self.extra),
        }


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
            base = self._deep_merge(base, raw)
            return base
        return raw

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        result = deepcopy(base)
        for key, value in override.items():
            if isinstance(result.get(key), dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        return result

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        with open(path) as f:
            return dict(yaml.safe_load(f) or {})

    def _to_config(self, raw: dict[str, Any]) -> Config:
        self._validate(raw)
        extra = {k: v for k, v in raw.items() if k not in Config.__dataclass_fields__}
        return Config(
            project=str(raw.get("project", "")),
            sdk_version=str(raw.get("sdk_version", "1.32.2")),
            seed=int(raw.get("seed", 42)),
            agent=str(raw.get("agent", "baseline")),
            runs=int(raw.get("runs", 200)),
            extra=extra,
        )

    def _validate(self, raw: dict[str, Any]) -> None:
        """Validate the supported experiment contract when present."""
        search = raw.get("search", {})
        if not isinstance(search, dict):
            raise ValueError("search must be a mapping")
        if search.get("manual_coin", False):
            raise ValueError("manual_coin must be false")
        evaluation = raw.get("evaluation", {})
        if evaluation and not isinstance(evaluation, dict):
            raise ValueError("evaluation must be a mapping")
        if isinstance(evaluation, dict) and evaluation.get("both_sides") is False:
            raise ValueError("evaluation.both_sides must be true at gates")


def load_config(name: str, config_dir: str | Path = "configs") -> Config:
    return ConfigLoader(config_dir).load(name)
