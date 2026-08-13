"""Audit Supporter and Honchkrow turn-planning patterns in CABT traces."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, TextIO

ARIANA = 1216
PETREL = 1219
PROTON = 1220
FACTORY = 1257
POKE_PAD = 1152
TRANSCEIVER = 1134
MURKROW = 463
HONCHKROW = 891
ROCKET_ENERGY = 15
IGNITION_ENERGY = 17
ROCKET_FEATHERS = 1285
TORMENT = 653
ROCKET_SUPPORTERS = {1216, 1217, 1218, 1219, 1220}
ROCKET_POKEMON = {463, 891, 473, 474, 414}
DECLARED_COUNTS = {MURKROW: 4, HONCHKROW: 3, 473: 2, 474: 1, 414: 2}


def _open_text(path: Path) -> TextIO:
    """Open plain JSONL or gzip-compressed JSONL as text."""
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open(encoding="utf-8")


def _card_id(value: Any) -> int:
    """Return a card identifier from a public card or option mapping."""
    if not isinstance(value, Mapping):
        return 0
    raw = value.get("cardId", value.get("id", 0))
    try:
        return int(raw or 0)
    except (TypeError, ValueError):
        return 0


def _selected_options(event: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Resolve selected options without changing simulator indices."""
    options = event.get("options", [])
    selected = event.get("selected_indices", [])
    if not isinstance(options, list) or not isinstance(selected, list):
        return []
    return [
        options[index]
        for index in selected
        if isinstance(index, int)
        and 0 <= index < len(options)
        and isinstance(options[index], Mapping)
    ]


def _option_card_id(event: Mapping[str, Any], option: Mapping[str, Any]) -> int:
    """Resolve an option's card through its public CABT area and index."""
    direct = _card_id(option)
    if direct:
        return direct
    state = event.get("state_before", {})
    if not isinstance(state, Mapping):
        return 0
    players = state.get("players", [])
    if not isinstance(players, list):
        return 0
    owner = option.get("playerIndex", state.get("yourIndex", 0))
    if not isinstance(owner, int) or not 0 <= owner < len(players):
        return 0
    player = players[owner]
    if not isinstance(player, Mapping):
        return 0
    option_type = option.get("type")
    area = 2 if option_type in {7, 8, 9} else option.get("area")
    index = 0 if option_type == 13 else option.get("index")
    if not isinstance(index, int):
        return 0
    zones: dict[int, Any] = {
        2: player.get("hand"),
        3: player.get("discard"),
        4: player.get("active"),
        5: player.get("bench"),
        6: player.get("prize"),
        7: state.get("stadium"),
        12: state.get("looking"),
    }
    zone = zones.get(area) if isinstance(area, int) else None
    if not isinstance(zone, list) or not 0 <= index < len(zone):
        return 0
    return _card_id(zone[index])


