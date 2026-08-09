"""Decision-level audit helpers for the Honchkrow/Porygon deck."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from src.agents.honchkrow_porygon import (
    DECEIT,
    HACKING,
    R_COMMAND,
    ROCKET_FEATHERS,
    TORMENT,
)

HAMMER_IN = 1286
MEGA_ABOMASNOW = 723
ROCKET_SUPPORTERS = {1216, 1217, 1218, 1219, 1220}


class OpportunityCategory:
    """Stable categories emitted by the attack-opportunity audit."""

    CORRECT_R_COMMAND_KO = "CORRECT_R_COMMAND_KO"
    R_COMMAND_NOT_READY = "R_COMMAND_NOT_READY"
    MISSED_LETHAL_ROCKET_FEATHERS = "MISSED_LETHAL_ROCKET_FEATHERS"
    MISSED_LETHAL_HAMMER = "MISSED_LETHAL_HAMMER"
    PARTIAL_DAMAGE_WITH_NEXT_TURN_KO = "PARTIAL_DAMAGE_WITH_NEXT_TURN_KO"
    PARTIAL_DAMAGE_WITHOUT_KO_HORIZON = "PARTIAL_DAMAGE_WITHOUT_KO_HORIZON"
    END_WITH_LETHAL_LINE = "END_WITH_LETHAL_LINE"
    RETREAT_WITHOUT_CONVERSION = "RETREAT_WITHOUT_CONVERSION"
    DECK_OUT_AFTER_CONSUMPTION = "DECK_OUT_AFTER_CONSUMPTION"
    UNRESOLVED_SEQUENCE = "UNRESOLVED_SEQUENCE"
    PARTIAL_LINE_BLOCKED_BEFORE_ATTACK = "PARTIAL_LINE_BLOCKED_BEFORE_ATTACK"
    PARTIAL_LINE_UNDERFUNDED = "PARTIAL_LINE_UNDERFUNDED"
    PARTIAL_LINE_ATTACKER_KO = "PARTIAL_LINE_ATTACKER_KO"
    PARTIAL_LINE_NO_NEXT_ATTACK = "PARTIAL_LINE_NO_NEXT_ATTACK"
    PARTIAL_LINE_NEXT_ATTACK_KO = "PARTIAL_LINE_NEXT_ATTACK_KO"
    LETHAL_LINE_NOT_SELECTED = "LETHAL_LINE_NOT_SELECTED"
    NON_DAMAGE_ATTACK_WITH_DAMAGE_ALTERNATIVE = "NON_DAMAGE_ATTACK_WITH_DAMAGE_ALTERNATIVE"
    DECK_OUT_AFTER_UNRESOLVED_LINE = "DECK_OUT_AFTER_UNRESOLVED_LINE"
    RETREAT_WITHOUT_KO_CONVERSION = "RETREAT_WITHOUT_KO_CONVERSION"


@dataclass(frozen=True, slots=True)
class OpportunityAudit:
    """Audit one complete Rocket attack opportunity, including setup prompts.

    All indices remain the simulator's original option indices.  The audit is
    deliberately factual: it derives outcomes from public before/after
    snapshots and never treats a discard prompt as a completed attack.
    """

    episode_id: int
    opportunity_id: int
    target_card_id: int | None
    target_hp: int
    attacker_card_id: int | None
    attacker_energy: int
    hand_supporters: int
    discard_supporters: int
    expected_damage: int
    observed_damage: int
    lethal_line_available: bool
    line_chosen: str
    result: str
    category: str
    decision_indices: tuple[int, ...] = ()
    original_indices: tuple[int, ...] = ()
    reasons: tuple[str, ...] = ()
    contexts: tuple[str, ...] = ()
    planned_damage: int = 0
    selected_supporters: int = 0
    target_hp_before: int = 0
    target_hp_after: int = 0
    attacker_survived: bool | None = None
    next_attack_available: bool = False
    next_attack_ko: bool = False
    deck_reserve_before: int = 0
    deck_reserve_after: int = 0
    sequence_result: str = ""
    failure_category: str = ""


def _as_int(value: Any, default: int = 0) -> int:
    """Convert a value to an integer without allowing malformed traces to fail."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _option_type(option: Mapping[str, Any]) -> str:
    """Return a normalized option type for mixed CABT traces."""
    value = option.get("type", "")
    if isinstance(value, int):
        return {
            7: "PLAY",
            8: "ATTACH",
            9: "EVOLVE",
            10: "ABILITY",
            11: "DISCARD",
            12: "RETREAT",
            13: "ATTACK",
            14: "END",
        }.get(value, str(value))
    return str(value).upper()


