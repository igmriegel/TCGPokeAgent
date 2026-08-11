from __future__ import annotations

import ast
import importlib
import io
import json
import os
import subprocess
import tarfile
import tempfile
from collections.abc import Mapping
from contextlib import redirect_stderr, redirect_stdout
from importlib.metadata import PackageNotFoundError, version
from importlib.util import find_spec
from pathlib import Path
from typing import Any, cast

from src.core.exceptions import PreflightError

DEFAULT_SDK_VERSION = "1.32.2"
REQUIRED_PACKAGE_PATHS = ("main.py", "src", "cg/api.py", "cg/libcg.so")
MAX_PACKAGE_BYTES = 197_700_000

__all__ = [
    "DEFAULT_SDK_VERSION",
    "PreflightError",
    "check_agent_output",
    "check_cabt_import",
    "check_deck",
    "check_observation",
    "check_package_layout",
    "check_sdk_version",
    "check_writable",
    "validate_package_archive",
]


def check_sdk_version(expected: str = DEFAULT_SDK_VERSION) -> str:
    """Validate that the installed SDK matches the pinned harness version.

    Args:
        expected: Exact ``kaggle-environments`` version required by the harness.

    Raises:
        PreflightError: If the distribution is absent or has a different version.

    Returns:
        The installed distribution version.
    """
    try:
        installed = version("kaggle-environments")
    except PackageNotFoundError as error:
        raise PreflightError("kaggle-environments not installed") from error

    if installed != expected:
        raise PreflightError(
            f"kaggle-environments version {installed} installed, expected {expected}"
        )
    return installed


def check_cabt_import() -> None:
    """Verify that the pinned SDK exposes the competition adapter.

    Raises:
        PreflightError: If the adapter cannot be imported or lacks ``first_agent``.
    """
    stdout_fd = os.dup(1)
    stderr_fd = os.dup(2)
    try:
        with open(os.devnull, "w", encoding="utf-8") as sink:
            os.dup2(sink.fileno(), 1)
            os.dup2(sink.fileno(), 2)
            with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                cabt = importlib.import_module("kaggle_environments.envs.cabt.cabt")
    except Exception as error:
        raise PreflightError(f"cabt adapter is not importable: {error}") from error
    finally:
        os.dup2(stdout_fd, 1)
        os.dup2(stderr_fd, 2)
        os.close(stdout_fd)
        os.close(stderr_fd)

    if not callable(getattr(cabt, "first_agent", None)):
        raise PreflightError("cabt adapter does not expose callable first_agent")


def check_package_layout(root: str | Path = ".") -> None:
    """Validate files required by the runnable package are present.

    Args:
        root: Repository or extracted package root to inspect.

    Raises:
        PreflightError: If a required package path is missing.
    """
    package_root = Path(root)
    missing = [path for path in REQUIRED_PACKAGE_PATHS if not (package_root / path).exists()]
    if not (
        (package_root / "deck.csv").is_file()
        or (package_root / "src" / "artifacts" / "deck.csv").is_file()
    ):
        missing.append("deck.csv or src/artifacts/deck.csv")
    if missing:
        raise PreflightError(f"package layout missing: {', '.join(missing)}")


