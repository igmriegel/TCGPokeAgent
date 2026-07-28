from __future__ import annotations

from pathlib import Path

from scripts.preflight import main


def test_preflight_succeeds_for_repository() -> None:
    root = Path(__file__).parents[1]

    assert main(["--root", str(root)]) == 0


def test_preflight_rejects_missing_root(tmp_path) -> None:
    assert main(["--root", str(tmp_path)]) == 2
