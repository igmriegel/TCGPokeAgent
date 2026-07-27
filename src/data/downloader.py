from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, cast

KAGGLE_DATA_DIR = Path("data/raw/kaggle")
MANIFEST_PATH = KAGGLE_DATA_DIR / "manifest.json"

COMPETITIONS = {
    "simulation": "pokemon-tcg-ai-battle",
    "strategy": "pokemon-tcg-ai-battle-challenge-strategy",
}

SAMPLE_FILE = "EN_Card_Data.csv"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        print("manifest.json not found — run from project root", file=sys.stderr)
        sys.exit(1)
    return cast(dict[str, Any], json.loads(MANIFEST_PATH.read_text()))


def check_data(output_dir: str | Path = KAGGLE_DATA_DIR) -> dict[str, bool]:
    output_dir = Path(output_dir)
    manifest = _load_manifest()

    simulation_ok = True
    strategy_ok = True

    for entry in manifest.get("files", []):
        comp = entry["competition"]
        rel_path = entry["path"]
        expected_sha = entry["sha256"]
        file_path = output_dir / rel_path

        if not file_path.exists():
            if comp == "simulation":
                simulation_ok = False
            else:
                strategy_ok = False
            continue

        actual_sha = _sha256(file_path)
        if actual_sha != expected_sha:
            print(f"  SHA-256 mismatch: {rel_path}", file=sys.stderr)
            if comp == "simulation":
                simulation_ok = False
            else:
                strategy_ok = False

    total_ok = simulation_ok and strategy_ok
    return {
        "simulation": simulation_ok,
        "strategy": strategy_ok,
        "total_ok": total_ok,
    }


def _download_competition(
    comp_alias: str,
    output_dir: Path,
    manifest: dict[str, Any],
) -> bool:
    comp_name = COMPETITIONS[comp_alias]
    comp_dir = output_dir / comp_alias
    comp_dir.mkdir(parents=True, exist_ok=True)

    try:
        import kagglehub
    except ImportError:
        print("kagglehub not installed. Run: uv sync", file=sys.stderr)
        return False

    print(f"  Downloading {comp_name} ...")
    try:
        cache_path = kagglehub.competition_download(comp_name)
    except Exception as e:
        print(f"  Download failed: {e}", file=sys.stderr)
        print("  Ensure ~/.kaggle/kaggle.json is set up correctly", file=sys.stderr)
        return False

    src_dir = Path(cache_path)
    if not src_dir.is_dir():
        print(f"  Unexpected cache path: {cache_path}", file=sys.stderr)
        return False

    for entry in manifest.get("files", []):
        if entry["competition"] != comp_alias:
            continue
        remote_name = entry["remote_name"]
        dest = comp_dir / remote_name
        src = src_dir / remote_name
        if not src.exists():
            print(f"  File not found in download: {remote_name}", file=sys.stderr)
            return False
        if not dest.exists() or _sha256(src) != entry["sha256"]:
            shutil.copy2(src, dest)
            print(f"    {remote_name}")

    for entry in manifest.get("files", []):
        if entry["competition"] != comp_alias:
            continue
        dest = comp_dir / entry["remote_name"]
        if not dest.exists():
            print(f"  Missing after copy: {entry['remote_name']}", file=sys.stderr)
            return False
        actual_sha = _sha256(dest)
        if actual_sha != entry["sha256"]:
            print(f"  SHA-256 mismatch: {entry['remote_name']}", file=sys.stderr)
            return False

    print(f"  {comp_alias} OK")
    return True


def download_data(
    output_dir: str | Path = KAGGLE_DATA_DIR,
    competition: str = "all",
) -> bool:
    output_dir = Path(output_dir)
    manifest = _load_manifest()

    status = check_data(output_dir)

    aliases = list(COMPETITIONS)
    if competition != "all":
        if competition not in COMPETITIONS:
            print(f"Unknown competition: {competition}", file=sys.stderr)
            print(f"Valid: {', '.join(COMPETITIONS)}", file=sys.stderr)
            return False
        aliases = [competition]

    all_ok = True
    for alias in aliases:
        if status[alias]:
            print(f"  {alias} data already present and valid — skipping")
            continue
        ok = _download_competition(alias, output_dir, manifest)
        if not ok:
            all_ok = False

    return all_ok


def _run_cli() -> None:
    parser = argparse.ArgumentParser(description="Download Kaggle datasets for Pokemon TCG Engine")
    parser.add_argument(
        "--output",
        default=KAGGLE_DATA_DIR,
        help=f"Output directory (default: {KAGGLE_DATA_DIR})",
    )
    parser.add_argument(
        "--competition",
        choices=list(COMPETITIONS) + ["all"],
        default="all",
        help="Which competition to download (default: all)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check if data exists, do not download",
    )
    args = parser.parse_args()

    if args.check:
        status = check_data(args.output)
        for comp, ok in status.items():
            if comp == "total_ok":
                continue
            print(f"  {comp}: {'OK' if ok else 'MISSING or CORRUPT'}")
        sys.exit(0 if status["total_ok"] else 1)

    success = download_data(args.output, args.competition)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    _run_cli()