def validate_package_archive(archive: str | Path) -> dict[str, Any]:
    """Validate and smoke-test a submission archive in an isolated directory.

    Args:
        archive: Tar-gzip package to inspect.

    Returns:
        Archive size and extracted smoke output.

    Raises:
        PreflightError: If the archive violates the submission contract.
    """
    path = Path(archive)
    if not path.is_file():
        raise PreflightError(f"package archive not found: {path}")
    if path.stat().st_size >= MAX_PACKAGE_BYTES:
        raise PreflightError("package archive exceeds 197.7 MiB")
    try:
        with tarfile.open(path, "r:gz") as package:
            members = package.getmembers()
            names = [member.name.removeprefix("./") for member in members]
            for name in names:
                candidate = Path(name)
                if candidate.is_absolute() or ".." in candidate.parts:
                    raise PreflightError(f"unsafe package path: {name}")
            if "main.py" not in names or "deck.csv" not in names:
                raise PreflightError("package must contain root main.py and deck.csv")
            with tempfile.TemporaryDirectory(prefix="pokemon-agent-validate-") as directory:
                root = Path(directory)
                package.extractall(root, filter="data")
                check_package_layout(root)
                manifest = _validate_package_manifest(root, path.stat().st_size)
                _validate_decision_ledger_contract(root, manifest)
                _check_python_311_syntax(root)
                initial = subprocess.run(
                    [os.fspath(_python_executable()), "main.py"],
                    cwd=root,
                    input='{"select": null}',
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=10,
                )
                if initial.returncode != 0:
                    raise PreflightError(f"isolated package failed: {initial.stderr.strip()}")
                deck = json.loads(initial.stdout)
                if not isinstance(deck, list) or len(deck) != 60:
                    raise PreflightError("isolated package returned an invalid deck")
                loader_result = _run_kaggle_loader_smoke(root)
                ranker_result = _run_ranker_smoke(root, manifest)
                cabt_result = _run_cabt_file_agent_smoke(root)
    except (tarfile.TarError, OSError, json.JSONDecodeError) as error:
        raise PreflightError(f"invalid package archive: {error}") from error
    return {
        "archive": str(path),
        "bytes": path.stat().st_size,
        "deck_cards": 60,
        "entry_point": loader_result["entry_point"],
        "python_target": "3.11",
        "cabt_file_agent": cabt_result,
        "backend": manifest["backend"],
        "ranker_smoke": ranker_result,
    }


def _validate_package_manifest(root: Path, archive_size: int) -> dict[str, Any]:
    manifest_path = root / "package_manifest.json"
    if not manifest_path.is_file():
        return {"backend": "heuristic"}
    try:
        manifest = cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as error:
        raise PreflightError("package manifest is invalid JSON") from error
    backend = manifest.get("backend")
    if backend not in {
        "heuristic",
        "expert_turn_loop",
        "hdi_v1",
        "xgboost_ranker",
        "lightgbm_ranker",
    }:
        raise PreflightError("package manifest declares an unsupported backend")
    required = {
        "backend_version",
        "feature_schema",
        "feature_schema_sha256",
        "dataset_id",
        "split_ids",
        "deck_id",
        "deck_sha256",
        "parameters",
        "metrics",
        "package_size_bytes",
        "package_payload_sha256",
        "latency",
        "extracted_validation",
    }
    missing = required - set(manifest)
    if missing:
        raise PreflightError(f"package manifest fields missing: {', '.join(sorted(missing))}")
    declared_size = manifest.get("package_size_bytes")
    if not isinstance(declared_size, int) or abs(declared_size - archive_size) > 2048:
        raise PreflightError("package manifest size does not match the archive")
    schema_path = root / str(manifest["feature_schema"])
    if not schema_path.is_file() or _sha256_path(schema_path) != manifest["feature_schema_sha256"]:
        raise PreflightError("package feature schema hash mismatch")
    if _sha256_path(root / "deck.csv") != manifest["deck_sha256"]:
        raise PreflightError("package deck hash mismatch")
    if _package_payload_sha256(root) != manifest["package_payload_sha256"]:
        raise PreflightError("package payload hash mismatch")
    if backend in {"heuristic", "expert_turn_loop", "hdi_v1"}:
        return manifest
    model_dir = root / "model"
    model_file = manifest.get("model_file")
    if not isinstance(model_file, str) or not (model_dir / model_file).is_file():
        raise PreflightError("ranker package model is unavailable")
    if _sha256_path(model_dir / model_file) != manifest.get("model_sha256"):
        raise PreflightError("ranker package model hash mismatch")
    required_backend = "xgboost" if backend == "xgboost_ranker" else "lightgbm"
    competing_backend = "lightgbm" if backend == "xgboost_ranker" else "xgboost"
    if not (root / "vendor" / required_backend).is_dir():
        raise PreflightError("ranker package does not contain its declared backend")
    if (root / "vendor" / competing_backend).exists():
        raise PreflightError("ranker package contains the competing backend")
    return manifest


