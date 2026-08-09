"""Tests for terminal and Mega Abomasnow evaluation telemetry."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from scripts.run_honchkrow_porygon_eval import (
    _is_partial_mega_abomasnow_attack,
    _load_stream_checkpoint,
    _selected_card_ids,
    _terminal_reason,
    _terminal_snapshot,
)
from src.agents.honchkrow_porygon import MEGA_ABOMASNOW_EX, R_COMMAND, ROCKET_FEATHERS


def test_damaged_mega_exact_lethal_is_not_counted_as_partial() -> None:
    """Rocket Feathers must use current target HP rather than printed HP."""
    target = {"id": MEGA_ABOMASNOW_EX, "hp": 110}

    assert not _is_partial_mega_abomasnow_attack(target, [ROCKET_FEATHERS], 2, 0)


def test_underfunded_mega_attack_remains_partial() -> None:
    """An attack below the visible target HP remains an actionable regression."""
    target = {"id": MEGA_ABOMASNOW_EX, "hp": 350}

    assert _is_partial_mega_abomasnow_attack(target, [ROCKET_FEATHERS], 4, 0)
    assert _is_partial_mega_abomasnow_attack(target, [R_COMMAND], 0, 17)


def test_selected_card_ids_resolve_main_phase_hand_indices() -> None:
    """Low-deck telemetry attributes a selected play to its public hand card."""
    options = [{"type": 7, "index": 1}, {"type": 14}]
    selected = [options[0], options[1]]

    assert _selected_card_ids(selected, [{"id": 1216}, {"id": 1152}]) == [1152, 0]


def test_stream_checkpoint_requires_the_requested_contiguous_seed_order(tmp_path) -> None:
    """A resumable stream cannot silently mix results from another run."""
    trace_path = tmp_path / "trace.jsonl"
    trace_path.write_text(
        "\n".join(
            [
                json.dumps({"match_id": "honchkrow_99_0"}),
                json.dumps({"match_id": "honchkrow_99_1"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert _load_stream_checkpoint(trace_path, 99, 4) == [
        {"match_id": "honchkrow_99_0"},
        {"match_id": "honchkrow_99_1"},
    ]
    with pytest.raises(ValueError, match="seed order"):
        _load_stream_checkpoint(trace_path, 100, 4)


def test_terminal_snapshot_prefers_visualizer_post_resolution_state() -> None:
    """The visualizer retains the result state omitted from the last observation."""
    pre_terminal = {"result": -1, "players": [{}, {}]}
    terminal = {"result": 1, "players": [{}, {}]}
    environment = SimpleNamespace(
        steps=[
            [
                {
                    "visualize": [
                        {
                            "current": terminal,
                            "logs": [{"type": "Result", "result": 1, "reason": 3}],
                        }
                    ],
                    "observation": {"current": pre_terminal},
                }
            ]
        ]
    )

    current, source, logs = _terminal_snapshot(environment)

    assert current == terminal
    assert source == "visualizer_terminal"
    assert _terminal_reason(environment, current, logs) == (3, "no_pokemon_in_play", True)
