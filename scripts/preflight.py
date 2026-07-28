"""Run deterministic environment and package checks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.config.loader import ConfigLoader
from src.core.exceptions import PreflightError
from src.eval.validation import (
    check_cabt_import,
    check_deck,
    check_package_layout,
    check_sdk_version,
    check_writable,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/default.yaml", help="Config file to validate")
    parser.add_argument("--root", default=".", help="Repository or package root")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run preflight checks and print a concise report.

    Args:
        argv: Optional command-line arguments without the executable name.

    Returns:
        Process exit code: zero on success, two for a failed preflight.
    """
    args = _build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    try:
        config_name = args.config
        if not Path(config_name).is_absolute() and config_name.startswith("configs/"):
            config_name = config_name.removeprefix("configs/")
        config = ConfigLoader(root / "configs").load(config_name)
        installed = check_sdk_version(config.sdk_version)
        check_cabt_import()
        check_package_layout(root)
        deck_path = root / "src" / "artifacts" / "deck.csv"
        cards = check_deck(deck_path)
        check_writable(root / "reports")
    except (PreflightError, FileNotFoundError, ValueError) as error:
        print(f"PREFLIGHT FAILED: {error}", file=sys.stderr)
        return 2

    print(f"SDK: kaggle-environments=={installed}")
    print(f"Deck: {deck_path} ({len(cards)} cards)")
    print(f"Package root: {root}")
    print("Preflight: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
