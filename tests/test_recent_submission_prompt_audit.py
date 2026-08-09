"""Tests for the isolated recent-submission prompt audit."""

from __future__ import annotations

from scripts.audit_recent_submission_prompts import _selected_types


def test_selected_types_preserves_option_order_and_invalid_indices() -> None:
    """The diagnostic record maps selected simulator indices without renumbering."""
    observation = {"select": {"option": [{"type": 8}, {"type": 14}]}}

    assert _selected_types(observation, [1, 0, 3]) == [14, 8, None]
