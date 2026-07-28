from __future__ import annotations

import json
import subprocess
import sys
import tarfile
from pathlib import Path


def test_extracted_package_runs_initial_deck(tmp_path) -> None:
    root = Path(__file__).parents[1]
    archive = tmp_path / "submission.tar.gz"
    extracted = tmp_path / "extracted"
    extracted.mkdir()

    subprocess.run(
        [str(root / "scripts" / "build_package.sh"), str(archive)],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    with tarfile.open(archive) as package:
        package.extractall(extracted)

    completed = subprocess.run(
        [sys.executable, "main.py"],
        cwd=extracted,
        input='{"select": null}',
        text=True,
        capture_output=True,
        check=True,
    )

    assert len(json.loads(completed.stdout)) == 60
    assert completed.stderr
