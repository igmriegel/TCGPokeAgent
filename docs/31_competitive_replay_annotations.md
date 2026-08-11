# Competitive replay annotations

**Status:** `FOUNDATION IMPLEMENTED`

This workflow records post-hoc human reviews of automated Kaggle
agent-versus-agent matches. It is separate from human gameplay demonstrations:
the engine chose every recorded action, while a reviewer later explains a
probable mistake or loss cause.

## Provenance contract

Every `competitive-gameplay-review-v1` record preserves:

- the Kaggle episode and immutable replay SHA-256;
- `actor_type: agent`;
- `review_kind: post_hoc_human_review`;
- the reviewed engine side and final outcome;
- the reviewer's original feedback;
- a separate technical interpretation;
- normalized cause and reason tags;
- confidence;
- intended follow-up and an optional `supersedes` link for corrections;
- exact replay step, turn, legal options, recorded action, and preferred
  alternative;
- only the actor-visible hand and public board snapshot.

The preferred action is review evidence, not an automatic optimal-play label.
Post-hoc outcome knowledge must not be inserted into runtime `GameState` or
used as an observation feature.

## Inspect a replay

List decisions where a card was in the reviewed engine's hand while its Bench
was empty:

```bash
uv run --frozen python -m src.data.gameplay_annotations inspect \
  --replay data/raw/kaggle/replays/remote/<submission_id>/episode-88879568-replay.json \
  --player 0 \
  --card-id 721 \
  --empty-bench
```

The output resolves original simulator indices to cards, attacks, and option
types without renumbering them.

## Add a review

```bash
uv run --frozen python -m src.data.gameplay_annotations add \
  --replay data/raw/kaggle/replays/remote/<submission_id>/episode-88879568-replay.json \
  --output data/annotations/gameplay_reviews/v1/annotations.jsonl \
  --annotation-id KGR-88879568-002 \
  --supersedes KGR-88879568-001 \
  --player 0 \
  --preferred 72:1 \
  --preferred 81:1 \
  --preferred 100:1 \
  --verdict mistake \
  --cause sequencing \
  --tag BOARD_PRESENCE \
  --tag EMPTY_BENCH \
  --tag SECOND_ATTACKER \
  --tag DEVELOP_BEFORE_ATTACK \
  --tag MISSED_LEGAL_DEVELOPMENT \
  --feedback "O erro é não colocar o Pokémon no banco antes de atacar." \
  --follow-up "Jogar o Pokémon e atacar no próximo MAIN." \
  --confidence 1.0
```

The append-only store rejects illegal preferred indices and duplicate
annotation identifiers. One match-level review may link multiple decisions
when the same strategic mistake recurs.

## Episode 88879568

Annotation `KGR-88879568-002` supersedes the initial interpretation and verifies
three missed development decisions:

| Step | Turn | Board | Legal development | Engine action |
|---:|---:|---|---|---|
| 72 | 11 | empty Bench, Active at 120 HP | play Kyogre at index 1 | Hammer-lanche at index 3 |
| 81 | 13 | empty Bench, Active at 80 HP | play Kyogre at index 1 | Hammer-lanche at index 5 |
| 100 | 15 | empty Bench, Active at 80 HP | play either Kyogre | Frost Barrier at index 8 |

The attack itself is not the mistake: attacking is better than passing. The
correct sequence was to play Kyogre, receive the next `MAIN` prompt, and then
attack. The earliest verified mistake is therefore the omitted development at
step 72. The engine repeated that omission twice and finished the match
without a replacement Pokémon.

This is direct evidence for the existing continuous-board-development backlog;
it does not by itself prove that every loss with an empty Bench has the same
cause. Corrections append a new record with `supersedes`; they never erase the
review history.
