"""Execute the downloaded Kaggle notebook in an isolated local experiment.

This runner preserves the notebook logic while adapting Kaggle-specific paths
and notebook assets to the local workspace so the experiment can be reproduced
outside Kaggle.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = EXPERIMENT_ROOT.parents[1]
NOTEBOOK_DIR = EXPERIMENT_ROOT / "notebook"
NOTEBOOK_PATH = NOTEBOOK_DIR / "a-sample-rule-based-agent-dragapult-ex-deck.ipynb"
RUN_DIR = EXPERIMENT_ROOT / "run"
SUBMISSION_DIR = EXPERIMENT_ROOT / "submission"
DECK_PATH = NOTEBOOK_DIR / "deck.csv"
RUNTIME_DECK_PATH = RUN_DIR / "deck.csv"
CG_SOURCE_DIR = PROJECT_ROOT / "cg"
CG_RUNTIME_DIR = RUN_DIR / "cg"


def _load_notebook(path: Path) -> dict[str, Any]:
    """Load a notebook JSON document.

    Args:
        path: Path to the notebook file.

    Returns:
        The parsed notebook document.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def _patch_cell_source(source: str) -> str:
    """Adapt Kaggle-specific code cells to the local experiment layout."""
    patched = source.replace(
        "glob.glob('/kaggle/input/**/cg-lib/cg', recursive=True)[0]",
        "glob.glob('cg', recursive=True)[0]",
    )
    patched = patched.replace(
        "glob.glob('/kaggle/input/**/dragapult-ex-deck/deck.csv', recursive=True)[0]",
        "glob.glob('deck.csv', recursive=True)[0]",
    )
    return patched


def _copy_runtime_assets() -> None:
    """Copy the deck and helper package into the local runtime directory."""
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DECK_PATH, RUNTIME_DECK_PATH)
    if CG_RUNTIME_DIR.exists():
        shutil.rmtree(CG_RUNTIME_DIR)
    shutil.copytree(CG_SOURCE_DIR, CG_RUNTIME_DIR)


def _write_sha256(path: Path) -> Path:
    """Write a SHA-256 sidecar for a file."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    sha_path = path.with_suffix(path.suffix + ".sha256")
    sha_path.write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    return sha_path


def _mirror_submission_artifacts() -> None:
    """Copy the generated submission archive to the experiment submission folder."""
    run_archive = RUN_DIR / "submission.tar.gz"
    if not run_archive.exists():
        return
    submission_archive = SUBMISSION_DIR / "submission.tar.gz"
    shutil.copy2(run_archive, submission_archive)
    _write_sha256(run_archive)
    _write_sha256(submission_archive)


def _execute_cell(source: str, namespace: dict[str, Any]) -> None:
    """Execute a single notebook code cell."""
    stripped = source.lstrip()
    if stripped.startswith("%%writefile main.py"):
        lines = source.splitlines()
        body = "\n".join(lines[1:]) + "\n"
        (RUN_DIR / "main.py").write_text(body, encoding="utf-8")
        code = _patch_cell_source(body)
    else:
        code = _patch_cell_source(source)
    exec(compile(code, "<notebook-cell>", "exec"), namespace)


def main() -> int:
    """Execute the notebook and build the submission archive locally."""
    _copy_runtime_assets()
    notebook = _load_notebook(NOTEBOOK_PATH)
    namespace: dict[str, Any] = {
        "__name__": "__main__",
        "__file__": str(NOTEBOOK_PATH),
    }

    previous_cwd = Path.cwd()
    previous_sys_path = sys.path[:]
    previous_env = os.environ.copy()
    os.chdir(RUN_DIR)
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        sys.path.insert(0, str(RUN_DIR))
        os.environ["PWD"] = str(RUN_DIR)
        for cell in notebook["cells"]:
            if cell.get("cell_type") != "code":
                continue
            source = cell.get("source", "")
            if isinstance(source, list):
                source = "".join(source)
            _execute_cell(str(source), namespace)
    finally:
        os.chdir(previous_cwd)
        sys.path[:] = previous_sys_path
        os.environ.clear()
        os.environ.update(previous_env)

    _mirror_submission_artifacts()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
