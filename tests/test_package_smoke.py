from __future__ import annotations

import json
import re
import subprocess
import sys
import tarfile
import zlib
from base64 import b64decode
from dataclasses import fields
from pathlib import Path

from src.agents.honchkrow_porygon import MatchTacticalLedger, TurnTacticalLedger
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
    assert manifest["parameters"]["canonical_policy_variant"] == "expert_turn_loop"
    ledger = manifest["parameters"]["decision_ledger"]
    assert ledger["event"] == "audit_decision_ledger"
    assert ledger["transport"] == "stderr_logger"
    assert ledger["dictionary"] == "src/artifacts/decision_ledger_dictionary.json"


def test_official_package_emits_complete_compressed_decision_ledger(tmp_path) -> None:
    """The submission callback keeps stdout clean and exposes the ledger in stderr."""
    root = Path(__file__).parents[1]
    archive = tmp_path / "honchkrow_expert_turn_loop.tar.gz"
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    fixture = root / "tests" / "fixtures" / "cabt_main_turn.json"

    subprocess.run(
        [str(root / "scripts" / "build_honchkrow_porygon_package.sh"), str(archive)],
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
        input=fixture.read_text(encoding="utf-8"),
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == [0]
    match = re.search(r"audit_decision_ledger=(\{.*\})", completed.stderr)
    assert match is not None
    envelope = json.loads(match.group(1))
    compact = zlib.decompress(b64decode(envelope["payload"])).decode("utf-8")
    assert envelope["encoding"] == "zlib+base64"
    assert len(match.group(1)) < 9_000
    assert {"s", "t", "r", "x", "tl", "ml"} <= json.loads(compact).keys()

    log_path = tmp_path / "kaggle-stderr.log"
    decoded_path = tmp_path / "decoded.jsonl"
    log_path.write_text(completed.stderr, encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "decode_kaggle_decision_ledger.py"),
            str(log_path),
            "--output",
            str(decoded_path),
        ],
        cwd=root,
        check=True,
    )
    decoded = json.loads(decoded_path.read_text(encoding="utf-8"))
    expected_fields = {"selection", "trace", "ranked", "features", "turn_ledger", "match_ledger"}
    assert expected_fields <= decoded.keys()


def test_decision_ledger_dictionary_describes_every_tactical_field() -> None:
    """The versioned dictionary cannot drift from the public tactical ledgers."""
    root = Path(__file__).parents[1]
    dictionary_path = root / "src" / "artifacts" / "decision_ledger_dictionary.json"
    dictionary = json.loads(dictionary_path.read_text(encoding="utf-8"))

    turn_fields = {field.name for field in fields(TurnTacticalLedger)}
    match_fields = {field.name for field in fields(MatchTacticalLedger)}

    assert set(dictionary["keys"]) <= dictionary["field_descriptions"].keys()
    assert turn_fields <= dictionary["turn_ledger_fields"].keys()
    assert match_fields <= dictionary["match_ledger_fields"].keys()


def test_stdout_debug_package_matches_the_official_auditable_package(tmp_path) -> None:
    root = Path(__file__).parents[1]
    archive = tmp_path / "honchkrow_porygon_stdout_debug.tar.gz"

    subprocess.run(
        ["bash", str(root / "scripts" / "build_kaggle_stdout_debug_package.sh"), str(archive)],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    with tarfile.open(archive) as package:
        main_file = package.extractfile("main.py")
        manifest_file = package.extractfile("package_manifest.json")
        assert main_file is not None
        assert manifest_file is not None
        main_source = main_file.read().decode("utf-8")
        manifest = json.load(manifest_file)

    assert "def _emit_decision_ledger() -> None:" in main_source
    assert "audit_decision_ledger" in main_source
    assert '"turn_ledger": _public_ledger' in main_source
    assert '"features": features' in main_source
    assert manifest["parameters"]["decision_ledger"]["schema_version"] == "decision-ledger-v1"
