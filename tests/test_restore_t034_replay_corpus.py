"""Tests for immutable replay corpus restoration helpers."""

from __future__ import annotations

import pytest

from scripts.restore_t034_replay_corpus import _episode_id


def test_episode_id_preserves_frozen_kaggle_name() -> None:
    """The restore command uses the exact episode encoded in the audit manifest."""
    assert _episode_id("episode-90813277-replay.json") == "90813277"


def test_episode_id_rejects_unfrozen_name() -> None:
    """Unexpected filenames cannot be sent to the Kaggle replay endpoint."""
    with pytest.raises(ValueError, match="unexpected replay filename"):
        _episode_id("90813277.json")
