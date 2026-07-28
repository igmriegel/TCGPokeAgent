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


def test_check_deck_rejects_wrong_card_count(tmp_path) -> None:
    deck_path = tmp_path / "deck.csv"
    deck_path.write_text("1\n" * 59, encoding="utf-8")

    with pytest.raises(validation.PreflightError, match="has 59 cards, expected 60"):
        validation.check_deck(deck_path)


def test_check_deck_rejects_malformed_row(tmp_path) -> None:
    deck_path = tmp_path / "deck.csv"
    deck_path.write_text("1\n" * 59 + "1,extra\n", encoding="utf-8")

    with pytest.raises(validation.PreflightError, match="one non-empty card identifier"):
        validation.check_deck(deck_path)


def test_check_observation_rejects_malformed_outer_shape() -> None:
    with pytest.raises(validation.PreflightError, match="must be a mapping"):
        validation.check_observation([])


def test_check_observation_rejects_malformed_options() -> None:
    observation = {"select": {"option": ["not an option"]}}

    with pytest.raises(validation.PreflightError, match="select.option"):
        validation.check_observation(observation)


def test_check_package_layout_rejects_missing_path(tmp_path) -> None:
    with pytest.raises(validation.PreflightError, match="package layout missing"):
        validation.check_package_layout(tmp_path)


def test_check_writable_rejects_missing_directory(tmp_path) -> None:
    with pytest.raises(validation.PreflightError, match="directory not found"):
        validation.check_writable(tmp_path / "reports")
