from __future__ import annotations

import json
import subprocess
import sys
import tarfile
from pathlib import Path

from src.eval.validation import validate_package_archive


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

    validation = validate_package_archive(archive)

    assert validation["entry_point"] == "agent"
    assert validation["python_target"] == "3.11"
    assert validation["cabt_file_agent"] == "passed"