def _validate_decision_ledger_contract(root: Path, manifest: Mapping[str, Any]) -> None:
    """Validate the active audit ledger declared by an official package.

    Args:
        root: Extracted package root.
        manifest: Parsed package manifest.

    Raises:
        PreflightError: If a declared ledger is incomplete or its dictionary is absent.
    """
    parameters = manifest.get("parameters", {})
    if not isinstance(parameters, Mapping):
        raise PreflightError("package parameters must be a mapping")
    ledger = parameters.get("decision_ledger")
    if ledger is None:
        return
    if not isinstance(ledger, Mapping):
        raise PreflightError("decision ledger manifest must be a mapping")
    required = {
        "event": "audit_decision_ledger",
        "schema_version": "decision-ledger-v1",
        "transport": "stderr_stream",
        "encoding": "zlib+base64",
        "integrity": "sha256",
    }
    for key, expected in required.items():
        if ledger.get(key) != expected:
            raise PreflightError(f"decision ledger manifest {key} is invalid")
    dictionary = ledger.get("dictionary")
    if not isinstance(dictionary, str) or not (root / dictionary).is_file():
        raise PreflightError("decision ledger dictionary is missing from the package")
    source = root / "main.py"
    if "def _emit_decision_ledger() -> None:" not in source.read_text(encoding="utf-8"):
        raise PreflightError("package does not contain the active decision ledger emitter")


