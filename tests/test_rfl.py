from __future__ import annotations

from hashlib import sha256

import pytest

from src.rfl.annotations import AnnotationStore, ExpertAnnotation
from src.rfl.dataset import partition_traces, split_matches
from src.rfl.profiles import PolicyProfile, load_profile
from src.rfl.rewards import hybrid_reward
from src.rfl.schemas import DecisionTrace


def _trace(match_id: str) -> DecisionTrace:
    return DecisionTrace(
        match_id,
        0,
        "deck",
        "hash",
        "matchup",
        1,
        {},
        [{"type": "YES"}],
        [0],
        [0],
        [0],
    )


def test_annotation_store_rejects_illegal_and_round_trips(tmp_path) -> None:
    store = AnnotationStore(tmp_path / "annotations.jsonl")
    annotation = ExpertAnnotation("deck", "hash", "m", "match-1", 1, [0], [[1]], confidence=0.8)
    store.append(annotation, [0, 1])
    assert store.read() == [annotation]
    with pytest.raises(ValueError):
        store.append(annotation, [1])


def test_partition_rejects_match_leakage(tmp_path) -> None:
    with pytest.raises(ValueError, match="leakage"):
        partition_traces([_trace("m")], {"train": {"m"}, "holdout": {"m"}}, tmp_path)
    splits = split_matches(["a", "b", "c", "d"])
    assert not splits["train"].intersection(splits["holdout"])


def test_reward_and_profile_hash_validation(tmp_path) -> None:
    deck = tmp_path / "deck.csv"
    deck.write_text("1\n")
    digest = sha256(deck.read_bytes()).hexdigest()
    profile = PolicyProfile("deck", str(deck), digest, "rfl-1", "v1", {"win_now": 100.0})
    profile.validate("deck", deck)
    assert hybrid_reward("win", before={"prize_count": 6}, after={"prize_count": 5}).total > 1
    broken = tmp_path / "broken.yaml"
    broken.write_text("not: a profile")
    assert load_profile(broken, active_deck_id="deck", active_deck_path=deck) is None