def _attack_id(option: Mapping[str, Any]) -> int | None:
    """Extract an attack identifier from a trace option."""
    value = option.get("attackId", option.get("attack_id"))
    return _as_int(value, -1) if value is not None else None


def _rocket_feathers_supporters_for_ko(target_card_id: int | None, target_hp: int) -> int:
    """Return the Supporter count required for a Rocket Feathers KO."""
    if target_card_id == MEGA_ABOMASNOW:
        return 6
    return max(1, (max(0, target_hp) + 59) // 60)


def _r_command_supporters_for_ko(target_card_id: int | None, target_hp: int) -> int:
    """Return the discarded Supporter count required for an R Command KO."""
    if target_card_id == MEGA_ABOMASNOW:
        return 18
    return max(1, (max(0, target_hp) + 19) // 20)


def _selected_options(decision: Any) -> list[Mapping[str, Any]]:
    """Resolve selected options while preserving their original indices."""
    options = getattr(decision, "options", None)
    selected = getattr(decision, "selected_indices", None)
    if isinstance(decision, Mapping):
        options = decision.get("options", options)
        selected = decision.get("selected_indices", selected)
    if not isinstance(options, list) or not isinstance(selected, list):
        return []
    return [
        option
        for index in selected
        if 0 <= _as_int(index, -1) < len(options)
        and isinstance((option := options[_as_int(index, -1)]), Mapping)
    ]


def audit_opportunities(matches: Iterable[Any]) -> list[OpportunityAudit]:
    """Group decision traces into complete Rocket attack opportunities.

    ``matches`` accepts ``MatchRecord`` instances or serialized mappings. A
    group starts at a Rocket attack or its discard preparation and ends at the
    next attack, a terminal transition, or a context change that proves the
    line was abandoned.
    """
    audits: list[OpportunityAudit] = []
    opportunity_id = 0
    for episode_id, match in enumerate(matches):
        decisions = getattr(match, "decisions", None)
        if isinstance(match, Mapping):
            decisions = match.get("decisions", match.get("events", decisions))
        if not isinstance(decisions, list):
            continue
        pending: list[Any] = []
        pending_attack_turn: int | None = None
        for decision in decisions + [None]:
            if decision is None:
                if pending:
                    audits.append(_build_opportunity(episode_id, opportunity_id, pending, []))
                    opportunity_id += 1
                continue
            options = getattr(decision, "options", []) if decision is not None else []
            if isinstance(decision, Mapping):
                options = decision.get("options", [])
            selected = _selected_options(decision)
            attack_options = [
                option
                for option in options
                if isinstance(option, Mapping) and _attack_id(option) is not None
            ]
            selected_attacks = [option for option in selected if _attack_id(option) is not None]
            is_rocket = any(
                _attack_id(option) in {ROCKET_FEATHERS, R_COMMAND, HAMMER_IN}
                for option in selected_attacks
            )
            is_setup = any(
                _option_type(option) in {"DISCARD", "DISCARD_CARD_OR_ATTACHED_CARD"}
                for option in selected
            )
            missed_end = any(_option_type(option) == "END" for option in selected) and any(
                _attack_id(option) in {ROCKET_FEATHERS, R_COMMAND, HAMMER_IN}
                for option in attack_options
            )
            decision_turn = _as_int(
                decision.get("turn")
                if isinstance(decision, Mapping)
                else getattr(decision, "turn", None),
                -1,
            )
            if (
                pending
                and pending_attack_turn is not None
                and decision_turn >= 0
                and decision_turn != pending_attack_turn
            ):
                audits.append(_build_opportunity(episode_id, opportunity_id, pending, []))
                opportunity_id += 1
                pending = []
                pending_attack_turn = None
            has_pending_attack = any(
                any(
                    _attack_id(option) in {ROCKET_FEATHERS, R_COMMAND, HAMMER_IN}
                    for option in _selected_options(item)
                )
                for item in pending
            )
            if pending and is_rocket and has_pending_attack:
                audits.append(_build_opportunity(episode_id, opportunity_id, pending, []))
                opportunity_id += 1
                pending = []
                pending_attack_turn = None
            if is_rocket or is_setup or missed_end or pending:
                pending.append(decision)
                if is_rocket:
                    pending_attack_turn = decision_turn if decision_turn >= 0 else None
                    has_pending_attack = True
            effects = (
                decision.get("transition", {})
                if isinstance(decision, Mapping)
                else getattr(decision, "transition", {})
            )
            if (
                has_pending_attack
                and isinstance(effects, Mapping)
                and (bool(effects.get("target_ko")) or _as_int(effects.get("target_damage"), 0) > 0)
            ):
                audits.append(
                    _build_opportunity(episode_id, opportunity_id, pending, selected_attacks)
                )
                opportunity_id += 1
                pending = []
                pending_attack_turn = None
    return audits


def _build_opportunity(
    episode_id: int,
    opportunity_id: int,
    decisions: list[Any],
    selected_attacks: list[Mapping[str, Any]],
) -> OpportunityAudit:
    """Build one audit record from grouped setup and attack decisions."""
    if not selected_attacks:
        selected_attacks = [
            option
            for decision in decisions
            for option in _selected_options(decision)
            if _attack_id(option) is not None
        ]
    first = decisions[0]
    before = getattr(first, "telemetry_before", {}) if first is not None else {}
    if isinstance(first, Mapping):
        before = first.get("telemetry_before", first.get("state_before", {}))
    before = before if isinstance(before, Mapping) else {}
    opponent = before.get("opponent", {}) if isinstance(before.get("opponent", {}), Mapping) else {}
    target = opponent.get("active", {}) if isinstance(opponent.get("active", {}), Mapping) else {}
    own = before.get("own", {}) if isinstance(before.get("own", {}), Mapping) else {}
    chosen = selected_attacks[0] if selected_attacks else {}
    chosen_id = _attack_id(chosen)
    hand = _as_int(own.get("hand_supporters"), 0)
    discard = _as_int(own.get("discard_supporters"), 0)
    target_hp = _as_int(target.get("hp"), 0)
    all_options = [
        option
        for decision in decisions
        for option in (
            getattr(decision, "options", [])
            if not isinstance(decision, Mapping)
            else decision.get("options", [])
        )
        if isinstance(option, Mapping)
    ]
    selected_types = {
        _option_type(option) for decision in decisions for option in _selected_options(decision)
    }
    if chosen_id == ROCKET_FEATHERS:
        expected = hand * 60
    elif chosen_id == R_COMMAND:
        expected = discard * 20
    elif chosen_id == HAMMER_IN:
        expected = 100
    else:
        expected = max(
            (_as_int(chosen.get(key)) for key in ("damage", "expectedDamage")), default=0
        )
    effects = getattr(decisions[-1], "transition", {}) if decisions else {}
    if isinstance(decisions[-1], Mapping):
        effects = decisions[-1].get("transition", {})
    effects = effects if isinstance(effects, Mapping) else {}
    observed = _as_int(effects.get("target_damage"), 0)
    after = getattr(decisions[-1], "telemetry_after", {}) if decisions else {}
    if isinstance(decisions[-1], Mapping):
        after = decisions[-1].get("telemetry_after", decisions[-1].get("state_after", {}))
    after = after if isinstance(after, Mapping) else {}
    after_opponent = (
        after.get("opponent", {}) if isinstance(after.get("opponent", {}), Mapping) else {}
    )
    after_target = (
        after_opponent.get("active", {})
        if isinstance(after_opponent.get("active", {}), Mapping)
        else {}
    )
    after_own = after.get("own", {}) if isinstance(after.get("own", {}), Mapping) else {}
    selected_supporters = sum(
        _as_int(option.get("cardId", option.get("card_id")), 0) in ROCKET_SUPPORTERS
        for decision in decisions
        for option in _selected_options(decision)
    )
    rocket_required = _rocket_feathers_supporters_for_ko(
        _as_int(target.get("card_id"), 0) or None, target_hp
    )
    r_command_required = _r_command_supporters_for_ko(
        _as_int(target.get("card_id"), 0) or None, target_hp
    )
    lethal = any(
        (_attack_id(option) == ROCKET_FEATHERS and hand >= rocket_required)
        or (_attack_id(option) == R_COMMAND and discard >= r_command_required)
        or (_attack_id(option) == HAMMER_IN and target_hp <= 100)
        for option in all_options
    )
    if chosen_id == R_COMMAND and discard >= 18 and bool(effects.get("target_ko")):
        category = OpportunityCategory.CORRECT_R_COMMAND_KO
    elif chosen_id == R_COMMAND and discard < 18:
        category = OpportunityCategory.R_COMMAND_NOT_READY
    elif "RETREAT" in selected_types and not bool(effects.get("target_ko")):
        category = OpportunityCategory.RETREAT_WITHOUT_CONVERSION
    elif not selected_attacks and "END" in selected_types and lethal:
        category = OpportunityCategory.END_WITH_LETHAL_LINE
    elif chosen_id != ROCKET_FEATHERS and any(
        _attack_id(option) == ROCKET_FEATHERS and hand >= rocket_required for option in all_options
    ):
        category = OpportunityCategory.MISSED_LETHAL_ROCKET_FEATHERS
    elif chosen_id != HAMMER_IN and any(
        _attack_id(option) == HAMMER_IN and target_hp <= 100 for option in all_options
    ):
        category = OpportunityCategory.MISSED_LETHAL_HAMMER
    elif chosen_id == ROCKET_FEATHERS and hand >= 6 and not bool(effects.get("target_ko")):
        remaining = max(0, target_hp - expected)
        horizon = remaining <= max(0, hand - 1) * 60 and _as_int(own.get("deck_count"), 0) > 2
        category = (
            OpportunityCategory.PARTIAL_DAMAGE_WITH_NEXT_TURN_KO
            if horizon
            else OpportunityCategory.PARTIAL_DAMAGE_WITHOUT_KO_HORIZON
        )
    elif chosen_id == ROCKET_FEATHERS and hand < rocket_required:
        category = OpportunityCategory.PARTIAL_LINE_UNDERFUNDED
    elif _as_int(own.get("deck_count"), 0) <= 0 and observed:
        category = OpportunityCategory.DECK_OUT_AFTER_CONSUMPTION
    elif selected_attacks:
        category = OpportunityCategory.UNRESOLVED_SEQUENCE
    else:
        category = OpportunityCategory.UNRESOLVED_SEQUENCE
    indices = tuple(
        _as_int(index)
        for decision in decisions
        for index in (
            getattr(decision, "selected_indices", [])
            if not isinstance(decision, Mapping)
            else decision.get("selected_indices", [])
        )
    )
    reasons = tuple(
        reason
        for decision in decisions
        for reason in (
            getattr(decision, "reasons", [])
            if not isinstance(decision, Mapping)
            else decision.get("reasons", [])
        )
    )
    contexts = tuple(
        str(getattr(decision, "context", ""))
        if not isinstance(decision, Mapping)
        else str(decision.get("context", ""))
        for decision in decisions
    )
    return OpportunityAudit(
        episode_id=episode_id,
        opportunity_id=opportunity_id,
        target_card_id=_as_int(target.get("card_id"), 0) or None,
        target_hp=target_hp,
        attacker_card_id=_as_int(
            (
                before.get("own", {}).get("active", {})
                if isinstance(before.get("own", {}), Mapping)
                else {}
            ).get("card_id"),
            0,
        )
        or None,
        attacker_energy=_as_int(
            (
                before.get("own", {}).get("active", {})
                if isinstance(before.get("own", {}), Mapping)
                else {}
            ).get("energy_count"),
            0,
        ),
        hand_supporters=hand,
        discard_supporters=discard,
        expected_damage=expected,
        observed_damage=observed,
        lethal_line_available=lethal,
        line_chosen=str(chosen_id or "none"),
        result="KO" if effects.get("target_ko") else "DAMAGE" if observed else "ABANDONED",
        category=category,
        decision_indices=tuple(
            getattr(decision, "decision_index", i)
            if not isinstance(decision, Mapping)
            else _as_int(decision.get("decision_index"), i)
            for i, decision in enumerate(decisions)
        ),
        original_indices=indices,
        reasons=reasons,
        contexts=contexts,
        planned_damage=expected,
        selected_supporters=selected_supporters,
        target_hp_before=target_hp,
        target_hp_after=_as_int(after_target.get("hp"), max(0, target_hp - observed)),
        attacker_survived=(not bool(effects.get("own_active_ko")) if effects else None),
        next_attack_available=bool(effects.get("next_attack_available", False)),
        next_attack_ko=bool(effects.get("next_attack_ko", False)),
        deck_reserve_before=_as_int(own.get("deck_count"), 0),
        deck_reserve_after=_as_int(after_own.get("deck_count"), 0),
        sequence_result=(
            "KO" if effects.get("target_ko") else "DAMAGE" if observed else "ABANDONED"
        ),
        failure_category=category
        if category
        not in {
            OpportunityCategory.CORRECT_R_COMMAND_KO,
        }
        else "",
    )


@dataclass(frozen=True, slots=True)
class DecisionEvidence:
    """Public evidence captured for one legal decision in a replay."""

    episode_id: int
    step_index: int
    turn: int
    context: int
    selected_indices: tuple[int, ...]
    legal_option_count: int
    active_card_id: int | None
    bench_card_ids: tuple[int, ...]
    supporter_ids_in_hand: tuple[int, ...]
    deck_count: int
    own_prizes: int
    opponent_prizes: int
    attack_id: int | None
    competing_attack_ids: tuple[int, ...]
    guaranteed_ko_available: bool
    disruption_without_damage: bool
    missed_post_draw_r_command: bool = False
    missed_ko: bool = False
    resource_waste: bool = False
    preventable_deck_out: bool = False
    opponent_active_card_id: int | None = None
    opponent_active_hp: int = 0
    rocket_supporters_in_discard: int = 0
    mega_abomasnow_partial_attack: bool = False


def _int(value: Any) -> int | None:
    """Convert a JSON value to an integer when possible."""
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


def _card_id(value: Any) -> int | None:
    """Extract a card ID from a card or option mapping."""
    if not isinstance(value, Mapping):
        return None
    return _int(value.get("cardId", value.get("id")))


def _option_attack_id(option: Mapping[str, Any]) -> int | None:
    """Extract an attack ID from a legal option."""
    return _int(option.get("attackId"))


def _player(observation: Mapping[str, Any], index: int) -> Mapping[str, Any]:
    """Return a player snapshot from an actor-visible observation."""
    current = observation.get("current", {})
    players = current.get("players", []) if isinstance(current, Mapping) else []
    player = players[index] if isinstance(players, list) and index < len(players) else {}
    return player if isinstance(player, Mapping) else {}


def decision_evidence(record: Mapping[str, Any]) -> DecisionEvidence:
    """Build decision evidence from one replay-decision JSON record."""
    observation = record.get("observation", {})
    if not isinstance(observation, Mapping):
        observation = {}
    current = observation.get("current", {})
    if not isinstance(current, Mapping):
        current = {}
    your_index = _int(current.get("yourIndex")) or 0
    opponent_index = 1 - your_index
    own = _player(observation, your_index)
    opponent = _player(observation, opponent_index)
    select = observation.get("select", {})
    if not isinstance(select, Mapping):
        select = {}
    options = select.get("option", [])
    options = options if isinstance(options, list) else []
    selected = record.get("selected_indices", [])
    selected_indices = (
        tuple(_int(index) or 0 for index in selected) if isinstance(selected, list) else ()
    )
    attack_ids = tuple(
        attack_id
        for attack_id in (
            _option_attack_id(option) for option in options if isinstance(option, Mapping)
        )
        if attack_id is not None
    )
    selected_attack_ids = tuple(
        _option_attack_id(options[index])
        for index in selected_indices
        if 0 <= index < len(options)
        and isinstance(options[index], Mapping)
        and _option_attack_id(options[index]) is not None
    )
    hand = own.get("hand") or []
    supporter_ids = (
        tuple(_card_id(card) for card in hand if _card_id(card) in {1216, 1217, 1218, 1219, 1220})
        if isinstance(hand, list)
        else ()
    )
    active = own.get("active") or []
    active_card_id = _card_id(active[0]) if isinstance(active, list) and active else None
    opponent_active = opponent.get("active") or []
    opponent_active_card_id = (
        _card_id(opponent_active[0])
        if isinstance(opponent_active, list) and opponent_active
        else None
    )
    opponent_active_hp = (
        _int(opponent_active[0].get("hp")) or 0
        if isinstance(opponent_active, list)
        and opponent_active
        and isinstance(opponent_active[0], Mapping)
        else 0
    )
    bench = own.get("bench") or []
    bench_ids = (
        tuple(
            card_id
            for card_id in (_card_id(card) for card in bench if isinstance(card, Mapping))
            if card_id is not None
        )
        if isinstance(bench, list)
        else ()
    )
    chosen_attack = selected_attack_ids[0] if selected_attack_ids else None
    damage_options = {
        _option_attack_id(option)
        for option in options
        if isinstance(option, Mapping)
        and _option_attack_id(option) is not None
        and (
            _int(option.get("damage"))
            or _int(option.get("expectedDamage"))
            or _int(option.get("ko"))
        )
    }
    disruptive = chosen_attack in {HACKING, DECEIT, TORMENT} and not damage_options.intersection(
        attack_ids
    )
    guaranteed_ko = any(
        isinstance(option, Mapping) and bool(option.get("ko", option.get("knockout", False)))
        for option in options
    )
    r_command_available = R_COMMAND in attack_ids
    selected_type = (
        options[selected_indices[0]].get("type")
        if selected_indices
        and 0 <= selected_indices[0] < len(options)
        and isinstance(options[selected_indices[0]], Mapping)
        else None
    )
    deck_count = _int(own.get("deckCount")) or 0
    discard = own.get("discard") or []
    rocket_supporters_in_discard = (
        sum(
            _card_id(card) in {1216, 1217, 1218, 1219, 1220}
            for card in discard
            if isinstance(card, Mapping)
        )
        if isinstance(discard, list)
        else 0
    )
    mega_abomasnow_partial_attack = bool(
        opponent_active_card_id == 723
        and (
            chosen_attack == ROCKET_FEATHERS
            and len(supporter_ids) < 6
            or chosen_attack == R_COMMAND
            and rocket_supporters_in_discard < 18
        )
    )
    return DecisionEvidence(
        episode_id=_int(record.get("episode_id")) or 0,
        step_index=_int(record.get("step_index")) or 0,
        turn=_int(current.get("turn")) or 0,
        context=_int(select.get("context")) or 0,
        selected_indices=selected_indices,
        legal_option_count=len(options),
        active_card_id=active_card_id,
        bench_card_ids=bench_ids,
        supporter_ids_in_hand=tuple(
            supporter_id for supporter_id in supporter_ids if supporter_id is not None
        ),
        deck_count=deck_count,
        own_prizes=len(own.get("prize") or []) if isinstance(own.get("prize"), list) else 0,
        opponent_prizes=len(opponent.get("prize") or [])
        if isinstance(opponent.get("prize"), list)
        else 0,
        attack_id=chosen_attack,
        competing_attack_ids=tuple(
            attack_id for attack_id in attack_ids if attack_id != chosen_attack
        ),
        guaranteed_ko_available=guaranteed_ko,
        disruption_without_damage=disruptive,
        missed_post_draw_r_command=r_command_available and chosen_attack not in {R_COMMAND, None},
        missed_ko=guaranteed_ko and chosen_attack not in attack_ids,
        resource_waste=chosen_attack == ROCKET_FEATHERS and not guaranteed_ko,
        preventable_deck_out=(deck_count <= 2 and selected_type == 14 and bool(attack_ids)),
        opponent_active_card_id=opponent_active_card_id,
        opponent_active_hp=opponent_active_hp,
        rocket_supporters_in_discard=rocket_supporters_in_discard,
        mega_abomasnow_partial_attack=mega_abomasnow_partial_attack,
    )


def load_decision_ledger(path: str | Path) -> list[DecisionEvidence]:
    """Load decision evidence from a JSONL replay-decision export."""
    ledger: list[DecisionEvidence] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            if isinstance(record, Mapping):
                ledger.append(decision_evidence(record))
    return ledger


def classify_loss(
    *,
    owner_deck_count: int,
    owner_field_count: int,
    owner_prizes: int,
    opponent_prizes: int,
    ledger: Iterable[DecisionEvidence] = (),
) -> str:
    """Classify a loss using terminal state and contextual decision evidence."""
    evidence = list(ledger)
    if owner_field_count == 0:
        return "DONK / BOARD_COLLAPSE"
    if any(item.preventable_deck_out for item in evidence):
        return "PREVENTABLE_DECK_OUT"
    if owner_deck_count == 0:
        return "DECK_OUT"
    if opponent_prizes == 0 or owner_prizes > opponent_prizes:
        return "PRIZE_RACE_LOSS"
    if any(item.disruption_without_damage for item in evidence):
        return "LOW_DAMAGE_OR_DISRUPTION"
    if any(item.mega_abomasnow_partial_attack for item in evidence):
        return "MEGA_ABOMASNOW_PARTIAL_ATTACK"
    if any(item.missed_post_draw_r_command for item in evidence):
        return "MISSED_POST_DRAW_R_COMMAND"
    if any(item.guaranteed_ko_available for item in evidence):
        return "MISSED_KO"
    return "UNDETERMINED"


def evidence_as_dict(evidence: DecisionEvidence) -> dict[str, Any]:
    """Serialize one evidence row for JSON reports."""
    return asdict(evidence)
