"""Execute the downloaded Kaggle notebook in an isolated local experiment.

This runner preserves the notebook logic while adapting the Kaggle-specific
paths and notebook magics to the local workspace so the experiment can be
reproduced outside Kaggle.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = EXPERIMENT_ROOT.parents[1]
NOTEBOOK_PATH = (
    EXPERIMENT_ROOT / "notebook" / "a-sample-rule-based-agent-mega-lucario-ex-deck.ipynb"
)
RUN_DIR = EXPERIMENT_ROOT / "run"


def _load_notebook(path: Path) -> dict[str, Any]:
    """Load a notebook JSON document."""
    return json.loads(path.read_text(encoding="utf-8"))


def _patch_cell_source(source: str) -> str:
    """Adapt Kaggle-specific code cells to the local experiment layout."""
    patched = source.replace(
        "glob.glob('/kaggle/input/**/cg-lib/cg', recursive=True)[0]",
        "glob.glob('cg', recursive=True)[0]",
    )
    patched = patched.replace(
        "glob.glob('/kaggle/input/datasets/**/deck.csv', recursive=True)[0]",
        "glob.glob('deck.csv', recursive=True)[0]",
    )
    return patched


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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
