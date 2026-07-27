from importlib.metadata import PackageNotFoundError

import pytest

from src.eval import validation


def test_check_sdk_version_accepts_expected_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validation, "version", lambda _: "1.32.2")

    validation.check_sdk_version()


def test_check_sdk_version_rejects_missing_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_version(_: str) -> str:
        raise PackageNotFoundError

    monkeypatch.setattr(validation, "version", missing_version)

    with pytest.raises(validation.PreflightError, match="not installed"):
        validation.check_sdk_version()


def test_check_sdk_version_rejects_mismatched_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validation, "version", lambda _: "1.31.0")

    with pytest.raises(
        validation.PreflightError,
        match=r"version 1\.31\.0 installed, expected 1\.32\.2",
    ):
        validation.check_sdk_version()
