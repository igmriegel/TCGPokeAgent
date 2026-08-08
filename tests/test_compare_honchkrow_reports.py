"""Contracts for independent Honchkrow/Porygon report comparison."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.compare_honchkrow_reports import compare


def _write_report(
    path: Path,
    results: tuple[tuple[int, str, str], ...],
    *,
    deck_out_losses: int,
) -> None:
    path.write_text(
        json.dumps(
            {
                "audit": {"deck_out_losses": deck_out_losses},
                "matches": [
                    {
                        "seed": seed,
                        "agent_side": side,
                        "result": result,
                        "status": "ok",
                    }
                    for seed, side, result in results
                ],
            }
        ),
        encoding="utf-8",
    )


def test_comparison_treats_nominal_cabt_seeds_as_independent(tmp_path: Path) -> None:
    """Matching report labels must not produce paired or McNemar output."""
    baseline = tmp_path / "baseline.json"
    variant = tmp_path / "variant.json"
    _write_report(
        baseline,
        ((1, "0", "win"), (1, "1", "loss")),
        deck_out_losses=1,
    )
    _write_report(
        variant,
        ((1, "0", "win"), (1, "1", "win")),
        deck_out_losses=0,
    )

    result = compare(baseline, variant)

    assert result["comparison_mode"] == "independent"
    assert "mcnemar" not in result
    assert "changed_episodes" not in result
    assert result["sample_sizes"] == {"baseline": 2, "variant": 2}
    assert result["win_rates"] == {"baseline": 0.5, "variant": 1.0}
    assert result["win_rate_difference"] == 0.5
    assert result["difference_ci95"][0] < 0.0
    assert result["difference_ci95"][1] > 0.0
    assert result["by_side"]["baseline"]["1"] == {"loss": 1}
    assert result["deck_out_losses"] == {"baseline": 1, "variant": 0}
    assert result["operational_status"] == {
        "baseline": {"ok": 2},
        "variant": {"ok": 2},
    }
