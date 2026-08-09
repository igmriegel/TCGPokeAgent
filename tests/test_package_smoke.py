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


def test_extracted_hdi_package_declares_and_runs_backend(tmp_path) -> None:
    root = Path(__file__).parents[1]
    archive = tmp_path / "submission_hdi_v1.tar.gz"

    subprocess.run(
        [str(root / "scripts" / "build_package.sh"), str(archive), "hdi_v1"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    validation = validate_package_archive(archive)
    with tarfile.open(archive) as package:
        names = {member.name.removeprefix("./") for member in package.getmembers()}
        manifest_file = package.extractfile("package_manifest.json")
        assert manifest_file is not None
        manifest = json.load(manifest_file)

    assert validation["backend"] == "hdi_v1"
    assert "src/agents/hdi.py" in names
    assert manifest["backend_version"] == "hdi-v1"
    assert manifest["deck_id"] == "mega_abomasnow_kyogre"
    assert len(manifest["package_payload_sha256"]) == 64


def test_extracted_expert_turn_loop_package_uses_revised_policy(tmp_path) -> None:
    root = Path(__file__).parents[1]
    archive = tmp_path / "submission_expert_turn_loop.tar.gz"

    subprocess.run(
        [str(root / "scripts" / "build_package.sh"), str(archive), "expert_turn_loop"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    validation = validate_package_archive(archive)
    with tarfile.open(archive) as package:
        names = {member.name.removeprefix("./") for member in package.getmembers()}
        manifest_file = package.extractfile("package_manifest.json")
        assert manifest_file is not None
        manifest = json.load(manifest_file)

    assert validation["backend"] == "expert_turn_loop"
    assert validation["cabt_file_agent"] == "passed"
    assert manifest["deck_id"] == "honchkrow_porygon"
    assert "src/agents/honchkrow_porygon.py" in names
    assert "src/artifacts/deck_profile_honchkrow_porygon.json" in names
    assert archive.with_name(archive.name + ".sha256").is_file()


def test_dedicated_expert_package_manifest_identifies_backend(tmp_path) -> None:
    root = Path(__file__).parents[1]
    archive = tmp_path / "honchkrow_expert_turn_loop.tar.gz"

    subprocess.run(
        [str(root / "scripts" / "build_honchkrow_porygon_package.sh"), str(archive)],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    with tarfile.open(archive) as package:
        manifest_file = package.extractfile("package_manifest.json")
        assert manifest_file is not None
        manifest = json.load(manifest_file)

    assert manifest["backend"] == "expert_turn_loop"
    assert manifest["backend_version"] == "expert-turn-loop"
    assert manifest["policy_variant"] == "expert_turn_loop"