def _players(event: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    """Return actor and opponent public states for one event."""
    state = event.get("state_before", {})
    if not isinstance(state, Mapping):
        return {}, {}
    players = state.get("players", [])
    if not isinstance(players, list) or len(players) < 2:
        return {}, {}
    your_index = int(state.get("yourIndex", 0) or 0)
    own = players[your_index] if isinstance(players[your_index], Mapping) else {}
    opponent_index = 1 - your_index
    opponent = players[opponent_index] if isinstance(players[opponent_index], Mapping) else {}
    return own, opponent


def _pokemon(player: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Return visible Active and Bench Pokémon."""
    result: list[Mapping[str, Any]] = []
    for key in ("active", "bench"):
        values = player.get(key, [])
        if isinstance(values, list):
            result.extend(value for value in values if isinstance(value, Mapping))
    return result


def _hand(player: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Return the actor-visible hand."""
    value = player.get("hand", [])
    return [card for card in value if isinstance(card, Mapping)] if isinstance(value, list) else []


def _ariana_marginal_draw(own: Mapping[str, Any]) -> int:
    """Estimate Ariana's public marginal draw after she leaves hand."""
    pokemon = _pokemon(own)
    target = 8 if pokemon and all(_card_id(card) in ROCKET_POKEMON for card in pokemon) else 5
    hand_count = int(own.get("handCount", len(_hand(own))) or 0)
    return max(0, target - max(0, hand_count - 1))


def _copies_remaining(own: Mapping[str, Any], card_id: int) -> int:
    """Count declared copies absent from visible zones."""
    known = sum(_card_id(card) == card_id for card in _pokemon(own))
    for key in ("hand", "discard", "prize"):
        cards = own.get(key, [])
        if isinstance(cards, list):
            known += sum(_card_id(card) == card_id for card in cards)
    return max(0, DECLARED_COUNTS.get(card_id, 0) - known)


def _proton_setup_useful(own: Mapping[str, Any], state: Mapping[str, Any] | None = None) -> bool:
    """Return whether public state proves a Proton board-development gain."""
    pokemon = _pokemon(own)
    bench = own.get("bench", [])
    bench_count = len(bench) if isinstance(bench, list) else 0
    bench_max = int(own.get("benchMax", 5) or 5)
    target = _copies_remaining(own, MURKROW) > 0 or _copies_remaining(own, 473) > 0
    first_own_turn = False
    if state is not None:
        turn = int(state.get("turn", 0) or 0)
        your_index = int(state.get("yourIndex", 0) or 0)
        first_player = int(state.get("firstPlayer", 0) or 0)
        own_turn = (turn + 1) // 2 if your_index == first_player else turn // 2
        first_own_turn = own_turn == 1
    return target and bench_count < bench_max and (len(pokemon) < 2 or first_own_turn)


def _energy_units(active: Mapping[str, Any]) -> int:
    """Conservatively count public units usable for Rocket Feathers."""
    energy_cards = active.get("energyCards", [])
    if isinstance(energy_cards, list) and energy_cards:
        return sum(
            2 if _card_id(card) == ROCKET_ENERGY else 3 if _card_id(card) == IGNITION_ENERGY else 1
            for card in energy_cards
        )
    energies = active.get("energies", [])
    return len(energies) if isinstance(energies, list) else 0


def _poke_pad_ko_available(event: Mapping[str, Any]) -> bool:
    """Require public search, evolution, Energy, and lethal-damage facts."""
    own, opponent = _players(event)
    active_values = own.get("active", [])
    target_values = opponent.get("active", [])
    if not isinstance(active_values, list) or not active_values:
        return False
    if not isinstance(target_values, list) or not target_values:
        return False
    active = active_values[0]
    target = target_values[0]
    if not isinstance(active, Mapping) or not isinstance(target, Mapping):
        return False
    options = event.get("options", [])
    if not isinstance(options, list):
        return False
    option_ids = {
        _option_card_id(event, option)
        for option in options
        if isinstance(option, Mapping) and option.get("type") == 7
    }
    supporters = sum(_card_id(card) in ROCKET_SUPPORTERS for card in _hand(own))
    return bool(
        POKE_PAD in option_ids
        and _card_id(active) == MURKROW
        and not bool(active.get("appearThisTurn", False))
        and _copies_remaining(own, HONCHKROW) > 0
        and _energy_units(active) >= 2
        and supporters * 60 >= int(target.get("hp", 0) or 0) > 0
    )


def audit_matches(matches: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Count target patterns and retain bounded factual examples."""
    counters: Counter[str] = Counter()
    examples: dict[str, list[dict[str, Any]]] = {}

    def record(
        name: str, match: Mapping[str, Any], event_index: int, event: Mapping[str, Any]
    ) -> None:
        counters[name] += 1
        bucket = examples.setdefault(name, [])
        if len(bucket) < 10:
            bucket.append(
                {
                    "match_id": match.get("match_id"),
                    "event_index": event_index,
                    "turn": (event.get("state_before") or {}).get("turn"),
                    "selected_indices": event.get("selected_indices", []),
                }
            )

    match_count = 0
    for match in matches:
        match_count += 1
        events = match.get("events", [])
        if not isinstance(events, list):
            continue
        transceiver_pending = False
        for event_index, event in enumerate(events):
            if not isinstance(event, Mapping):
                continue
            own, _ = _players(event)
            state = event.get("state_before", {})
            state = state if isinstance(state, Mapping) else {}
            selected = _selected_options(event)
            selected_ids = {_option_card_id(event, option) for option in selected}
            selected_play_ids = {
                _option_card_id(event, option) for option in selected if option.get("type") == 7
            }
            options = event.get("options", [])
            playable_ids = {
                _option_card_id(event, option)
                for option in options
                if isinstance(options, list)
                and isinstance(option, Mapping)
                and option.get("type") == 7
            }
            marginal = _ariana_marginal_draw(own)
            hand_ids = {_card_id(card) for card in _hand(own)}
            if ARIANA in selected_play_ids:
                counters["ariana_plays"] += 1
                if marginal <= 1:
                    record("ariana_draw_at_most_one", match, event_index, event)
                if PROTON in hand_ids and _proton_setup_useful(own, state):
                    record("ariana_with_required_proton", match, event_index, event)
            factory_active = any(
                _card_id(card) == FACTORY
                for card in (event.get("state_before") or {}).get("stadium", [])
                if isinstance(card, Mapping)
            )
            petrel_factory = (
                marginal <= 1 and {ARIANA, PETREL}.issubset(playable_ids) and not factory_active
            )
            if petrel_factory:
                counters["petrel_factory_opportunities"] += 1
                if PETREL in selected_play_ids:
                    counters["petrel_factory_conversions"] += 1
                if ARIANA in selected_play_ids:
                    record("ariana_over_petrel_factory", match, event_index, event)
            if transceiver_pending:
                if selected_ids & ROCKET_SUPPORTERS:
                    target = next(iter(selected_ids & ROCKET_SUPPORTERS))
                    counters[f"transceiver_target_{target}"] += 1
                    if target == PROTON and not _proton_setup_useful(own, state):
                        record("late_proton_without_gain", match, event_index, event)
                transceiver_pending = False
            if TRANSCEIVER in selected_play_ids:
                transceiver_pending = True
            poke_pad_ko = _poke_pad_ko_available(event)
            if poke_pad_ko:
                counters["poke_pad_ko_opportunities"] += 1
                if TORMENT in {int(option.get("attackId", 0) or 0) for option in selected}:
                    record("torment_with_proven_poke_pad_ko", match, event_index, event)
    return {"matches": match_count, "counters": dict(counters), "examples": examples}


def _load_matches(path: Path) -> Iterable[Mapping[str, Any]]:
    """Yield serialized match records from JSONL input."""
    with _open_text(path) as stream:
        for line in stream:
            value = json.loads(line)
            if isinstance(value, Mapping):
                yield value


def audit_ledger_records(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Audit decoded Honchkrow decision-ledger JSONL records.

    The remote decision-log format contains one compressed ledger expansion per
    line rather than the replay-event envelope consumed by ``audit_matches``.
    This path preserves the public ledger facts without inventing missing board
    state or treating replay identifiers as policy inputs.
    """
    count = 0
    max_turn_roto = 0
    max_revealed = 0
    max_selected = 0
    ariana_plays = 0
    transceiver_targets: Counter[str] = Counter()
    deckout_vetoes = 0
    for record in records:
        decision = record.get("decision", record)
        if not isinstance(decision, Mapping):
            continue
        count += 1
        ledger = decision.get("turn_ledger", {})
        if not isinstance(ledger, Mapping):
            continue
        max_turn_roto = max(max_turn_roto, int(ledger.get("roto_sticks_played", 0) or 0))
        max_revealed = max(max_revealed, int(ledger.get("roto_supporters_revealed", 0) or 0))
        max_selected = max(max_selected, int(ledger.get("roto_supporters_selected", 0) or 0))
        ariana_plays = max(ariana_plays, int(ledger.get("ariana_plays", 0) or 0))
        target = ledger.get("transceiver_target")
        if target is not None:
            transceiver_targets[str(target)] += 1
        if ledger.get("deckout_veto_reason"):
            deckout_vetoes += 1
    return {
        "records": count,
        "counters": {
            "roto_sticks_played_max": max_turn_roto,
            "roto_supporters_revealed_max": max_revealed,
            "roto_supporters_selected_max": max_selected,
            "roto_zero_over_zero_consistent": bool(
                max_turn_roto > 0 and max_revealed == 0 and max_selected == 0
            ),
            "ariana_plays_max": ariana_plays,
            "transceiver_targets": dict(transceiver_targets),
            "deckout_veto_records": deckout_vetoes,
        },
        "evidence_boundary": "decoded_public_decision_ledger_only",
    }


def main() -> int:
    """Run the audit and write a reproducible JSON report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = list(_load_matches(args.trace))
    if records and isinstance(records[0].get("decision"), Mapping):
        report = audit_ledger_records(records)
    else:
        report = audit_matches(records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["counters"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