def _run_ranker_smoke(root: Path, manifest: Mapping[str, Any]) -> str:
    backend = manifest.get("backend", "heuristic")
    if backend in {"heuristic", "expert_turn_loop", "hdi_v1"}:
        return "not-applicable"
    smoke = """
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(root))
import main

deck = main.agent_policy({"select": None})
observation = {
    "current": {
        "turn": 1,
        "turnActionCount": 0,
        "yourIndex": 0,
        "firstPlayer": 0,
        "players": [
            {"deckCount": 53, "prize": [None] * 6, "hand": [], "bench": []},
            {"deckCount": 53, "prize": [None] * 6, "handCount": 0, "bench": []},
        ],
    },
    "select": {
        "type": 9,
        "context": 41,
        "minCount": 1,
        "maxCount": 1,
        "option": [{"type": 1}, {"type": 2}],
    },
}
action = main.agent_policy(observation)
decision = main._agent.last_decision
model_used = decision.model_backend == sys.argv[2] and not decision.fallback_used

class Broken:
    def predict(self, values):
        raise RuntimeError("forced package fallback")

main._agent._ranker._predictor = Broken()
fallback_action = main.agent_policy(observation)
fallback = main._agent.last_decision
print(json.dumps({
    "deck": len(deck),
    "action": action,
    "model_used": model_used,
    "duration_ms": decision.duration_ms,
    "fallback_legal": fallback_action in ([0], [1]),
    "fallback_used": fallback.fallback_used,
    "fallback_count": main._agent.fallback_count,
}))
"""
    completed = subprocess.run(
        [
            os.fspath(_python_executable()),
            "-S",
            "-c",
            smoke,
            os.fspath(root),
            str(backend),
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip()
        raise PreflightError(f"ranker package smoke failed: {details}")
    try:
        result = cast(dict[str, Any], json.loads(completed.stdout))
    except json.JSONDecodeError as error:
        raise PreflightError("ranker package smoke returned invalid JSON") from error
    if not result.get("model_used"):
        raise PreflightError("ranker package did not execute an in-game model decision")
    if not result.get("fallback_used") or result.get("fallback_count") != 1:
        raise PreflightError("ranker package did not exercise heuristic inference fallback")
    if not result.get("fallback_legal"):
        raise PreflightError("ranker package fallback returned an invalid decision")
    if float(result.get("duration_ms", float("inf"))) > 100.0:
        raise PreflightError("ranker package decision exceeded the 100ms budget")
    return "passed"


def _check_python_311_syntax(root: Path) -> None:
    """Parse every packaged module using the Python 3.11 grammar."""
    for source_path in sorted(root.rglob("*.py")):
        if "vendor" in source_path.relative_to(root).parts:
            continue
        try:
            ast.parse(
                source_path.read_text(encoding="utf-8-sig"),
                filename=os.fspath(source_path),
                feature_version=(3, 11),
            )
        except SyntaxError as error:
            relative = source_path.relative_to(root)
            raise PreflightError(
                f"package is not Python 3.11 compatible: {relative}: {error}"
            ) from error


def _sha256_path(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _package_payload_sha256(root: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.name == "package_manifest.json" or "__pycache__" in path.parts:
            continue
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _run_kaggle_loader_smoke(root: Path) -> dict[str, Any]:
    """Run the package without site packages and select its last callable."""
    loader = """
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
sys.path.append(str(root))
source = root / "main.py"
environment = {}
exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"), environment)
entry_point = [value for value in environment.values() if callable(value)][-1]
action = entry_point({"select": None})
print(json.dumps({"entry_point": entry_point.__name__, "action": action}))
"""
    completed = subprocess.run(
        [os.fspath(_python_executable()), "-S", "-c", loader, os.fspath(root)],
        cwd=root.parent,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip()
        raise PreflightError(f"Kaggle loader smoke failed without site packages: {details}")
    try:
        result = cast(dict[str, Any], json.loads(completed.stdout))
    except json.JSONDecodeError as error:
        raise PreflightError("Kaggle loader smoke returned invalid JSON") from error
    if not isinstance(result, dict):
        raise PreflightError("Kaggle loader smoke returned a non-object result")
    if result.get("entry_point") != "agent":
        raise PreflightError(
            f"Kaggle loader selected {result.get('entry_point')!r}, expected 'agent'"
        )
    action = result.get("action")
    if not isinstance(action, list) or len(action) != 60:
        raise PreflightError("Kaggle loader smoke returned an invalid deck")
    return result


def _run_cabt_file_agent_smoke(root: Path) -> str:
    """Run one CABT episode with both agents loaded from the extracted file."""
    if find_spec("kaggle_environments") is None:
        return "sdk-unavailable"

    smoke = """
import json
import pathlib
import sys

from kaggle_environments import make

agent_path = str(pathlib.Path(sys.argv[1]) / "main.py")
environment = make("cabt", debug=False)
environment.run([agent_path, agent_path])
statuses = [getattr(player, "status", None) for player in environment.state]
errors = [
    log.get("stderr", "")
    for turn in environment.logs
    for log in turn
    if log.get("stderr")
]
print("CABT_FILE_AGENT_RESULT=" + json.dumps({"statuses": statuses, "errors": errors}))
"""
    completed = subprocess.run(
        [os.fspath(_python_executable()), "-c", smoke, os.fspath(root)],
        cwd=root.parent,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    marker = "CABT_FILE_AGENT_RESULT="
    result_line = next(
        (line for line in reversed(completed.stdout.splitlines()) if line.startswith(marker)),
        "",
    )
    if completed.returncode != 0 or not result_line:
        details = completed.stderr.strip() or completed.stdout.strip()
        raise PreflightError(f"CABT file-agent smoke failed: {details}")
    try:
        result = cast(dict[str, Any], json.loads(result_line.removeprefix(marker)))
    except json.JSONDecodeError as error:
        raise PreflightError("CABT file-agent smoke returned invalid JSON") from error
    statuses = result.get("statuses")
    if statuses != ["DONE", "DONE"]:
        raise PreflightError(
            f"CABT file-agent smoke ended with statuses {statuses}: {result.get('errors')}"
        )
    return "passed"


def _python_executable() -> str:
    """Return the interpreter running the validation command."""
    import sys

    return sys.executable


def check_deck(deck_path: str | Path) -> list[list[str]]:
    """Validate and load a 60-card deck file.

    Args:
        deck_path: Path to a newline-delimited CSV deck.

    Returns:
        The non-empty CSV rows in deterministic file order.

    Raises:
        PreflightError: If the file is missing, malformed, or not 60 cards long.
    """
    import csv

    path = Path(deck_path)
    if not path.exists():
        raise PreflightError(f"deck not found: {path}")

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        cards = list(reader)

    if len(cards) != 60:
        raise PreflightError(f"deck has {len(cards)} cards, expected 60")
    if any(len(row) != 1 or not row[0].strip() for row in cards):
        raise PreflightError("deck must contain one non-empty card identifier per row")
    try:
        if any(int(row[0]) <= 0 for row in cards):
            raise PreflightError("deck card identifiers must be positive integers")
    except ValueError as error:
        raise PreflightError("deck card identifiers must be integers") from error

    return cards


def check_agent_output(output: Any) -> None:
    """Validate the public agent output shape.

    Args:
        output: Value returned by an agent policy.

    Raises:
        PreflightError: If the value is not a list of integers.
    """
    if not isinstance(output, list):
        raise PreflightError(f"agent output is {type(output).__name__}, expected list[int]")
    for item in output:
        if isinstance(item, bool) or not isinstance(item, int):
            raise PreflightError(f"agent output contains {type(item).__name__}, expected int")


def check_writable(directory: str | Path) -> None:
    """Verify that an existing directory accepts a temporary file.

    Args:
        directory: Existing directory to probe.

    Raises:
        PreflightError: If the path is absent, not a directory, or not writable.
    """
    path = Path(directory)
    if not path.is_dir():
        raise PreflightError(f"writable directory not found: {path}")
    probe = path / ".write_test"
    try:
        probe.touch()
        probe.unlink()
    except OSError as e:
        raise PreflightError(f"directory not writable: {path}") from e


def check_observation(observation: Any) -> None:
    """Validate the outer shape of an SDK observation.

    Args:
        observation: Raw observation supplied to the agent.

    Raises:
        PreflightError: If observation sections have invalid container types.
    """
    if not isinstance(observation, Mapping):
        raise PreflightError("observation must be a mapping")

    for field in ("current", "select", "search_begin_input"):
        value = observation.get(field)
        if value is not None and not isinstance(value, Mapping):
            raise PreflightError(f"observation field {field!r} must be a mapping or null")

    select = observation.get("select")
    if select is None:
        return
    options = select.get("option")
    if not isinstance(options, list) or any(not isinstance(option, Mapping) for option in options):
        raise PreflightError("observation select.option must be a list of mappings")


def check_legal_selection(observation: Any, output: Any) -> None:
    """Validate selection indices against the active SDK decision.

    Args:
        observation: Raw SDK observation containing the current selection.
        output: Candidate option indices returned by the agent.

    Raises:
        PreflightError: If the output violates the decision bounds.
    """
    check_agent_output(output)
    if not isinstance(observation, Mapping):
        raise PreflightError("observation must be a mapping")
    select = observation.get("select")
    if select is None:
        return
    if not isinstance(select, Mapping):
        raise PreflightError("observation field 'select' must be a mapping or null")
    options = select.get("option")
    if not isinstance(options, list):
        raise PreflightError("observation select.option must be a list")
    if len(output) != len(set(output)):
        raise PreflightError("agent output contains duplicate option indices")
    if any(index < 0 or index >= len(options) for index in output):
        raise PreflightError("agent output contains an out-of-range option index")

    min_count = int(select.get("minCount", 0) or 0)
    max_count = int(select.get("maxCount", 0) or 0)
    if not min_count <= len(output) <= max_count:
        raise PreflightError(
            f"agent output has {len(output)} indices, expected between {min_count} and {max_count}"
        )

    energy_required = int(select.get("remainEnergyCost", 0) or 0)
    damage_required = int(select.get("remainDamageCounter", 0) or 0)
    selected_options = [options[index] for index in output]
    for required, field, label in (
        (energy_required, "count", "energy"),
        (damage_required, "count", "damage"),
    ):
        if required <= 0:
            continue
        counts = [option.get(field, 1) for option in selected_options]
        if any(isinstance(count, bool) or not isinstance(count, int) for count in counts):
            raise PreflightError(f"selected option {field} values must be integers")
        total = sum(counts)
        if total < required:
            raise PreflightError(
                f"agent output provides {total} {label} count, expected at least {required}"
            )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate the agent package or repository.")
    parser.add_argument("--package", type=Path)
    args = parser.parse_args()
    if args.package:
        print(validate_package_archive(args.package))
    else:
        check_sdk_version()
        check_cabt_import()
        check_package_layout()
        check_deck(Path("src/artifacts/deck.csv"))
        print("Preflight: PASS")
