"""Store post-hoc human reviews of automated Kaggle gameplay replays."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.core import CardCatalog
from src.core.parser import DefaultParser

SCHEMA_VERSION = "competitive-gameplay-review-v1"
REVIEW_KIND = "post_hoc_human_review"
ACTOR_TYPE = "agent"
VERDICTS = {"acceptable", "mistake", "forced", "uncertain"}
CAUSE_CODES = {
    "board_collapse",
    "deck_limit",
    "energy_management",
    "illegal_or_runtime_failure",
    "prize_mapping",
    "resource_management",
    "sequencing",
    "target_selection",
    "unknown",
}
REASON_TAGS = {
    "BOARD_PRESENCE",
    "EMPTY_BENCH",
    "SECOND_ATTACKER",
    "SUPPORT_POKEMON",
    "EVOLUTION_SETUP",
    "ENERGY_ENABLE_ATTACK",
    "ENERGY_PREPARE_BENCH",
    "KO_NOW",
    "PRIZE_TRADE",
    "RESOURCE_PRESERVATION",
    "DEVELOP_BEFORE_ATTACK",
    "MISSED_LEGAL_DEVELOPMENT",
    "TERMINAL_ACTION_TOO_EARLY",
    "OTHER",
}


@dataclass(frozen=True, slots=True)
class DecisionEvidence:
    """Capture one reviewed agent decision using only actor-visible state."""

    decision_id: str
    step_index: int
    turn: int
    select_type: int
    select_context: int
    selected_indices: tuple[int, ...]
    preferred_indices: tuple[int, ...]
    legal_options: tuple[dict[str, Any], ...]
    visible_state: dict[str, Any]


@dataclass(frozen=True, slots=True)
class GameplayReviewAnnotation:
    """Explain a competitive agent outcome with linked decision evidence."""

    annotation_id: str
    episode_id: int
    player_index: int
    match_outcome: str
    verdict: str
    cause_code: str
    reason_tags: tuple[str, ...]
    raw_feedback: str
    technical_interpretation: str
    confidence: float
    decisions: tuple[DecisionEvidence, ...]
    replay_sha256: str
    created_at: str
    intended_follow_up: str = ""
    supersedes: str | None = None
    schema_version: str = SCHEMA_VERSION
    review_kind: str = REVIEW_KIND
    actor_type: str = ACTOR_TYPE

    def validate(self) -> None:
        """Validate annotation semantics and post-hoc provenance."""
        if not self.annotation_id.strip():
            raise ValueError("annotation_id cannot be empty")
        if self.player_index not in {0, 1}:
            raise ValueError("player_index must be 0 or 1")
        if self.match_outcome not in {"win", "draw", "loss"}:
            raise ValueError("match_outcome must be win, draw, or loss")
        if self.verdict not in VERDICTS:
            raise ValueError(f"unsupported verdict: {self.verdict}")
        if self.cause_code not in CAUSE_CODES:
            raise ValueError(f"unsupported cause code: {self.cause_code}")
        unknown_tags = set(self.reason_tags) - REASON_TAGS
        if unknown_tags:
            raise ValueError(f"unsupported reason tags: {sorted(unknown_tags)}")
        if not self.raw_feedback.strip():
            raise ValueError("raw_feedback cannot be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not self.decisions:
            raise ValueError("at least one decision must support the annotation")
        if len({item.step_index for item in self.decisions}) != len(self.decisions):
            raise ValueError("decision evidence contains duplicate steps")
        if self.supersedes == self.annotation_id:
            raise ValueError("an annotation cannot supersede itself")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the immutable annotation to JSON-compatible data."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> GameplayReviewAnnotation:
        """Deserialize and validate one annotation record."""
        annotation = cls(
            annotation_id=str(data["annotation_id"]),
            episode_id=int(data["episode_id"]),
            player_index=int(data["player_index"]),
            match_outcome=str(data["match_outcome"]),
            verdict=str(data["verdict"]),
            cause_code=str(data["cause_code"]),
            reason_tags=tuple(str(tag) for tag in data.get("reason_tags", ())),
            raw_feedback=str(data["raw_feedback"]),
            technical_interpretation=str(data.get("technical_interpretation", "")),
            confidence=float(data["confidence"]),
            decisions=tuple(
                DecisionEvidence(
                    decision_id=str(item["decision_id"]),
                    step_index=int(item["step_index"]),
                    turn=int(item["turn"]),
                    select_type=int(item["select_type"]),
                    select_context=int(item["select_context"]),
                    selected_indices=tuple(int(index) for index in item["selected_indices"]),
                    preferred_indices=tuple(int(index) for index in item["preferred_indices"]),
                    legal_options=tuple(dict(option) for option in item["legal_options"]),
                    visible_state=dict(item["visible_state"]),
                )
                for item in data["decisions"]
            ),
            replay_sha256=str(data["replay_sha256"]),
            created_at=str(data["created_at"]),
            intended_follow_up=str(data.get("intended_follow_up", "")),
            supersedes=(str(data["supersedes"]) if data.get("supersedes") is not None else None),
            schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
            review_kind=str(data.get("review_kind", REVIEW_KIND)),
            actor_type=str(data.get("actor_type", ACTOR_TYPE)),
        )
        annotation.validate()
        return annotation


class GameplayAnnotationStore:
    """Persist immutable competitive gameplay reviews as append-only JSONL."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, annotation: GameplayReviewAnnotation) -> None:
        """Validate and append a unique annotation."""
        annotation.validate()
        existing = self.read()
        if any(item.annotation_id == annotation.annotation_id for item in existing):
            raise ValueError(f"annotation already exists: {annotation.annotation_id}")
        if annotation.supersedes and not any(
            item.annotation_id == annotation.supersedes for item in existing
        ):
            raise ValueError(f"superseded annotation does not exist: {annotation.supersedes}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(
                json.dumps(annotation.to_dict(), sort_keys=True, separators=(",", ":")) + "\n"
            )

    def read(self) -> list[GameplayReviewAnnotation]:
        """Read all gameplay review annotations."""
        if not self.path.exists():
            return []
        return [
            GameplayReviewAnnotation.from_dict(json.loads(line))
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


def annotation_from_replay(
    replay_path: str | Path,
    *,
    annotation_id: str,
    player_index: int,
    preferred_by_step: Mapping[int, Sequence[int]],
    verdict: str,
    cause_code: str,
    reason_tags: Iterable[str],
    raw_feedback: str,
    technical_interpretation: str,
    confidence: float,
    intended_follow_up: str = "",
    supersedes: str | None = None,
    created_at: str | None = None,
) -> GameplayReviewAnnotation:
    """Build a validated review from exact replay decisions.

    Args:
        replay_path: CABT Kaggle replay JSON.
        annotation_id: Stable unique review identifier.
        player_index: Reviewed engine side.
        preferred_by_step: Replay step to reviewer-preferred simulator indices.
        verdict: Review classification.
        cause_code: Normalized match-loss category.
        reason_tags: Tactical or strategic labels.
        raw_feedback: Reviewer's original feedback without rewriting.
        technical_interpretation: Separate derived diagnosis.
        confidence: Post-hoc confidence from zero to one.
        intended_follow_up: Correct sequence after the preferred decision.
        supersedes: Earlier annotation corrected without deleting its history.
        created_at: Optional immutable UTC timestamp.

    Returns:
        Annotation linked to verified legal decisions.
    """
    path = Path(replay_path)
    replay = _read_replay(path)
    episode_id = int(replay.get("info", {}).get("EpisodeId", path.stem))
    rewards = replay.get("rewards", [0, 0])
    if player_index not in {0, 1}:
        raise ValueError("player_index must be 0 or 1")
    if not isinstance(rewards, list) or len(rewards) != 2:
        raise ValueError("replay does not expose two final rewards")
    decisions = tuple(
        _decision_evidence(replay, episode_id, player_index, step, preferred)
        for step, preferred in sorted(preferred_by_step.items())
    )
    reward = float(rewards[player_index])
    annotation = GameplayReviewAnnotation(
        annotation_id=annotation_id,
        episode_id=episode_id,
        player_index=player_index,
        match_outcome="win" if reward > 0 else "loss" if reward < 0 else "draw",
        verdict=verdict,
        cause_code=cause_code,
        reason_tags=tuple(sorted(set(reason_tags))),
        raw_feedback=raw_feedback,
        technical_interpretation=technical_interpretation,
        confidence=confidence,
        decisions=decisions,
        replay_sha256=_sha256_file(path),
        created_at=created_at or datetime.now(timezone.utc).isoformat(),
        intended_follow_up=intended_follow_up,
        supersedes=supersedes,
    )
    annotation.validate()
    return annotation


def inspect_replay(
    replay_path: str | Path,
    *,
    player_index: int,
    card_id: int | None = None,
    empty_bench: bool = False,
) -> list[dict[str, Any]]:
    """Return compact decision summaries for interactive replay review."""
    path = Path(replay_path)
    replay = _read_replay(path)
    episode_id = int(replay.get("info", {}).get("EpisodeId", path.stem))
    summaries: list[dict[str, Any]] = []
    for step in range(len(replay["steps"]) - 1):
        participant_step = replay["steps"][step][player_index]
        if participant_step.get("status") != "ACTIVE":
            continue
        observation = participant_step.get("observation", {})
        current = observation.get("current")
        select = observation.get("select")
        if not isinstance(current, Mapping) or not isinstance(select, Mapping):
            continue
        players = current.get("players")
        if not isinstance(players, list) or len(players) != 2:
            continue
        actor = players[player_index]
        if not isinstance(actor, Mapping):
            continue
        hand_ids = [int(card.get("id", -1)) for card in actor.get("hand", [])]
        if card_id is not None and card_id not in hand_ids:
            continue
        if empty_bench and actor.get("bench"):
            continue
        evidence = _decision_evidence(replay, episode_id, player_index, step, None)
        summaries.append(
            {
                "decision_id": evidence.decision_id,
                "step_index": step,
                "turn": evidence.turn,
                "selected_indices": list(evidence.selected_indices),
                "hand_card_ids": hand_ids,
                "bench_count": len(actor.get("bench", [])),
                "legal_options": list(evidence.legal_options),
            }
        )
    return summaries


def _decision_evidence(
    replay: Mapping[str, Any],
    episode_id: int,
    player_index: int,
    step_index: int,
    preferred_indices: Sequence[int] | None,
) -> DecisionEvidence:
    steps = replay.get("steps")
    if not isinstance(steps, list) or not 0 <= step_index < len(steps) - 1:
        raise ValueError(f"step {step_index} cannot be aligned with a following action")
    observation = steps[step_index][player_index].get("observation", {})
    if steps[step_index][player_index].get("status") != "ACTIVE":
        raise ValueError(f"step {step_index} is not an active agent decision")
    select = observation.get("select")
    current = observation.get("current")
    if not isinstance(select, Mapping) or not isinstance(current, Mapping):
        raise ValueError(f"step {step_index} is not a selectable decision")
    following = steps[step_index + 1][player_index]
    selected = following.get("action")
    if not isinstance(selected, list):
        raise ValueError(f"step {step_index} has no following agent action")
    options = select.get("option")
    if not isinstance(options, list):
        raise ValueError(f"step {step_index} has no legal options")
    _validate_selection(selected, select, "recorded")
    if preferred_indices is not None:
        _validate_selection(preferred_indices, select, "preferred")
    parsed = DefaultParser(CardCatalog.from_cg()).parse(dict(observation))
    by_index = {candidate.option_index: candidate for candidate in parsed.candidates}
    legal_options = []
    for index, raw_option in enumerate(options):
        candidate = by_index.get(index)
        card = candidate.card if candidate and candidate.card else {}
        attack = candidate.attack if candidate and candidate.attack else {}
        legal_options.append(
            {
                "index": index,
                "option_type": candidate.option_type.name if candidate else "UNKNOWN",
                "card_id": card.get("id"),
                "card_name": card.get("name"),
                "attack_id": attack.get("id"),
                "attack_name": attack.get("name"),
                "raw_type": raw_option.get("type") if isinstance(raw_option, Mapping) else None,
            }
        )
    return DecisionEvidence(
        decision_id=f"{episode_id}:{step_index}:{player_index}",
        step_index=step_index,
        turn=int(current.get("turn", 0) or 0),
        select_type=int(select.get("type", -1)),
        select_context=int(select.get("context", -1)),
        selected_indices=tuple(int(index) for index in selected),
        preferred_indices=tuple(int(index) for index in preferred_indices or ()),
        legal_options=tuple(legal_options),
        visible_state=_visible_state(current, player_index),
    )


def _visible_state(current: Mapping[str, Any], player_index: int) -> dict[str, Any]:
    players = current.get("players", [])
    actor = players[player_index] if isinstance(players, list) and len(players) == 2 else {}
    opponent = players[1 - player_index] if isinstance(players, list) and len(players) == 2 else {}

    def cards(zone: Any) -> list[dict[str, Any]]:
        if not isinstance(zone, list):
            return []
        return [
            {
                "id": card.get("id"),
                "serial": card.get("serial"),
                "hp": card.get("hp"),
            }
            for card in zone
            if isinstance(card, Mapping)
        ]

    return {
        "turn": current.get("turn"),
        "actor": {
            "active": cards(actor.get("active") if isinstance(actor, Mapping) else []),
            "bench": cards(actor.get("bench") if isinstance(actor, Mapping) else []),
            "hand": cards(actor.get("hand") if isinstance(actor, Mapping) else []),
            "deck_count": actor.get("deckCount") if isinstance(actor, Mapping) else None,
            "prize_count": actor.get("prizeCount") if isinstance(actor, Mapping) else None,
        },
        "opponent_public": {
            "active": cards(opponent.get("active") if isinstance(opponent, Mapping) else []),
            "bench": cards(opponent.get("bench") if isinstance(opponent, Mapping) else []),
            "deck_count": opponent.get("deckCount") if isinstance(opponent, Mapping) else None,
            "prize_count": opponent.get("prizeCount") if isinstance(opponent, Mapping) else None,
        },
    }


def _validate_selection(
    indices: Sequence[Any],
    select: Mapping[str, Any],
    label: str,
) -> None:
    options = select.get("option", [])
    if any(isinstance(index, bool) or not isinstance(index, int) for index in indices):
        raise ValueError(f"{label} selection contains a non-integer index")
    if len(indices) != len(set(indices)):
        raise ValueError(f"{label} selection contains duplicate indices")
    if any(index < 0 or index >= len(options) for index in indices):
        raise ValueError(f"{label} selection contains an illegal index")
    minimum = int(select.get("minCount", 0) or 0)
    maximum = int(select.get("maxCount", 0) or 0)
    if not minimum <= len(indices) <= maximum:
        raise ValueError(f"{label} selection violates decision cardinality")


def _read_replay(path: Path) -> dict[str, Any]:
    try:
        replay = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read replay: {path}") from error
    if not isinstance(replay, dict) or replay.get("name") != "cabt":
        raise ValueError(f"unsupported replay: {path}")
    return replay


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_preferred(values: Sequence[str]) -> dict[int, tuple[int, ...]]:
    parsed: dict[int, tuple[int, ...]] = {}
    for value in values:
        step_text, separator, indices_text = value.partition(":")
        if not separator:
            raise ValueError("preferred decisions use STEP:INDEX[,INDEX] format")
        parsed[int(step_text)] = tuple(
            int(index.strip()) for index in indices_text.split(",") if index.strip()
        )
    return parsed


def _run_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect", help="List reviewable replay decisions")
    inspect_parser.add_argument("--replay", required=True)
    inspect_parser.add_argument("--player", type=int, required=True)
    inspect_parser.add_argument("--card-id", type=int)
    inspect_parser.add_argument("--empty-bench", action="store_true")

    add_parser = subparsers.add_parser("add", help="Append a verified replay review")
    add_parser.add_argument("--replay", required=True)
    add_parser.add_argument("--output", required=True)
    add_parser.add_argument("--annotation-id", required=True)
    add_parser.add_argument("--player", type=int, required=True)
    add_parser.add_argument("--preferred", action="append", required=True)
    add_parser.add_argument("--verdict", choices=sorted(VERDICTS), required=True)
    add_parser.add_argument("--cause", choices=sorted(CAUSE_CODES), required=True)
    add_parser.add_argument("--tag", action="append", default=[])
    add_parser.add_argument("--feedback", required=True)
    add_parser.add_argument("--interpretation", default="")
    add_parser.add_argument("--follow-up", default="")
    add_parser.add_argument("--supersedes")
    add_parser.add_argument("--confidence", type=float, required=True)
    args = parser.parse_args()

    if args.command == "inspect":
        records = inspect_replay(
            args.replay,
            player_index=args.player,
            card_id=args.card_id,
            empty_bench=args.empty_bench,
        )
        print(json.dumps(records, indent=2, sort_keys=True))
        return

    annotation = annotation_from_replay(
        args.replay,
        annotation_id=args.annotation_id,
        player_index=args.player,
        preferred_by_step=_parse_preferred(args.preferred),
        verdict=args.verdict,
        cause_code=args.cause,
        reason_tags=args.tag,
        raw_feedback=args.feedback,
        technical_interpretation=args.interpretation,
        confidence=args.confidence,
        intended_follow_up=args.follow_up,
        supersedes=args.supersedes,
    )
    GameplayAnnotationStore(args.output).append(annotation)
    print(json.dumps(annotation.to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    _run_cli()
