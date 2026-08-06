from pathlib import Path

import pytest

from scripts.submit_simulation import (
    COMPETITION,
    PROJECT_ROOT,
    _confirmed,
    _package_command,
    _parser,
    _sha256,
    _submission_command,
    _submission_env,
)


def test_confirmation_requires_explicit_yes() -> None:
    assert _confirmed("y")
    assert _confirmed("YES")
    assert not _confirmed("")
    assert not _confirmed("no")


def test_submission_command_uses_official_cli_shape(tmp_path: Path) -> None:
    archive = tmp_path / "submission.tar.gz"

    command = _submission_command("/usr/bin/kaggle", archive, "first simulation")

    assert command == [
        "/usr/bin/kaggle",
        "competitions",
        "submit",
        COMPETITION,
        "-f",
        str(archive),
        "-m",
        "first simulation",
    ]


def test_sha256_reads_archive(tmp_path: Path) -> None:
    archive = tmp_path / "submission.tar.gz"
    archive.write_bytes(b"pokemon")

    assert _sha256(archive) == "eaa2bded32cc585d3f37c5319abe8890ad28a697ed66d5823f10536cc9c0fdb9"


def test_hdi_mode_is_available_to_guarded_submission_pipeline() -> None:
    args = _parser().parse_args(["--agent-mode", "hdi_v1", "--dry-run"])

    assert args.agent_mode == "hdi_v1"


def test_dedicated_package_kind_uses_dedicated_builder(tmp_path: Path) -> None:
    archive = tmp_path / "honchkrow.tar.gz"
    assert _package_command("honchkrow_porygon", archive, "heuristic") == [
        "scripts/build_honchkrow_porygon_package.sh",
        str(archive),
    ]


def test_submission_env_ignores_repo_root_kaggle_config_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KAGGLE_CONFIG_DIR", str(PROJECT_ROOT))

    env = _submission_env()

    assert "KAGGLE_CONFIG_DIR" not in env


def test_submission_env_keeps_non_repo_kaggle_config_dir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    custom_config_dir = tmp_path / "kaggle-config"
    monkeypatch.setenv("KAGGLE_CONFIG_DIR", str(custom_config_dir))

    env = _submission_env()

    assert env["KAGGLE_CONFIG_DIR"] == str(custom_config_dir)
