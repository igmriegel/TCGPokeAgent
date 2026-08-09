"""Audit isolated prompts from the two latest replay submissions.

The report compares the current policy's legal decision with a historical
prompt. It is diagnostic evidence only and never infers a different match
result from one changed decision.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.factory import build_agent, load_deck  # noqa: E402
from src.core import DeckDefinition  # noqa: E402
from src.eval.validation import check_legal_selection  # noqa: E402

PROMPTS = (
    (55379107, 91326464, 16),
    (55379107, 91329200, 37),
)


def _load_replay(path: Path) -> dict[str, Any]:
    """Load one CABT replay mapping.

    Args:
        path: Replay JSON path.

    Returns:
        Parsed CABT replay mapping.
    """
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("name") != "cabt":
        raise ValueError(f"unsupported replay: {path}")
    return value


def _owner_index(replay: Mapping[str, Any]) -> int:
    """Resolve the local owner's side from public replay metadata.

    Args:
        replay: Parsed CABT replay mapping.

    Returns:
        Zero-based player side belonging to the owner.
    """
    agents = replay.get("info", {}).get("Agents", [])
    if isinstance(agents, list):
        matches = [
            index
            for index, agent in enumerate(agents)
            if isinstance(agent, Mapping) and agent.get("Name") == "Igor Riegel"
        ]
        if len(matches) == 1:
            return matches[0]
    raise ValueError("could not resolve owner side from replay metadata")


def _selected_types(observation: Mapping[str, Any], selected: list[int]) -> list[int | None]:
    """Return option type values selected from one replay prompt.

    Args:
        observation: CABT observation containing the select prompt.
        selected: Simulator option indices returned by the policy.

    Returns:
        Selected option type values in selection order.
    """
    select = observation.get("select", {})
    options = select.get("option", []) if isinstance(select, Mapping) else []
    if not isinstance(options, list):
        return []
    return [
        options[index].get("type")
        if 0 <= index < len(options) and isinstance(options[index], Mapping)
        else None
        for index in selected
    ]


def audit_prompt(submission_id: int, episode_id: int, step_index: int) -> dict[str, Any]:
    """Evaluate the current policy on one historical prompt in isolation.

    Args:
        submission_id: Kaggle submission directory containing the replay.
        episode_id: Kaggle episode identifier.
        step_index: Replay step containing the owner's active prompt.

    Returns:
        A legal-decision diagnostic record without outcome inference.
    """
    replay_path = (
        ROOT / "replays" / "remote" / str(submission_id) / (f"episode-{episode_id}-replay.json")
    )
    replay = _load_replay(replay_path)
    owner = _owner_index(replay)
    steps = replay.get("steps", [])
    if not isinstance(steps, list) or step_index >= len(steps):
        raise ValueError(f"replay step is unavailable: {step_index}")
    step = steps[step_index]
    if not isinstance(step, list) or owner >= len(step):
        raise ValueError(f"owner prompt is unavailable at step: {step_index}")
    record = step[owner]
    if not isinstance(record, Mapping) or record.get("status") != "ACTIVE":
        raise ValueError(f"owner is not active at step: {step_index}")
    observation = record.get("observation")
    if not isinstance(observation, Mapping):
        raise ValueError(f"owner observation is unavailable at step: {step_index}")

    deck = load_deck(ROOT, "expert_turn_loop")
    agent = build_agent("expert_turn_loop", root=ROOT)
    agent.start_match(DeckDefinition.from_cards(deck, "honchkrow_porygon"))
    selected = list(agent.select(dict(observation)))
    legal = True
    error = ""
    try:
        check_legal_selection(observation, selected)
    except Exception as exception:  # noqa: BLE001
        legal = False
        error = f"{type(exception).__name__}: {exception}"
    select = observation.get("select", {})
    current = observation.get("current", {})
    return {
        "submission_id": submission_id,
        "episode_id": episode_id,
        "step": step_index,
        "owner_index": owner,
        "turn": int(current.get("turn", 0) or 0) if isinstance(current, Mapping) else 0,
        "select_context": select.get("context") if isinstance(select, Mapping) else None,
        "selected_indices": selected,
        "selected_types": _selected_types(observation, selected),
        "legal_selection": legal,
        "error": error,
        "counterfactual_scope": "isolated_prompt_only",
        "outcome_inference_prohibited": True,
    }


def main() -> None:
    """Write the current-policy diagnostics for the curated replay prompts."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports" / "replay_audits" / "recent_submission_prompt_audit.json",
    )
    args = parser.parse_args()
    results = [audit_prompt(*prompt) for prompt in PROMPTS]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"prompts": results}, indent=2) + "\n", encoding="utf-8")
    print(f"audited {len(results)} prompts: {args.output}")


if __name__ == "__main__":
    main()
