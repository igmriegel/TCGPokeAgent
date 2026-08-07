"""Compare independent Honchkrow/Porygon evaluation reports."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


def _wilson(wins: int, total: int) -> tuple[float, float]:
    """Return a 95% Wilson interval for a binomial win rate."""
    if total == 0:
        return 0.0, 0.0
    p = wins / total
    z = 1.96
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5) / denominator
    return center - margin, center + margin


def _side_outcomes(matches: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Return W/D/L counts for each evaluated agent side."""
    sides: dict[str, Counter[str]] = {}
    for match in matches:
        side = str(match.get("agent_side", "unknown"))
        sides.setdefault(side, Counter()).update([str(match.get("result", "unknown"))])
    return {side: dict(outcomes) for side, outcomes in sorted(sides.items())}


def _two_proportion_test(
    baseline_wins: int,
    baseline_total: int,
    variant_wins: int,
    variant_total: int,
) -> dict[str, float]:
    """Return the pooled two-sided z-test for independent win proportions."""
    if baseline_total == 0 or variant_total == 0:
        return {"z": 0.0, "p_two_sided": 1.0}
    pooled = (baseline_wins + variant_wins) / (baseline_total + variant_total)
    standard_error = (pooled * (1.0 - pooled) * (1.0 / baseline_total + 1.0 / variant_total)) ** 0.5
    if standard_error == 0.0:
        return {"z": 0.0, "p_two_sided": 1.0}
    z_score = (variant_wins / variant_total - baseline_wins / baseline_total) / standard_error
    return {
        "z": z_score,
        "p_two_sided": math.erfc(abs(z_score) / math.sqrt(2.0)),
    }


def compare(baseline_path: Path, variant_path: Path) -> dict[str, Any]:
    """Compare reports as independent samples.

    CABT 1.32.2 does not forward the configured evaluation seed to the battle
    engine. Nominally matching ``(seed, agent_side)`` values therefore do not
    identify paired episodes and must not be used for McNemar inference.
    """
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    variant = json.loads(variant_path.read_text(encoding="utf-8"))
    baseline_matches = list(baseline.get("matches", []))
    variant_matches = list(variant.get("matches", []))
    outcomes = {
        "baseline": Counter(str(item.get("result", "unknown")) for item in baseline_matches),
        "variant": Counter(str(item.get("result", "unknown")) for item in variant_matches),
    }
    baseline_wins = outcomes["baseline"]["win"]
    variant_wins = outcomes["variant"]["win"]
    baseline_total = len(baseline_matches)
    variant_total = len(variant_matches)
    return {
        "comparison_mode": "independent",
        "pairing_warning": (
            "CABT nominal seeds are metadata only; McNemar and episode conversion "
            "tables are not valid for these reports."
        ),
        "sample_sizes": {"baseline": baseline_total, "variant": variant_total},
        "outcomes": {name: dict(values) for name, values in outcomes.items()},
        "win_rates": {
            "baseline": baseline_wins / baseline_total if baseline_total else 0.0,
            "variant": variant_wins / variant_total if variant_total else 0.0,
        },
        "wilson_95": {
            "baseline": _wilson(baseline_wins, baseline_total),
            "variant": _wilson(variant_wins, variant_total),
        },
        "two_proportion_test": _two_proportion_test(
            baseline_wins,
            baseline_total,
            variant_wins,
            variant_total,
        ),
        "by_side": {
            "baseline": _side_outcomes(baseline_matches),
            "variant": _side_outcomes(variant_matches),
        },
        "deck_out_losses": {
            "baseline": int(baseline.get("audit", {}).get("deck_out_losses", 0)),
            "variant": int(variant.get("audit", {}).get("deck_out_losses", 0)),
        },
        "operational_status": {
            "baseline": dict(
                Counter(str(item.get("status", "unknown")) for item in baseline_matches)
            ),
            "variant": dict(
                Counter(str(item.get("status", "unknown")) for item in variant_matches)
            ),
        },
    }


def main() -> None:
    """Parse report paths and print the independent comparison as JSON."""
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("variant", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(args.baseline, args.variant), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
