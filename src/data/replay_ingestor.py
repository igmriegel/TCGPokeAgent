"""Transform CABT Kaggle replays into deterministic, model-safe datasets."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.agents.heuristic import HeuristicAgent
from src.core import CardCatalog, DeckDefinition, DeckProfile

SCHEMA_VERSION = "replay-decisions-v1"
MAX_SHARD_BYTES = 25 * 1024 * 1024
_BANNED_MODEL_KEYS = {
    "visualize",
    "reward",
    "rewards",
    "status",
    "statuses",
    "search_begin_input",
    "opponent_name",
    "agent_name",
}


@dataclass(frozen=True, slots=True)
class ReplayDatasetSummary:
    """High-level deterministic counts for one ingested dataset."""

    matches: int
    decisions: int
    meaningful_decisions: int
    own_decisions: int
    opponent_decisions: int
    unique_opponent_decks: int
    own_agreements: int
    opponent_agreements: int

    @property
    def divergences(self) -> int:
        """Return total disagreements with the reference heuristic."""
        return self.decisions - self.own_agreements - self.opponent_agreements

    def to_dict(self) -> dict[str, int]:
        """Serialize summary counts."""
        return {
            "matches": self.matches,
            "decisions": self.decisions,
            "meaningful_decisions": self.meaningful_decisions,
            "own_decisions": self.own_decisions,
            "opponent_decisions": self.opponent_decisions,
            "unique_opponent_decks": self.unique_opponent_decks,
            "own_agreements": self.own_agreements,
            "opponent_agreements": self.opponent_agreements,
            "divergences": self.divergences,
        }


def ingest_replays(
    input_dir: str | Path,
    output_dir: str | Path,
    *,
    owner_name: str,
) -> ReplayDatasetSummary:
    """Ingest raw replay JSON files and write a versioned dataset.

    Args:
        input_dir: Directory containing Kaggle episode JSON files.
        output_dir: New derived-dataset directory.
        owner_name: Local identity used only to classify own versus opponent records.

    Returns:
        Dataset summary.

    Raises:
        FileExistsError: If the immutable output directory already exists.
        ValueError: If a replay violates the expected CABT schema.
    """
    source_dir = Path(input_dir)
    destination = Path(output_dir)
    if destination.exists():
        raise FileExistsError(f"derived dataset already exists: {destination}")
    sources = sorted(source_dir.glob("*.json"))
    if not sources:
        raise ValueError(f"no replay JSON files found in {source_dir}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    source_records: list[dict[str, Any]] = []
    matches: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    deck_records: dict[str, dict[str, Any]] = {}
    opponent_deck_first_episode: dict[str, int] = {}
    catalog = CardCatalog.from_cg()

    for source in sources:
        replay = _read_replay(source)
        episode_id = int(replay.get("info", {}).get("EpisodeId", source.stem))
        agents = replay.get("info", {}).get("Agents", [])
        owner_indices = [
            index
            for index, agent in enumerate(agents)
            if isinstance(agent, Mapping) and agent.get("Name") == owner_name
        ]
        if len(owner_indices) != 1:
            raise ValueError(f"episode {episode_id} does not identify exactly one owner side")
        own_index = owner_indices[0]
        steps = replay.get("steps")
        if not isinstance(steps, list) or len(steps) < 2:
            raise ValueError(f"episode {episode_id} has no usable steps")
        decks = _extract_decks(replay, episode_id)
        rewards = replay.get("rewards", [0, 0])
        if not isinstance(rewards, list) or len(rewards) != 2:
            raise ValueError(f"episode {episode_id} has invalid rewards")

        for player, deck in enumerate(decks):
            deck_hash = deck.sha256
            deck_records.setdefault(
                deck_hash,
                {
                    "schema_version": "replay-deck-v1",
                    "deck_sha256": deck_hash,
                    "card_ids": list(sorted(deck.card_ids)),
                    "card_counts": {
                        str(card_id): count for card_id, count in sorted(deck.counts.items())
                    },
                    "card_names": {
                        str(card_id): str((catalog.get_card(str(card_id)) or {}).get("name", ""))
                        for card_id in sorted(deck.counts)
                    },
                    "source_episodes": [],
                },
            )
            deck_records[deck_hash]["source_episodes"].append(episode_id)
            if player != own_index:
                opponent_deck_first_episode.setdefault(deck_hash, episode_id)

        source_records.append(
            {
                "episode_id": episode_id,
                "path": source.name,
                "size_bytes": source.stat().st_size,
                "sha256": _sha256_file(source),
            }
        )
        matches.append(
            {
                "schema_version": "replay-match-v1",
                "episode_id": episode_id,
                "sdk_version": str(replay.get("module_version", "")),
                "steps": len(steps),
                "own_side": own_index,
                "own_deck_sha256": decks[own_index].sha256,
                "opponent_deck_sha256": decks[1 - own_index].sha256,
                "own_reward": rewards[own_index],
                "opponent_reward": rewards[1 - own_index],
                "statuses": list(replay.get("statuses", [])),
            }
        )

        configured_profile = _bundled_deck_profile()
        policies = [
            HeuristicAgent(deck_profile=configured_profile if player == own_index else None)
            for player in range(2)
        ]
        for player in range(2):
            policies[player].start_match(decks[player])
        for step_index in range(len(steps) - 1):
            for player in range(2):
                current = steps[step_index][player]
                if (
                    not isinstance(current, Mapping)
                    or current.get("status") != "ACTIVE"
                    or not isinstance(current.get("observation"), Mapping)
                    or current["observation"].get("select") is None
                ):
                    continue
                following = steps[step_index + 1][player]
                action = following.get("action") if isinstance(following, Mapping) else None
                if not isinstance(action, list):
                    raise ValueError(
                        f"episode {episode_id} step {step_index} has no following action"
                    )
                observation = _model_safe_observation(current["observation"])
                _validate_action(observation, action)
                reference_action = policies[player].select(observation)
                select = observation["select"]
                legal_selection_count = _legal_selection_count(select)
                actor_role = "own" if player == own_index else "opponent"
                decisions.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "decision_id": f"{episode_id}:{step_index}:{player}",
                        "episode_id": episode_id,
                        "step_index": step_index,
                        "player_index": player,
                        "actor_role": actor_role,
                        "actor_deck_sha256": decks[player].sha256,
                        "opponent_deck_sha256": decks[1 - player].sha256,
                        "observation": observation,
                        "selected_indices": action,
                        "reference_indices": reference_action,
                        "reference_agreement": reference_action == action,
                        "forced": legal_selection_count <= 1,
                        "legal_selection_count": legal_selection_count,
                        "outcome_label": _outcome_label(rewards[player]),
                        "behavior_confidence": 0.6 if rewards[player] > 0 else 0.4,
                        "label_source": "observed_behavior",
                    }
                )

    splits = _deck_group_splits(opponent_deck_first_episode)
    for decision in decisions:
        decision["split"] = (
            "regression"
            if decision["actor_role"] == "own"
            else splits[decision["actor_deck_sha256"]]
        )

    leakage_findings = _audit_leakage(decisions)
    if leakage_findings:
        raise ValueError(f"model-safe leakage audit failed: {leakage_findings[:3]}")

    summary = _summary(matches, decisions)
    dataset_id = _dataset_id(source_records)
    with tempfile.TemporaryDirectory(
        prefix=f".{destination.name}-", dir=destination.parent
    ) as temporary:
        build_root = Path(temporary) / destination.name
        build_root.mkdir(parents=True)
        _write_jsonl(build_root / "matches.jsonl", matches)
        _write_jsonl(build_root / "decks.jsonl", deck_records.values())
        deck_dir = build_root / "decks"
        deck_dir.mkdir()
        for deck_hash, record in sorted(deck_records.items()):
            (deck_dir / f"{deck_hash}.csv").write_text(
                "".join(f"{card_id}\n" for card_id in record["card_ids"]),
                encoding="utf-8",
            )
        for split in ("train", "validation", "holdout", "regression"):
            _write_sharded_jsonl(
                build_root / "decisions" / split,
                (decision for decision in decisions if decision["split"] == split),
            )
        _write_json(
            build_root / "splits.json",
            {
                "schema_version": "replay-splits-v1",
                "method": "actor_deck_grouped_chronological_70_15_15",
                "deck_splits": splits,
            },
        )
        _write_json(
            build_root / "leakage_report.json",
            {
                "schema_version": "leakage-audit-v1",
                "status": "passed",
                "banned_keys": sorted(_BANNED_MODEL_KEYS),
                "records_checked": len(decisions),
                "findings": [],
            },
        )
        divergences = [
            {
                "decision_id": decision["decision_id"],
                "episode_id": decision["episode_id"],
                "actor_role": decision["actor_role"],
                "context": decision["observation"]["select"].get("context"),
                "selected_indices": decision["selected_indices"],
                "reference_indices": decision["reference_indices"],
            }
            for decision in decisions
            if not decision["reference_agreement"]
        ]
        _write_json(
            build_root / "divergence_report.json",
            {
                "schema_version": "policy-divergence-v1",
                "reference_policy": "generic_heuristic",
                "summary": summary.to_dict(),
                "records": divergences,
            },
        )
        replay_metrics = _replay_metrics(matches, decisions)
        _write_json(build_root / "metrics.json", replay_metrics)
        (build_root / "summary.md").write_text(
            _summary_markdown(dataset_id, summary, replay_metrics), encoding="utf-8"
        )
        outputs = _output_hashes(build_root)
        _write_json(
            build_root / "manifest.json",
            {
                "schema_version": "replay-dataset-manifest-v1",
                "dataset_id": dataset_id,
                "status": "COMPLETED",
                "transformation": {
                    "name": "src.data.replay_ingestor",
                    "version": SCHEMA_VERSION,
                    "action_alignment": "observation[t] -> action[t+1]",
                },
                "sources": source_records,
                "summary": summary.to_dict(),
                "outputs": outputs,
                "leakage_risk": "audited_model_safe_observations",
            },
        )
        build_root.rename(destination)
    return summary


def _read_replay(path: Path) -> dict[str, Any]:
    try:
        replay = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read replay {path}") from error
    if not isinstance(replay, dict) or replay.get("name") != "cabt":
        raise ValueError(f"unsupported replay schema: {path}")
    return replay


def _bundled_deck_profile() -> DeckProfile | None:
    profile_path = Path(__file__).parents[1] / "artifacts" / "deck_profile.json"
    try:
        data = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return DeckProfile.from_dict(data) if isinstance(data, Mapping) else None


def _extract_decks(replay: Mapping[str, Any], episode_id: int) -> list[DeckDefinition]:
    try:
        raw_decks = replay["steps"][0][0]["visualize"][0]["action"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError(f"episode {episode_id} has no initial deck payload") from error
    if not isinstance(raw_decks, list) or len(raw_decks) != 2:
        raise ValueError(f"episode {episode_id} has invalid initial decks")
    decks = [
        DeckDefinition.from_cards(list(cards), f"episode-{episode_id}-player-{player}")
        for player, cards in enumerate(raw_decks)
        if isinstance(cards, list)
    ]
    if len(decks) != 2:
        raise ValueError(f"episode {episode_id} has malformed deck entries")
    return decks


def _model_safe_observation(observation: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "step": observation.get("step"),
        "current": observation.get("current"),
        "logs": observation.get("logs", []),
        "select": observation.get("select"),
    }


def _validate_action(observation: Mapping[str, Any], action: Sequence[Any]) -> None:
    select = observation.get("select")
    if not isinstance(select, Mapping):
        raise ValueError("decision has no select mapping")
    options = select.get("option")
    if not isinstance(options, list):
        raise ValueError("decision has no option list")
    if any(isinstance(index, bool) or not isinstance(index, int) for index in action):
        raise ValueError("action contains non-integer index")
    if len(action) != len(set(action)):
        raise ValueError("action contains duplicate index")
    if any(index < 0 or index >= len(options) for index in action):
        raise ValueError("action contains out-of-range index")
    minimum = int(select.get("minCount", 0) or 0)
    maximum = int(select.get("maxCount", 0) or 0)
    if not minimum <= len(action) <= maximum:
        raise ValueError("action violates selection cardinality")


def _legal_selection_count(select: Mapping[str, Any]) -> int:
    options = select.get("option")
    count = len(options) if isinstance(options, list) else 0
    minimum = max(0, int(select.get("minCount", 0) or 0))
    maximum = min(count, int(select.get("maxCount", 0) or 0))
    return sum(math.comb(count, size) for size in range(minimum, maximum + 1))


def _deck_group_splits(first_episode: Mapping[str, int]) -> dict[str, str]:
    groups = sorted(first_episode, key=lambda deck: (first_episode[deck], deck))
    train_end = int(len(groups) * 0.70)
    validation_end = train_end + int(len(groups) * 0.15)
    return {
        deck: (
            "train" if index < train_end else "validation" if index < validation_end else "holdout"
        )
        for index, deck in enumerate(groups)
    }


def _audit_leakage(records: Iterable[Mapping[str, Any]]) -> list[str]:
    findings: list[str] = []

    def inspect(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if key in _BANNED_MODEL_KEYS:
                    findings.append(child_path)
                inspect(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                inspect(child, f"{path}[{index}]")

    for record in records:
        inspect(record.get("observation"), str(record.get("decision_id")))
    return findings


def _summary(
    matches: Sequence[Mapping[str, Any]], decisions: Sequence[Mapping[str, Any]]
) -> ReplayDatasetSummary:
    own = [decision for decision in decisions if decision["actor_role"] == "own"]
    opponents = [decision for decision in decisions if decision["actor_role"] == "opponent"]
    return ReplayDatasetSummary(
        matches=len(matches),
        decisions=len(decisions),
        meaningful_decisions=sum(not decision["forced"] for decision in decisions),
        own_decisions=len(own),
        opponent_decisions=len(opponents),
        unique_opponent_decks=len({str(match["opponent_deck_sha256"]) for match in matches}),
        own_agreements=sum(bool(decision["reference_agreement"]) for decision in own),
        opponent_agreements=sum(bool(decision["reference_agreement"]) for decision in opponents),
    )


def _outcome_label(reward: Any) -> str:
    value = float(reward) if isinstance(reward, (int, float)) else 0.0
    return "win" if value > 0 else "loss" if value < 0 else "draw"


def _replay_metrics(
    matches: Sequence[Mapping[str, Any]], decisions: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    outcomes = Counter(_outcome_label(match.get("own_reward")) for match in matches)
    by_actor_context: dict[str, dict[str, dict[str, int | float]]] = {}
    for decision in decisions:
        actor = str(decision["actor_role"])
        select = decision["observation"].get("select", {})
        context = str(select.get("context", "unknown"))
        bucket = by_actor_context.setdefault(actor, {}).setdefault(
            context, {"decisions": 0, "agreements": 0, "divergences": 0}
        )
        bucket["decisions"] = int(bucket["decisions"]) + 1
        key = "agreements" if decision["reference_agreement"] else "divergences"
        bucket[key] = int(bucket[key]) + 1
    for contexts in by_actor_context.values():
        for bucket in contexts.values():
            bucket["agreement_rate"] = (
                int(bucket["agreements"]) / int(bucket["decisions"]) if bucket["decisions"] else 0.0
            )
    split_counts = Counter(str(decision["split"]) for decision in decisions)
    return {
        "schema_version": "replay-metrics-v1",
        "own_results": {
            "wins": outcomes["win"],
            "draws": outcomes["draw"],
            "losses": outcomes["loss"],
            "match_score_rate": (
                (outcomes["win"] + 0.5 * outcomes["draw"]) / len(matches) if matches else 0.0
            ),
        },
        "decision_splits": dict(sorted(split_counts.items())),
        "by_actor_context": by_actor_context,
    }


def _dataset_id(sources: Sequence[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    digest.update(SCHEMA_VERSION.encode())
    for source in sorted(sources, key=lambda item: int(item["episode_id"])):
        digest.update(str(source["episode_id"]).encode())
        digest.update(str(source["sha256"]).encode())
    return digest.hexdigest()[:16]


def _write_sharded_jsonl(directory: Path, records: Iterable[Mapping[str, Any]]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    part = 0
    size = 0
    handle = None
    try:
        for record in records:
            line = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            encoded_size = len(line.encode())
            if handle is None or size + encoded_size > MAX_SHARD_BYTES:
                if handle is not None:
                    handle.close()
                handle = (directory / f"part-{part:05d}.jsonl").open("w", encoding="utf-8")
                part += 1
                size = 0
            handle.write(line)
            size += encoded_size
    finally:
        if handle is not None:
            handle.close()
    if part == 0:
        (directory / "part-00000.jsonl").write_text("", encoding="utf-8")


def _write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n" for record in records
        ),
        encoding="utf-8",
    )


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _output_hashes(root: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": str(path.relative_to(root)),
            "size_bytes": path.stat().st_size,
            "sha256": _sha256_file(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    ]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _summary_markdown(
    dataset_id: str,
    summary: ReplayDatasetSummary,
    metrics: Mapping[str, Any],
) -> str:
    results = metrics.get("own_results", {})
    return "\n".join(
        (
            f"# Replay dataset {dataset_id}",
            "",
            f"- Matches: {summary.matches}",
            f"- Own W/D/L: {results.get('wins', 0)}/"
            f"{results.get('draws', 0)}/{results.get('losses', 0)}",
            f"- Decisions: {summary.decisions}",
            f"- Non-forced decisions: {summary.meaningful_decisions}",
            f"- Own decisions: {summary.own_decisions}",
            f"- Opponent decisions: {summary.opponent_decisions}",
            f"- Unique opponent decks: {summary.unique_opponent_decks}",
            f"- Own/reference divergences: {summary.own_decisions - summary.own_agreements}",
            f"- Opponent/reference divergences: "
            f"{summary.opponent_decisions - summary.opponent_agreements}",
            "",
        )
    )


def _run_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Directory containing replay JSON files")
    parser.add_argument("--output", required=True, help="New derived dataset directory")
    parser.add_argument(
        "--owner-name",
        required=True,
        help="Owner name used for classification and never persisted",
    )
    args = parser.parse_args()
    summary = ingest_replays(args.input, args.output, owner_name=args.owner_name)
    print(json.dumps(summary.to_dict(), sort_keys=True))


if __name__ == "__main__":
    _run_cli()
