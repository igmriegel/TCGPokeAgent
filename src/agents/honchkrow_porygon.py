"""Deck-specific heuristic policy for the Honchkrow/Porygon deck."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from math import comb
from typing import Any

from src.agents.heuristic import (
    _CG_CATALOG,
    DecisionPhase,
    HeuristicAgent,
    SimpleHeuristicScorer,
)
from src.core import (
    Candidate,
    DeckDefinition,
    DeckProfile,
    GameState,
    OptionType,
    SelectContext,
    Selection,
)
from src.core.damage import calculate_damage, has_splashing_dodge_protection, types_equal
from src.ranking.features import SelectionFeatureExtractor

MURKROW = 463
HONCHKROW = 891
PORYGON = 473
PORYGON2 = 474
ARTICUNO = 414
FROSLASS = 104
GRIMMSNARL_EX = 648
ARIANA = 1216
ARCHER = 1217
GIOVANNI = 1218
PETREL = 1219
PROTON = 1220
POKE_PAD = 1152
TRANSCEIVER = 1134
ROTO_STICK = 1077
NIGHT_STRETCHER = 1097
ULTRA_BALL = 1121
TOOL_SCRAPPER = 1137
HEROS_CAPE = 1159
CYNTHIAS_POWER_WEIGHT = 1173
MIRACLE_HEADSET = 1109
FACTORY = 1257
SPIKEMUTH_GYM = 1259
ROCKET_ENERGY = 15
IGNITION_ENERGY = 17
ENHANCED_HAMMER = 1081
ROCKET_FEATHERS = 1285
R_COMMAND = 670
HACKING = 669
DECEIT = 652
TORMENT = 653
HAMMER_IN = 1286
ARTICUNO_ATTACK = 583
DREEPY = 119
DRAKLOAK = 120
DRAGAPULT_EX = 121
ABRA = 741
KADABRA = 742
ALAKAZAM = 743
ROTO_STICK_MAX_REVEAL_COUNT = 4
CANONICAL_POLICY_VARIANT = "expert_turn_loop"


class TurnObjective(StrEnum):
    """Ordered result that the policy commits to for one public turn."""

    WIN_NOW = "win_now"
    PREVENT_NO_POKEMON_LOSS = "prevent_no_pokemon_loss"
    HIGHEST_PRIZE_KO = "highest_prize_ko"
    BUILD_ATTACKER_AND_BOARD = "build_attacker_and_board"
    IMPROVE_RESOURCES = "improve_resources"
    ATTACK_OR_CONTROL = "attack_or_control"


class CanonicalTurnStage(StrEnum):
    """Ordered stages of the Owner-defined turn loop."""

    DEVELOP = "develop"
    SEARCH = "search"
    CALCULATE = "calculate"
    SUPPORTER = "supporter"
    FACTORY = "factory"
    ROTO = "roto"
    HEADSET = "headset"
    ATTACK = "attack"


@dataclass(frozen=True, slots=True)
class BoardSetupPlan:
    """Public assessment of whether the current board still needs development."""

    productive: bool
    missing_roles: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class RecoveryPlan:
    """Public assessment of one recovery line and its same-turn conversion."""

    productive: bool
    recovered_cards: tuple[int, ...] = ()
    reason: str = ""
    deferred_petrel_reason: str = ""


@dataclass(slots=True)
class TurnTacticalLedger:
    """Public, turn-scoped tactical evidence for the dedicated policy.

    The engine presents one decision at a time.  This ledger therefore joins
    the public snapshots from a turn without inventing hidden cards or state.
    """

    turn: int = 0
    own_turn: int = 0
    turn_action_count: int = 0
    first_own_turn: bool = False
    objective: str = ""
    stage: str = "observe"
    previous_stage: str = ""
    replans: int = 0
    last_replan_reason: str = ""
    last_replan_previous_stage: str = ""
    last_replan_new_stage: str = ""
    supporters_in_hand: int = 0
    supporters_in_discard: int = 0
    effective_supporters_in_hand: int = 0
    supporters_needed_for_ko: int = 0
    rocket_feathers_damage: int = 0
    r_command_damage: int = 0
    active_attacker_card_id: int | None = None
    bench_attacker_card_id: int | None = None
    active_energy_units: int = 0
    energy_cards_in_hand: int = 0
    energy_attachable: bool = False
    deck_reserve: int = 0
    pre_draw_ko_candidates: tuple[int, ...] = ()
    post_draw_ko_candidates: tuple[int, ...] = ()
    potential_damage: dict[int, int] = field(default_factory=dict)
    chosen_attacker: int | None = None
    chosen_target: int | None = None
    draw_sequence: list[str] = field(default_factory=list)
    resource_guard: str = ""
    deck_risk: str = "safe"
    roto_sticks_played: int = 0
    roto_supporters_revealed: int = 0
    roto_supporters_selected: int = 0
    roto_damage_acquired: int = 0
    roto_preserved_reason: str = ""
    roto_post_supporter_lethal_attempt: bool = False
    roto_post_supporter_required: int = 0
    roto_post_supporter_outcome: str = ""
    transceiver_proton_in_hand: bool = False
    transceiver_target: int | None = None
    transceiver_rejected_target: int | None = None
    transceiver_lethal_exception: bool = False
    transceiver_objective: str = ""
    ariana_opportunities: int = 0
    ariana_plays: int = 0
    ariana_marginal_draw: int = 0
    ariana_supporters_in_hand: int = 0
    ariana_with_required_proton: int = 0
    petrel_factory_opportunities: int = 0
    petrel_factory_conversions: int = 0
    poke_pad_ko_opportunities: int = 0
    poke_pad_ko_conversions: int = 0
    poke_pad_ko_misses: int = 0
    torment_with_superior_line: int = 0
    no_pokemon_risk: bool = False
    supporter_played: int | None = None
    second_supporter_attempts: int = 0
    rocket_planned_damage: int = 0
    rocket_supporters_needed: int = 0
    rocket_supporters_available: int = 0
    rocket_supporters_discarded: int = 0
    rocket_supporters_preserved: int = 0
    lethal_lines_executed: int = 0
    lethal_lines_missed: int = 0
    lethal_lines_converted: int = 0
    miracle_headsets_played: int = 0
    miracle_supporters_recovered: int = 0
    canonical_exception: str = ""
    canonical_violations: int = 0
    factory_effects_activated: int = 0
    headset_reason: str = ""
    end_options_visible: int = 0
    end_with_productive_line: int = 0
    end_only_after_filter: int = 0
    unresolved_obligations: tuple[str, ...] = ()
    next_attacker_serial: int | None = None
    ariana_retained_cards: dict[int, str] = field(default_factory=dict)
    r_command_required_damage: int = 0
    r_command_supporter_deficit: int = 0
    ultra_ball_supporter_discards: int = 0
    ultra_ball_r_command_line: str = ""
    froslass_count: int = 0
    froslass_ping: int = 0
    archer_veto_reason: str = ""
    headset_recovery_reason: str = ""
    setup_guard_reason: str = ""
    giovanni_pivot_reason: str = ""
    target_priority_reason: str = ""
    chosen_target_prize_value: int = 0
    night_stretcher_priority_reason: str = ""
    r_command_projected_supporters: int = 0
    r_command_projected_damage: int = 0
    headset_ariana_recovery: bool = False
    development_obligations_pending: tuple[str, ...] = ()
    recovery_plan_reason: str = ""
    recovery_plan_cards: tuple[int, ...] = ()
    deferred_petrel_reason: str = ""
    end_reason: str = ""
    heros_cape_scrapped: bool = False
    public_line_evaluations: list[dict[str, Any]] = field(default_factory=list)
    search_plan_objective: str = ""
    search_resource_used_this_turn: int | None = None
    proton_gain_remaining: int = 0
    ariana_already_available: bool = False
    petrel_reserved: bool = False
    best_draw_sequence: tuple[str, ...] = ()
    energy_attachment_reason: str = ""
    energy_veto_threat: str = ""
    giovanni_line: str = ""
    ariana_petrel_comparison: str = ""
    archer_line_comparison: str = ""
    headset_preservation_reason: str = ""
    end_veto_reason: str = ""

    def reset(self, turn: int) -> None:
        """Clear evidence when the public turn changes."""
        self.turn = turn
        self.own_turn = 0
        self.turn_action_count = 0
        self.first_own_turn = False
        self.objective = ""
        self.stage = "observe"
        self.previous_stage = ""
        self.replans = 0
        self.last_replan_reason = ""
        self.last_replan_previous_stage = ""
        self.last_replan_new_stage = ""
        self.supporters_in_hand = 0
        self.supporters_in_discard = 0
        self.effective_supporters_in_hand = 0
        self.supporters_needed_for_ko = 0
        self.rocket_feathers_damage = 0
        self.r_command_damage = 0
        self.active_attacker_card_id = None
        self.bench_attacker_card_id = None
        self.active_energy_units = 0
        self.energy_cards_in_hand = 0
        self.energy_attachable = False
        self.deck_reserve = 0
        self.pre_draw_ko_candidates = ()
        self.post_draw_ko_candidates = ()
        self.potential_damage.clear()
        self.chosen_attacker = None
        self.chosen_target = None
        self.draw_sequence.clear()
        self.resource_guard = ""
        self.deck_risk = "safe"
        self.roto_sticks_played = 0
        self.roto_supporters_revealed = 0
        self.roto_supporters_selected = 0
        self.roto_damage_acquired = 0
        self.roto_preserved_reason = ""
        self.roto_post_supporter_lethal_attempt = False
        self.roto_post_supporter_required = 0
        self.roto_post_supporter_outcome = ""
        self.transceiver_proton_in_hand = False
        self.transceiver_target = None
        self.transceiver_rejected_target = None
        self.transceiver_lethal_exception = False
        self.transceiver_objective = ""
        self.ariana_opportunities = 0
        self.ariana_plays = 0
        self.ariana_marginal_draw = 0
        self.ariana_supporters_in_hand = 0
        self.ariana_with_required_proton = 0
        self.petrel_factory_opportunities = 0
        self.petrel_factory_conversions = 0
        self.poke_pad_ko_opportunities = 0
        self.poke_pad_ko_conversions = 0
        self.poke_pad_ko_misses = 0
        self.torment_with_superior_line = 0
        self.no_pokemon_risk = False
        self.supporter_played = None
        self.second_supporter_attempts = 0
        self.rocket_planned_damage = 0
        self.rocket_supporters_needed = 0
        self.rocket_supporters_available = 0
        self.rocket_supporters_discarded = 0
        self.rocket_supporters_preserved = 0
        self.lethal_lines_executed = 0
        self.lethal_lines_missed = 0
        self.lethal_lines_converted = 0
        self.miracle_headsets_played = 0
        self.miracle_supporters_recovered = 0
        self.canonical_exception = ""
        self.canonical_violations = 0
        self.factory_effects_activated = 0
        self.headset_reason = ""
        self.end_options_visible = 0
        self.end_with_productive_line = 0
        self.end_only_after_filter = 0
        self.unresolved_obligations = ()
        self.next_attacker_serial = None
        self.ariana_retained_cards.clear()
        self.r_command_required_damage = 0
        self.r_command_supporter_deficit = 0
        self.ultra_ball_supporter_discards = 0
        self.ultra_ball_r_command_line = ""
        self.froslass_count = 0
        self.froslass_ping = 0
        self.archer_veto_reason = ""
        self.headset_recovery_reason = ""
        self.setup_guard_reason = ""
        self.giovanni_pivot_reason = ""
        self.target_priority_reason = ""
        self.chosen_target_prize_value = 0
        self.night_stretcher_priority_reason = ""
        self.r_command_projected_supporters = 0
        self.r_command_projected_damage = 0
        self.headset_ariana_recovery = False
        self.development_obligations_pending = ()
        self.recovery_plan_reason = ""
        self.recovery_plan_cards = ()
        self.deferred_petrel_reason = ""
        self.end_reason = ""
        self.heros_cape_scrapped = False
        self.public_line_evaluations.clear()
        self.search_plan_objective = ""
        self.search_resource_used_this_turn = None
        self.proton_gain_remaining = 0
        self.ariana_already_available = False
        self.petrel_reserved = False
        self.best_draw_sequence = ()
        self.energy_attachment_reason = ""
        self.energy_veto_threat = ""
        self.giovanni_line = ""
        self.ariana_petrel_comparison = ""
        self.archer_line_comparison = ""
        self.headset_preservation_reason = ""
        self.end_veto_reason = ""


@dataclass(slots=True)
class MatchTacticalLedger:
    """Persist public terminal-line evidence across turns of one match."""

    target_serial: int | None = None
    target_card_id: int | None = None
    target_hp: int = 0
    own_prizes_remaining: int = 0
    target_prize_value: int = 0
    projected_porygon_damage: int = 0
    roto_sticks_played: int = 0
    roto_supporters_revealed: int = 0
    roto_supporters_selected: int = 0
    r_command_terminal_opportunities: int = 0
    porygon_terminal_opportunities: int = 0
    porygon_terminal_conversions: int = 0
    porygon_terminal_misses: int = 0
    ignition_attachments: int = 0
    ignition_attacks: int = 0
    ignition_without_attack: int = 0
    late_proton_without_gain: int = 0
    petrel_factory_opportunities: int = 0
    petrel_factory_conversions: int = 0
    poke_pad_ko_opportunities: int = 0
    poke_pad_ko_conversions: int = 0
    poke_pad_ko_misses: int = 0
    torment_with_superior_line: int = 0
    last_terminal_signature: tuple[int | None, int, int] | None = None

    def reset(self) -> None:
        """Clear match evidence before a new match starts."""
        self.target_serial = None
        self.target_card_id = None
        self.target_hp = 0
        self.own_prizes_remaining = 0
        self.target_prize_value = 0
        self.projected_porygon_damage = 0
        self.roto_sticks_played = 0
        self.roto_supporters_revealed = 0
        self.roto_supporters_selected = 0
        self.r_command_terminal_opportunities = 0
        self.porygon_terminal_opportunities = 0
        self.porygon_terminal_conversions = 0
        self.porygon_terminal_misses = 0
        self.ignition_attachments = 0
        self.ignition_attacks = 0
        self.ignition_without_attack = 0
        self.late_proton_without_gain = 0
        self.petrel_factory_opportunities = 0
        self.petrel_factory_conversions = 0
        self.poke_pad_ko_opportunities = 0
        self.poke_pad_ko_conversions = 0
        self.poke_pad_ko_misses = 0
        self.torment_with_superior_line = 0
        self.last_terminal_signature = None


@dataclass(slots=True)
class EvolutionKoCommitment:
    """Persist a verified Poké Pad to Honchkrow Knock Out line."""

    turn: int
    murkrow_serial: int | None
    target_card_id: int
    target_prize_value: int
    planned_damage: int
    supporters_required: int
    stage: str = "play_poke_pad"


@dataclass(slots=True)
class RocketEvolutionCommitment:
    """Bind a Rocket attachment to the same-turn Murkrow evolution."""

    turn: int
    murkrow_serial: int | None


@dataclass(slots=True)
class AttackSequence:
    """Record a committed attack until its intermediate prompts resolve."""

    attack_id: int
    target_card_id: int
    target_hp_before: int
    attacker_card_id: int
    attacker_energy: int
    supporters_available: int
    planned_damage: int
    minimum_damage: int
    ko_threshold: int
    deck_reserve_before: int
    pending_intermediate: bool = True


@dataclass(frozen=True, slots=True)
class PublicAttackLine:
    """A state-derived, auditable public attack line.

    This record deliberately contains only visible state and declared action
    effects.  It is the common calculation used by terminal filters and
    resource-recovery plans; a ledger value can describe it but never drive it.
    """

    attacker_card_id: int
    attacker_serial: int | None
    target_card_id: int
    target_serial: int | None
    attack_id: int
    damage_before: int
    damage_after: int
    supporters_recovered: tuple[int, ...]
    supporters_spent: tuple[int, ...]
    attack_ready: bool
    knocks_out: bool
    prizes_taken: int
    wins_game: bool
    veto_reason: str = ""


@dataclass(frozen=True, slots=True)
class SwitchCommitment:
    """Bind a voluntary switch to one ready attacker and immediate attack."""

    method: str
    turn: int
    target_card_id: int
    target_serial: int | None
    attack_id: int
    planned_damage: int
    requires_ignition: bool = False
    opponent_target_card_id: int | None = None
    opponent_target_serial: int | None = None


class HonchkrowPorygonScorer(SimpleHeuristicScorer):
    """Score selections using the reviewed Honchkrow/Porygon priorities."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._proton_used_previous_turn = False
        self._own_ko_observed = False
        self._reference_roto = False
        self._persistent_target_serial: int | None = None
        self._persistent_target_card_id: int | None = None

    @property
    def _strategy(self) -> Mapping[str, Any]:
        """Return the immutable strategic data declared by this deck profile."""
        return self.deck_profile.strategic_context if self.deck_profile else {}

    def set_proton_used_previous_turn(self, used: bool) -> None:
        """Set the public early-game Proton history for the current decision."""
        self._proton_used_previous_turn = used

    def set_own_ko_observed(self, observed: bool) -> None:
        """Record the public transition that immediately followed our KO."""
        self._own_ko_observed = observed

    def set_reference_roto(self, enabled: bool) -> None:
        """Select the frozen pre-probabilistic-Roto reference policy."""
        self._reference_roto = enabled

    def reset_persistent_target(self) -> None:
        """Forget a target when the public objective ends."""
        self._persistent_target_serial = None
        self._persistent_target_card_id = None

    def set_persistent_target(self, target: Any) -> None:
        """Persist the public identity of a selected opponent Pokémon."""
        if target is None:
            return
        serial = getattr(target, "serial", None)
        card_id = getattr(target, "card_id", None)
        self._persistent_target_serial = serial if isinstance(serial, int) else None
        self._persistent_target_card_id = card_id if isinstance(card_id, int) else None

    def _sdk_score(
        self,
        state: GameState,
        candidate: Candidate,
        context: SelectContext | None,
    ) -> tuple[float, list[str]]:
        if context is SelectContext.IS_FIRST:
            if candidate.option_type is OptionType.YES:
                return 1000.0, ["choose_first_for_proton_setup"]
            if candidate.option_type is OptionType.NO:
                return -1000.0, ["decline_second_turn"]
        return super()._sdk_score(state, candidate, context)

    def _play_score(self, state: GameState, candidate: Candidate) -> tuple[float, list[str]]:
        card_id = self._feature_int(candidate, "card_id")
        card_type = self._metadata_int(candidate.card, "cardType")
        if card_type == 0:
            if self._own_field_count(state) < 2 and card_id in {MURKROW, PORYGON}:
                return 1800.0, ["opening_backup_pokemon"]
            if card_id == ARTICUNO:
                if self._grimmsnarl_froslass_matchup(state):
                    return -1800.0, ["avoid_articuno_against_grimmsnarl_froslass"]
                if self._articuno_is_needed(state):
                    return 920.0, ["play_articuno_matchup_tech"]
                return -1500.0, ["preserve_articuno_until_needed"]
            if card_id == HONCHKROW:
                return 620.0, ["develop_primary_honchkrow"]
            if card_id == PORYGON2:
                return 480.0, ["develop_secondary_porygon"]
            return 430.0, ["develop_attacker_line"]
        if card_id == ARIANA:
            if not self._ariana_is_safe_and_useful(state):
                return -2600.0, ["ariana_deck_out_guard"]
            if self._proton_setup_is_useful(state) and self._card_in_hand(state, PROTON):
                return -1800.0, ["delay_ariana_for_required_proton_setup"]
            if self._petrel_factory_is_superior(state):
                return -1600.0, ["delay_ariana_for_petrel_factory"]
            return 1400.0, [
                "ariana_before_factory_hand_refresh",
                "ariana_hand_refresh_and_energy_access",
            ]
        if card_id == GIOVANNI:
            if self._giovanni_pivot_is_productive(state):
                return 1500.0, ["giovanni_pivots_porygon_to_bench_attacker"]
            if self._giovanni_is_lethal_or_promoting(state, candidate):
                return 1600.0, ["giovanni_immediate_ko_line"]
            if self._supporters_in_hand_after(card_id, state) >= self._supporters_needed_for_ko(
                state
            ):
                return 760.0, ["giovanni_preserves_ko_supporters"]
            return 80.0, ["giovanni_preserves_supporters_until_ko"]
        if card_id == PROTON:
            targets = self._proton_targets_remaining(state)
            if not self._proton_setup_is_useful(state):
                return -2400.0, ["proton_without_setup_gain"]
            priority = self._proton_priority_score(state, targets)
            reasons = ["proton_targets_remaining"]
            if targets.get(MURKROW, 0) > 0:
                reasons.append("proton_murkrow_priority")
            if self._articuno_is_needed(state) and targets.get(ARTICUNO, 0) > 0:
                reasons.append("proton_matchup_articuno")
            return 420.0 + priority, reasons
        if card_id == TRANSCEIVER:
            if self._proton_setup_is_useful(state):
                return 1200.0, ["transceiver_proton_early_game"]
            if self._transceiver_is_better_than_petrel_for_ariana(state):
                return 1550.0, ["transceiver_ariana_preserves_petrel"]
            if self._ariana_is_safe_and_useful(state):
                return 980.0, ["transceiver_ariana_resource_engine"]
            if self._proton_was_used_previous_turn(state):
                return 690.0, ["transceiver_ariana_after_proton"]
            return 720.0, ["transceiver_proton_early_game"]
        if card_id == POKE_PAD:
            if self._pokepad_honchkrow_is_useful(state, candidate):
                return 860.0, ["poke_pad_honchkrow_search"]
            return 620.0, ["poke_pad_murkrow_search"]
        if card_id == ULTRA_BALL:
            if not self._ultra_ball_is_productive(state):
                return -2200.0, ["ultra_ball_without_target_or_safe_discard"]
            return 590.0, ["ultra_ball_attacker_search_or_r_command_boost"]
        if card_id == FACTORY:
            if not self._factory_is_useful(state):
                if self._factory_play_is_useful(state):
                    return 1450.0, ["play_stadium_before_ariana"]
                return -1800.0, ["factory_without_post_supporter_draw"]
            return 1250.0, ["factory_after_ariana_draw_engine"]
        if card_id == PETREL:
            if self._petrel_factory_is_superior(state):
                return 1700.0, ["petrel_factory_two_card_draw"]
            if self._petrel_is_emergency(state):
                return 820.0, ["petrel_emergency_ariana_search"]
            return self._petrel_search_score(state)
        if card_id == ROTO_STICK:
            if self._card_in_hand(state, ROTO_STICK):
                return 980.0, ["roto_stick_required_before_partial_damage"]
            if self._roto_stick_is_needed(state):
                return 980.0, ["roto_stick_closes_supporter_deficit"]
            return -1800.0, ["preserve_roto_stick_for_supporter_ko"]
        if card_id == MIRACLE_HEADSET:
            if not self._miracle_headset_is_useful(state):
                return -2200.0, ["reserve_miracle_headset"]
            return 700.0, ["miracle_headset_ko_or_emergency_line"]
        if card_id == NIGHT_STRETCHER:
            if not self._canonical_night_stretcher_is_productive(state):
                return -2200.0, ["night_stretcher_without_immediate_play"]
            return 1300.0, ["night_stretcher_hand_reduction_before_ariana"]
        if card_id == ARCHER:
            if not self._archer_is_safe_and_useful(state, candidate):
                return -2400.0, ["archer_without_safe_disruption"]
            reasons = ["archer_after_own_ko"]
            score = 780.0
            if self._archer_alakazam_hand_pressure(state):
                score += 120.0
                reasons.append("archer_alakazam_hand_pressure")
            return score, reasons
        if card_type == 4:
            return 450.0, ["stadium_after_supporter"]
        if card_type == 3:
            return 340.0, ["play_supporter_for_factory"]
        return super()._play_score(state, candidate)

    def _attachment_score(self, state: GameState, candidate: Candidate) -> tuple[float, list[str]]:
        card_type = self._metadata_int(candidate.card, "cardType")
        target_id = self._feature_int(candidate, "target_card_id")
        energy_count = self._target_energy_units(state, candidate)
        if card_type not in {5, 6}:
            return super()._attachment_score(state, candidate)
        target = 0
        if target_id == HONCHKROW:
            target = 260
        elif target_id == PORYGON2:
            target = 190
        elif target_id == MURKROW:
            target = 120
        elif target_id == ARTICUNO and self._articuno_is_needed(state):
            target = 170
        if (
            target_id == HONCHKROW
            and self._own_active_card_id(state) == HONCHKROW
            and self._energy_units_in_hand(state) > 0
        ):
            target += 700
        if energy_count >= self._attack_energy_target(target_id):
            return -500.0, ["avoid_energy_above_attack_plan"]
        energy_id = self._feature_int(candidate, "card_id")
        if (
            energy_id in {ROCKET_ENERGY, IGNITION_ENERGY}
            and self._enhanced_hammer_is_public_risk(state)
            and not self._energy_attachment_is_committed(state, candidate)
        ):
            return -2300.0, ["preserve_energy_against_enhanced_hammer"]
        if card_type == 6 and self._feature_int(candidate, "card_id") == IGNITION_ENERGY:
            if not self._ignition_attachment_is_productive(state, candidate):
                return -2400.0, ["ignition_energy_without_attack_line"]
            target += 180
        if self._feature_int(candidate, "card_id") == ROCKET_ENERGY:
            target += 25
        return 300.0 + target, ["attach_energy_to_attack_line"]

    def _enhanced_hammer_is_public_risk(self, state: GameState) -> bool:
        """Return whether Enhanced Hammer is visible in the opponent's resources."""
        opponent = self._opponent_player(state)
        if opponent is None:
            return False
        return any(
            self._card_id_from_value(card) == ENHANCED_HAMMER
            for zone in (opponent.hand or (), opponent.discard or ())
            for card in zone
        )

    def _energy_attachment_is_committed(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether an attachment completes an immediate or persistent attack."""
        target_id = self._feature_int(candidate, "target_card_id")
        current_units = self._target_energy_units(state, candidate)
        energy_id = self._feature_int(candidate, "card_id")
        added_units = 3 if energy_id == IGNITION_ENERGY else 2 if energy_id == ROCKET_ENERGY else 1
        if target_id in {
            HONCHKROW,
            PORYGON2,
        } and current_units + added_units >= self._attack_energy_target(target_id):
            if target_id == HONCHKROW and self._effective_supporters_in_hand(state) > 0:
                return True
            if target_id == PORYGON2 and self._rocket_supporters_in_discard(state) > 0:
                return True
        return (
            self._persistent_target_card_id == target_id
            and self._persistent_target_serial == self._feature_int(candidate, "target_serial")
        )

    def _attack_score(self, state: GameState, candidate: Candidate) -> tuple[float, list[str]]:
        attack_id = self._attack_id(candidate)
        target = self._target_opponent_pokemon(state, candidate)
        if target is not None and has_splashing_dodge_protection(state.raw, target.serial):
            return -5000.0, ["splashing_dodge_damage_prevented"]
        opponent_hp = max(0, int(target.hp)) if target is not None else self._raw_opponent_hp(state)
        explicit_damage = max(
            self._metadata_int(candidate.attack, "damage"),
            self._metadata_int(candidate.option, "damage"),
            self._metadata_int(candidate.option, "expectedDamage"),
        )
        if self._truthy(candidate.option, "win", "wins", "gameOver"):
            return 5000.0, ["honchkrow_win_now"]
        reasons: list[str] = ["honchkrow_attack_for_prize_progress"]
        score = 260.0 + explicit_damage
        if self._truthy(candidate.option, "ko", "knockout", "isKo") or (
            explicit_damage > 0 and opponent_hp > 0 and explicit_damage >= opponent_hp
        ):
            score += 1500.0
            reasons.append("honchkrow_guaranteed_ko")
        if attack_id == ROCKET_FEATHERS:
            effective_supporters = self._effective_supporters_in_hand(state)
            damage = self._attack_damage(state, candidate, effective_supporters * 60, target)
            bonus = 700.0 if self._own_active_card_id(state) == HONCHKROW else 0.0
            reasons = ["honchkrow_rocket_feathers", "rocket_hand_damage"]
            if damage < self._effective_opponent_hp(state):
                reasons.append("rocket_feathers_below_ko_threshold")
                bonus -= 450.0
            if effective_supporters == 0:
                bonus -= 1000.0
            score = max(score, 300.0 + damage + bonus)
            if damage >= opponent_hp > 0:
                score += 1100.0
                reasons.append("rocket_feathers_ko")
            return score, reasons
        if attack_id == R_COMMAND:
            damage = self._attack_damage(
                state, candidate, self._rocket_supporters_in_discard(state) * 20, target
            )
            score = max(score, 500.0 + damage)
            if damage >= opponent_hp > 0:
                score += 2000.0
                reasons.append("r_command_ko")
            return score, [
                "porygon2_r_command",
                "rocket_discard_damage",
                *reasons,
            ]
        if attack_id == HAMMER_IN:
            damage = self._attack_damage(state, candidate, max(100, explicit_damage), target)
            if damage >= opponent_hp > 0:
                score += 1200.0
                reasons.append("hammer_in_ko")
            return score + damage, ["hammer_in_fixed_damage", *reasons]
        if attack_id == HACKING:
            return -5000.0, ["hacking_forbidden", "hacking_without_decisive_interrupt"]
        if attack_id == DECEIT:
            if not self._deceit_is_decisive(state, candidate, explicit_damage):
                return -2200.0, ["deceit_without_decisive_damage_or_interrupt"]
            return 420.0 + explicit_damage, ["deceit_contextual_tempo"]
        if attack_id == TORMENT:
            if self._torment_single_attack_lock(state, candidate):
                return 560.0 + explicit_damage, ["torment_blocks_next_attack"]
            return 300.0 + explicit_damage, ["torment_damage_only"]
        if attack_id == ARTICUNO_ATTACK:
            return -3000.0, ["articuno_never_attacks_in_honchkrow"]
        return super()._attack_score(state, candidate)

    def _attack_damage(
        self,
        state: GameState,
        candidate: Candidate,
        base_damage: int,
        target: Any | None = None,
    ) -> int:
        """Calculate public attack damage including only applicable modifiers."""
        if base_damage <= 0:
            return 0
        target = target or self._target_opponent_pokemon(state, candidate)
        if target is None:
            return base_damage
        attacker = self._own_active(state)
        attacker_card = self.catalog.get_card(str(attacker.card_id)) if attacker else None
        attacker_type = (attacker_card or {}).get("energyType")
        return calculate_damage(
            base_damage,
            attacker_type,
            self.catalog.get_card(str(target.card_id)) or {},
            prevented=has_splashing_dodge_protection(state.raw, target.serial),
            state_raw=state.raw,
            defender_serial=target.serial,
        )

    def _card_selection_score(
        self,
        state: GameState,
        candidate: Candidate,
        context: SelectContext | None,
    ) -> tuple[float, list[str]]:
        card_id = self._feature_int(candidate, "card_id")
        if (
            context is SelectContext.TO_HAND
            and candidate.option.get("sourceCardId") == TRANSCEIVER
            and card_id == ARIANA
            and self._effective_supporters_in_hand(state) >= 2
        ):
            return -2400.0, ["avoid_redundant_ariana_transceiver_search"]
        if context is SelectContext.SETUP_ACTIVE_POKEMON:
            setup_active_scores = {
                MURKROW: (3000.0, "opening_active_murkrow"),
                PORYGON: (2000.0, "opening_active_porygon"),
            }
            if card_id in setup_active_scores:
                score, reason = setup_active_scores[card_id]
                return score, [reason]
        if context is SelectContext.SETUP_BENCH_POKEMON and card_id == MURKROW:
            return 2600.0, ["opening_bench_maximize_murkrow"]
        if context is SelectContext.TO_HAND and candidate.option.get("sourceCardId") == PETREL:
            if card_id == ULTRA_BALL:
                if self._ultra_ball_completes_r_command(state):
                    return 2200.0, ["petrel_ultra_ball_terminal_r_command"]
                if self._has_murkrow_ready_to_evolve(state) and self._ultra_ball_is_productive(
                    state
                ):
                    return 1900.0, ["petrel_ultra_ball_evolution_line"]
                if self._ariana_is_safe_and_useful(state):
                    return -900.0, ["petrel_prefers_ariana_over_ultra_ball"]
                if self._ultra_ball_is_productive(state):
                    return 650.0, ["petrel_ultra_ball_conversion_only"]
                return -1600.0, ["petrel_ultra_ball_without_useful_conversion"]
            if card_id == ARIANA and self._ariana_is_safe_and_useful(state):
                return 1850.0, ["petrel_take_ariana_for_hand_refresh"]
        if (
            context is SelectContext.TO_HAND
            and candidate.option.get("sourceCardId") == PETREL
            and card_id in self._supporter_ids()
        ):
            if card_id == ARIANA and self._petrel_is_emergency(state):
                return 1650.0, ["petrel_emergency_ariana"]
            target = Candidate(
                option_index=candidate.option_index,
                option=candidate.option,
                option_type=OptionType.PLAY,
                card=candidate.card,
                features={"card_id": card_id},
            )
            score, reasons = self._play_score(state, target)
            return score, ["petrel_target_any_supporter", *reasons]
        if context is SelectContext.TO_HAND and card_id == PROTON:
            if self._proton_setup_is_useful(state):
                return 1800.0, ["select_proton_for_early_setup"]
        if (
            context is SelectContext.TO_HAND
            and candidate.option.get("sourceCardId") == POKE_PAD
            and self._own_field_count(state) <= 1
            and card_id in {MURKROW, PORYGON}
        ):
            return 2900.0, ["select_basic_for_no_pokemon_survival"]
        if context is SelectContext.TO_HAND and card_id == HONCHKROW:
            if self._pokepad_honchkrow_is_useful(state, candidate):
                return 1750.0, ["select_honchkrow_for_attack_or_hand_refresh"]
        if context is SelectContext.TO_HAND and candidate.option.get("sourceCardId") in {
            ULTRA_BALL,
            POKE_PAD,
            PROTON,
            TRANSCEIVER,
        }:
            score, reasons = self._search_target_priority_score(state, candidate)
            if reasons:
                return score, reasons
        is_effect_target = context is not None and context.value == "EFFECT_TARGET"
        if context in {SelectContext.TO_ACTIVE, SelectContext.SWITCH} or is_effect_target:
            if is_effect_target and card_id not in {
                HONCHKROW,
                PORYGON2,
                MURKROW,
                ARTICUNO,
            }:
                return super()._card_selection_score(state, candidate, context)
            if is_effect_target:
                return self._giovanni_target_score(state, candidate)
            if card_id == ARTICUNO and self._articuno_is_needed(state):
                if self._promotion_line_is_lethal(
                    state, HONCHKROW
                ) or self._promotion_line_is_lethal(state, PORYGON2):
                    return -2600.0, ["keep_articuno_benched_for_defense"]
                return 900.0, ["promote_articuno_only_without_better_attacker"]
            if card_id == HONCHKROW and self._pokemon_is_ready(state, candidate):
                if self._r_command_is_best_damage_line(state):
                    return 800.0, ["defer_honchkrow_to_r_command"]
                if self._promotion_line_is_lethal(state, HONCHKROW):
                    return 4700.0, ["promote_honchkrow_rocket_feathers_ko"]
                return 1500.0, ["promote_ready_honchkrow"]
            if card_id == PORYGON2 and self._pokemon_is_ready(state, candidate):
                if context is SelectContext.TO_ACTIVE:
                    if not self.r_command_knocks_out_active(state):
                        return -2400.0, ["veto_porygon2_r_command_damage_insufficient"]
                    if self._r_command_wins_game(state):
                        return 5200.0, [
                            "promote_porygon2_game_winning_r_command",
                            "r_command_takes_last_prizes",
                        ]
                    return 4800.0, ["promote_porygon2_r_command_ko"]
                if self._r_command_wins_game(state):
                    return 5200.0, [
                        "promote_porygon2_game_winning_r_command",
                        "r_command_takes_last_prizes",
                    ]
                if self._porygon2_prize_pressure_line(state):
                    reasons = ["promote_porygon2_prize_pressure"]
                    if self._porygon2_next_turn_setup_available(state):
                        reasons.append("porygon2_next_turn_setup_available")
                    return 2600.0, reasons
                if self._r_command_is_best_damage_line(state):
                    reasons = ["promote_porygon2_best_r_command"]
                    if self._porygon2_prize_race_line(state):
                        reasons.append("porygon2_prize_race_line")
                    return 1800.0 + (900.0 if len(reasons) > 1 else 0.0), reasons
                return 1250.0, ["promote_ready_porygon2"]
            if card_id == PORYGON2 and self._promotion_line_is_lethal(state, PORYGON2):
                return 5200.0, ["promote_porygon2_projected_r_command_ko"]
            if card_id == PORYGON2 and self._porygon2_prize_pressure_line(state):
                reasons = ["promote_porygon2_prize_pressure"]
                if self._porygon2_next_turn_setup_available(state):
                    reasons.append("porygon2_next_turn_setup_available")
                return 2300.0, reasons
            if card_id == PORYGON2 and self._porygon2_terminal_promotion_available(
                state, candidate
            ):
                return 5100.0, [
                    "promote_porygon2_terminal_ignition_line",
                    "ignition_reaches_r_command_attack_cost",
                ]
            if card_id == MURKROW:
                if self._murkrow_torment_knocks_out_active(state, candidate):
                    return 5000.0, ["promote_murkrow_torment_public_ko"]
                return 100.0, ["promote_murkrow_only_without_evolved_attacker"]
            if card_id == ARTICUNO and not self._articuno_is_needed(state):
                return -1800.0, ["avoid_articuno_promotion_without_matchup"]
        if context is SelectContext.EFFECT_TARGET and self._contains_type(
            (candidate.card or {}).get("weakness") or (candidate.card or {}).get("weaknesses"),
            "dark",
        ):
            return 1400.0, ["giovanni_dark_weakness_target"]
        if card_id == ARTICUNO and context in {
            SelectContext.SETUP_ACTIVE_POKEMON,
            SelectContext.SETUP_BENCH_POKEMON,
            SelectContext.TO_ACTIVE,
            SelectContext.TO_FIELD,
            SelectContext.TO_HAND,
        }:
            if self._articuno_is_needed(state):
                return 700.0, ["select_articuno_matchup_tech"]
            return -1500.0, ["avoid_articuno_without_matchup_need"]
        if context in {SelectContext.DISCARD, SelectContext.DISCARD_CARD_OR_ATTACHED_CARD}:
            if self._is_energy_card(card_id, candidate.card):
                return -2500.0, ["protect_energy_from_discard"]
            if self._is_rocket_supporter(card_id, candidate.card):
                if card_id == ARIANA:
                    if self._discard_is_required_for_ko(state, candidate):
                        return 1550.0, ["discard_ariana_to_close_ko"]
                    return -500.0, ["preserve_ariana_until_last"]
                if self._effective_supporters_in_hand(state) <= 1:
                    return -1000.0, ["preserve_last_supporter"]
                return 220.0, ["discard_redundant_rocket_supporter"]
            if card_id in {MURKROW, HONCHKROW, PORYGON, PORYGON2, ARTICUNO}:
                return -150.0, ["preserve_pokemon_line"]
        if context is SelectContext.TO_HAND and card_id == ARTICUNO:
            return (260.0, ["recover_articuno_against_dragapult"])
        return super()._card_selection_score(state, candidate, context)

    def _murkrow_torment_knocks_out_active(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether the selected ready Murkrow has a public Torment KO."""
        player = self._own_player(state)
        opponent = self._opponent_player(state)
        target = opponent.active if opponent is not None else None
        serial = self._feature_int(candidate, "target_serial")
        murkrow = next(
            (
                pokemon
                for pokemon in ([player.active, *player.bench] if player is not None else [])
                if pokemon is not None
                and pokemon.card_id == MURKROW
                and (not serial or pokemon.serial == serial)
            ),
            None,
        )
        attack = self.catalog.get_attack(str(TORMENT)) or {}
        damage = self._metadata_int(attack, "damage")
        return bool(
            murkrow is not None
            and target is not None
            and self._energy_units_for_pokemon(murkrow) >= self._attack_energy_target(MURKROW)
            and damage >= max(0, int(target.hp))
        )

    def _own_field_count(self, state: GameState) -> int:
        """Count own Active and Bench Pokémon visible to the policy."""
        player = self._own_player(state)
        if player is None:
            return 0
        return int(player.active is not None) + sum(pokemon is not None for pokemon in player.bench)

    def _articuno_is_needed(self, state: GameState) -> bool:
        """Return whether the visible matchup justifies preserving Articuno."""
        if self._grimmsnarl_froslass_matchup(state):
            return False
        visible = self._visible_opponent_card_ids(state)
        dragapult_line = bool(visible & {DREEPY, DRAKLOAK, DRAGAPULT_EX})
        alakazam_line = bool(visible & {ABRA, KADABRA, ALAKAZAM})
        return dragapult_line or alakazam_line

    def _grimmsnarl_froslass_matchup(self, state: GameState) -> bool:
        """Return whether both public Grimmsnarl and Froslass threats are visible."""
        visible = self._visible_opponent_card_ids(state)
        return {GRIMMSNARL_EX, FROSLASS}.issubset(visible)

    def _articuno_is_on_field(self, state: GameState) -> bool:
        """Return whether Articuno is already Active or Benched."""
        player = self._own_player(state)
        return bool(
            player
            and any(
                pokemon is not None and pokemon.card_id == ARTICUNO
                for pokemon in [player.active, *player.bench]
            )
        )

    def _has_playable_supporter(self, state: GameState) -> bool:
        """Return whether the hand contains a supporter with a current conversion line."""
        if state.supporter_played:
            return False
        for card in self._hand_cards(state):
            card_id = self._card_id_from_value(card)
            if card_id == ARIANA and self._ariana_is_safe_and_useful(state):
                return True
            if card_id == GIOVANNI and self._canonical_giovanni_target_exists(state):
                return True
            if card_id == PROTON and self._proton_setup_is_useful(state):
                return True
            if card_id == ARCHER and self._archer_is_safe_and_useful(
                state, Candidate(option={}, option_index=-1, option_type=OptionType.PLAY)
            ):
                return True
            if card_id == PETREL and self._petrel_factory_is_superior(state):
                return True
            if card_id == TRANSCEIVER and self._roto_remaining_supporters(state) > 0:
                return True
        return False

    def _canonical_giovanni_target_exists(self, state: GameState) -> bool:
        """Return whether Giovanni has a visible high-value target."""
        player = self._own_player(state)
        opponent = self._opponent_player(state)
        if player is None or opponent is None:
            return False
        prizes_left = len(player.prize)
        return any(
            pokemon is not None
            and (
                int(
                    getattr(
                        pokemon,
                        "effective_prize_value",
                        self.catalog.get_traits(str(pokemon.card_id)).base_prize_value,
                    )
                )
                >= 2
                or int(
                    getattr(
                        pokemon,
                        "effective_prize_value",
                        self.catalog.get_traits(str(pokemon.card_id)).base_prize_value,
                    )
                )
                >= prizes_left
            )
            for pokemon in opponent.bench
        )

    def _own_bench_full(self, state: GameState) -> bool:
        player = self._own_player(state)
        return bool(player and self._own_bench_count(state) >= player.bench_max)

    def _declared_count(self, card_id: int) -> int:
        counts = self._strategy.get("pokemon_counts", {})
        value = (
            counts.get(str(card_id), counts.get(card_id, 0)) if isinstance(counts, Mapping) else 0
        )
        return int(value) if isinstance(value, (int, float)) else 0

    def _proton_targets_remaining(self, state: GameState) -> dict[int, int]:
        """Count visible-deck Proton targets after known cards are removed."""
        player = self._own_player(state)
        if player is None:
            return {}
        result: dict[int, int] = {}
        field = [player.active, *player.bench]
        for card_id in (MURKROW, PORYGON, PORYGON2, ARTICUNO):
            known = sum(
                1 for pokemon in field if pokemon is not None and pokemon.card_id == card_id
            )
            known += sum(
                1
                for card in list(player.hand or ()) + list(player.discard) + list(player.prize)
                if self._card_id_from_value(card) == card_id
            )
            result[card_id] = max(0, self._declared_count(card_id) - known)
        return result

    def _proton_priority_score(self, state: GameState, targets: Mapping[int, int]) -> float:
        values = {
            MURKROW: 520.0,
            PORYGON: 330.0,
            PORYGON2: 260.0,
            ARTICUNO: 520.0 if self._articuno_is_needed(state) else 60.0,
        }
        raw = max((values[key] for key, count in targets.items() if count > 0), default=-500.0)
        return raw - max(0, self._own_bench_count(state) - 1) * 100.0

    def _search_target_priority_score(
        self, state: GameState, candidate: Candidate
    ) -> tuple[float, list[str]]:
        card_id = self._feature_int(candidate, "card_id")
        if card_id == PORYGON2:
            if self._r_command_wins_game(state):
                return 2800.0, ["search_porygon2_game_winning_r_command"]
            if self._porygon2_terminal_promotion_available(state, candidate):
                return 2500.0, [
                    "search_porygon2_terminal_ignition_line",
                    "ignition_reaches_r_command_attack_cost",
                ]
            if self._r_command_is_best_damage_line(state) or self._porygon2_prize_race_line(state):
                return 2100.0, ["search_porygon2_prize_race_line"]
            if self._promotion_line_is_lethal(state, PORYGON2):
                return 1600.0, ["search_porygon2_promotion_line"]
            return 1000.0, ["search_porygon2_primary_line"]
        if card_id == HONCHKROW:
            if self._pokemon_is_ready(state, candidate):
                return 1450.0, ["search_honchkrow_ready_attacker"]
            return 820.0, ["search_honchkrow_setup_line"]
        if card_id == PORYGON:
            if self._proton_setup_is_useful(state):
                return 1150.0, ["search_porygon_setup_line"]
            return 760.0, ["search_porygon_development_line"]
        if card_id == MURKROW:
            if self._own_field_count(state) < 2:
                return 1100.0, ["search_murkrow_opening_line"]
            return 700.0, ["search_murkrow_development_line"]
        if card_id == ARTICUNO:
            if self._articuno_is_needed(state):
                return 1500.0, ["search_articuno_matchup_tech"]
            return -1800.0, ["avoid_articuno_without_matchup_need"]
        return 0.0, []

    def _proton_targets_exist(self, state: GameState) -> bool:
        """Return whether Proton has at least one visible-deck target left."""
        return any(count > 0 for count in self._proton_targets_remaining(state).values())

    def _petrel_is_emergency(self, state: GameState) -> bool:
        """Return whether Petrel is the only available Rocket Supporter."""
        supporters = [
            self._card_id_from_value(card)
            for card in self._hand_cards(state)
            if self._card_id_from_value(card) in self._supporter_ids()
        ]
        return supporters == [PETREL]

    def _early_proton_window(self, state: GameState) -> bool:
        return self._own_turn_number(state) <= 2

    @staticmethod
    def _own_turn_number(state: GameState) -> int:
        """Return the one-based turn number for the acting player."""
        if state.turn <= 0:
            return 0
        return (state.turn + 1) // 2 if state.your_index == state.first_player else state.turn // 2

    def _proton_setup_is_useful(self, state: GameState) -> bool:
        """Require a real Basic target, Bench space, and development gain."""
        return self.board_setup_plan(state).productive

    def board_setup_plan(self, state: GameState) -> BoardSetupPlan:
        """Return the public attacker-development plan for the current board.

        A defensive Articuno is valuable protection but is not an attacker
        staging line.  Proton therefore remains productive while Murkrow or
        Porygon can still create the missing attacker role.
        """
        targets = self._proton_targets_remaining(state)
        player = self._own_player(state)
        if player is None or self._own_bench_full(state):
            return BoardSetupPlan(False)
        field = [pokemon for pokemon in [player.active, *player.bench] if pokemon is not None]
        has_murkrow = any(pokemon.card_id in {MURKROW, HONCHKROW} for pokemon in field)
        has_porygon = any(pokemon.card_id in {PORYGON, PORYGON2} for pokemon in field)
        missing: list[str] = []
        if not has_murkrow and targets.get(MURKROW, 0) > 0:
            missing.append("murkrow_attacker")
        if not has_porygon and targets.get(PORYGON, 0) > 0:
            missing.append("porygon_attacker")
        if self._articuno_is_needed(state) and targets.get(ARTICUNO, 0) > 0:
            missing.append("articuno_protection")
        # Articuno alone never discharges attacker development.
        attacker_missing = any(role.endswith("attacker") for role in missing)
        productive = attacker_missing or (self._own_turn_number(state) == 1 and bool(missing))
        return BoardSetupPlan(
            productive,
            tuple(missing),
            "proton_multi_basic_attacker_setup" if productive else "attacker_staging_complete",
        )

    def _card_in_hand(self, state: GameState, card_id: int) -> bool:
        return any(self._card_id_from_value(card) == card_id for card in self._hand_cards(state))

    def _roto_stick_is_needed(self, state: GameState) -> bool:
        """Return whether Roto-Stick has positive expected value for the KO line."""
        if self._roto_closes_visible_ko(state):
            return True
        if self._roto_can_close_r_command_line(state):
            return True
        if self._reference_roto:
            needed = self._supporters_needed_for_ko(state)
            hand = self._effective_supporters_in_hand(state)
            return bool(
                hand < needed
                and (self._rocket_supporters_in_discard(state) or self._card_in_hand(state, ARIANA))
            )
        if not self._card_in_hand(state, ROTO_STICK):
            return False
        needed = self._supporters_needed_for_ko(state)
        hand = self._effective_supporters_in_hand(state)
        if hand >= needed:
            return False
        active = self._own_active(state)
        player = self._own_player(state)
        if active is None or player is None or active.card_id != HONCHKROW:
            return False
        if self._energy_units_for_pokemon(active) < 2:
            return False
        if player.deck_count <= 0:
            return False
        return self._roto_expected_value(state, needed - hand)[0] > 0

    def _roto_closes_visible_ko(self, state: GameState) -> bool:
        """Return whether Roto can convert a visible partial line into a KO."""
        active = self._own_active(state)
        player = self._own_player(state)
        if active is None or player is None or not self._card_in_hand(state, ROTO_STICK):
            return False
        deck_room = min(ROTO_STICK_MAX_REVEAL_COUNT, self._roto_remaining_supporters(state))
        if deck_room <= 0:
            return False
        target_hp = self._raw_opponent_hp(state)
        if target_hp <= 0:
            return False
        if active.card_id == HONCHKROW and self._energy_units_for_pokemon(active) >= 2:
            needed = self._supporters_needed_for_ko(state)
            hand = self._effective_supporters_in_hand(state)
            return bool(
                hand < needed
                and (hand + deck_room) >= needed
                and (hand + deck_room) * 60 >= target_hp
            )
        if active.card_id == PORYGON2 and self._energy_units_for_pokemon(
            active
        ) >= self._attack_energy_target(PORYGON2):
            needed = self._r_command_supporters_needed(state)
            discard = self._rocket_supporters_in_discard(state)
            return bool(
                discard < needed
                and (discard + deck_room) >= needed
                and (discard + deck_room) * 20 >= target_hp
            )
        return False

    def _roto_remaining_supporters(self, state: GameState) -> int:
        """Estimate Supporters remaining in the hidden deck from public zones."""
        player = self._own_player(state)
        if player is None:
            return 0
        total = int(self._strategy.get("supporter_count", 20))
        visible = self._supporters_in_hand(state) + self._rocket_supporters_in_discard(state)
        visible += self._count_supporters(player.prize)
        return max(0, min(int(player.deck_count), total - visible))

    def _supporter_hit_probability(self, state: GameState, draws: int, required: int) -> float:
        """Estimate the chance that a hidden draw contains enough Supporters."""
        player = self._own_player(state)
        if player is None or draws <= 0 or required <= 0:
            return 0.0
        deck = max(0, int(player.deck_count))
        draws = min(draws, deck)
        supporters = min(self._roto_remaining_supporters(state), deck)
        if draws == 0 or supporters == 0 or required > draws:
            return 0.0
        denominator = comb(deck, draws)
        miss = sum(
            comb(supporters, successes) * comb(deck - supporters, draws - successes)
            for successes in range(min(required, supporters + 1))
            if 0 <= draws - successes <= deck - supporters
        )
        return max(0.0, min(1.0, 1.0 - miss / denominator))

    def _roto_hit_probability(self, state: GameState, required: int) -> float:
        """Estimate the chance that Roto's four revealed cards close the deficit."""
        return self._supporter_hit_probability(state, ROTO_STICK_MAX_REVEAL_COUNT, required)

    def _roto_expected_value(self, state: GameState, required: int) -> tuple[float, float]:
        """Return expected Roto value and its probability of closing the deficit."""
        player = self._own_player(state)
        if player is None or required <= 0:
            return 0.0, 0.0
        probability = self._roto_hit_probability(state, required)
        prize_value = self._active_target_prize_value(state)
        ko_value = 600.0 + prize_value * 200.0
        deck_risk = max(0, 8 - int(player.deck_count)) * 100.0
        action_cost = 450.0
        return probability * ko_value - action_cost - deck_risk, probability

    def _all_own_pokemon_are_rocket(self, state: GameState) -> bool:
        """Return whether Ariana draws to eight from only public card metadata."""
        player = self._own_player(state)
        if player is None:
            return False
        pokemon = [item for item in [player.active, *player.bench] if item is not None]
        if not pokemon:
            return False
        return all(
            "team rocket"
            in str((self.catalog.get_card(str(item.card_id)) or {}).get("name", "")).casefold()
            for item in pokemon
        )

    def _ariana_draw_count(self, state: GameState) -> int:
        """Return Ariana's public draw-to target for the current board."""
        return 8 if self._all_own_pokemon_are_rocket(state) else 5

    def _ariana_marginal_draw(self, state: GameState) -> int:
        """Return cards drawn after Ariana itself leaves the visible hand."""
        player = self._own_player(state)
        if player is None:
            return 0
        return int(max(0, self._ariana_draw_count(state) - max(0, player.hand_count - 1)))

    def _ariana_expected_value(
        self, state: GameState, hand_reduction: int = 0, factory_will_be_played: bool = False
    ) -> float:
        """Estimate Ariana's value after safely removing cards from the hand."""
        player = self._own_player(state)
        if player is None or state.supporter_played:
            return -2400.0
        hand_after_play = max(0, int(player.hand_count) - max(0, hand_reduction) - 1)
        ariana_draws = min(
            max(0, self._ariana_draw_count(state) - hand_after_play), player.deck_count
        )
        factory_draws = 2 if self._factory_in_play(state) or factory_will_be_played else 0
        draws = min(ariana_draws + factory_draws, player.deck_count)
        if ariana_draws <= 0:
            return -1800.0
        deck = max(1, int(player.deck_count))
        expected_supporters = draws * self._roto_remaining_supporters(state) / deck
        return float(expected_supporters * 650.0 + draws * 35.0)

    def _factory_in_play(self, state: GameState) -> bool:
        return self._stadium_in_play(state, FACTORY)

    def _stadium_in_play(self, state: GameState, stadium_id: int) -> bool:
        """Return whether a public stadium with the requested card ID is in play."""
        stadium = state.stadium
        if isinstance(stadium, list):
            return any(
                isinstance(card, Mapping) and self._card_id_from_value(card) == stadium_id
                for card in stadium
            )
        if isinstance(stadium, Mapping):
            return self._card_id_from_value(stadium) == stadium_id
        return str(stadium) == str(stadium_id)

    def _petrel_factory_is_superior(self, state: GameState) -> bool:
        """Prefer Petrel into Factory when Ariana would draw at most two cards."""
        player = self._own_player(state)
        return bool(
            player
            and not state.supporter_played
            and not self._factory_in_play(state)
            and not state.stadium_played
            and self._card_in_hand(state, PETREL)
            and self._ariana_marginal_draw(state) <= 2
            and player.deck_count > 0
        )

    def _pokepad_ariana_hand_reduction_is_useful(self, state: GameState) -> bool:
        """Return whether Poké Pad improves a proven Ariana redraw."""
        player = self._own_player(state)
        return bool(
            player
            and self._card_in_hand(state, ARIANA)
            and not state.supporter_played
            and self._ariana_is_safe_and_useful(state)
            and not self._proton_setup_is_useful(state)
            and player.hand_count >= 2
            and self._card_copies_remaining(state, HONCHKROW) > 0
        )

    def _transceiver_is_better_than_petrel_for_ariana(self, state: GameState) -> bool:
        """Prefer Transceiver for Ariana when it preserves Petrel for a better line."""
        return bool(
            self._card_in_hand(state, TRANSCEIVER)
            and self._card_in_hand(state, PETREL)
            and self._ariana_is_safe_and_useful(state)
            and not self._proton_setup_is_useful(state)
        )

    def _petrel_search_score(self, state: GameState) -> tuple[float, list[str]]:
        """Score Petrel by the best Supporter target it can legally access."""
        target_scores: list[tuple[float, int, list[str]]] = []
        for target_id in (ARIANA, ARCHER, GIOVANNI, PROTON):
            card = self.catalog.get_card(str(target_id)) or {
                "cardType": 3,
                "cardId": target_id,
            }
            target = Candidate(
                option_index=-1,
                option={"type": OptionType.PLAY.value, "cardId": target_id},
                option_type=OptionType.PLAY,
                card=card,
                features={"card_id": target_id},
            )
            score, reasons = self._play_score(state, target)
            if target_id == PROTON:
                # Petrel consumes the turn's Supporter play.  Fetching Proton
                # therefore cannot be represented as immediate setup.
                score = -2000.0
                reasons = ["petrel_proton_deferred_until_next_turn"]
            if target_id == ARIANA and self._transceiver_is_better_than_petrel_for_ariana(state):
                score -= 650.0
                reasons = [*reasons, "prefer_transceiver_for_ariana"]
            target_scores.append((score, target_id, reasons))
        best_score, target_id, reasons = max(target_scores, default=(-2000.0, 0, []))
        if best_score <= -1500.0:
            if target_id == PROTON:
                return -900.0, ["petrel_only_target_is_deferred_proton"]
            return -900.0, ["petrel_without_useful_supporter_target"]
        target_card = self.catalog.get_card(str(target_id)) or {}
        target_name = target_card.get("name", str(target_id))
        return best_score - 100.0, [
            "petrel_search_any_supporter",
            f"petrel_target_{target_name}",
            *reasons,
        ]

    def _ariana_is_safe_and_useful(self, state: GameState) -> bool:
        """Reject Ariana when it cannot draw safely or improve the visible hand."""
        player = self._own_player(state)
        if player is None:
            return True
        if state.supporter_played:
            return False
        draws = self._ariana_marginal_draw(state)
        return bool(draws > 0 and player.deck_count > 0)

    def _factory_play_is_useful(self, state: GameState) -> bool:
        """Return whether Factory can be played before the draw sequence."""
        player = self._own_player(state)
        if player is None or state.stadium_played:
            return False
        return bool(
            int(player.deck_count) > 0
            and (state.supporter_played or self._has_playable_supporter(state))
        )

    def _factory_is_useful(self, state: GameState) -> bool:
        """Return whether Factory can draw at least one card after a Supporter."""
        player = self._own_player(state)
        return bool(player and state.supporter_played and player.deck_count > 0)

    def _night_stretcher_is_productive(self, state: GameState) -> bool:
        """Require a recovery target that can immediately leave the hand."""
        player = self._own_player(state)
        if player is None:
            return False
        return any(
            self._night_stretcher_target_is_immediately_playable(
                state, self._card_id_from_value(card)
            )
            for card in player.discard
        )

    def _night_stretcher_target_is_immediately_playable(
        self, state: GameState, card_id: int
    ) -> bool:
        """Return whether a recovered Pokémon can Bench or evolve this turn."""
        if card_id in {MURKROW, PORYGON}:
            return not self._own_bench_full(state)
        if card_id == HONCHKROW:
            return self._has_murkrow_ready_to_evolve(state)
        if card_id == PORYGON2:
            return self._has_porygon_ready_to_evolve(state)
        return (
            card_id == ARTICUNO
            and self._articuno_is_needed(state)
            and not self._own_bench_full(state)
        )

    def _canonical_night_stretcher_is_productive(self, state: GameState) -> bool:
        """Return the canonical Night Stretcher predicate used by scoring."""
        return self._night_stretcher_is_productive(state)

    def _has_porygon_ready_to_evolve(self, state: GameState) -> bool:
        player = self._own_player(state)
        return bool(
            player
            and any(
                pokemon is not None and pokemon.card_id == PORYGON
                for pokemon in [player.active, *player.bench]
            )
        )

    def _ultra_ball_is_productive(self, state: GameState) -> bool:
        """Require both a useful Pokémon target and two disposable hand cards."""
        player = self._own_player(state)
        if player is None or player.deck_count == 0 or player.hand_count < 3:
            return False
        if self._headset_line_is_lethal(state):
            return False
        useful_target = (
            self._proton_targets_exist(state)
            or self._has_murkrow_ready_to_evolve(state)
            or self._has_porygon_ready_to_evolve(state)
        )
        if self._ultra_ball_completes_r_command(state):
            return True
        disposable = sum(
            (
                self._card_id_from_value(card) != NIGHT_STRETCHER
                or not self._night_stretcher_is_productive(state)
            )
            and not self._is_energy_card(
                self._card_id_from_value(card),
                self.catalog.get_card(str(self._card_id_from_value(card))),
            )
            and not self._is_rocket_supporter(
                self._card_id_from_value(card),
                self.catalog.get_card(str(self._card_id_from_value(card))),
            )
            for card in self._hand_cards(state)
        )
        return useful_target and disposable >= 2

    def _ultra_ball_completes_r_command(self, state: GameState) -> bool:
        """Return whether Ultra Ball can discard exactly two Supporters for a winning R Command."""
        required = self._r_command_supporters_needed(state)
        discard = self._rocket_supporters_in_discard(state)
        deficit = required - discard
        if deficit != 2 or not self._has_porygon_ready_to_evolve(state):
            return False
        supporter_discards = sum(
            self._is_rocket_supporter(self._card_id_from_value(card), card)
            for card in self._hand_cards(state)
        )
        return supporter_discards >= 2

    def _miracle_headset_emergency_is_useful(self, state: GameState) -> bool:
        """Return whether Headset can restore a collapsed, supporter-poor hand."""
        player = self._own_player(state)
        if player is None or player.deck_count == 0 or player.hand_count > 3:
            return False
        if self._has_playable_supporter(state):
            return False
        has_ariana = any(self._card_id_from_value(card) == ARIANA for card in player.discard)
        return bool(has_ariana and self._ariana_draw_count(state) > player.hand_count)

    def _miracle_headset_is_useful(self, state: GameState) -> bool:
        """Reserve the ACE SPEC for two KO supporters or an Ariana emergency."""
        player = self._own_player(state)
        if player is None or player.deck_count == 0:
            return False
        discarded = self._rocket_supporters_in_discard(state)
        needed = self._supporters_needed_for_ko(state) - self._effective_supporters_in_hand(state)
        return bool(
            discarded >= 1
            and needed > 0
            and min(2, discarded) >= needed
            or (
                self._effective_supporters_in_hand(state) == 0
                and any(self._card_id_from_value(card) == ARIANA for card in player.discard)
                and self._ariana_draw_count(state) > player.hand_count
            )
            or self._miracle_headset_emergency_is_useful(state)
        )

    def _opponent_deck_is_low(self, state: GameState, threshold: int = 3) -> bool:
        """Return whether the opponent has no more than the given deck reserve."""
        opponent = self._opponent_player(state)
        return bool(opponent is not None and int(opponent.deck_count) <= threshold)

    def _headset_line_is_lethal(self, state: GameState) -> bool:
        """Return whether Miracle Headset supplies the missing Rocket damage."""
        if not self._card_in_hand(state, MIRACLE_HEADSET):
            return False
        active = self._own_active(state)
        if active is None or active.card_id != HONCHKROW:
            return False
        recoverable = min(2, self._rocket_supporters_in_discard(state))
        return (
            recoverable > 0
            and self._effective_supporters_in_hand(state) < self._supporters_needed_for_ko(state)
            and self._effective_supporters_in_hand(state) + recoverable
            >= self._supporters_needed_for_ko(state)
        )

    def _archer_can_draw_five(self, state: GameState) -> bool:
        """Return whether Archer can legally complete its draw-five effect."""
        player = self._own_player(state)
        if player is None or player.deck_count + max(0, player.hand_count - 1) < 5:
            return False
        return True

    def _archer_is_safe_and_useful(self, state: GameState, candidate: Candidate) -> bool:
        """Use Archer after any public own KO when its redraw is feasible."""
        if self._opponent_deck_is_low(state):
            return False
        if not self._archer_can_draw_five(state):
            return False
        prior_ko = self._own_ko_observed or self._truthy(
            candidate.option, "eligibleAfterKo", "ownKo", "beneficial"
        )
        return prior_ko and not self._visible_non_archer_line_exists(state)

    def _archer_preserves_nonlethal_rocket_resources(
        self, state: GameState, candidate: Candidate
    ) -> bool:
        """Return whether a legal Archer redraw beats a nonlethal Supporter discard.

        This is intentionally limited to the public post-KO Archer window.  It
        does not assume that a redraw finds a particular hidden card.
        """
        return bool(
            self._own_ko_observed
            and self._archer_can_draw_five(state)
            and self._effective_supporters_in_hand(state) > 0
            and self._own_active_card_id(state) == HONCHKROW
            and self._effective_supporters_in_hand(state) < self._supporters_needed_for_ko(state)
        )

    def _archer_alakazam_hand_pressure(self, state: GameState) -> bool:
        """Return whether public Alakazam-line evidence makes Archer more valuable."""
        player = self._own_player(state)
        opponent = self._opponent_player(state)
        return bool(
            player
            and opponent
            and bool(self._visible_opponent_card_ids(state) & {ABRA, KADABRA, ALAKAZAM})
            and opponent.hand_count > player.hand_count
        )

    def _visible_non_archer_line_exists(self, state: GameState) -> bool:
        """Reject Archer while a card can still change this turn's public board."""
        return bool(
            (self._card_in_hand(state, ARIANA) and self._ariana_is_safe_and_useful(state))
            or (self._proton_setup_is_useful(state) and self._card_in_hand(state, PROTON))
            or (self._card_in_hand(state, ROTO_STICK) and self._roto_stick_is_needed(state))
            or (
                self._card_in_hand(state, GIOVANNI)
                and self._giovanni_switch_line_is_productive(state)
            )
            or (
                self._card_in_hand(state, PETREL)
                and (
                    self._has_murkrow_ready_to_evolve(state)
                    or self._ultra_ball_is_productive(state)
                )
            )
            or self._has_live_basic_development(state)
            or self._has_live_energy_attachment(state)
        )

    def _has_live_basic_development(self, state: GameState) -> bool:
        """Return whether a Basic in hand can legally improve the current field."""
        return bool(
            not self._own_bench_full(state)
            and any(
                self._card_id_from_value(card) in {MURKROW, PORYGON, ARTICUNO}
                for card in self._hand_cards(state)
            )
        )

    def _has_live_energy_attachment(self, state: GameState) -> bool:
        """Return whether an unused Energy can complete an available attack line."""
        if state.energy_attached:
            return False
        player = self._own_player(state)
        if player is None or not any(
            self._is_energy_card(
                self._card_id_from_value(card),
                self.catalog.get_card(str(self._card_id_from_value(card))),
            )
            for card in self._hand_cards(state)
        ):
            return False
        return any(
            pokemon is not None
            and pokemon.card_id in {MURKROW, HONCHKROW, PORYGON2}
            and self._energy_units_for_pokemon(pokemon)
            < self._attack_energy_target(int(pokemon.card_id))
            for pokemon in [player.active, *player.bench]
        )

    def _giovanni_pivot_is_productive(self, state: GameState) -> bool:
        """Allow Giovanni to free an exposed Porygon for a ready Bench attacker."""
        player = self._own_player(state)
        if (
            player is None
            or player.active is None
            or player.active.card_id not in {PORYGON, PORYGON2}
        ):
            return False
        return any(
            pokemon is not None
            and pokemon.card_id == HONCHKROW
            and self._energy_units_for_pokemon(pokemon) >= self._attack_energy_target(HONCHKROW)
            for pokemon in player.bench
        )

    def _giovanni_switch_line_is_productive(self, state: GameState) -> bool:
        """Return whether Giovanni converts a ready bench attacker into an immediate KO."""
        player = self._own_player(state)
        opponent = self._opponent_player(state)
        if player is None or opponent is None:
            return False
        targets = [pokemon for pokemon in [opponent.active, *opponent.bench] if pokemon is not None]
        for pokemon in player.bench:
            if pokemon is None:
                continue
            energy = self._energy_units_for_pokemon(pokemon)
            if pokemon.card_id == HONCHKROW and energy >= self._attack_energy_target(HONCHKROW):
                damage = max(0, self._effective_supporters_in_hand(state) - 1) * 60
                if any(damage >= max(0, int(target.hp)) > 0 for target in targets):
                    return True
            if pokemon.card_id == PORYGON2 and energy >= self._attack_energy_target(PORYGON2):
                damage = (self._rocket_supporters_in_discard(state) + 1) * 20
                if any(damage >= max(0, int(target.hp)) > 0 for target in targets):
                    return True
        return False

    @staticmethod
    def _is_energy_card(card_id: int, card: Mapping[str, Any] | None) -> bool:
        return card_id in {ROCKET_ENERGY, IGNITION_ENERGY} or (
            isinstance(card, Mapping) and int(card.get("cardType", -1)) in {5, 6}
        )

    def _target_opponent_pokemon(self, state: GameState, candidate: Candidate) -> Any:
        opponent = self._opponent_player(state)
        if opponent is None:
            return None
        target_serial = self._feature_int(candidate, "target_serial")
        if self._persistent_target_serial is not None and not target_serial:
            target_serial = self._persistent_target_serial
        target_id = (
            self._feature_int(candidate, "target_card_id")
            or self._persistent_target_card_id
            or int(candidate.option.get("targetCardId", 0) or 0)
        )
        return next(
            (
                p
                for p in [opponent.active, *opponent.bench]
                if p is not None
                and (not target_serial or p.serial == target_serial)
                and (not target_id or p.card_id == target_id)
            ),
            opponent.active,
        )

    def _effective_target_hp(self, state: GameState, target: Any) -> int:
        if target is None:
            return 0
        card = self.catalog.get_card(str(target.card_id)) or {}
        weakness = card.get("weakness") or card.get("weaknesses")
        attacker = self._own_active(state)
        attacker_card = self.catalog.get_card(str(attacker.card_id)) if attacker else None
        if types_equal(weakness, (attacker_card or {}).get("energyType")):
            return (max(0, int(target.hp)) + 1) // 2
        return max(0, int(target.hp))

    def _ignition_attachment_is_productive(self, state: GameState, candidate: Candidate) -> bool:
        target_id = self._feature_int(candidate, "target_card_id")
        target_energy = self._target_energy_units(state, candidate)
        completes = target_energy + 3 >= self._attack_energy_target(target_id)
        explicit_damage = max(
            self._metadata_int(candidate.attack, "damage"),
            self._metadata_int(candidate.option, "damage"),
            self._metadata_int(candidate.option, "expectedDamage"),
        )
        return (
            completes
            and (
                explicit_damage > 0
                or bool(
                    candidate.option.get("enablesAttack", candidate.option.get("enables", False))
                )
            )
            and target_id in {HONCHKROW, PORYGON2, MURKROW}
        )

    def _deceit_is_decisive(self, state: GameState, candidate: Candidate, damage: int) -> bool:
        target = self._target_opponent_pokemon(state, candidate)
        return (
            damage > 0
            or (target is not None and damage >= self._effective_target_hp(state, target))
            or self._truthy(candidate.option, "decisive", "win", "gameOver")
        )

    def _deceit_is_survival_line(self, state: GameState) -> bool:
        """Allow Deceit only as a conservative no-Supporter, low-hand Ariana line."""
        player = self._own_player(state)
        return bool(
            player
            and self._effective_supporters_in_hand(state) == 0
            and player.hand_count <= 2
            and self._supporter_copies_remaining(state, ARIANA) > 0
        )

    def _supporter_copies_remaining(self, state: GameState, card_id: int) -> int:
        """Count a four-copy Supporter outside actor-visible non-deck zones."""
        player = self._own_player(state)
        if player is None:
            return 0
        known = sum(
            self._card_id_from_value(card) == card_id
            for card in list(player.hand or ()) + list(player.discard) + list(player.prize)
        )
        return max(0, 4 - known)

    def _torment_single_attack_lock(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether Torment disables the sole attack on a lone opposing Pokémon."""
        opponent = self._opponent_player(state)
        if opponent is None or opponent.active is None:
            return False
        field = [opponent.active, *opponent.bench]
        if sum(pokemon is not None for pokemon in field) != 1:
            return False
        card = self.catalog.get_card(str(opponent.active.card_id)) or {}
        attacks = card.get("attacks")
        return bool(
            isinstance(attacks, Sequence)
            and not isinstance(attacks, (str, bytes))
            and len(attacks) == 1
            and self._truthy(candidate.option, "preventsAttack", "disablesAttack")
        )

    def _has_murkrow_ready_to_evolve(self, state: GameState) -> bool:
        """Return whether a visible Murkrow can support Honchkrow search."""
        player = self._own_player(state)
        return bool(
            player
            and any(
                pokemon is not None and pokemon.card_id == MURKROW and not pokemon.appear_this_turn
                for pokemon in [player.active, *player.bench]
            )
        )

    def _card_copies_remaining(self, state: GameState, card_id: int) -> int:
        """Count declared copies not present in actor-visible zones."""
        availability = self.prize_check.availability(card_id) if self.prize_check else None
        if availability is not None and availability.searchable_exact is not None:
            return int(availability.searchable_exact)
        player = self._own_player(state)
        if player is None:
            return 0
        known = sum(
            pokemon is not None and pokemon.card_id == card_id
            for pokemon in [player.active, *player.bench]
        )
        known += sum(
            self._card_id_from_value(card) == card_id
            for card in list(player.hand or ()) + list(player.discard) + list(player.prize)
        )
        return int(max(0, self._declared_count(card_id) - known))

    def _pokepad_honchkrow_is_useful(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether Poké Pad fetching Honchkrow has an immediate purpose."""
        if (
            self._own_field_count(state) <= 1
            and self._proton_targets_remaining(state).get(MURKROW, 0) > 0
            and any(
                self._card_id_from_value(card) in {MURKROW, PORYGON}
                for card in self._hand_cards(state)
            )
        ):
            return False
        if self._card_in_hand(state, HONCHKROW) and not self._has_murkrow_ready_to_evolve(state):
            return False
        if self._has_murkrow_ready_to_evolve(state) or self._honchkrow_ready_to_attack(state):
            return True
        player = self._own_player(state)
        if self._own_turn_number(state) == 1 and player is not None:
            return any(
                pokemon is not None and pokemon.card_id == MURKROW
                for pokemon in [player.active, *player.bench]
            )
        return self._articuno_hand_reduction_needed(state, candidate)

    def _porygon2_search_is_valid(self, state: GameState) -> bool:
        """Return whether a Porygon2 search has a visible Porygon to evolve."""
        return self._has_porygon_ready_to_evolve(state)

    def _giovanni_target_score(
        self, state: GameState, candidate: Candidate
    ) -> tuple[float, list[str]]:
        """Rank targets by immediate win, guaranteed prizes, weakness, then Energy."""
        target = self._target_opponent_pokemon(state, candidate)
        if target is None:
            return 0.0, ["giovanni_no_target_data"]
        declared_prizes = candidate.option.get(
            "prizes", candidate.option.get("prizeCount", candidate.option.get("prizeValue"))
        )
        prizes = (
            int(declared_prizes)
            if isinstance(declared_prizes, int) and not isinstance(declared_prizes, bool)
            else self.catalog.get_traits(target.card_id).base_prize_value
        )
        hp = max(0, int(getattr(target, "hp", 0)) - self._froslass_ping_for_target(state, target))
        guaranteed = self._truthy(candidate.option, "ko", "knockout", "isKo")
        economic = self._economic_two_prize_ko(state, target, prizes)
        opponent = self._opponent_player(state)
        bench_target = bool(opponent and opponent.active is not target)
        energy = self._energy_units_for_pokemon(target)
        weakness = self._target_has_darkness_weakness(target)
        player = self._own_player(state)
        wins = guaranteed and player is not None and prizes >= len(player.prize)
        reasons = ["giovanni_target_fallback"]
        score = 900.0 + max(0, 300 - hp)
        if wins:
            score += 6000.0
            reasons = ["giovanni_immediate_win_target"]
        elif guaranteed:
            score += 4000.0 + prizes * 500.0
            reasons = ["giovanni_guaranteed_ko_highest_prize"]
        elif weakness:
            score += 1200.0
            reasons = ["giovanni_dark_weakness_target"]
        elif bench_target and energy > 0:
            score += 900.0 + energy * 40.0
            reasons = ["giovanni_energized_bench_target"]
        if economic:
            reasons.append("economic_two_prize_ko")
        if target.card_id == 140 and economic:
            reasons.append("giovanni_fezandipiti_two_prize_ko")
        if self._persistent_target_serial == getattr(target, "serial", None):
            reasons.append("preserve_persistent_effect_target")
        return score + (900.0 if economic else 0.0), reasons

    def _target_has_darkness_weakness(self, target: Any) -> bool:
        """Return whether public card metadata gives the target Darkness weakness."""
        card = self.catalog.get_card(str(getattr(target, "card_id", 0))) or {}
        weakness = card.get("weakness")
        if isinstance(weakness, Mapping):
            return self._metadata_int(weakness, "type") == 5
        return self._metadata_int(card, "weaknessType") == 5

    def _economic_two_prize_ko(self, state: GameState, target: Any, prizes: int) -> bool:
        """Return whether a visible attack takes a multi-Prize target economically."""
        if prizes < 2 or target is None:
            return False
        hp = max(0, int(target.hp))
        player = self._own_player(state)
        attackers = [player.active, *player.bench] if player is not None else []
        available = 0
        for attacker in attackers:
            if attacker is None:
                continue
            energy = self._energy_units_for_pokemon(attacker)
            if attacker.card_id == HONCHKROW and energy >= self._attack_energy_target(HONCHKROW):
                available = max(available, self._effective_supporters_in_hand(state) * 60)
            elif attacker.card_id == PORYGON2 and energy >= self._attack_energy_target(PORYGON2):
                available = max(available, self._rocket_supporters_in_discard(state) * 20)
            elif attacker.card_id not in {MURKROW, PORYGON}:
                card = self.catalog.get_card(str(attacker.card_id)) or {}
                if any(
                    self._metadata_int(self.catalog.get_attack(str(attack_id)) or {}, "damage")
                    >= hp
                    for attack_id in card.get("attacks", [])
                ):
                    available = max(available, 100)
        return available >= hp > 0

    def _porygon2_prize_race_line(self, state: GameState) -> bool:
        """Return whether Porygon2 can finish the visible Prize race in two attacks."""
        player = self._own_player(state)
        opponent = self._opponent_player(state)
        if player is None or opponent is None or not player.prize:
            return False
        porygon = next(
            (
                pokemon
                for pokemon in [player.active, *player.bench]
                if pokemon and pokemon.card_id == PORYGON2
            ),
            None,
        )
        if porygon is None or self._energy_units_for_pokemon(porygon) < self._attack_energy_target(
            PORYGON2
        ):
            return False
        damage = self._rocket_supporters_in_discard(state) * 20
        targets = [pokemon for pokemon in [opponent.active, *opponent.bench] if pokemon]
        return (
            len(targets) <= 2
            and sum(
                self.catalog.get_traits(str(target.card_id)).base_prize_value for target in targets
            )
            >= len(player.prize)
            and all(max(0, int(target.hp)) <= damage for target in targets)
        )

    def _discard_is_required_for_ko(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether the SDK explicitly marks this discard as KO-enabling."""
        return self._truthy(
            candidate.option,
            "requiredForKo",
            "enablesKo",
            "enablesKO",
            "koLine",
            "lethal",
        ) or bool(candidate.features.get("required_for_ko", False))

    def _honchkrow_ready_to_attack(self, state: GameState) -> bool:
        """Return whether a visible Honchkrow has its declared attack cost."""
        player = self._own_player(state)
        if player is None:
            return False
        return any(
            pokemon is not None
            and pokemon.card_id == HONCHKROW
            and self._energy_units_for_pokemon(pokemon) >= self._attack_energy_target(HONCHKROW)
            for pokemon in [player.active, *player.bench]
        )

    @staticmethod
    def _card_selected_from_night_stretcher(candidate: Candidate) -> bool:
        """Return whether a card option is the payload of Night Stretcher."""
        source = candidate.option.get("sourceCardId", candidate.option.get("sourceId", 0))
        return bool(source == NIGHT_STRETCHER)

    def _visible_opponent_card_ids(self, state: GameState) -> set[int]:
        """Return Pokémon identifiers visible on the opposing field."""
        opponent = self._opponent_player(state)
        if opponent is None:
            return set()
        return {
            int(pokemon.card_id)
            for pokemon in [opponent.active, *opponent.bench]
            if pokemon is not None and isinstance(pokemon.card_id, int)
        }

    def _articuno_hand_reduction_needed(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether Articuno is a useful hand-size reduction play."""
        return bool(
            candidate.option.get("reducesHand", False)
            or candidate.option.get("handReduction", False)
            or (self._own_player(state) is not None and self._own_player(state).hand_count >= 8)
        )

    def _supporter_ids(self) -> set[int]:
        """Return all Team Rocket supporter identifiers in this deck."""
        return {ARIANA, ARCHER, GIOVANNI, PETREL, PROTON}

    def _hand_cards(self, state: GameState) -> list[Any]:
        """Return the visible own hand, or an empty list when it is hidden."""
        player = self._own_player(state)
        return list(player.hand or ()) if player is not None and player.hand is not None else []

    def _supporters_in_hand(self, state: GameState | None = None) -> int:
        """Count visible Team Rocket supporters in hand."""
        if state is None:
            state = self._energy_context_state
        if state is None:
            return 0
        return sum(
            1
            for card in self._hand_cards(state)
            if self._is_rocket_supporter(
                self._card_id_from_value(card),
                self.catalog.get_card(str(self._card_id_from_value(card))) or {},
            )
        )

    def _effective_supporters_in_hand(self, state: GameState) -> int:
        """Count visible supporters plus a usable Transceiver before the Supporter play."""
        supporters = self._supporters_in_hand(state)
        if state.supporter_played:
            return supporters
        transceivers = sum(
            1 for card in self._hand_cards(state) if self._card_id_from_value(card) == TRANSCEIVER
        )
        if transceivers == 0:
            return supporters
        remaining = self._roto_remaining_supporters(state)
        if remaining <= 0:
            return supporters
        return supporters + min(transceivers, remaining)

    def _supporters_in_hand_after(
        self, excluded_card_id: int, state: GameState | None = None
    ) -> int:
        """Count supporters after hypothetically playing one supporter."""
        return max(
            0, self._supporters_in_hand(state) - int(excluded_card_id in self._supporter_ids())
        )

    def _pokemon_is_ready(self, state: GameState, candidate: Candidate) -> bool:
        energy_count = self._target_energy_units(state, candidate)
        if energy_count:
            return energy_count >= self._attack_energy_target(
                self._feature_int(candidate, "card_id")
            )
        player = self._own_player(state)
        return bool(
            player
            and any(
                pokemon is not None
                and pokemon.card_id == self._feature_int(candidate, "card_id")
                and self._energy_units_for_pokemon(pokemon)
                >= self._attack_energy_target(int(pokemon.card_id))
                for pokemon in player.bench
            )
        ) or bool(candidate.option.get("ready", candidate.option.get("energized", False)))

    def _giovanni_is_lethal_or_promoting(self, state: GameState, candidate: Candidate) -> bool:
        if self._truthy(candidate.option, "win", "gameOver", "ko", "knockout"):
            return True
        player = self._own_player(state)
        if player is None:
            return False
        return (
            any(
                pokemon is not None
                and pokemon.card_id == HONCHKROW
                and self._energy_units_for_pokemon(pokemon) >= self._attack_energy_target(HONCHKROW)
                for pokemon in player.bench
            )
            and self._effective_opponent_hp(state) <= 100
        )

    def _supporter_zone_counts(self, state: GameState) -> dict[str, int]:
        """Count known supporters by zone using conservative hidden-Prize handling."""
        player = self._own_player(state)
        if player is None:
            return {"hand": 0, "deck": 0, "discard": 0, "prize": 0, "hidden_prize": 0}
        hand = self._count_supporters(player.hand or ())
        discard = self._count_supporters(player.discard)
        prize = self._count_supporters(player.prize)
        hidden_prize = sum(1 for card in player.prize if self._card_id_from_value(card) == 0)
        known_total = hand + discard + prize + hidden_prize
        total = 20
        deck = max(0, total - known_total)
        return {
            "hand": hand,
            "deck": deck,
            "discard": discard,
            "prize": prize,
            "hidden_prize": hidden_prize,
        }

    def _count_supporters(self, cards: Sequence[Any]) -> int:
        """Count Team Rocket supporters in a visible card zone."""
        return sum(
            1
            for card in cards
            if self._is_rocket_supporter(
                self._card_id_from_value(card),
                self.catalog.get_card(str(self._card_id_from_value(card))) or {},
            )
        )

    def _own_bench_count(self, state: GameState) -> int:
        """Count occupied own Bench positions."""
        player = self._own_player(state)
        return sum(pokemon is not None for pokemon in player.bench) if player else 0

    def _supporters_needed_for_ko(self, state: GameState) -> int:
        """Return Rocket Feathers' exact public Supporter requirement for the Active."""
        opponent = self._opponent_player(state)
        target = opponent.active if opponent is not None else None
        if target is None:
            return 0
        candidate = Candidate(0, {"attackId": ROCKET_FEATHERS}, OptionType.ATTACK)
        damage_per_supporter = self._attack_damage(state, candidate, 60, target)
        if damage_per_supporter <= 0:
            return 0
        return (max(0, int(target.hp)) + damage_per_supporter - 1) // damage_per_supporter

    def _promotion_line_is_lethal(self, state: GameState, card_id: int) -> bool:
        """Return whether a visible promotion can attack lethally this turn."""
        player = self._own_player(state)
        opponent = self._opponent_player(state)
        target = opponent.active if opponent is not None else None
        if player is None or target is None:
            return False
        pokemon = next(
            (
                item
                for item in [player.active, *player.bench]
                if item is not None and item.card_id == card_id
            ),
            None,
        )
        if pokemon is None:
            return False
        energy = self._energy_units_for_pokemon(pokemon)
        if not state.energy_attached:
            energy += self._energy_units_in_hand(state, IGNITION_ENERGY)
        if card_id == PORYGON2:
            return energy >= self._attack_energy_target(
                PORYGON2
            ) and self._rocket_supporters_in_discard(state) * 20 >= max(0, int(target.hp))
        if card_id == HONCHKROW:
            return energy >= self._attack_energy_target(HONCHKROW) and self._supporters_in_hand(
                state
            ) * 60 >= max(0, int(target.hp))
        return False

    def _energy_units_in_hand(self, state: GameState, card_id: int | None = None) -> int:
        """Count attachable attack-energy units in the visible hand."""
        total = 0
        for card in self._hand_cards(state):
            current = self._card_id_from_value(card)
            if card_id is not None and current != card_id:
                continue
            if current == ROCKET_ENERGY:
                total += 2
            elif current == IGNITION_ENERGY:
                total += 3
            elif self._is_energy_card(current, self.catalog.get_card(str(current))):
                total += 1
        return total

    def _r_command_is_best_damage_line(self, state: GameState) -> bool:
        """Return whether public discard makes Porygon2 the best current attacker."""
        opponent_hp = self._raw_opponent_hp(state)
        r_command = self._rocket_supporters_in_discard(state) * 20
        feathers = self._effective_supporters_in_hand(state) * 60
        hammer = 100
        if r_command >= opponent_hp > 0 and feathers < opponent_hp:
            return True
        return r_command > max(feathers, hammer)

    def r_command_knocks_out_active(
        self, state: GameState, *, discarded_supporters: int | None = None
    ) -> bool:
        """Return whether public R Command damage knocks out the opposing Active.

        Args:
            state: Current public game state.
            discarded_supporters: Optional public projected count after a known effect.

        Returns:
            Whether the public damage reaches the opposing Active's current HP.
        """
        opponent = self._opponent_player(state)
        active = opponent.active if opponent is not None else None
        if active is None:
            return False
        supporters = (
            self._rocket_supporters_in_discard(state)
            if discarded_supporters is None
            else discarded_supporters
        )
        candidate = Candidate(0, {"attackId": R_COMMAND}, OptionType.ATTACK)
        damage = self._attack_damage(state, candidate, supporters * 20, active)
        return damage >= max(0, int(active.hp)) > 0

    def _r_command_wins_game(self, state: GameState) -> bool:
        """Return whether the visible Porygon2 R Command ends the Prize race."""
        target = self._opponent_player(state)
        active = target.active if target is not None else None
        if active is None or active.hp <= 0:
            return False
        if not self.r_command_knocks_out_active(state):
            return False
        prizes_needed = len(self._own_player(state).prize) if self._own_player(state) else 0
        prize_value = self._active_target_prize_value(state)
        return prizes_needed > 0 and prize_value >= prizes_needed

    def _r_command_supporters_needed(self, state: GameState) -> int:
        """Return the exact discard-supporter count needed for the visible KO."""
        opponent = self._opponent_player(state)
        target = opponent.active if opponent is not None else None
        if target is None:
            return 0
        candidate = Candidate(0, {"attackId": R_COMMAND}, OptionType.ATTACK)
        damage_per_supporter = self._attack_damage(state, candidate, 20, target)
        if damage_per_supporter <= 0:
            return 0
        return (max(0, int(target.hp)) + damage_per_supporter - 1) // damage_per_supporter

    def _roto_can_close_r_command_line(self, state: GameState) -> bool:
        """Return whether Roto can provide the final supporter for Porygon2."""
        active = self._own_active(state)
        if (
            active is None
            or active.card_id != PORYGON2
            or self._energy_units_for_pokemon(active) < self._attack_energy_target(PORYGON2)
        ):
            return False
        needed = self._r_command_supporters_needed(state)
        discard = self._rocket_supporters_in_discard(state)
        return bool(
            needed > discard
            and needed - discard == 1
            and self._roto_remaining_supporters(state) > 0
        )

    def _porygon2_terminal_promotion_available(
        self, state: GameState, candidate: Candidate
    ) -> bool:
        """Return whether promotion plus an Ignition attachment wins next turn."""
        if self._feature_int(candidate, "card_id") != PORYGON2:
            return False
        if not self._r_command_wins_game(state):
            return False
        if self._pokemon_is_ready(state, candidate):
            return False
        return bool(self._card_in_hand(state, IGNITION_ENERGY) and not state.energy_attached)

    def _porygon2_next_turn_setup_available(self, state: GameState) -> bool:
        """Return whether a visible Porygon2 line can be completed on the next turn."""
        player = self._own_player(state)
        if player is None:
            return False
        porygon2 = next(
            (
                pokemon
                for pokemon in [player.active, *player.bench]
                if pokemon is not None and pokemon.card_id == PORYGON2
            ),
            None,
        )
        if porygon2 is None:
            return False
        target_energy = self._attack_energy_target(PORYGON2)
        energy = self._energy_units_for_pokemon(porygon2)
        if energy >= target_energy:
            return True
        return bool(
            not state.energy_attached
            and self._card_in_hand(state, IGNITION_ENERGY)
            and energy + 3 >= target_energy
        )

    def _porygon2_prize_pressure_line(self, state: GameState) -> bool:
        """Return whether Porygon2 pressure is relevant to the remaining prize race."""
        player = self._own_player(state)
        opponent = self._opponent_player(state)
        if player is None or opponent is None or not player.prize:
            return False
        prizes_remaining = len(player.prize)
        if prizes_remaining <= 0:
            return False
        projected_damage = self._rocket_supporters_in_discard(state) * 20
        opponent_hp = self._raw_opponent_hp(state)
        if projected_damage >= opponent_hp > 0:
            return True
        if prizes_remaining <= 2 and self._porygon2_next_turn_setup_available(state):
            target_prize_value = self._active_target_prize_value(state)
            return projected_damage >= max(60, min(opponent_hp, target_prize_value * 20))
        return False

    def _active_target_prize_value(self, state: GameState) -> int:
        """Return the effective public Prize value of the opposing Active."""
        active = self._opponent_player(state)
        pokemon = active.active if active is not None else None
        if pokemon is None:
            return 0
        if self.prize_map is not None:
            for target in self.prize_map.targets:
                if target.zone == "active" and target.card_id == pokemon.card_id:
                    return target.effective_prize_value
        return self.catalog.get_traits(str(pokemon.card_id)).base_prize_value

    def _active_has_immediate_ko(self, state: GameState) -> bool:
        """Return whether the current Active has a public, legal immediate KO."""
        active = self._own_active(state)
        return bool(active and self._pokemon_has_immediate_ko(state, active))

    def _pokemon_has_immediate_ko(self, state: GameState, pokemon: Any) -> bool:
        """Return whether a Pokémon's public resources can KO the opposing Active.

        This intentionally uses current HP and the common public damage pipeline,
        including attack costs, weakness, resistance, and active prevention.
        """
        opponent = self._opponent_player(state)
        target = opponent.active if opponent is not None else None
        if target is None or max(0, int(target.hp)) == 0:
            return False
        card_id = int(pokemon.card_id) if isinstance(pokemon.card_id, int) else 0
        choices: list[tuple[int, int]] = []
        if card_id == HONCHKROW:
            choices.extend(
                [
                    (ROCKET_FEATHERS, self._effective_supporters_in_hand(state) * 60),
                    (HAMMER_IN, 100),
                ]
            )
        elif card_id == PORYGON2:
            choices.append((R_COMMAND, self._rocket_supporters_in_discard(state) * 20))
        card = self.catalog.get_card(str(card_id)) or {}
        for attack_id in card.get("attacks", []):
            if isinstance(attack_id, int) and attack_id not in {
                ROCKET_FEATHERS,
                R_COMMAND,
                HAMMER_IN,
            }:
                attack = self.catalog.get_attack(str(attack_id)) or {}
                choices.append((attack_id, self._metadata_int(attack, "damage")))
        attacker_card = self.catalog.get_card(str(card_id)) or {}
        for attack_id, base_damage in choices:
            attack = self.catalog.get_attack(str(attack_id)) or {}
            if base_damage <= 0 or not self._attack_cost_is_satisfied(pokemon, attack):
                continue
            damage = calculate_damage(
                base_damage,
                attacker_card.get("energyType"),
                self.catalog.get_card(str(target.card_id)) or {},
                prevented=has_splashing_dodge_protection(state.raw, target.serial),
                state_raw=state.raw,
                defender_serial=target.serial,
            )
            if damage >= max(0, int(target.hp)):
                return True
        return False

    def _attack_cost_is_satisfied(self, pokemon: Any, attack: Mapping[str, Any]) -> bool:
        """Return whether public energy units pay an attack's declared cost."""
        energies = attack.get("energies", [])
        return isinstance(energies, list) and len(energies) <= self._energy_units_for_pokemon(
            pokemon
        )

    def _attack_has_committed_ko(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether a resource-intensive attack converts into the current KO."""
        target = self._target_opponent_pokemon(state, candidate)
        if target is None:
            return True
        attack_id = self._attack_id(candidate)
        if attack_id not in {ROCKET_FEATHERS, R_COMMAND, HAMMER_IN}:
            return True
        target_hp = max(0, int(target.hp))
        if attack_id == ROCKET_FEATHERS:
            base_damage = self._effective_supporters_in_hand(state) * 60
        elif attack_id == R_COMMAND:
            base_damage = self._rocket_supporters_in_discard(state) * 20
        else:
            base_damage = 100
        damage = self._attack_damage(state, candidate, base_damage, target)
        return damage >= target_hp > 0

    def _candidate_visible_damage(self, candidate: Candidate) -> int:
        """Return deterministic damage declared by a legal attack candidate."""
        return max(
            self._metadata_int(candidate.attack, "damage"),
            self._metadata_int(candidate.option, "damage"),
            self._metadata_int(candidate.option, "expectedDamage"),
        )

    def _opponent_active_card_id(self, state: GameState) -> int:
        """Return the visible opposing Active card identifier."""
        opponent = self._opponent_player(state)
        if opponent is None or opponent.active is None:
            return 0
        return int(opponent.active.card_id) if isinstance(opponent.active.card_id, int) else 0

    def _effective_opponent_hp(self, state: GameState) -> int:
        """Estimate active HP after public weakness and resistance metadata."""
        opponent = self._opponent_player(state)
        if opponent is None or opponent.active is None:
            return 0
        hp = max(0, int(opponent.active.hp))
        card = self.catalog.get_card(str(opponent.active.card_id)) or {}
        weakness = card.get("weakness") or card.get("weaknesses")
        resistance = card.get("resistance") or card.get("resistances")
        attacker = self._own_active(state)
        attacker_card = self.catalog.get_card(str(attacker.card_id)) if attacker else None
        attacker_type = (attacker_card or {}).get("energyType")
        if types_equal(weakness, attacker_type):
            hp = (hp + 1) // 2
        if types_equal(resistance, attacker_type):
            hp += 30
        return max(0, hp - self._froslass_ping_for_target(state, opponent.active))

    def _froslass_ping_for_target(self, state: GameState, target: Any | None) -> int:
        """Return the cumulative post-attack Froslass ping for an Ability Pokémon."""
        if target is None:
            return 0
        card = self.catalog.get_card(str(getattr(target, "card_id", 0))) or {}
        if not card.get("skills"):
            return 0
        opponent = self._opponent_player(state)
        froslasses = sum(
            pokemon is not None and pokemon.card_id == FROSLASS
            for pokemon in ([opponent.active, *opponent.bench] if opponent is not None else [])
        )
        return 10 * int(froslasses)

    def _raw_opponent_hp(self, state: GameState) -> int:
        """Return the opposing Active's remaining HP without attack-specific modifiers."""
        opponent = self._opponent_player(state)
        return max(0, int(opponent.active.hp)) if opponent and opponent.active else 0

    def _productive_line_available(self, state: GameState) -> bool:
        """Return whether ending now would abandon a visible winning line."""
        player = self._own_player(state)
        if player is None:
            return False
        if any(
            (
                self._card_id_from_value(card) in {MURKROW, PORYGON}
                and not self._own_bench_full(state)
            )
            or self._card_id_from_value(card) in {HONCHKROW, PORYGON2}
            for card in self._hand_cards(state)
        ):
            return True
        if self._ultra_ball_is_productive(state) or self._night_stretcher_is_productive(state):
            return True
        if self._card_in_hand(state, ARIANA) and self._ariana_is_safe_and_useful(state):
            return True
        if self._factory_play_is_useful(state) or self._proton_setup_is_useful(state):
            return True
        if not player.hand:
            return self._night_stretcher_is_productive(state)
        has_energy = any(
            self._is_energy_card(
                self._card_id_from_value(card),
                self.catalog.get_card(str(self._card_id_from_value(card))),
            )
            for card in player.hand
        )
        if not has_energy:
            return False
        supporters = self._effective_supporters_in_hand(state)
        if self._own_active_card_id(state) in {HONCHKROW, PORYGON2} and supporters > 0:
            return self._supporters_needed_for_ko(state) <= supporters
        return (
            any(
                pokemon is not None
                and pokemon.card_id in {HONCHKROW, PORYGON2}
                and self._energy_units_for_pokemon(pokemon) + 1
                >= self._attack_energy_target(int(pokemon.card_id))
                for pokemon in player.bench
            )
            and supporters > 0
        )

    @staticmethod
    def _energy_units_for_pokemon(pokemon: Any) -> int:
        """Return attack-energy units, including the multi-unit Rocket cards."""
        units = 0
        entries = getattr(pokemon, "energies", ()) or ()
        ids = getattr(pokemon, "energy_card_ids", ()) or ()
        values = list(ids) if ids else list(entries)
        for energy in values:
            if isinstance(energy, Mapping):
                card_id = int(energy.get("id", energy.get("cardId", 0)) or 0)
            else:
                try:
                    card_id = int(energy)
                except (TypeError, ValueError):
                    card_id = 0
            units += 2 if card_id == ROCKET_ENERGY else 3 if card_id == IGNITION_ENERGY else 1
        return units

    def _target_energy_units(self, state: GameState, candidate: Candidate) -> int:
        """Resolve a target's typed energy total before trusting candidate metadata."""
        target_id = self._feature_int(candidate, "target_card_id")
        player = self._own_player(state)
        if player is not None:
            for pokemon in [player.active, *player.bench]:
                if pokemon is not None and int(pokemon.card_id or 0) == target_id:
                    return self._energy_units_for_pokemon(pokemon)
        return self._feature_int(candidate, "target_energy_count") or self._feature_int(
            candidate, "energy_count"
        )

    @staticmethod
    def _contains_type(value: Any, expected: str) -> bool:
        """Match SDK weakness/resistance representations by normalized text."""
        if isinstance(value, Mapping):
            return expected in str(value.get("type", value.get("name", ""))).casefold()
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return any(HonchkrowPorygonScorer._contains_type(item, expected) for item in value)
        return expected in str(value).casefold()

    @staticmethod
    def _card_id_from_value(card: Any) -> int:
        """Extract a numeric card identifier from a visible card value."""
        if isinstance(card, Mapping):
            value = card.get("id", card.get("cardId", 0))
            return int(value) if isinstance(value, int) and not isinstance(value, bool) else 0
        if isinstance(card, str) and card.isdigit():
            return int(card)
        return 0

    def _proton_was_used_previous_turn(self, state: GameState) -> bool:
        """Return whether public current-state history records prior Proton use."""
        if self._proton_used_previous_turn:
            return True
        logs = state.raw.get("logs", []) if isinstance(state.raw, Mapping) else []
        if not isinstance(logs, list):
            return False
        return any(
            isinstance(event, Mapping)
            and self._card_id_from_value(event) == PROTON
            and int(event.get("turn", state.turn)) < state.turn
            for event in logs
        )

    def _rocket_supporters_in_discard(self, state: GameState) -> int:
        player = self._own_player(state)
        if player is None:
            return 0
        return sum(
            1
            for card in player.discard
            if isinstance(card, Mapping)
            and self._is_rocket_supporter(
                int(card.get("id", card.get("cardId", 0)) or 0),
                self.catalog.get_card(str(card.get("id", card.get("cardId", 0)))) or {},
            )
        )

    def _active_has_rocket_energy(self, state: GameState) -> bool:
        active = self._own_active(state)
        return bool(
            active
            and any(
                isinstance(energy, Mapping)
                and int(energy.get("id", energy.get("cardId", 0)) or 0) == ROCKET_ENERGY
                for energy in active.energies
            )
        )

    @staticmethod
    def _is_rocket_supporter(card_id: int, card: Mapping[str, Any] | None) -> bool:
        return card_id in {ARIANA, ARCHER, GIOVANNI, PETREL, PROTON} or (
            isinstance(card, Mapping)
            and int(card.get("cardType", -1)) == 3
            and "team rocket" in str(card.get("name", "")).casefold()
        )

    @staticmethod
    def _attack_id(candidate: Candidate) -> int:
        value = candidate.option.get("attackId")
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value if isinstance(value, int) and not isinstance(value, bool) else 0


class HonchkrowPorygonAgent(HeuristicAgent):
    """Run the isolated Honchkrow/Porygon heuristic with shared legal plumbing."""

    def __init__(self, profile: DeckProfile, policy_variant: str | None = None) -> None:
        super().__init__(deck_profile=profile)
        self._scorer: HonchkrowPorygonScorer = HonchkrowPorygonScorer(
            deck_profile=profile, catalog=_CG_CATALOG
        )
        self._feature_extractor = SelectionFeatureExtractor(self._scorer)
        self._configured_profile = profile
        self._active_deck_profile = profile
        self._turn_ledger = TurnTacticalLedger()
        self._attack_sequence: AttackSequence | None = None
        self._switch_commitment: SwitchCommitment | None = None
        self._evolution_ko_commitment: EvolutionKoCommitment | None = None
        self._rocket_evolution_commitment: RocketEvolutionCommitment | None = None
        self._headset_turn: int | None = None
        self._roto_turn: int | None = None
        self._transceiver_turn: int | None = None
        self._previous_own_pokemon_keys: tuple[tuple[int, int | None], ...] | None = None
        self._previous_opponent_prize_count: int | None = None
        self._own_ko_turn: int | None = None
        self._match_ledger = MatchTacticalLedger()
        self.policy_variant = CANONICAL_POLICY_VARIANT
        self._scorer.set_reference_roto(False)

    @property
    def _uses_retreat_guard(self) -> bool:
        """Return whether the promoted committed-switch policy is active."""
        return True

    @property
    def _uses_supporter_lethal_commitment(self) -> bool:
        """Return whether exact Rocket Feathers commitments are enabled."""
        return True

    @property
    def _uses_resource_variant(self) -> bool:
        """Return whether Roto-Stick and Transceiver resource logic is enabled."""
        return True

    @property
    def _uses_expert_rounds_1_3(self) -> bool:
        """Return whether the first three ratified interview rounds are active."""
        return True

    @property
    def _uses_expert_turn_loop(self) -> bool:
        """Return whether the official Owner-defined turn loop is active."""
        return True

    @property
    def turn_ledger(self) -> TurnTacticalLedger:
        """Return the current turn's public tactical evidence."""
        return self._turn_ledger

    @property
    def match_ledger(self) -> MatchTacticalLedger:
        """Return public terminal-line evidence accumulated for this match."""
        return self._match_ledger

    def _update_alakazam_matchup(self, observation: Mapping[str, Any], state: GameState) -> None:
        """Preserve generic Alakazam evidence before applying deck-specific history."""
        super()._update_alakazam_matchup(observation, state)
        logs = observation.get("logs", [])
        used_previous_turn = False
        if isinstance(logs, list):
            used_previous_turn = any(
                isinstance(event, Mapping)
                and self._event_card_id(event) == PROTON
                and int(event.get("turn", state.turn)) < state.turn
                for event in logs
            )
        self._scorer.set_proton_used_previous_turn(used_previous_turn)

    @staticmethod
    def _event_card_id(event: Mapping[str, Any]) -> int:
        """Extract a card identifier from a public event record."""
        value = event.get("cardId", event.get("card_id", event.get("id", 0)))
        return int(value) if isinstance(value, int) and not isinstance(value, bool) else 0

    def start_match(self, deck: DeckDefinition) -> None:
        """Reset Honchkrow-only public history at the start of a match."""
        super().start_match(deck)
        self._scorer.set_proton_used_previous_turn(False)
        self._scorer.set_own_ko_observed(False)
        self._turn_ledger.reset(0)
        self._attack_sequence = None
        self._switch_commitment = None
        self._evolution_ko_commitment = None
        self._rocket_evolution_commitment = None
        self._headset_turn = None
        self._roto_turn = None
        self._transceiver_turn = None
        self._previous_own_pokemon_keys = None
        self._previous_opponent_prize_count = None
        self._own_ko_turn = None
        self._match_ledger.reset()

    @staticmethod
    def _own_pokemon_keys(state: GameState) -> tuple[tuple[int, int | None], ...]:
        """Return stable public identities for the actor's Active and Bench."""
        player = (
            state.players[state.your_index]
            if state.players and state.your_index < len(state.players)
            else None
        )
        if player is None:
            return ()
        pokemon = [item for item in [player.active, *player.bench] if item is not None]
        return tuple(
            sorted(
                (int(item.card_id), item.serial)
                for item in pokemon
                if isinstance(item.card_id, int)
            )
        )

    def _update_public_ko_transition(self, state: GameState) -> None:
        """Derive an own-KO event only from consecutive public snapshots."""
        current = self._own_pokemon_keys(state)
        opponent = self._scorer._opponent_player(state)
        opponent_prize_count = len(opponent.prize) if opponent is not None else 0
        if self._previous_own_pokemon_keys is not None:
            opponent_took_prize = (
                self._previous_opponent_prize_count is not None
                and opponent_prize_count < self._previous_opponent_prize_count
            )
            if len(current) < len(self._previous_own_pokemon_keys) or opponent_took_prize:
                self._own_ko_turn = state.turn
        self._previous_own_pokemon_keys = current
        self._previous_opponent_prize_count = opponent_prize_count
        self._scorer.set_own_ko_observed(
            self._own_ko_turn is not None and state.turn <= self._own_ko_turn + 1
        )

    def decide(self, observation: dict[str, Any]) -> Any:
        """Decide while recording only public pre/post-draw tactical evidence."""
        parsed = self._parser.parse(observation)
        self._update_public_ko_transition(parsed.state)
        if parsed.state.turn != self._turn_ledger.turn:
            if self._evolution_ko_commitment is not None:
                self._turn_ledger.poke_pad_ko_misses += 1
                self._match_ledger.poke_pad_ko_misses += 1
            if self._switch_commitment is not None and self._switch_commitment.method == "ignition":
                self._match_ledger.ignition_without_attack += 1
            self._turn_ledger.reset(parsed.state.turn)
            self._evolution_ko_commitment = None
            self._scorer.reset_persistent_target()
        self._turn_ledger.turn_action_count = parsed.state.turn_action_count
        self._turn_ledger.own_turn = self._scorer._own_turn_number(parsed.state)
        self._turn_ledger.first_own_turn = self._turn_ledger.own_turn == 1
        self._turn_ledger.no_pokemon_risk = self._scorer._own_field_count(parsed.state) <= 1
        self._refresh_public_turn_facts(parsed.state)
        self._refresh_evolution_ko_commitment(parsed.state, parsed.candidates)
        if not self._turn_ledger.objective:
            self._turn_ledger.objective = self._choose_turn_objective(
                parsed.state, parsed.candidates
            ).value
        if (
            self._switch_commitment is not None
            and self._switch_commitment.turn != parsed.state.turn
        ):
            self._switch_commitment = None
        if self._headset_turn is not None and self._headset_turn != parsed.state.turn:
            self._headset_turn = None
        attacks = [
            candidate
            for candidate in parsed.candidates
            if candidate.option_type is OptionType.ATTACK
        ]
        opponent = self._scorer._opponent_player(parsed.state)
        opponent_active = opponent.active if opponent is not None else None
        own_player = self._scorer._own_player(parsed.state)
        if opponent_active is not None:
            self._match_ledger.target_serial = opponent_active.serial
            self._match_ledger.target_card_id = (
                int(opponent_active.card_id) if isinstance(opponent_active.card_id, int) else None
            )
            self._match_ledger.target_hp = int(opponent_active.hp)
            self._match_ledger.target_prize_value = self._scorer._active_target_prize_value(
                parsed.state
            )
        self._match_ledger.own_prizes_remaining = (
            len(own_player.prize) if own_player is not None else 0
        )
        self._match_ledger.projected_porygon_damage = (
            self._scorer._rocket_supporters_in_discard(parsed.state) * 20
        )
        terminal_signature = (
            self._match_ledger.target_serial,
            self._match_ledger.target_hp,
            self._match_ledger.own_prizes_remaining,
        )
        if (
            self._scorer._r_command_wins_game(parsed.state)
            and terminal_signature != self._match_ledger.last_terminal_signature
        ):
            self._match_ledger.r_command_terminal_opportunities += 1
            porygon_line = any(
                candidate.option_type is OptionType.ATTACK
                and self._scorer._attack_id(candidate) == R_COMMAND
                for candidate in attacks
            ) or any(
                candidate.option_type is OptionType.PLAY
                and self._scorer._porygon2_terminal_promotion_available(parsed.state, candidate)
                for candidate in parsed.candidates
            )
            if porygon_line:
                self._match_ledger.porygon_terminal_opportunities += 1
            self._match_ledger.last_terminal_signature = terminal_signature
        damage = {
            self._scorer._attack_id(candidate): self._candidate_damage(parsed.state, candidate)
            for candidate in attacks
        }
        ko_candidates = tuple(
            self._scorer._attack_id(candidate)
            for candidate in attacks
            if self._candidate_damage(parsed.state, candidate)
            >= self._target_hp(parsed.state, candidate)
            and self._target_hp(parsed.state, candidate) > 0
        )
        self._turn_ledger.potential_damage.update(damage)
        if (
            "ariana" in self._turn_ledger.draw_sequence
            or "factory" in self._turn_ledger.draw_sequence
        ):
            self._turn_ledger.post_draw_ko_candidates = ko_candidates
        else:
            self._turn_ledger.pre_draw_ko_candidates = ko_candidates
        decision = super().decide(observation)
        self._record_end_telemetry(parsed.state, parsed.candidates, decision.selection)
        if not self._uses_expert_turn_loop:
            self._set_turn_stage(
                str(getattr(self.last_decision, "decision_phase", "") or "observe").casefold()
            )
        by_index = {candidate.option_index: candidate for candidate in parsed.candidates}
        if parsed.select_context is SelectContext.EFFECT_TARGET:
            for index in decision.selection.indices:
                candidate = by_index.get(index)
                if candidate is not None:
                    target = self._scorer._target_opponent_pokemon(parsed.state, candidate)
                    self._scorer.set_persistent_target(target)
                    score, reasons = self._scorer._giovanni_target_score(parsed.state, candidate)
                    del score
                    self._turn_ledger.target_priority_reason = reasons[0] if reasons else ""
                    if target is not None:
                        self._turn_ledger.chosen_target_prize_value = int(
                            self._scorer.catalog.get_traits(target.card_id).base_prize_value
                        )
                    break
        for index in decision.selection.indices:
            candidate = by_index.get(index)
            if candidate is None:
                continue
            card_id = self._scorer._feature_int(candidate, "card_id")
            if (
                self._uses_expert_turn_loop
                and self._headset_turn == parsed.state.turn
                and card_id in {ARIANA, ARCHER, GIOVANNI, PETREL, PROTON}
            ):
                self._turn_ledger.miracle_supporters_recovered += 1
            if self._evolution_ko_commitment is not None:
                if candidate.option_type is OptionType.PLAY and card_id == POKE_PAD:
                    self._evolution_ko_commitment.stage = "select_honchkrow"
                elif candidate.option_type is OptionType.CARD and card_id == HONCHKROW:
                    self._evolution_ko_commitment.stage = "evolve_murkrow"
                elif candidate.option_type in {OptionType.PLAY, OptionType.EVOLVE} and (
                    card_id == HONCHKROW
                ):
                    self._evolution_ko_commitment.stage = "attack"
            if (
                candidate.option_type is OptionType.PLAY
                and self._scorer._metadata_int(candidate.card, "cardType") == 3
            ):
                if self._turn_ledger.supporter_played is None:
                    self._turn_ledger.supporter_played = card_id
                else:
                    self._turn_ledger.second_supporter_attempts += 1
            if candidate.option_type is OptionType.PLAY and card_id == ROTO_STICK:
                self._turn_ledger.roto_sticks_played += 1
                self._match_ledger.roto_sticks_played += 1
                self._turn_ledger.roto_preserved_reason = "played_to_improve_rocket_feathers"
                self._turn_ledger.draw_sequence.append("roto")
                self._roto_turn = parsed.state.turn
                if self._uses_expert_turn_loop:
                    self._turn_ledger.stage = CanonicalTurnStage.HEADSET.value
            if candidate.option_type is OptionType.ATTACH and card_id == IGNITION_ENERGY:
                ignition_plan = self._ignition_attack_plan(parsed.state, candidate)
                if ignition_plan is not None:
                    self._switch_commitment = ignition_plan
                    self._match_ledger.ignition_attachments += 1
            if (
                self._rocket_evolution_commitment is not None
                and candidate.option_type is OptionType.ATTACH
                and card_id == ROCKET_ENERGY
            ):
                self._turn_ledger.stage = CanonicalTurnStage.DEVELOP.value
            if (
                self._uses_expert_turn_loop
                and candidate.option_type
                in {
                    OptionType.PLAY,
                    OptionType.EVOLVE,
                }
                and card_id in {MURKROW, PORYGON, HONCHKROW, PORYGON2, ARTICUNO}
            ):
                self._turn_ledger.stage = CanonicalTurnStage.DEVELOP.value
            if candidate.option_type is OptionType.PLAY and card_id == TRANSCEIVER:
                self._turn_ledger.transceiver_proton_in_hand = self._scorer._card_in_hand(
                    parsed.state, PROTON
                )
                self._transceiver_turn = parsed.state.turn
            if candidate.option_type is OptionType.PLAY and card_id == ARIANA:
                self._turn_ledger.ariana_plays += 1
                self._turn_ledger.ariana_marginal_draw = self._scorer._ariana_marginal_draw(
                    parsed.state
                )
                self._turn_ledger.ariana_supporters_in_hand = self._scorer._supporters_in_hand(
                    parsed.state
                )
                if self._scorer._card_in_hand(
                    parsed.state, PROTON
                ) and self._scorer._proton_setup_is_useful(parsed.state):
                    self._turn_ledger.ariana_with_required_proton += 1
                self._turn_ledger.draw_sequence.append("ariana")
                if self._uses_expert_turn_loop:
                    self._turn_ledger.stage = CanonicalTurnStage.FACTORY.value
            elif candidate.option_type is OptionType.PLAY and card_id == PETREL:
                if self._scorer._petrel_factory_is_superior(parsed.state):
                    self._turn_ledger.petrel_factory_conversions += 1
                    self._match_ledger.petrel_factory_conversions += 1
            elif candidate.option_type is OptionType.PLAY and card_id == FACTORY:
                self._turn_ledger.draw_sequence.append("factory")
                if self._uses_expert_turn_loop:
                    self._turn_ledger.stage = (
                        CanonicalTurnStage.FACTORY.value
                        if self._turn_ledger.supporter_played
                        else CanonicalTurnStage.SUPPORTER.value
                    )
            elif self._uses_expert_turn_loop and self._is_factory_effect_candidate(
                candidate, parsed.state
            ):
                self._turn_ledger.factory_effects_activated += 1
                self._turn_ledger.draw_sequence.append("factory_effect")
                self._turn_ledger.stage = CanonicalTurnStage.ROTO.value
            elif candidate.option_type is OptionType.PLAY and card_id == NIGHT_STRETCHER:
                self._turn_ledger.draw_sequence.append("night_stretcher")
            elif (
                self._uses_retreat_guard
                and candidate.option_type is OptionType.PLAY
                and card_id == GIOVANNI
            ):
                self._switch_commitment = self._giovanni_switch_plan(parsed.state)
            elif (
                self._uses_retreat_guard
                and candidate.option_type is OptionType.PLAY
                and card_id == MIRACLE_HEADSET
            ):
                self._turn_ledger.miracle_headsets_played += 1
                self._headset_turn = parsed.state.turn
            elif self._uses_retreat_guard and candidate.option_type is OptionType.RETREAT:
                self._switch_commitment = self._paid_retreat_plan(parsed.state)
            elif candidate.option_type is OptionType.PLAY and card_id == MIRACLE_HEADSET:
                self._turn_ledger.miracle_headsets_played += 1
                self._headset_turn = parsed.state.turn
                if self._uses_expert_turn_loop:
                    self._turn_ledger.stage = CanonicalTurnStage.DEVELOP.value
            elif candidate.option_type is OptionType.ATTACK:
                if self._uses_expert_turn_loop:
                    self._turn_ledger.stage = CanonicalTurnStage.ATTACK.value
                if self._scorer._attack_id(candidate) == TORMENT and (
                    self._evolution_ko_commitment is not None
                    or any(
                        attack_id != TORMENT
                        for attack_id in self._turn_ledger.pre_draw_ko_candidates
                    )
                ):
                    self._turn_ledger.torment_with_superior_line += 1
                    self._match_ledger.torment_with_superior_line += 1
                if (
                    self._evolution_ko_commitment is not None
                    and self._scorer._attack_id(candidate) == ROCKET_FEATHERS
                ):
                    self._turn_ledger.poke_pad_ko_conversions += 1
                    self._match_ledger.poke_pad_ko_conversions += 1
                    self._evolution_ko_commitment = None
                if (
                    self._switch_commitment is not None
                    and self._switch_commitment.method == "ignition"
                ):
                    self._match_ledger.ignition_attacks += 1
                    if self._switch_commitment.target_card_id == self._scorer._feature_int(
                        candidate, "target_card_id"
                    ):
                        self._match_ledger.porygon_terminal_conversions += int(
                            self._scorer._r_command_wins_game(parsed.state)
                        )
                self._turn_ledger.chosen_attacker = self._scorer._attack_id(candidate)
                self._turn_ledger.chosen_target = self._scorer._feature_int(
                    candidate, "target_card_id"
                )
                if self._scorer._attack_id(candidate) == ROCKET_FEATHERS:
                    player = self._scorer._own_player(parsed.state)
                    active = self._scorer._own_active(parsed.state)
                    required = self._supporters_required_for_candidate(parsed.state, candidate)
                    self._attack_sequence = AttackSequence(
                        attack_id=ROCKET_FEATHERS,
                        target_card_id=self._scorer._feature_int(candidate, "target_card_id"),
                        target_hp_before=self._target_hp(parsed.state, candidate),
                        attacker_card_id=active.card_id if active else 0,
                        attacker_energy=len(active.energies) if active else 0,
                        supporters_available=self._scorer._supporters_in_hand(parsed.state),
                        planned_damage=self._candidate_damage(parsed.state, candidate),
                        minimum_damage=self._target_hp(parsed.state, candidate),
                        ko_threshold=self._target_hp(parsed.state, candidate),
                        deck_reserve_before=player.deck_count if player else 0,
                    )
                    self._turn_ledger.rocket_planned_damage = self._candidate_damage(
                        parsed.state, candidate
                    )
                    self._turn_ledger.rocket_supporters_needed = required
                    self._turn_ledger.rocket_supporters_available = (
                        self._scorer._supporters_in_hand(parsed.state)
                    )
                    if self._variant_attack_is_lethal(parsed.state, candidate):
                        self._turn_ledger.lethal_lines_executed += 1
                if self._uses_retreat_guard:
                    self._switch_commitment = None
        replan_reason = self._replan_reason(
            parsed.state,
            decision.selection,
            by_index,
            parsed.select_context,
        )
        if replan_reason:
            previous_stage = self._turn_ledger.stage
            self._turn_ledger.objective = ""
            self._turn_ledger.replans += 1
            self._turn_ledger.last_replan_reason = replan_reason
            self._turn_ledger.last_replan_previous_stage = previous_stage
            self._turn_ledger.last_replan_new_stage = "observe"
            self._set_turn_stage("observe")
        if (
            self._uses_retreat_guard
            and parsed.select_context is SelectContext.TO_HAND
            and self._headset_turn == parsed.state.turn
        ):
            self._headset_turn = None
        if self._uses_resource_variant and parsed.select_context is SelectContext.TO_HAND:
            if self._roto_turn == parsed.state.turn:
                self._roto_turn = None
            if self._transceiver_turn == parsed.state.turn:
                self._transceiver_turn = None
        player = self._scorer._own_player(parsed.state)
        if player is not None and player.deck_count <= 2:
            self._turn_ledger.deck_risk = "critical"
        elif player is not None and player.deck_count <= 5:
            self._turn_ledger.deck_risk = "low"
        return decision

    def _refresh_public_turn_facts(self, state: GameState) -> None:
        """Refresh the candidate plan exclusively from the current public observation."""
        player = self._scorer._own_player(state)
        active = player.active if player is not None else None
        bench = [pokemon for pokemon in (player.bench if player is not None else []) if pokemon]
        supporters_in_hand = self._scorer._supporters_in_hand(state)
        effective_supporters_in_hand = self._scorer._effective_supporters_in_hand(state)
        supporters_in_discard = self._scorer._rocket_supporters_in_discard(state)
        self._turn_ledger.supporters_in_hand = supporters_in_hand
        self._turn_ledger.supporters_in_discard = supporters_in_discard
        self._turn_ledger.effective_supporters_in_hand = effective_supporters_in_hand
        recoverable = min(2, supporters_in_discard)
        if (
            self._scorer._card_in_hand(state, MIRACLE_HEADSET)
            and recoverable > 0
            and effective_supporters_in_hand + recoverable
            >= self._scorer._supporters_needed_for_ko(state)
        ):
            self._turn_ledger.effective_supporters_in_hand += recoverable
        self._turn_ledger.supporters_needed_for_ko = self._scorer._supporters_needed_for_ko(state)
        self._turn_ledger.rocket_feathers_damage = effective_supporters_in_hand * 60
        self._turn_ledger.r_command_damage = supporters_in_discard * 20
        self._turn_ledger.active_attacker_card_id = (
            int(active.card_id) if active is not None and isinstance(active.card_id, int) else None
        )
        best_bench = max(
            bench,
            key=self._scorer._energy_units_for_pokemon,
            default=None,
        )
        self._turn_ledger.bench_attacker_card_id = (
            int(best_bench.card_id)
            if best_bench is not None and isinstance(best_bench.card_id, int)
            else None
        )
        self._turn_ledger.active_energy_units = (
            self._scorer._energy_units_for_pokemon(active) if active is not None else 0
        )
        hand = player.hand if player is not None and player.hand is not None else []
        self._turn_ledger.energy_cards_in_hand = sum(
            self._scorer._is_energy_card(
                int(card.get("id", card.get("cardId", 0)) or 0),
                card,
            )
            for card in hand
            if isinstance(card, Mapping)
        )
        self._turn_ledger.energy_attachable = bool(
            self._turn_ledger.energy_cards_in_hand and not state.energy_attached
        )
        self._turn_ledger.ariana_already_available = self._scorer._card_in_hand(state, ARIANA)
        proton_targets = self._scorer._proton_targets_remaining(state)
        self._turn_ledger.proton_gain_remaining = sum(
            max(0, int(value)) for value in proton_targets.values()
        )
        self._turn_ledger.search_plan_objective = self._turn_ledger.objective
        self._turn_ledger.search_resource_used_this_turn = self._transceiver_turn
        self._turn_ledger.petrel_reserved = bool(
            self._scorer._card_in_hand(state, PETREL)
            and self._scorer._card_in_hand(state, TRANSCEIVER)
        )
        self._turn_ledger.best_draw_sequence = tuple(self._turn_ledger.draw_sequence)
        self._turn_ledger.deck_reserve = player.deck_count if player is not None else 0
        required = self._scorer._r_command_supporters_needed(state)
        discard = self._scorer._rocket_supporters_in_discard(state)
        self._turn_ledger.r_command_required_damage = max(0, self._scorer._raw_opponent_hp(state))
        self._turn_ledger.r_command_supporter_deficit = max(0, required - discard)
        projected_supporters = self._projected_r_command_supporters(state)
        self._turn_ledger.r_command_projected_supporters = projected_supporters
        self._turn_ledger.r_command_projected_damage = projected_supporters * 20
        if self._scorer._ultra_ball_completes_r_command(state):
            self._turn_ledger.ultra_ball_supporter_discards = 2
            self._turn_ledger.ultra_ball_r_command_line = "confirmed_exact_two_supporters"
        opponent = self._scorer._opponent_player(state)
        ping = self._scorer._froslass_ping_for_target(
            state, opponent.active if opponent is not None else None
        )
        self._turn_ledger.froslass_count = ping // 10
        self._turn_ledger.froslass_ping = ping
        self._refresh_turn_obligations(state)

    def _record_end_telemetry(
        self,
        state: GameState,
        candidates: Sequence[Candidate],
        selection: Selection,
    ) -> None:
        """Record visible productive lines whenever the policy selects END."""
        end_candidates = [
            candidate for candidate in candidates if candidate.option_type is OptionType.END
        ]
        self._turn_ledger.end_options_visible += int(bool(end_candidates))
        selected_end = any(
            candidate.option_index in selection.indices for candidate in end_candidates
        )
        if selected_end and self._scorer._productive_line_available(state):
            self._turn_ledger.end_with_productive_line += 1
        elif selected_end:
            self._turn_ledger.end_reason = "selected_no_productive_line"

    def _set_turn_stage(self, stage: str) -> None:
        """Move the public turn ledger to a new observable decision stage."""
        if stage == self._turn_ledger.stage:
            return
        self._turn_ledger.previous_stage = self._turn_ledger.stage
        self._turn_ledger.stage = stage

    def _replan_reason(
        self,
        state: GameState,
        selection: Selection,
        by_index: Mapping[int, Candidate],
        context: SelectContext | None,
    ) -> str:
        """Return the ratified reason to recompute the objective after this decision."""
        if not self._uses_expert_rounds_1_3:
            return ""
        if context is SelectContext.TO_PRIZE:
            return "prize_selection"
        for index in selection.indices:
            candidate = by_index.get(index)
            if candidate is None:
                continue
            card_id = self._scorer._feature_int(candidate, "card_id")
            source_id = self._scorer._metadata_int(candidate.option, "sourceCardId")
            if self._uses_expert_turn_loop:
                if candidate.option_type is OptionType.RETREAT:
                    return "retreat"
                if candidate.option_type is OptionType.PLAY:
                    card_type = self._scorer._metadata_int(candidate.card, "cardType")
                    if card_type == 0:
                        return "pokemon_placement"
                    if card_type == 3:
                        return f"supporter_{card_id}"
                    if card_id in {POKE_PAD, NIGHT_STRETCHER, ULTRA_BALL}:
                        return f"search_{card_id}"
                if context in {
                    SelectContext.DISCARD,
                    SelectContext.DISCARD_CARD_OR_ATTACHED_CARD,
                }:
                    return "discard"
            if candidate.option_type is OptionType.ATTACH:
                return "energy_attachment"
            if candidate.option_type is OptionType.EVOLVE or (
                candidate.option_type is OptionType.PLAY and card_id in {HONCHKROW, PORYGON2}
            ):
                return "evolution"
            if card_id in {
                ARIANA,
                FACTORY,
                ROTO_STICK,
                ULTRA_BALL,
                TRANSCEIVER,
                MIRACLE_HEADSET,
            }:
                return f"card_{card_id}"
            if source_id in {FACTORY, ROTO_STICK, TRANSCEIVER, MIRACLE_HEADSET}:
                return f"effect_{source_id}"
            if context is SelectContext.TO_HAND and (
                self._roto_turn == state.turn
                or self._transceiver_turn == state.turn
                or self._headset_turn == state.turn
            ):
                return "resolved_search_or_recovery"
        return ""

    def _choose_turn_objective(
        self, state: GameState, candidates: Sequence[Candidate]
    ) -> TurnObjective:
        """Choose the highest reachable public objective once per own turn."""
        attacks = [
            candidate for candidate in candidates if candidate.option_type is OptionType.ATTACK
        ]
        lethal = [
            candidate for candidate in attacks if self._variant_attack_is_lethal(state, candidate)
        ]
        player = self._scorer._own_player(state)
        prizes_remaining = len(player.prize) if player is not None else 0
        if any(
            self._scorer._truthy(candidate.option, "win", "wins", "gameOver")
            for candidate in lethal
        ) or (
            prizes_remaining > 0
            and lethal
            and self._scorer._active_target_prize_value(state) >= prizes_remaining
        ):
            return TurnObjective.WIN_NOW
        if self._scorer._own_field_count(state) <= 1:
            if any(
                candidate.option_type in {OptionType.PLAY, OptionType.EVOLVE}
                and self._scorer._feature_int(candidate, "card_id") == PORYGON2
                and self._scorer._porygon2_terminal_promotion_available(state, candidate)
                for candidate in candidates
            ):
                return TurnObjective.HIGHEST_PRIZE_KO
            return TurnObjective.PREVENT_NO_POKEMON_LOSS
        if lethal or self._evolution_ko_commitment is not None:
            return TurnObjective.HIGHEST_PRIZE_KO
        if self._scorer._proton_setup_is_useful(state) or self._scorer._own_field_count(state) < 2:
            return TurnObjective.BUILD_ATTACKER_AND_BOARD
        if any(
            candidate.option_type is OptionType.PLAY
            and self._scorer._feature_int(candidate, "card_id")
            in {ARIANA, PETREL, TRANSCEIVER, FACTORY, POKE_PAD}
            for candidate in candidates
        ):
            return TurnObjective.IMPROVE_RESOURCES
        return TurnObjective.ATTACK_OR_CONTROL

    def _refresh_evolution_ko_commitment(
        self, state: GameState, candidates: Sequence[Candidate]
    ) -> None:
        """Create one commitment only after every public KO precondition is proven."""
        if self._evolution_ko_commitment is not None:
            return
        if not any(
            candidate.option_type is OptionType.PLAY
            and self._scorer._feature_int(candidate, "card_id") == POKE_PAD
            for candidate in candidates
        ):
            return
        player = self._scorer._own_player(state)
        opponent = self._scorer._opponent_player(state)
        murkrow = player.active if player is not None else None
        target = opponent.active if opponent is not None else None
        if (
            murkrow is None
            or murkrow.card_id != MURKROW
            or murkrow.appear_this_turn
            or target is None
            or self._scorer._card_copies_remaining(state, HONCHKROW) <= 0
            or not self._attack_cost_satisfied(murkrow, ROCKET_FEATHERS)
        ):
            return
        damage_per_supporter = self._scorer._attack_damage(
            state,
            Candidate(0, {"attackId": ROCKET_FEATHERS}, OptionType.ATTACK),
            60,
            target,
        )
        if damage_per_supporter <= 0:
            return
        supporters = self._scorer._effective_supporters_in_hand(state)
        required = (max(0, int(target.hp)) + damage_per_supporter - 1) // damage_per_supporter
        if required <= 0 or supporters < required:
            return
        self._evolution_ko_commitment = EvolutionKoCommitment(
            turn=state.turn,
            murkrow_serial=murkrow.serial,
            target_card_id=int(target.card_id) if isinstance(target.card_id, int) else 0,
            target_prize_value=self._scorer._active_target_prize_value(state),
            planned_damage=supporters * damage_per_supporter,
            supporters_required=required,
        )
        self._turn_ledger.poke_pad_ko_opportunities += 1
        self._match_ledger.poke_pad_ko_opportunities += 1

    def _candidate_damage(self, state: GameState, candidate: Candidate) -> int:
        """Calculate the candidate's visible tactical damage."""
        attack_id = self._scorer._attack_id(candidate)
        target = self._scorer._target_opponent_pokemon(state, candidate)
        if attack_id == ROCKET_FEATHERS:
            base = self._scorer._effective_supporters_in_hand(state) * 60
        elif attack_id == R_COMMAND:
            base = self._scorer._rocket_supporters_in_discard(state) * 20
        elif attack_id == HAMMER_IN:
            base = 100
        else:
            base = max(
                self._scorer._metadata_int(candidate.attack, "damage"),
                self._scorer._metadata_int(candidate.option, "damage"),
                self._scorer._metadata_int(candidate.option, "expectedDamage"),
            )
        return self._scorer._attack_damage(state, candidate, base, target)

    def _target_hp(self, state: GameState, candidate: Candidate) -> int:
        """Return the raw remaining HP for the candidate's selected target."""
        target = self._scorer._target_opponent_pokemon(state, candidate)
        return max(0, int(target.hp)) if target is not None else 0

    def _main_phase_selections(
        self,
        state: GameState,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
    ) -> tuple[str, str, list[Selection]]:
        """Apply the persistent objective before lower-priority MAIN actions."""
        if self._uses_expert_turn_loop:
            return self._canonical_main_phase_selections(state, selections, candidates)
        safe = self._filter_forbidden_selections(state, selections, candidates, SelectContext.MAIN)
        by_index = {candidate.option_index: candidate for candidate in candidates}
        if not self._turn_ledger.objective:
            self._refresh_evolution_ko_commitment(state, candidates)
            self._turn_ledger.objective = self._choose_turn_objective(state, candidates).value

        def matching(predicate: Any) -> list[Selection]:
            return [
                selection
                for selection in safe
                if any(
                    predicate(candidate)
                    for index in selection.indices
                    if (candidate := by_index.get(index))
                )
            ]

        game_wins = matching(
            lambda candidate: (
                candidate.option_type is OptionType.ATTACK
                and self._attack_wins_game(state, candidate)
            )
        )
        if game_wins:
            return DecisionPhase.ATTACK_PRIORITY.value, "pre_draw_game_win", game_wins

        if self._transceiver_line_requires_resolution(state):
            transceiver = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == TRANSCEIVER
                )
            )
            if transceiver:
                return (
                    DecisionPhase.PLAY_SUPPORTER.value,
                    "resolve_transceiver_before_attack",
                    transceiver,
                )

        if self._headset_line_requires_resolution(state):
            headset = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == MIRACLE_HEADSET
                )
            )
            if headset:
                return (
                    DecisionPhase.PLAY_ITEMS.value,
                    "resolve_headset_before_attack",
                    headset,
                )

        if (
            self._uses_retreat_guard
            and self._active_matches_switch_commitment(state)
            and self._switch_commitment is not None
        ):
            committed_attack = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.ATTACK
                    and self._scorer._attack_id(candidate) == self._switch_commitment.attack_id
                )
            )
            if not committed_attack and self._switch_commitment.method == "ignition":
                committed_attack = matching(
                    lambda candidate: candidate.option_type is OptionType.ATTACK
                )
            if committed_attack:
                return (
                    DecisionPhase.ATTACK_PRIORITY.value,
                    (
                        "execute_committed_ignition_attack"
                        if self._switch_commitment.method == "ignition"
                        else "execute_committed_switch_attack"
                    ),
                    committed_attack,
                )

        if (
            self._uses_retreat_guard
            and self._switch_commitment is not None
            and self._switch_commitment.requires_ignition
        ):
            ignition = matching(self._candidate_completes_committed_ignition)
            if ignition:
                return (
                    DecisionPhase.ATTACK_PRIORITY.value,
                    "attach_ignition_to_committed_attacker",
                    ignition,
                )

        if self._uses_retreat_guard and self._giovanni_switch_plan(state) is not None:
            giovanni_switch = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == GIOVANNI
                )
            )
            if giovanni_switch:
                return (
                    DecisionPhase.ATTACK_PRIORITY.value,
                    "giovanni_free_switch_to_committed_attacker",
                    giovanni_switch,
                )

        if self._uses_resource_variant:
            factory_play = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == FACTORY
                    and self._scorer._factory_play_is_useful(state)
                )
            )
            if factory_play:
                reason = (
                    "factory_drawn_by_ariana"
                    if self._uses_expert_turn_loop and state.supporter_played
                    else "stadium_before_ariana"
                )
                return DecisionPhase.STADIUM.value, reason, factory_play

        energy_attachment = matching(
            lambda candidate: self._energy_attachment_before_ariana_is_needed(state, candidate)
        )
        if energy_attachment:
            return (
                DecisionPhase.ATTACH_PRIORITY.value,
                "attach_energy_before_ariana",
                energy_attachment,
            )

        if self._uses_supporter_lethal_commitment and not self._uses_expert_rounds_1_3:
            lethal_attacks = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.ATTACK
                    and self._variant_attack_is_lethal(state, candidate)
                )
            )
            if lethal_attacks:
                return (
                    DecisionPhase.ATTACK_PRIORITY.value,
                    "supporter_lethal_attack",
                    lethal_attacks,
                )

        commitment = self._evolution_ko_commitment
        if commitment is not None:
            if commitment.stage == "play_poke_pad":
                poke_pad = matching(
                    lambda candidate: (
                        candidate.option_type is OptionType.PLAY
                        and self._scorer._feature_int(candidate, "card_id") == POKE_PAD
                    )
                )
                if poke_pad:
                    return DecisionPhase.PLAY_ITEMS.value, "commit_poke_pad_honchkrow_ko", poke_pad
            if commitment.stage == "evolve_murkrow":
                evolution = matching(
                    lambda candidate: self._candidate_matches_evolution_commitment(candidate)
                )
                if evolution:
                    return (
                        DecisionPhase.EVOLVE.value,
                        "evolve_committed_murkrow_for_ko",
                        evolution,
                    )
            if commitment.stage == "attack":
                feathers = matching(
                    lambda candidate: (
                        candidate.option_type is OptionType.ATTACK
                        and self._scorer._attack_id(candidate) == ROCKET_FEATHERS
                        and self._variant_attack_is_lethal(state, candidate)
                    )
                )
                if feathers:
                    return DecisionPhase.ATTACK_PRIORITY.value, "execute_poke_pad_ko", feathers

        setup_supporter = matching(
            lambda candidate: (
                candidate.option_type is OptionType.PLAY
                and (
                    self._scorer._feature_int(candidate, "card_id") == PROTON
                    or (
                        self._scorer._feature_int(candidate, "card_id") == TRANSCEIVER
                        and not self._scorer._card_in_hand(state, PROTON)
                    )
                )
                and self._scorer._proton_setup_is_useful(state)
            )
        )
        if setup_supporter:
            return (
                DecisionPhase.PLAY_SUPPORTER.value,
                "required_proton_board_setup",
                setup_supporter,
            )

        if self._uses_expert_rounds_1_3:
            setup_roto = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == ROTO_STICK
                    and self._roto_setup_mode(state)
                )
            )
            if setup_roto:
                return DecisionPhase.PLAY_ITEMS.value, "roto_opening_setup_or_survival", setup_roto

        petrel_factory = matching(
            lambda candidate: (
                candidate.option_type is OptionType.PLAY
                and self._scorer._feature_int(candidate, "card_id") == PETREL
                and self._scorer._petrel_factory_is_superior(state)
            )
        )
        if petrel_factory:
            if self._turn_ledger.petrel_factory_opportunities == 0:
                self._turn_ledger.petrel_factory_opportunities = 1
                self._match_ledger.petrel_factory_opportunities += 1
            return (
                DecisionPhase.PLAY_SUPPORTER.value,
                "petrel_factory_over_low_draw_ariana",
                petrel_factory,
            )

        night_stretcher = matching(
            lambda candidate: (
                candidate.option_type is OptionType.PLAY
                and self._scorer._feature_int(candidate, "card_id") == NIGHT_STRETCHER
            )
        )
        if night_stretcher:
            return DecisionPhase.PLAY_ITEMS.value, "recover_before_ariana", night_stretcher

        hand_reduction = matching(
            lambda candidate: self._is_safe_pre_draw_hand_reduction(state, candidate)
        )
        if hand_reduction:
            return DecisionPhase.PLAY_POKEMON.value, "reduce_hand_before_ariana", hand_reduction

        ariana = matching(
            lambda candidate: (
                candidate.option_type is OptionType.PLAY
                and self._scorer._feature_int(candidate, "card_id") == ARIANA
                and self._scorer._ariana_is_safe_and_useful(state)
            )
        )
        if ariana:
            if self._turn_ledger.ariana_opportunities == 0:
                self._turn_ledger.ariana_opportunities = 1
                self._turn_ledger.ariana_marginal_draw = self._scorer._ariana_marginal_draw(state)
                self._turn_ledger.ariana_supporters_in_hand = self._scorer._supporters_in_hand(
                    state
                )
            return DecisionPhase.PLAY_SUPPORTER.value, "ariana_before_factory", ariana

        if self._uses_resource_variant:
            roto = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == ROTO_STICK
                    and self._scorer._roto_stick_is_needed(state)
                )
            )
            if roto:
                return DecisionPhase.PLAY_ITEMS.value, "roto_after_ariana", roto

        factory = matching(
            lambda candidate: (
                self._is_factory_effect_candidate(candidate, state)
                and self._scorer._factory_is_useful(state)
            )
        )
        if factory:
            return DecisionPhase.UTILITY.value, "factory_after_ariana_and_roto", factory

        porygon_bench_evolution = matching(
            lambda candidate: self._porygon_bench_evolution_is_preferred(state, candidate)
        )
        if porygon_bench_evolution:
            return (
                DecisionPhase.EVOLVE.value,
                "protect_benched_porygon_before_exposed_active",
                porygon_bench_evolution,
            )

        productive_evolution = matching(
            lambda candidate: (
                candidate.option_type in {OptionType.PLAY, OptionType.EVOLVE}
                and self._scorer._feature_int(candidate, "card_id") in {HONCHKROW, PORYGON2}
            )
        )
        if productive_evolution:
            return (
                DecisionPhase.EVOLVE.value,
                "productive_evolution_before_control",
                productive_evolution,
            )

        if self._uses_expert_rounds_1_3 and self._scorer._deceit_is_survival_line(state):
            deceit = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.ATTACK
                    and self._scorer._attack_id(candidate) == DECEIT
                )
            )
            if deceit:
                return DecisionPhase.ATTACK.value, "deceit_searches_ariana_survival_line", deceit

        attacks = matching(lambda candidate: candidate.option_type is OptionType.ATTACK)
        if attacks:
            return DecisionPhase.ATTACK.value, "post_draw_best_damage", attacks
        return super()._main_phase_selections(state, safe, candidates)

    def _canonical_main_phase_selections(
        self,
        state: GameState,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
    ) -> tuple[str, str, list[Selection]]:
        """Select only actions belonging to the current canonical turn stage."""
        safe = self._filter_forbidden_selections(state, selections, candidates, SelectContext.MAIN)
        by_index = {candidate.option_index: candidate for candidate in candidates}

        def matching(predicate: Any) -> list[Selection]:
            return [
                selection
                for selection in safe
                if any(
                    predicate(candidate)
                    for index in selection.indices
                    if (candidate := by_index.get(index)) is not None
                )
            ]

        tool_scrapper = matching(
            lambda candidate: (
                candidate.option_type is OptionType.PLAY
                and self._scorer._feature_int(candidate, "card_id") == TOOL_SCRAPPER
                and self._opponent_has_scrappable_tool(state)
            )
        )
        if tool_scrapper:
            self._turn_ledger.heros_cape_scrapped = True
            return (
                DecisionPhase.PLAY_ITEMS.value,
                "canonical_scrap_visible_tool",
                tool_scrapper,
            )

        spikemuth_replacement = matching(
            lambda candidate: (
                candidate.option_type is OptionType.PLAY
                and self._scorer._metadata_int(candidate.card, "cardType") == 4
                and self._scorer._stadium_in_play(state, SPIKEMUTH_GYM)
            )
        )
        if spikemuth_replacement:
            self._turn_ledger.resource_guard = "replace_spikemuth_gym"
            return (
                DecisionPhase.STADIUM.value,
                "canonical_replace_spikemuth_gym",
                spikemuth_replacement,
            )

        immediate = matching(
            lambda candidate: (
                candidate.option_type is OptionType.ATTACK
                and self._attack_wins_game(state, candidate)
            )
        )
        if immediate:
            self._turn_ledger.canonical_exception = "immediate_win"
            return DecisionPhase.ATTACK_PRIORITY.value, "canonical_immediate_win", immediate

        factory_play = matching(
            lambda candidate: (
                candidate.option_type is OptionType.PLAY
                and self._scorer._feature_int(candidate, "card_id") == FACTORY
                and self._scorer._factory_play_is_useful(state)
            )
        )
        if factory_play:
            reason = (
                "canonical_place_factory_drawn_by_supporter"
                if state.supporter_played
                else "canonical_place_factory_before_supporter"
            )
            return DecisionPhase.STADIUM.value, reason, factory_play

        energy_attachment = matching(
            lambda candidate: self._energy_attachment_before_ariana_is_needed(state, candidate)
        )
        if energy_attachment:
            return (
                DecisionPhase.ATTACH_PRIORITY.value,
                "canonical_attach_energy_before_supporter",
                energy_attachment,
            )

        preserve_supporters_with_archer = matching(
            lambda candidate: (
                candidate.option_type is OptionType.PLAY
                and self._scorer._feature_int(candidate, "card_id") == ARCHER
                and self._scorer._archer_preserves_nonlethal_rocket_resources(state, candidate)
            )
        )
        if preserve_supporters_with_archer:
            self._turn_ledger.resource_guard = "archer_before_nonlethal_rocket_feathers"
            return (
                DecisionPhase.PLAY_SUPPORTER.value,
                "canonical_archer_preserves_nonlethal_rocket_supporters",
                preserve_supporters_with_archer,
            )

        if self._scorer._own_ko_observed and not (
            self._giovanni_switch_plan(state) is not None
            or any(
                candidate.option_type in {OptionType.PLAY, OptionType.EVOLVE}
                and self._scorer._feature_int(candidate, "card_id") == PORYGON2
                and self._scorer._porygon2_terminal_promotion_available(state, candidate)
                for candidate in candidates
            )
            or self._canonical_night_stretcher_is_productive(state)
        ):
            post_ko_supporters = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id")
                    in {ARIANA, ARCHER, GIOVANNI, PETREL, PROTON}
                )
            )
            if post_ko_supporters:
                by_index = {candidate.option_index: candidate for candidate in candidates}
                ranked: list[tuple[float, Selection]] = []
                for selection in post_ko_supporters:
                    supporter = next(
                        (
                            by_index[index]
                            for index in selection.indices
                            if index in by_index
                            and by_index[index].option_type is OptionType.PLAY
                            and self._scorer._feature_int(by_index[index], "card_id")
                            in {ARIANA, ARCHER, GIOVANNI, PETREL, PROTON}
                        ),
                        None,
                    )
                    if supporter is None:
                        continue
                    score, _ = self._scorer._play_score(state, supporter)
                    ranked.append((score, selection))
                best_score = max((score for score, _ in ranked), default=-float("inf"))
                best = [selection for score, selection in ranked if score == best_score]
                if best:
                    self._turn_ledger.canonical_exception = "post_ko_supporter_comparison"
                    return (
                        DecisionPhase.PLAY_SUPPORTER.value,
                        "canonical_post_ko_best_supporter",
                        best,
                    )

        porygon2_terminal = matching(
            lambda candidate: (
                candidate.option_type in {OptionType.PLAY, OptionType.EVOLVE}
                and self._scorer._feature_int(candidate, "card_id") == PORYGON2
                and self._scorer._porygon2_terminal_promotion_available(state, candidate)
            )
        )
        if porygon2_terminal:
            self._turn_ledger.canonical_exception = "porygon2_terminal_promotion"
            return (
                DecisionPhase.EVOLVE.value,
                "canonical_porygon2_terminal_promotion",
                porygon2_terminal,
            )

        night_stretcher = matching(
            lambda candidate: (
                candidate.option_type is OptionType.PLAY
                and self._scorer._feature_int(candidate, "card_id") == NIGHT_STRETCHER
                and self._canonical_night_stretcher_is_productive(state)
            )
        )
        if night_stretcher:
            return (
                DecisionPhase.PLAY_ITEMS.value,
                "canonical_recover_playable_pokemon",
                night_stretcher,
            )

        if self._scorer._own_field_count(state) <= 1:
            survivor = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._metadata_int(candidate.card, "cardType") == 0
                    and self._scorer._feature_int(candidate, "card_id") in {MURKROW, PORYGON}
                )
            )
            if survivor:
                self._turn_ledger.canonical_exception = "prevent_no_pokemon_loss"
                return (
                    DecisionPhase.PLAY_POKEMON.value,
                    "canonical_play_backup_basic",
                    survivor,
                )

        if self._scorer._own_bench_count(
            state
        ) == 0 and not self._articuno_should_precede_development(state, candidates):
            development = matching(
                lambda candidate: (
                    candidate.option_type in {OptionType.PLAY, OptionType.EVOLVE}
                    and self._scorer._metadata_int(candidate.card, "cardType") == 0
                    and self._scorer._feature_int(candidate, "card_id")
                    in {MURKROW, PORYGON, HONCHKROW, PORYGON2, ARTICUNO}
                )
            )
            if development:
                self._turn_ledger.canonical_exception = "empty_bench_development"
                return (
                    DecisionPhase.PLAY_POKEMON.value,
                    "canonical_develop_empty_bench",
                    development,
                )

        if self._switch_commitment is not None and self._active_matches_switch_commitment(state):
            committed_attack = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.ATTACK
                    and self._scorer._attack_id(candidate) == self._switch_commitment.attack_id
                )
            )
            if committed_attack:
                return (
                    DecisionPhase.ATTACK_PRIORITY.value,
                    "canonical_execute_ignition_attack",
                    committed_attack,
                )

        rocket_commitment = self._rocket_evolution_commitment
        if rocket_commitment is not None:
            if rocket_commitment.turn != state.turn:
                self._rocket_evolution_commitment = None
                rocket_commitment = None
            else:
                player = self._scorer._own_player(state)
                active = player.active if player is not None else None
                if (
                    active is None
                    or rocket_commitment.murkrow_serial is not None
                    and active.serial != rocket_commitment.murkrow_serial
                ):
                    self._rocket_evolution_commitment = None
                    rocket_commitment = None
        if rocket_commitment is not None:
            evolution = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.EVOLVE
                    and self._scorer._feature_int(candidate, "card_id") == HONCHKROW
                    and self._scorer._feature_int(candidate, "target_serial")
                    == rocket_commitment.murkrow_serial
                )
            )
            if evolution:
                self._rocket_evolution_commitment = None
                return DecisionPhase.EVOLVE.value, "canonical_evolve_rocket_murkrow", evolution
            self._rocket_evolution_commitment = None

        player = self._scorer._own_player(state)
        murkrow = player.active if player is not None else None
        murkrow_serial = murkrow.serial if murkrow is not None else None
        rocket_attach = matching(
            lambda candidate: (
                candidate.option_type is OptionType.ATTACH
                and self._scorer._feature_int(candidate, "card_id") == ROCKET_ENERGY
                and self._scorer._feature_int(candidate, "target_card_id") == MURKROW
                and murkrow_serial is not None
                and self._scorer._feature_int(candidate, "target_serial") == murkrow_serial
                and any(
                    item.option_type is OptionType.EVOLVE
                    and self._scorer._feature_int(item, "card_id") == HONCHKROW
                    and self._scorer._feature_int(item, "target_serial") == murkrow_serial
                    for item in candidates
                )
            )
        )
        if rocket_attach:
            self._rocket_evolution_commitment = RocketEvolutionCommitment(
                state.turn, murkrow_serial
            )
            return (
                DecisionPhase.ATTACH_PRIORITY.value,
                "canonical_attach_rocket_then_evolve",
                rocket_attach,
            )

        porygon_bench_evolution = matching(
            lambda candidate: self._porygon_bench_evolution_is_preferred(state, candidate)
        )
        if porygon_bench_evolution:
            self._turn_ledger.canonical_exception = "protect_benched_porygon"
            return (
                DecisionPhase.EVOLVE.value,
                "canonical_protect_benched_porygon_before_exposed_active",
                porygon_bench_evolution,
            )

        stage = self._turn_ledger.stage
        if stage in {"", "observe", CanonicalTurnStage.DEVELOP.value}:
            self._turn_ledger.stage = CanonicalTurnStage.DEVELOP.value
            stadium = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == FACTORY
                    and self._scorer._factory_play_is_useful(state)
                )
            )
            if stadium:
                return DecisionPhase.STADIUM.value, "canonical_stadium_before_ariana", stadium
            if self._scorer._articuno_is_needed(state) and not self._scorer._articuno_is_on_field(
                state
            ):
                articuno = matching(
                    lambda candidate: (
                        candidate.option_type in {OptionType.PLAY, OptionType.CARD}
                        and self._scorer._feature_int(candidate, "card_id") == ARTICUNO
                    )
                )
                if articuno:
                    self._turn_ledger.canonical_exception = "dragapult_articuno_first"
                    return (
                        DecisionPhase.PLAY_POKEMON.value,
                        "canonical_articuno_before_evolution",
                        articuno,
                    )
            development = matching(
                lambda candidate: (
                    candidate.option_type in {OptionType.PLAY, OptionType.EVOLVE}
                    and self._scorer._metadata_int(candidate.card, "cardType") == 0
                    and self._scorer._feature_int(candidate, "card_id")
                    in {MURKROW, PORYGON, HONCHKROW, PORYGON2, ARTICUNO}
                    and (
                        not self._scorer._articuno_is_needed(state)
                        or self._scorer._articuno_is_on_field(state)
                        or not self._articuno_should_precede_development(state, candidates)
                        or self._scorer._feature_int(candidate, "card_id") == ARTICUNO
                    )
                )
            )
            if development:
                next_attacker = next(
                    (
                        candidate
                        for selection in development
                        for index in selection.indices
                        if (candidate := by_index.get(index)) is not None
                        and candidate.option_type is OptionType.EVOLVE
                    ),
                    None,
                )
                if next_attacker is not None:
                    self._turn_ledger.next_attacker_serial = (
                        self._scorer._feature_int(next_attacker, "target_serial") or None
                    )
                return DecisionPhase.PLAY_POKEMON.value, "canonical_develop_board", development
            self._turn_ledger.stage = CanonicalTurnStage.SEARCH.value

        if self._turn_ledger.stage == CanonicalTurnStage.SEARCH.value:
            proton = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == PROTON
                    and self._scorer._proton_setup_is_useful(state)
                )
            )
            if proton:
                return (
                    DecisionPhase.PLAY_SUPPORTER.value,
                    "canonical_proton_setup",
                    proton,
                )
            poke_pad = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == POKE_PAD
                    and (
                        (
                            self._evolution_ko_commitment is not None
                            and self._scorer._pokepad_honchkrow_is_useful(state, candidate)
                        )
                        or self._scorer._pokepad_ariana_hand_reduction_is_useful(state)
                    )
                )
            )
            if poke_pad:
                return DecisionPhase.PLAY_ITEMS.value, "canonical_poke_pad_before_ariana", poke_pad
            search = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == ULTRA_BALL
                    and self._canonical_ultra_ball_is_productive(state)
                )
            )
            if search:
                return DecisionPhase.PLAY_ITEMS.value, "canonical_search_with_ariana", search
            self._turn_ledger.stage = CanonicalTurnStage.CALCULATE.value

        if self._turn_ledger.stage == CanonicalTurnStage.CALCULATE.value:
            self._refresh_public_turn_facts(state)
            self._turn_ledger.stage = CanonicalTurnStage.SUPPORTER.value

        if self._turn_ledger.stage == CanonicalTurnStage.SUPPORTER.value:
            factory_rescue_proton = matching(
                lambda candidate: (
                    self._scorer._factory_in_play(state)
                    and candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == PROTON
                    and self._scorer._proton_setup_is_useful(state)
                )
            )
            if factory_rescue_proton:
                self._turn_ledger.resource_guard = "factory_rescue_proton_before_draw"
                return (
                    DecisionPhase.PLAY_SUPPORTER.value,
                    "canonical_factory_rescue_proton",
                    factory_rescue_proton,
                )
            factory_rescue_giovanni = matching(
                lambda candidate: (
                    self._scorer._factory_in_play(state)
                    and candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == GIOVANNI
                    and self._canonical_giovanni_is_productive(state)
                )
            )
            if factory_rescue_giovanni:
                self._turn_ledger.resource_guard = "factory_rescue_giovanni_before_draw"
                return (
                    DecisionPhase.PLAY_SUPPORTER.value,
                    "canonical_factory_rescue_giovanni",
                    factory_rescue_giovanni,
                )
            roto_without_supporter = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == ROTO_STICK
                    and self._scorer._effective_supporters_in_hand(state) == 0
                    and self._canonical_roto_is_productive(state)
                )
            )
            if roto_without_supporter:
                return (
                    DecisionPhase.PLAY_ITEMS.value,
                    "canonical_roto_before_supporter_conversion",
                    roto_without_supporter,
                )
            emergency_headset = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == MIRACLE_HEADSET
                    and (
                        self._headset_ariana_recovery_is_useful(state)
                        or self._scorer._miracle_headset_emergency_is_useful(state)
                    )
                )
            )
            if emergency_headset:
                self._turn_ledger.canonical_exception = "headset_recover_ariana_from_reduced_hand"
                self._turn_ledger.headset_ariana_recovery = self._headset_ariana_recovery_is_useful(
                    state
                )
                self._turn_ledger.headset_recovery_reason = "ariana_plus_second_supporter"
                return (
                    DecisionPhase.PLAY_ITEMS.value,
                    "canonical_emergency_headset_before_factory",
                    emergency_headset,
                )
            petrel_factory = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == PETREL
                    and self._scorer._petrel_factory_is_superior(state)
                    and not self._scorer._ariana_is_safe_and_useful(state)
                    and not (
                        self._scorer._card_in_hand(state, PROTON)
                        and self._scorer._proton_setup_is_useful(state)
                    )
                )
            )
            if petrel_factory:
                if self._turn_ledger.petrel_factory_opportunities == 0:
                    self._turn_ledger.petrel_factory_opportunities = 1
                    self._match_ledger.petrel_factory_opportunities += 1
                return (
                    DecisionPhase.PLAY_SUPPORTER.value,
                    "petrel_factory_over_low_draw_ariana",
                    petrel_factory,
                )
            giovanni = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == GIOVANNI
                    and self._canonical_giovanni_is_productive(state)
                )
            )
            if giovanni:
                return (
                    DecisionPhase.PLAY_SUPPORTER.value,
                    "canonical_giovanni_prize_target",
                    giovanni,
                )
            transceiver = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == TRANSCEIVER
                    and (
                        self._scorer._proton_setup_is_useful(state)
                        or self._transceiver_line_requires_resolution(state)
                    )
                )
            )
            if transceiver:
                return (
                    DecisionPhase.PLAY_SUPPORTER.value,
                    "canonical_transceiver_for_proton",
                    transceiver,
                )
            ariana = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == ARIANA
                    and self._scorer._ariana_is_safe_and_useful(state)
                )
            )
            if ariana:
                self._record_ariana_retained_candidates(safe, by_index)
                return (
                    DecisionPhase.PLAY_SUPPORTER.value,
                    "canonical_ariana_resource_engine",
                    ariana,
                )
            proton = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == PROTON
                    and self._scorer._proton_setup_is_useful(state)
                )
            )
            if proton:
                return DecisionPhase.PLAY_SUPPORTER.value, "canonical_proton_setup", proton
            blocked_roto = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == ROTO_STICK
                    and self._scorer._effective_supporters_in_hand(state) == 0
                    and self._roto_setup_mode(state)
                )
            )
            if blocked_roto:
                self._turn_ledger.canonical_exception = "roto_without_playable_supporter"
                return (
                    DecisionPhase.PLAY_ITEMS.value,
                    "canonical_roto_supporter_block",
                    blocked_roto,
                )
            self._turn_ledger.stage = CanonicalTurnStage.FACTORY.value

        if self._turn_ledger.stage == CanonicalTurnStage.FACTORY.value:
            factory = matching(
                lambda candidate: (
                    self._is_factory_effect_candidate(candidate, state)
                    and self._scorer._factory_is_useful(state)
                )
            )
            if factory:
                return DecisionPhase.UTILITY.value, "canonical_factory_after_supporter", factory
            self._turn_ledger.stage = CanonicalTurnStage.ROTO.value

        if self._turn_ledger.stage == CanonicalTurnStage.ROTO.value:
            roto = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == ROTO_STICK
                    and self._canonical_roto_is_productive(state)
                )
            )
            if roto:
                return DecisionPhase.PLAY_ITEMS.value, "canonical_roto_after_factory", roto
            self._turn_ledger.stage = CanonicalTurnStage.HEADSET.value

        if self._turn_ledger.stage == CanonicalTurnStage.HEADSET.value:
            porygon2 = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.EVOLVE
                    and self._scorer._feature_int(candidate, "card_id") == PORYGON2
                    and self._scorer._porygon2_terminal_promotion_available(state, candidate)
                )
            )
            if porygon2:
                return (
                    DecisionPhase.EVOLVE.value,
                    "canonical_evolve_porygon2_before_headset",
                    porygon2,
                )
            headset = matching(
                lambda candidate: (
                    candidate.option_type is OptionType.PLAY
                    and self._scorer._feature_int(candidate, "card_id") == MIRACLE_HEADSET
                    and self._canonical_headset_is_useful(state)
                )
            )
            if headset:
                return DecisionPhase.PLAY_ITEMS.value, "canonical_headset_contextual", headset
            self._turn_ledger.stage = CanonicalTurnStage.ATTACK.value

        lethal = matching(
            lambda candidate: (
                candidate.option_type is OptionType.ATTACK
                and self._variant_attack_is_lethal(state, candidate)
            )
        )
        if lethal:
            return DecisionPhase.ATTACK_PRIORITY.value, "canonical_attack_lethal", lethal
        pressure_attack = matching(lambda candidate: candidate.option_type is OptionType.ATTACK)
        if (
            self._scorer._proton_setup_is_useful(state)
            and self._scorer._own_turn_number(state) <= 2
        ):
            pressure_attack = [
                selection
                for selection in pressure_attack
                if not any(
                    self._scorer._attack_id(candidate) == HACKING
                    for index in selection.indices
                    if (candidate := by_index.get(index)) is not None
                )
            ]
        if pressure_attack:
            return (
                DecisionPhase.ATTACK_PRIORITY.value,
                "canonical_attack_pressure",
                pressure_attack,
            )
        self._turn_ledger.canonical_exception = "legal_fallback"
        return super()._main_phase_selections(state, safe, candidates)

    def _record_ariana_retained_candidates(
        self,
        selections: Sequence[Selection],
        by_index: Mapping[int, Candidate],
    ) -> None:
        """Record each presently playable card deliberately retained for Ariana's redraw."""
        retained: dict[int, str] = {}
        for selection in selections:
            for index in selection.indices:
                candidate = by_index.get(index)
                if candidate is None or candidate.option_type not in {
                    OptionType.PLAY,
                    OptionType.ATTACH,
                    OptionType.EVOLVE,
                }:
                    continue
                card_id = self._scorer._feature_int(candidate, "card_id")
                if card_id == ARIANA:
                    continue
                retained[index] = "preserve_for_post_ariana_reassessment"
        self._turn_ledger.ariana_retained_cards = retained

    def _canonical_ultra_ball_is_productive(self, state: GameState) -> bool:
        """Allow Ariana hand reduction or the exact two-Supporter R Command conversion."""
        if (
            self._scorer._own_turn_number(state) > 0
            and self._scorer._proton_setup_is_useful(state)
            and not self._scorer._ultra_ball_completes_r_command(state)
        ):
            self._turn_ledger.setup_guard_reason = "preserve_ultra_ball_for_proton_setup"
            return False
        return self._scorer._ultra_ball_completes_r_command(state) or (
            self._scorer._card_in_hand(state, ARIANA)
            and self._scorer._ultra_ball_is_productive(state)
        )

    def _canonical_night_stretcher_is_productive(self, state: GameState) -> bool:
        """Return whether Night Stretcher has a same-turn public conversion."""
        return self._recovery_plan(state).productive

    def _recovery_plan(self, state: GameState) -> RecoveryPlan:
        """Evaluate recovery once for Headset, Stretcher, Petrel, and END guards."""
        player = self._scorer._own_player(state)
        if player is None:
            return RecoveryPlan(False, reason="no_public_recovery_target")
        discard_ids = tuple(self._scorer._card_id_from_value(card) for card in player.discard)
        # Rocket Energy is evaluated outside target ranking to keep the shared
        # plan acyclic: target ranking itself reads this plan for payload choice.
        active = player.active
        if (
            ROCKET_ENERGY in discard_ids
            and not state.energy_attached
            and active is not None
            and active.card_id in {MURKROW, HONCHKROW}
            and self._scorer._energy_units_for_pokemon(active)
            < self._scorer._attack_energy_target(active.card_id)
        ):
            return RecoveryPlan(
                True, (ROCKET_ENERGY,), "recover_rocket_energy_for_same_turn_attachment"
            )
        for card_id in discard_ids:
            if card_id == ROCKET_ENERGY:
                continue
            priority, reason = self._night_stretcher_target_priority(state, card_id)
            if priority:
                return RecoveryPlan(True, (card_id,), reason)
        # Rocket Energy recovery is intentionally narrow: it must attach now
        # and advance the active (or already committed) attacker before Ariana.
        return RecoveryPlan(False, reason="recovery_has_no_same_turn_conversion")

    def _opponent_has_heros_cape(self, state: GameState) -> bool:
        """Return whether a public opposing Pokémon has Hero's Cape attached."""
        return self._opponent_has_tool(state, HEROS_CAPE)

    def _opponent_has_scrappable_tool(self, state: GameState) -> bool:
        """Return whether a public opposing Pokémon has a priority Tool Scrapper target."""
        return any(
            self._opponent_has_tool(state, tool_id)
            for tool_id in (HEROS_CAPE, CYNTHIAS_POWER_WEIGHT)
        )

    def _opponent_has_tool(self, state: GameState, tool_id: int) -> bool:
        """Return whether a public opposing Pokémon has the requested tool attached."""
        opponent = self._scorer._opponent_player(state)
        if opponent is None:
            return False
        return any(
            str(tool_id) in pokemon.tool_ids
            for pokemon in [opponent.active, *opponent.bench]
            if pokemon is not None
        )

    def _is_tool_scrapper_priority_target(self, candidate: Candidate) -> bool:
        """Return whether a Tool Scrapper prompt candidate is a priority opposing Tool."""
        return bool(
            self._scorer._metadata_int(candidate.option, "sourceCardId") == TOOL_SCRAPPER
            and self._scorer._feature_int(candidate, "card_id")
            in {HEROS_CAPE, CYNTHIAS_POWER_WEIGHT}
        )

    def _projected_r_command_supporters(self, state: GameState) -> int:
        """Project public Supporters after a lethal Rocket Feathers and next-turn Supporter.

        The extra Supporter is counted only when the current public hand can both
        pay the exact Rocket Feathers requirement and preserve one Supporter for
        the following turn.  This deliberately makes no claim about hidden draws.
        """
        discard = self._scorer._rocket_supporters_in_discard(state)
        active = self._scorer._own_active(state)
        if active is None or active.card_id != HONCHKROW:
            return discard
        required = self._scorer._supporters_needed_for_ko(state)
        available = self._scorer._effective_supporters_in_hand(state)
        if required <= 0 or available < required + 1:
            return discard
        return discard + required + 1

    def _night_stretcher_target_priority(self, state: GameState, card_id: int) -> tuple[int, str]:
        """Rank Night Stretcher targets from public immediate and projected lines."""
        player = self._scorer._own_player(state)
        if player is None:
            return 0, ""
        if card_id == ROCKET_ENERGY:
            plan = self._recovery_plan(state)
            return (
                (325, plan.reason)
                if plan.productive and plan.recovered_cards == (ROCKET_ENERGY,)
                else (0, "")
            )
        if not self._scorer._night_stretcher_target_is_immediately_playable(state, card_id):
            return 0, ""
        field = [pokemon for pokemon in [player.active, *player.bench] if pokemon is not None]
        has_murkrow = any(pokemon.card_id == MURKROW for pokemon in field)
        has_porygon = any(pokemon.card_id == PORYGON for pokemon in field)
        projected_damage = self._projected_r_command_supporters(state) * 20
        r_command_ko = projected_damage >= self._scorer._raw_opponent_hp(state) > 0
        if card_id == MURKROW and not has_murkrow:
            return 400, "recover_murkrow_for_incomplete_setup"
        if card_id == PORYGON2 and has_porygon:
            return (
                350 if r_command_ko else 300,
                "recover_porygon2_for_projected_r_command_ko"
                if r_command_ko
                else "recover_porygon2_for_r_command_line",
            )
        if card_id == PORYGON and not has_porygon:
            return (
                275 if r_command_ko else 250,
                "recover_porygon_for_projected_r_command_ko"
                if r_command_ko
                else "recover_porygon_for_r_command_line",
            )
        if card_id == HONCHKROW and has_murkrow:
            required = self._scorer._supporters_needed_for_ko(state)
            if required > 0 and self._scorer._effective_supporters_in_hand(state) >= required:
                return 200, "recover_honchkrow_for_rocket_feathers_ko"
        if card_id == ARTICUNO and self._scorer._articuno_is_needed(state):
            return 100, "recover_articuno_for_ratified_matchup_protection"
        return 0, ""

    def _canonical_roto_is_productive(self, state: GameState) -> bool:
        """Require a legal Roto only for setup or a bounded post-Supporter KO."""
        if not self._scorer._card_in_hand(state, ROTO_STICK):
            return False
        if self._opponent_budew_item_lock(state):
            self._turn_ledger.resource_guard = "budew_itchy_pollen_item_lock"
            return False
        player = self._scorer._own_player(state)
        if player is not None and player.deck_count <= 0:
            self._turn_ledger.resource_guard = "roto_requires_cards_to_reveal"
            return False
        if state.supporter_played:
            return self._post_supporter_roto_can_close_rocket_ko(state)
        self._turn_ledger.roto_preserved_reason = "play_roto_before_partial_damage"
        return True

    def _post_supporter_roto_can_close_rocket_ko(self, state: GameState) -> bool:
        """Allow post-Supporter Roto only for one-to-four missing KO Supporters."""
        active = self._scorer._own_active(state)
        opponent = self._scorer._opponent_player(state)
        target = opponent.active if opponent is not None else None
        if (
            active is None
            or target is None
            or active.card_id != HONCHKROW
            or self._scorer._energy_units_for_pokemon(active) < 2
        ):
            return False
        per_supporter = self._scorer._attack_damage(
            state,
            Candidate(0, {"attackId": ROCKET_FEATHERS}, OptionType.ATTACK),
            60,
            target,
        )
        if per_supporter <= 0:
            return False
        required = (max(0, int(target.hp)) + per_supporter - 1) // per_supporter
        deficit = required - self._scorer._effective_supporters_in_hand(state)
        self._turn_ledger.roto_post_supporter_required = max(0, deficit)
        if not 1 <= deficit <= ROTO_STICK_MAX_REVEAL_COUNT:
            self._turn_ledger.roto_post_supporter_outcome = "deficit_out_of_range"
            return False
        if self._scorer._roto_remaining_supporters(state) < deficit:
            self._turn_ledger.roto_post_supporter_outcome = "insufficient_remaining_supporters"
            return False
        self._turn_ledger.roto_post_supporter_lethal_attempt = True
        self._turn_ledger.roto_post_supporter_outcome = "awaiting_reveal"
        self._turn_ledger.roto_preserved_reason = "post_supporter_rocket_feathers_ko_attempt"
        return True

    def _articuno_is_reachable(self, state: GameState, candidates: Sequence[Candidate]) -> bool:
        """Return whether Articuno is already present or reachable in this prompt."""
        if self._scorer._articuno_is_on_field(state):
            return True
        return any(
            self._scorer._feature_int(candidate, "card_id") == ARTICUNO
            and candidate.option_type in {OptionType.PLAY, OptionType.CARD}
            for candidate in candidates
        )

    def _articuno_should_precede_development(
        self, state: GameState, candidates: Sequence[Candidate]
    ) -> bool:
        """Return whether matchup protection must precede normal evolution."""
        return (
            self._scorer._articuno_is_needed(state)
            and not self._scorer._articuno_is_on_field(state)
            and self._articuno_is_reachable(state, candidates)
        )

    def _canonical_giovanni_is_productive(self, state: GameState) -> bool:
        """Require a public two/three-Prize or final-Prize bench target."""
        plan = self._giovanni_switch_plan(state)
        if plan is not None and plan.opponent_target_serial is not None:
            self._switch_commitment = plan
            self._turn_ledger.next_attacker_serial = plan.target_serial
            self._turn_ledger.giovanni_pivot_reason = "giovanni_porygon2_bench_ko"
            return True
        if self._scorer._giovanni_pivot_is_productive(state):
            self._turn_ledger.giovanni_pivot_reason = "free_porygon_for_ready_honchkrow"
            return True
        if self._scorer._giovanni_switch_line_is_productive(state):
            return True
        player = self._scorer._own_player(state)
        opponent = self._scorer._opponent_player(state)
        if player is None or opponent is None or not opponent.bench:
            return False
        prizes_left = len(player.prize)
        for pokemon in opponent.bench:
            prize_value = int(
                getattr(
                    pokemon,
                    "effective_prize_value",
                    self._scorer.catalog.get_traits(str(pokemon.card_id)).base_prize_value,
                )
            )
            if prize_value >= 2 or prize_value >= prizes_left:
                required = max(1, (max(0, int(pokemon.hp)) + 59) // 60)
                if self._scorer._effective_supporters_in_hand(state) >= required:
                    self._turn_ledger.supporters_needed_for_ko = required
                    return True
            active = self._scorer._own_active(state)
            if active is not None and active.card_id == HONCHKROW:
                damage = self._scorer._attack_damage(
                    state,
                    Candidate(
                        0,
                        {"attackId": ROCKET_FEATHERS},
                        OptionType.ATTACK,
                        features={
                            "target_card_id": pokemon.card_id,
                            "target_serial": pokemon.serial,
                        },
                    ),
                    self._scorer._effective_supporters_in_hand(state) * 60,
                    pokemon,
                )
                if damage >= max(0, int(pokemon.hp)):
                    self._turn_ledger.giovanni_pivot_reason = "giovanni_targets_public_ko"
                    return True
        return False

    def _canonical_headset_is_useful(self, state: GameState) -> bool:
        """Choose Headset only for a line recalculated from the public target."""
        plan = self._headset_plan(state)
        self._turn_ledger.headset_reason = plan[0] if plan is not None else ""
        return plan is not None

    def _headset_plan(self, state: GameState) -> tuple[str, tuple[int, ...]] | None:
        """Return the exact public Headset plan and its required Supporters.

        The requirement is intentionally derived from the current target on every
        prompt.  Ledger values describe prior observations and are never inputs
        to a damage decision.
        """
        player = self._scorer._own_player(state)
        opponent = self._scorer._opponent_player(state)
        if player is None or opponent is None:
            return None
        discard_ids = tuple(
            self._scorer._card_id_from_value(card)
            for card in player.discard
            if self._scorer._is_rocket_supporter(
                self._scorer._card_id_from_value(card),
                self._scorer.catalog.get_card(str(self._scorer._card_id_from_value(card))) or {},
            )
        )
        if not discard_ids:
            return None
        held_ids = {
            self._scorer._card_id_from_value(card) for card in self._scorer._hand_cards(state)
        }
        recovery_ids = tuple(
            card_id for card_id in discard_ids if card_id != ARIANA or ARIANA not in held_ids
        )
        active = player.active
        if active is not None and active.card_id == HONCHKROW:
            target = opponent.active
            if target is not None and self._scorer._energy_units_for_pokemon(active) >= 2:
                per_supporter = self._scorer._attack_damage(
                    state,
                    Candidate(0, {"attackId": ROCKET_FEATHERS}, OptionType.ATTACK),
                    60,
                    target,
                )
                needed = (max(0, int(target.hp)) + per_supporter - 1) // per_supporter
                hand = self._scorer._effective_supporters_in_hand(state)
                missing = max(0, needed - hand)
                if 0 < missing <= min(2, len(recovery_ids)):
                    self._record_public_line(
                        "headset_rocket_feathers_ko",
                        active,
                        target,
                        hand * per_supporter,
                        (hand + missing) * per_supporter,
                        recovery_ids[:missing],
                        "selected",
                    )
                    return "headset_rocket_feathers_ko", recovery_ids[:missing]
                if (
                    ARIANA in discard_ids
                    and any(card_id != ARIANA for card_id in discard_ids)
                    and hand + 1 > hand
                    and per_supporter >= 60
                ):
                    self._record_public_line(
                        "headset_rocket_feathers_plus_ariana",
                        active,
                        target,
                        hand * per_supporter,
                        (hand + 1) * per_supporter,
                        (ARIANA,),
                        "preserve_ariana_next_turn",
                    )
                    return "headset_rocket_feathers_plus_ariana", (
                        ARIANA,
                        next(card_id for card_id in discard_ids if card_id != ARIANA),
                    )
        for attacker in player.bench:
            if attacker is None or attacker.card_id != PORYGON2:
                continue
            for target in opponent.bench:
                if target is None or GIOVANNI not in discard_ids:
                    continue
                line = self._evaluate_public_attack_line(
                    state, attacker, target, R_COMMAND, supporters_spent=(GIOVANNI,)
                )
                if line.knocks_out:
                    self._record_public_line(
                        "headset_giovanni_porygon2_bench_ko",
                        attacker,
                        target,
                        line.damage_before,
                        line.damage_after,
                        (GIOVANNI,),
                        "selected",
                    )
                    return "headset_giovanni_porygon2_bench_ko", (GIOVANNI,)
        if self._scorer._effective_supporters_in_hand(state) == 0 or (
            self._scorer._card_in_hand(state, PETREL)
            and self._scorer._petrel_search_score(state)[0] < 0
        ):
            useful = tuple(
                dict.fromkeys(
                    card_id
                    for card_id in discard_ids
                    if card_id in {ARIANA, ARCHER, GIOVANNI, PETREL, PROTON}
                )
            )
            if useful:
                if PETREL in {
                    self._scorer._card_id_from_value(card)
                    for card in self._scorer._hand_cards(state)
                }:
                    self._turn_ledger.deferred_petrel_reason = (
                        "petrel_only_target_is_deferred_proton"
                    )
                return "headset_supporter_recovery", useful[:2]
        return None

    def _record_public_line(
        self,
        line_type: str,
        attacker: Any,
        target: Any,
        damage_before: int,
        damage_after: int,
        supporters: tuple[int, ...],
        verdict: str,
    ) -> None:
        """Record bounded, public evidence for a calculated tactical line."""
        record: dict[str, Any] = {
            "line_type": line_type,
            "attacker": getattr(attacker, "card_id", None),
            "attacker_serial": getattr(attacker, "serial", None),
            "target": getattr(target, "card_id", None),
            "target_serial": getattr(target, "serial", None),
            "damage_before": damage_before,
            "damage_after": damage_after,
            "supporters": list(supporters),
            "prizes": int(
                getattr(
                    target,
                    "effective_prize_value",
                    self._scorer.catalog.get_traits(
                        str(getattr(target, "card_id", 0))
                    ).base_prize_value,
                )
            )
            if target is not None
            else 0,
            "verdict": verdict,
        }
        if record not in self._turn_ledger.public_line_evaluations:
            self._turn_ledger.public_line_evaluations.append(record)

    def _evaluate_public_attack_line(
        self,
        state: GameState,
        attacker: Any,
        target: Any,
        attack_id: int,
        *,
        supporters_recovered: tuple[int, ...] = (),
        supporters_spent: tuple[int, ...] = (),
    ) -> PublicAttackLine:
        """Calculate a public attack line for one attacker, target, and action."""
        attacker_id = int(getattr(attacker, "card_id", 0) or 0)
        target_id = int(getattr(target, "card_id", 0) or 0)
        ready = (
            attacker is not None
            and target is not None
            and self._attack_cost_satisfied(attacker, attack_id)
        )
        supporters_in_hand = self._scorer._effective_supporters_in_hand(state) + len(
            supporters_recovered
        )
        supporters_in_discard = self._scorer._rocket_supporters_in_discard(state) + len(
            supporters_spent
        )
        before_base = 0
        after_base = 0
        if attack_id == ROCKET_FEATHERS:
            before_base = self._scorer._effective_supporters_in_hand(state) * 60
            after_base = max(0, supporters_in_hand - len(supporters_spent)) * 60
        elif attack_id == R_COMMAND:
            before_base = self._scorer._rocket_supporters_in_discard(state) * 20
            after_base = supporters_in_discard * 20
        else:
            attack = self._scorer.catalog.get_attack(str(attack_id)) or {}
            before_base = self._scorer._metadata_int(attack, "damage")
            after_base = before_base
        candidate = Candidate(
            0,
            {"attackId": attack_id},
            OptionType.ATTACK,
            features={
                "target_card_id": target_id,
                "target_serial": int(getattr(target, "serial", 0) or 0),
            },
        )
        damage_before = self._scorer._attack_damage(state, candidate, before_base, target)
        damage_after = self._scorer._attack_damage(state, candidate, after_base, target)
        target_hp = max(0, int(getattr(target, "hp", 0) or 0))
        knocks_out = ready and damage_after >= target_hp > 0
        prizes_taken = (
            int(
                getattr(
                    target,
                    "effective_prize_value",
                    self._scorer.catalog.get_traits(str(target_id)).base_prize_value,
                )
            )
            if knocks_out
            else 0
        )
        own_player = self._scorer._own_player(state)
        wins_game = bool(own_player and prizes_taken >= len(own_player.prize) > 0)
        veto_reason = ""
        if not ready:
            veto_reason = "attack_cost_not_ready"
        elif not knocks_out:
            veto_reason = "public_damage_insufficient"
        line = PublicAttackLine(
            attacker_card_id=attacker_id,
            attacker_serial=getattr(attacker, "serial", None),
            target_card_id=target_id,
            target_serial=getattr(target, "serial", None),
            attack_id=attack_id,
            damage_before=damage_before,
            damage_after=damage_after,
            supporters_recovered=supporters_recovered,
            supporters_spent=supporters_spent,
            attack_ready=ready,
            knocks_out=knocks_out,
            prizes_taken=prizes_taken,
            wins_game=wins_game,
            veto_reason=veto_reason,
        )
        evaluation = {
            "line_type": "public_attack",
            "attacker": line.attacker_card_id,
            "attacker_serial": line.attacker_serial,
            "target": line.target_card_id,
            "target_serial": line.target_serial,
            "attack_id": line.attack_id,
            "damage_before": line.damage_before,
            "damage_after": line.damage_after,
            "supporters_recovered": list(line.supporters_recovered),
            "supporters_spent": list(line.supporters_spent),
            "prizes": line.prizes_taken,
            "wins_game": line.wins_game,
            "verdict": "ko" if line.knocks_out else "veto",
            "veto_reason": line.veto_reason,
        }
        if evaluation not in self._turn_ledger.public_line_evaluations:
            self._turn_ledger.public_line_evaluations.append(evaluation)
        return line

    def _headset_ariana_recovery_is_useful(self, state: GameState) -> bool:
        """Return whether Headset restores Ariana and a second public useful Supporter."""
        player = self._scorer._own_player(state)
        if player is None or self._scorer._card_in_hand(state, ARIANA) or state.supporter_played:
            return False
        discard_ids = {self._scorer._card_id_from_value(card) for card in player.discard}
        petrel_only_deferred = (
            self._scorer._card_in_hand(state, PETREL)
            and self._scorer._petrel_search_score(state)[0] < 0
        )
        return bool(
            ARIANA in discard_ids
            and bool(discard_ids & {ARCHER, GIOVANNI, PETREL, PROTON})
            and (self._scorer._effective_supporters_in_hand(state) == 0 or petrel_only_deferred)
            and self._scorer._ariana_is_safe_and_useful(state)
        )

    def _transceiver_line_requires_resolution(self, state: GameState) -> bool:
        """Return whether Transceiver must resolve before a lethal attack."""
        if not self._scorer._card_in_hand(state, TRANSCEIVER):
            return False
        needed = self._turn_ledger.supporters_needed_for_ko or (
            self._scorer._supporters_needed_for_ko(state)
        )
        visible = self._scorer._supporters_in_hand(state)
        effective = self._scorer._effective_supporters_in_hand(state)
        return bool(
            self._scorer._proton_setup_is_useful(state)
            or self._scorer._giovanni_pivot_is_productive(state)
            or (needed > 0 and visible < needed <= effective)
        )

    def _supporter_resolution_required_before_attack(self, state: GameState) -> bool:
        """Return whether a public Supporter search/recovery must precede an attack."""
        if state.supporter_played:
            return False
        active = self._scorer._own_active(state)
        if active is None:
            return False
        hand = self._scorer._effective_supporters_in_hand(state)
        if active.card_id == HONCHKROW:
            required = self._scorer._supporters_needed_for_ko(state)
            deficit = hand < required
            return bool(
                deficit
                and (
                    self._transceiver_line_requires_resolution(state)
                    or self._headset_line_requires_resolution(state)
                    or self._scorer._roto_stick_is_needed(state)
                )
            )
        if active.card_id == PORYGON2:
            required = self._scorer._r_command_supporters_needed(state)
            deficit = self._scorer._rocket_supporters_in_discard(state) < required
            return bool(
                deficit
                and (
                    self._headset_line_requires_resolution(state)
                    or self._scorer._roto_can_close_r_command_line(state)
                )
            )
        return False

    def _refresh_turn_obligations(self, state: GameState) -> None:
        """Refresh public obligations after every state-changing decision."""
        obligations: list[str] = []
        if self._supporter_resolution_required_before_attack(state):
            if self._scorer._card_in_hand(state, TRANSCEIVER):
                obligations.append("must_search_supporter")
            if self._scorer._card_in_hand(state, MIRACLE_HEADSET):
                obligations.append("must_play_headset")
            if self._scorer._card_in_hand(state, ROTO_STICK):
                obligations.append("must_play_roto")
        board_plan = self._scorer.board_setup_plan(state)
        has_concrete_development = bool(
            self._scorer._card_in_hand(state, PROTON)
            or any(
                self._scorer._card_in_hand(state, card_id)
                for card_id in (MURKROW, PORYGON, HONCHKROW, PORYGON2)
            )
        )
        if board_plan.productive and has_concrete_development:
            obligations.append("must_develop_board")
        player = self._scorer._own_player(state)
        if player is not None:
            if not self._scorer._own_bench_full(state) and any(
                self._scorer._card_in_hand(state, card_id) for card_id in (MURKROW, PORYGON)
            ):
                obligations.append("must_play_basic_before_ariana")
            if (
                self._scorer._card_in_hand(state, HONCHKROW)
                and self._scorer._has_murkrow_ready_to_evolve(state)
            ) or (
                self._scorer._card_in_hand(state, PORYGON2)
                and self._scorer._has_porygon_ready_to_evolve(state)
            ):
                obligations.append("must_evolve_before_ariana")
            recovery_plan = self._recovery_plan(state)
            self._turn_ledger.recovery_plan_reason = recovery_plan.reason
            self._turn_ledger.recovery_plan_cards = recovery_plan.recovered_cards
            self._turn_ledger.deferred_petrel_reason = recovery_plan.deferred_petrel_reason
            if recovery_plan.productive:
                obligations.append("must_recover_before_ariana")
            if (
                self._scorer._articuno_is_needed(state)
                and not self._scorer._articuno_is_on_field(state)
                and not self._scorer._own_bench_full(state)
                and self._scorer._card_in_hand(state, ARTICUNO)
            ):
                obligations.append("must_develop_articuno")
            if not state.energy_attached and self._turn_ledger.energy_cards_in_hand:
                if self._energy_has_same_turn_productive_line(state):
                    obligations.append("must_attach_energy_for_attack")
        if obligations or self._scorer._productive_line_available(state):
            obligations.append("must_not_end")
        self._turn_ledger.unresolved_obligations = tuple(dict.fromkeys(obligations))
        self._turn_ledger.development_obligations_pending = tuple(
            obligation
            for obligation in self._turn_ledger.unresolved_obligations
            if obligation.endswith("before_ariana") or obligation == "must_develop_board"
        )

    def _energy_has_same_turn_productive_line(self, state: GameState) -> bool:
        """Return whether visible Energy enables a committed attack this turn."""
        player = self._scorer._own_player(state)
        if player is None:
            return False
        if self._public_abra_threat(state) and not self._turn_ledger.first_own_turn:
            return False
        return any(
            pokemon is not None
            and pokemon.card_id in {HONCHKROW, PORYGON2, MURKROW}
            and self._scorer._energy_units_for_pokemon(pokemon) + 1
            >= self._scorer._attack_energy_target(int(pokemon.card_id))
            for pokemon in [player.active, *player.bench]
        )

    def _public_abra_threat(self, state: GameState) -> bool:
        """Return whether the opponent publicly exposes the Abra evolution line."""
        return bool(self._scorer._visible_opponent_card_ids(state) & {ABRA, KADABRA, ALAKAZAM})

    def _headset_line_requires_resolution(self, state: GameState) -> bool:
        """Return whether Miracle Headset must resolve before a lethal attack."""
        if not self._scorer._card_in_hand(state, MIRACLE_HEADSET):
            return False
        return bool(self._canonical_headset_is_useful(state))

    def _attack_wins_game(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether an attack explicitly or arithmetically takes the last Prizes."""
        if self._scorer._truthy(candidate.option, "win", "wins", "gameOver"):
            return True
        player = self._scorer._own_player(state)
        return bool(
            player
            and len(player.prize) > 0
            and self._variant_attack_is_lethal(state, candidate)
            and self._scorer._active_target_prize_value(state) >= len(player.prize)
        )

    def _roto_setup_mode(self, state: GameState) -> bool:
        """Return whether Roto may search opening setup or a no-Supporter survival line."""
        return bool(
            self._scorer._own_turn_number(state) == 1
            and not self._scorer._card_in_hand(state, PROTON)
            and not self._scorer._card_in_hand(state, ARIANA)
        )

    def _variant_attack_is_lethal(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether a public attack candidate takes the current Active KO."""
        target_hp = self._target_hp(state, candidate)
        if target_hp <= 0:
            return False
        attack_id = self._scorer._attack_id(candidate)
        if attack_id in {ROCKET_FEATHERS, R_COMMAND, HAMMER_IN}:
            return self._candidate_damage(state, candidate) >= target_hp
        return self._candidate_damage(state, candidate) >= target_hp

    def _rocket_feathers_is_immediate_ko(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether Rocket Feathers reaches its public target HP this turn."""
        return bool(
            self._scorer._attack_id(candidate) == ROCKET_FEATHERS
            and self._variant_attack_is_lethal(state, candidate)
        )

    def _supporters_required_for_candidate(self, state: GameState, candidate: Candidate) -> int:
        """Return the exact Supporter count required by Rocket Feathers."""
        if self._scorer._attack_id(candidate) != ROCKET_FEATHERS:
            return 0
        target = self._scorer._target_opponent_pokemon(state, candidate)
        if target is None:
            return 0
        damage_per_supporter = self._scorer._attack_damage(state, candidate, 60, target)
        if damage_per_supporter <= 0:
            return 0
        return (max(0, int(target.hp)) + damage_per_supporter - 1) // damage_per_supporter

    def _is_factory_effect_candidate(self, candidate: Candidate, state: GameState) -> bool:
        """Return whether a candidate activates the Factory already in play."""
        card_id = self._scorer._feature_int(candidate, "card_id")
        if card_id == FACTORY and candidate.option_type is OptionType.ABILITY:
            return True
        source = candidate.option.get("sourceCardId", candidate.option.get("cardId"))
        if source == FACTORY and candidate.option_type is not OptionType.PLAY:
            return True
        stadium = state.stadium
        if candidate.option_type is OptionType.ABILITY and isinstance(stadium, list):
            return any(
                isinstance(card, Mapping) and self._scorer._card_id_from_value(card) == FACTORY
                for card in stadium
            )
        return False

    def _ignition_attack_plan(
        self, state: GameState, candidate: Candidate
    ) -> SwitchCommitment | None:
        """Build an immediate attack commitment for a legal Ignition attachment."""
        if (
            candidate.option_type is not OptionType.ATTACH
            or self._scorer._feature_int(candidate, "card_id") != IGNITION_ENERGY
            or state.energy_attached
        ):
            return None
        player = self._scorer._own_player(state)
        active = player.active if player is not None else None
        if active is None or not self._candidate_targets_active(candidate, active):
            return None
        target_id = self._scorer._feature_int(candidate, "target_card_id")
        if target_id and target_id != int(active.card_id):
            return None
        choice = self._pokemon_attack_choice(state, active, giovanni_played=False)
        if choice is None or not choice[2] or choice[1] <= 0:
            return None
        attack_id, damage, _ = choice
        return SwitchCommitment(
            method="ignition",
            turn=state.turn,
            target_card_id=int(active.card_id),
            target_serial=active.serial,
            attack_id=attack_id,
            planned_damage=damage,
            requires_ignition=False,
        )

    @staticmethod
    def _candidate_targets_active(candidate: Candidate, active: Any) -> bool:
        """Resolve an active attachment target from CABT area or serial metadata."""
        if bool(candidate.features.get("target_is_active", False)):
            return True
        target_serial = candidate.features.get("target_serial")
        active_serial = getattr(active, "serial", None)
        return (
            isinstance(target_serial, int)
            and isinstance(active_serial, int)
            and target_serial > 0
            and target_serial == active_serial
        )

    def _roto_can_improve_rocket_line(self, state: GameState) -> bool:
        """Return whether a legal Roto-Stick can improve a nonlethal line."""
        active = self._scorer._own_active(state)
        player = self._scorer._own_player(state)
        if active is None or player is None:
            return False
        if active.card_id != HONCHKROW or self._scorer._energy_units_for_pokemon(active) < 2:
            return False
        if player.deck_count <= 0:
            return False
        target_hp = self._scorer._raw_opponent_hp(state)
        current_damage = self._scorer._effective_supporters_in_hand(state) * 60
        return current_damage < target_hp

    def _is_safe_pre_draw_hand_reduction(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether a Pokémon/evolution can leave hand before Ariana safely."""
        card_id = self._scorer._feature_int(candidate, "card_id")
        if candidate.option_type is OptionType.EVOLVE:
            return card_id in {HONCHKROW, PORYGON2}
        if candidate.option_type is not OptionType.PLAY:
            return False
        if self._scorer._metadata_int(candidate.card, "cardType") != 0:
            return False
        return card_id in {MURKROW, PORYGON} and not self._scorer._own_bench_full(state)

    def _porygon_bench_evolution_is_preferred(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether a bench Porygon evolution should outrank exposed active play."""
        if candidate.option_type not in {OptionType.PLAY, OptionType.EVOLVE}:
            return False
        if self._scorer._feature_int(candidate, "card_id") != PORYGON2:
            return False
        player = self._scorer._own_player(state)
        active = self._scorer._own_active(state)
        if player is None or active is None or active.card_id != PORYGON:
            return False
        target_serial = self._scorer._feature_int(candidate, "target_serial")
        if not target_serial:
            return False
        if active.serial is not None and target_serial == active.serial:
            return False
        return any(
            pokemon is not None and pokemon.card_id == PORYGON and pokemon.serial == target_serial
            for pokemon in player.bench
        )

    def _energy_attachment_before_ariana_is_needed(
        self, state: GameState, candidate: Candidate
    ) -> bool:
        """Return whether an energy attachment must resolve before Ariana."""
        return bool(
            candidate.option_type is OptionType.ATTACH
            and self._scorer._energy_attachment_is_committed(state, candidate)
        )

    def _probabilistic_pre_draw_hand_reduction(
        self, state: GameState, candidate: Candidate
    ) -> bool:
        """Return whether a safe action increases the estimated value of Ariana."""
        if not self._scorer._ariana_is_safe_and_useful(state):
            return False
        if self._is_safe_pre_draw_hand_reduction(state, candidate):
            reduction = 1
        elif candidate.option_type is OptionType.ATTACH:
            card_id = self._scorer._feature_int(candidate, "card_id")
            reduction = int(
                self._scorer._is_energy_card(card_id, candidate.card)
                and self._scorer._attachment_score(state, candidate)[0] > 0
            )
        elif candidate.option_type is OptionType.PLAY:
            card_id = self._scorer._feature_int(candidate, "card_id")
            if card_id == FACTORY and self._scorer._factory_play_is_useful(state):
                reduction = 1
            elif card_id == POKE_PAD and self._scorer._pokepad_honchkrow_is_useful(
                state, candidate
            ):
                reduction = 1
            elif card_id == ULTRA_BALL and self._canonical_ultra_ball_is_productive(state):
                reduction = 2
            else:
                return False
        else:
            return False
        factory_will_be_played = (
            candidate.option_type is OptionType.PLAY
            and self._scorer._feature_int(candidate, "card_id") == FACTORY
        )
        return self._scorer._ariana_expected_value(state, reduction, factory_will_be_played) > (
            self._scorer._ariana_expected_value(state) + 20.0
        )

    def _filter_forbidden_selections(
        self,
        state: GameState,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
        context: SelectContext | None,
    ) -> list[Selection]:
        """Apply Honchkrow discard cardinality without changing shared policy."""
        by_index = {candidate.option_index: candidate for candidate in candidates}
        if context in {SelectContext.DISCARD, SelectContext.DISCARD_CARD_OR_ATTACHED_CARD}:
            disposable = {
                candidate.option_index
                for candidate in candidates
                if self._scorer._feature_int(candidate, "card_id") in {ARTICUNO, FACTORY}
            }
            if disposable:
                preferred = [
                    selection
                    for selection in selections
                    if any(index in disposable for index in selection.indices)
                ]
                if preferred:
                    self._turn_ledger.resource_guard = "discard_articuno_or_factory_before_headset"
                    selections = preferred
            cape_targets = {
                candidate.option_index
                for candidate in candidates
                if self._is_tool_scrapper_priority_target(candidate)
            }
            if cape_targets:
                selected = [
                    selection
                    for selection in selections
                    if any(index in cape_targets for index in selection.indices)
                ]
                if selected:
                    self._turn_ledger.heros_cape_scrapped = True
                    return selected
        if context is SelectContext.TO_HAND:
            stretcher_targets = [
                candidate
                for candidate in candidates
                if self._scorer._card_selected_from_night_stretcher(candidate)
            ]
            if stretcher_targets:
                ranked_targets = [
                    (
                        self._night_stretcher_target_priority(
                            state, self._scorer._feature_int(candidate, "card_id")
                        ),
                        candidate.option_index,
                    )
                    for candidate in stretcher_targets
                ]
                best_priority, reason = max((rank for rank, _ in ranked_targets), default=(0, ""))
                if best_priority > 0:
                    accepted = {index for rank, index in ranked_targets if rank[0] == best_priority}
                    selected = [
                        selection
                        for selection in selections
                        if any(index in accepted for index in selection.indices)
                    ]
                    if selected:
                        self._turn_ledger.night_stretcher_priority_reason = reason
                        plan = self._recovery_plan(state)
                        self._turn_ledger.recovery_plan_reason = plan.reason
                        self._turn_ledger.recovery_plan_cards = plan.recovered_cards
                        selections = selected
        if (
            context in {SelectContext.TO_ACTIVE, SelectContext.SWITCH}
            and self._scorer._articuno_is_needed(state)
            and (
                self._scorer._promotion_line_is_lethal(state, HONCHKROW)
                or self._scorer._promotion_line_is_lethal(state, PORYGON2)
            )
        ):
            non_articuno = [
                selection
                for selection in selections
                if not any(
                    by_index.get(index) is not None
                    and self._scorer._feature_int(by_index[index], "card_id") == ARTICUNO
                    for index in selection.indices
                )
            ]
            if non_articuno:
                self._turn_ledger.resource_guard = "preserve_articuno_for_matchup_defense"
                selections = non_articuno
        if context is SelectContext.TO_HAND and self._scorer._articuno_is_needed(state):
            proton_articuno = {
                candidate.option_index
                for candidate in candidates
                if candidate.option.get("sourceCardId") == PROTON
                and self._scorer._feature_int(candidate, "card_id") == ARTICUNO
            }
            if proton_articuno:
                protected = [
                    selection
                    for selection in selections
                    if any(index in proton_articuno for index in selection.indices)
                ]
                if protected:
                    self._turn_ledger.resource_guard = (
                        "proton_prioritizes_articuno_against_dragapult"
                    )
                    selections = protected
        if context is SelectContext.TO_HAND and self._evolution_ko_commitment is not None:
            if self._evolution_ko_commitment.stage == "select_honchkrow":
                honchkrow = [
                    selection
                    for selection in selections
                    if any(
                        self._scorer._feature_int(candidate, "card_id") == HONCHKROW
                        for index in selection.indices
                        if (candidate := by_index.get(index)) is not None
                    )
                ]
                if honchkrow:
                    self._turn_ledger.resource_guard = "select_committed_honchkrow"
                    return honchkrow
        if (
            self._uses_supporter_lethal_commitment
            and context
            in {
                SelectContext.DISCARD,
                SelectContext.DISCARD_CARD_OR_ATTACHED_CARD,
            }
            and self._attack_sequence is not None
            and self._attack_sequence.attack_id == ROCKET_FEATHERS
        ):
            if self._attack_sequence.planned_damage < self._attack_sequence.ko_threshold:
                self._turn_ledger.resource_guard = "rocket_feathers_nonlethal_veto"
                return list(selections)
            required = self._attack_sequence.minimum_damage
            target = self._scorer._opponent_player(state)
            if target is not None and target.active is not None:
                per_supporter = self._scorer._attack_damage(
                    state,
                    Candidate(0, {"attackId": ROCKET_FEATHERS}, OptionType.ATTACK),
                    60,
                    target.active,
                )
                required = (max(0, int(target.active.hp)) + per_supporter - 1) // per_supporter
            exact = [
                selection
                for selection in selections
                if self._rocket_supporter_count(selection, by_index) == required
            ]
            available = self._scorer._effective_supporters_in_hand(state)
            if exact and required <= available:
                self._turn_ledger.resource_guard = "discard_exact_supporters_for_rocket_ko"
                self._turn_ledger.rocket_supporters_discarded = required
                self._turn_ledger.rocket_supporters_preserved = max(0, available - required)
                return exact
        if self._uses_resource_variant and context is SelectContext.TO_HAND:
            roto_exact = self._roto_recovery_selections(state, selections, candidates)
            if roto_exact is not None:
                self._turn_ledger.roto_supporters_revealed = roto_exact[0]
                self._turn_ledger.roto_supporters_selected = roto_exact[0]
                self._match_ledger.roto_supporters_revealed += roto_exact[0]
                self._match_ledger.roto_supporters_selected += roto_exact[0]
                self._turn_ledger.roto_damage_acquired = roto_exact[0] * 60
                self._turn_ledger.resource_guard = "select_all_roto_supporters"
                return roto_exact[1]
            transceiver_safe = self._transceiver_selections(state, selections, candidates)
            if transceiver_safe is not None:
                return transceiver_safe
        if (
            self._uses_retreat_guard
            and context in {SelectContext.TO_ACTIVE, SelectContext.SWITCH}
            and self._switch_commitment is not None
        ):
            exact_switch = [
                selection
                for selection in selections
                if any(
                    self._candidate_matches_switch_commitment(by_index.get(index))
                    for index in selection.indices
                )
            ]
            if exact_switch:
                self._turn_ledger.resource_guard = "promote_committed_switch_attacker"
                return exact_switch
        if (
            self._switch_commitment is not None
            and context is SelectContext.EFFECT_TARGET
            and self._switch_commitment.opponent_target_serial is not None
        ):
            committed_target = [
                selection
                for selection in selections
                if any(
                    (candidate := by_index.get(index)) is not None
                    and self._scorer._feature_int(candidate, "target_serial")
                    == self._switch_commitment.opponent_target_serial
                    for index in selection.indices
                )
            ]
            if committed_target:
                self._turn_ledger.resource_guard = "select_committed_giovanni_target"
                return committed_target
        if (
            self._uses_retreat_guard
            and context is SelectContext.TO_HAND
            and self._headset_turn == state.turn
        ):
            headset_plan = self._headset_plan(state)
            if headset_plan is not None:
                reason, required_ids = headset_plan
                exact_plan = [
                    selection
                    for selection in selections
                    if all(
                        any(
                            self._scorer._feature_int(candidate, "card_id") == card_id
                            for index in selection.indices
                            if (candidate := by_index.get(index)) is not None
                        )
                        for card_id in required_ids
                    )
                ]
                if exact_plan:
                    self._turn_ledger.headset_reason = reason
                    self._turn_ledger.headset_recovery_reason = reason
                    self._turn_ledger.recovery_plan_reason = reason
                    self._turn_ledger.recovery_plan_cards = required_ids
                    self._turn_ledger.resource_guard = (
                        "headset_prefers_ariana_plus_second_supporter"
                        if reason == "headset_supporter_recovery" and ARIANA in required_ids
                        else f"headset_plan_{reason}"
                    )
                    return exact_plan
            recoverable = min(2, self._scorer._rocket_supporters_in_discard(state))
            exact_two = [
                selection
                for selection in selections
                if self._rocket_supporter_count(selection, by_index) == recoverable
            ]
            if exact_two:
                holds_ariana = any(
                    self._scorer._card_id_from_value(card) == ARIANA
                    for card in self._scorer._hand_cards(state)
                )
                without_duplicate_ariana = [
                    selection
                    for selection in exact_two
                    if not holds_ariana
                    or all(
                        self._scorer._feature_int(candidate, "card_id") != ARIANA
                        for index in selection.indices
                        if (candidate := by_index.get(index)) is not None
                    )
                ]
                if self._uses_expert_turn_loop and (
                    self._turn_ledger.headset_reason
                    or self._turn_ledger.headset_ariana_recovery
                    or self._headset_ariana_recovery_is_useful(state)
                ):
                    preferred_id = (
                        GIOVANNI
                        if self._turn_ledger.headset_reason == "giovanni_prize_target"
                        else ARIANA
                    )
                    preferred = [
                        selection
                        for selection in (without_duplicate_ariana or exact_two)
                        if any(
                            self._scorer._feature_int(candidate, "card_id") == preferred_id
                            for index in selection.indices
                            if (candidate := by_index.get(index)) is not None
                        )
                    ]
                    if preferred:
                        preference = (
                            self._turn_ledger.headset_reason or "ariana_plus_second_supporter"
                        )
                        self._turn_ledger.resource_guard = f"headset_prefers_{preference}"
                        return preferred
                self._turn_ledger.resource_guard = f"headset_recovers_{recoverable}_supporter"
                return without_duplicate_ariana or exact_two
        safe = super()._filter_forbidden_selections(state, selections, candidates, context)
        if context is SelectContext.MAIN:
            original_has_non_end = any(
                any(
                    by_index.get(index) is not None
                    and by_index[index].option_type is not OptionType.END
                    for index in selection.indices
                )
                for selection in selections
            )
            safe_has_non_end = any(
                any(
                    by_index.get(index) is not None
                    and by_index[index].option_type is not OptionType.END
                    for index in selection.indices
                )
                for selection in safe
            )
            if original_has_non_end and not safe_has_non_end:
                self._turn_ledger.end_only_after_filter += 1
        committed = [
            selection
            for selection in safe
            if not any(
                self._violates_attack_commitment(state, by_index.get(index), context)
                for index in selection.indices
            )
        ]
        safe = committed or safe
        if context not in {SelectContext.DISCARD, SelectContext.DISCARD_CARD_OR_ATTACHED_CARD}:
            diversified = self._filter_duplicate_proton_roles(state, safe, candidates, context)
            return diversified or safe
        required = self._scorer._supporters_needed_for_ko(state)
        capped = [
            selection
            for selection in safe
            if sum(
                self._scorer._is_rocket_supporter(
                    self._scorer._feature_int(candidate, "card_id"), candidate.card
                )
                for index in selection.indices
                if (candidate := by_index.get(index)) is not None
            )
            <= required
        ]
        proton_safe = self._filter_duplicate_proton_roles(
            state, capped or safe, candidates, context
        )
        return proton_safe or capped or safe

    def _roto_recovery_selections(
        self,
        state: GameState,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
    ) -> tuple[int, list[Selection]] | None:
        """Keep selections that take every Supporter revealed by Roto-Stick."""
        revealed = [
            candidate
            for candidate in candidates
            if candidate.option_type is OptionType.CARD
            and (
                candidate.option.get("sourceCardId") == ROTO_STICK or self._roto_turn == state.turn
            )
            and self._scorer._is_rocket_supporter(
                self._scorer._feature_int(candidate, "card_id"), candidate.card
            )
        ]
        if (
            not any(candidate.option.get("sourceCardId") == ROTO_STICK for candidate in candidates)
            and self._roto_turn != state.turn
        ):
            return None
        if self._uses_expert_rounds_1_3 and self._roto_setup_mode(state):
            by_card_id: dict[int, list[int]] = {}
            for candidate in revealed:
                card_id = self._scorer._feature_int(candidate, "card_id")
                by_card_id.setdefault(card_id, []).append(candidate.option_index)
            wanted: set[int] = set()
            if by_card_id.get(PROTON):
                wanted.add(by_card_id[PROTON][0])
            wanted.update(by_card_id.get(ARIANA, ()))
            if not wanted and self._scorer._effective_supporters_in_hand(state) == 0:
                if by_card_id.get(PETREL):
                    wanted.add(by_card_id[PETREL][0])
            exact = [
                selection
                for selection in selections
                if {index for index in selection.indices if index in wanted} == wanted
                and all(index in wanted for index in selection.indices)
            ]
            return len(wanted), exact or list(selections)
        wanted = {candidate.option_index for candidate in revealed}
        if state.supporter_played and self._turn_ledger.roto_post_supporter_lethal_attempt:
            required = self._turn_ledger.roto_post_supporter_required
            if len(wanted) < required:
                self._turn_ledger.roto_post_supporter_outcome = "reveal_did_not_confirm_ko"
                preserve = [
                    selection
                    for selection in selections
                    if all(index not in wanted for index in selection.indices)
                ]
                return 0, preserve or list(selections)
            self._turn_ledger.roto_post_supporter_outcome = "reveal_confirmed_ko"
        exact = [
            selection
            for selection in selections
            if {index for index in selection.indices if index in wanted} == wanted
        ]
        return len(wanted), exact or list(selections)

    def _transceiver_selections(
        self,
        state: GameState,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
    ) -> list[Selection] | None:
        """Resolve Transceiver from the persistent objective without a Proton fallback."""
        if (
            not any(candidate.option.get("sourceCardId") == TRANSCEIVER for candidate in candidates)
            and self._transceiver_turn != state.turn
        ):
            return None
        by_index = {candidate.option_index: candidate for candidate in candidates}
        selection_ids: list[tuple[Selection, set[int]]] = []
        for selection in selections:
            ids = {
                self._scorer._feature_int(candidate, "card_id")
                for index in selection.indices
                if (candidate := by_index.get(index)) is not None
            }
            selection_ids.append((selection, ids))

        objective = (
            self._turn_ledger.objective or self._choose_turn_objective(state, candidates).value
        )
        target_order: list[int]
        if self._transceiver_line_requires_resolution(state):
            target_order = [PETREL, ARCHER, PROTON, GIOVANNI, ARIANA]
            self._turn_ledger.transceiver_objective = "rocket_feathers_required_supporter"
        elif self._scorer._giovanni_pivot_is_productive(state):
            target_order = [GIOVANNI, PROTON, ARIANA, PETREL]
            self._turn_ledger.giovanni_pivot_reason = "transceiver_fetches_giovanni_pivot"
        elif (
            objective
            in {
                TurnObjective.PREVENT_NO_POKEMON_LOSS.value,
                TurnObjective.BUILD_ATTACKER_AND_BOARD.value,
            }
            and self._scorer._proton_setup_is_useful(state)
            and not self._scorer._card_in_hand(state, PROTON)
        ):
            target_order = [PROTON, ARIANA, PETREL, GIOVANNI]
        elif objective in {TurnObjective.WIN_NOW.value, TurnObjective.HIGHEST_PRIZE_KO.value}:
            target_order = [GIOVANNI, ARIANA, PETREL]
        elif (
            self._scorer._ariana_marginal_draw(state) <= 1
            and not self._scorer._factory_in_play(state)
            and not state.stadium_played
        ):
            target_order = [PETREL, ARIANA, GIOVANNI]
        else:
            target_order = [ARIANA, PETREL, GIOVANNI]

        # A second Transceiver in one public turn must not repeat a Proton
        # setup gain that the first search already delivered.
        if self._transceiver_turn == state.turn and self._turn_ledger.proton_gain_remaining == 0:
            target_order = [target_id for target_id in target_order if target_id != PROTON]
            self._turn_ledger.resource_guard = "transceiver_proton_already_resolved"
        if self._turn_ledger.ariana_already_available:
            target_order = [target_id for target_id in target_order if target_id != ARIANA]
            self._turn_ledger.resource_guard = "transceiver_ariana_already_in_hand"

        if state.supporter_played and ARIANA in target_order:
            self._turn_ledger.transceiver_rejected_target = ARIANA
            self._turn_ledger.resource_guard = "transceiver_ariana_after_supporter_veto"
            target_order = [target_id for target_id in target_order if target_id != ARIANA]

        for target_id in target_order:
            exact = [selection for selection, ids in selection_ids if target_id in ids]
            if exact:
                self._turn_ledger.transceiver_target = target_id
                self._turn_ledger.transceiver_objective = objective
                return exact
        non_proton = [selection for selection, ids in selection_ids if PROTON not in ids]
        if non_proton:
            return non_proton
        if (
            self._scorer._proton_setup_is_useful(state)
            and self._turn_ledger.proton_gain_remaining > 0
        ):
            self._turn_ledger.transceiver_target = PROTON
            self._turn_ledger.transceiver_objective = objective
            return list(selections)
        self._match_ledger.late_proton_without_gain += 1
        self._turn_ledger.transceiver_rejected_target = PROTON
        return list(selections)

    def _rocket_supporter_count(
        self, selection: Selection, by_index: Mapping[int, Candidate]
    ) -> int:
        """Count Team Rocket Supporters in one legal multi-card selection."""
        return sum(
            self._scorer._is_rocket_supporter(
                self._scorer._feature_int(candidate, "card_id"), candidate.card
            )
            for index in selection.indices
            if (candidate := by_index.get(index)) is not None
        )

    def _violates_attack_commitment(
        self,
        state: GameState,
        candidate: Candidate | None,
        context: SelectContext | None,
    ) -> bool:
        """Return whether an optional action spends attack resources without an immediate KO."""
        if candidate is None:
            return False
        if candidate.option_type is OptionType.END:
            # State snapshots change after each resolved action.  END must use
            # freshly derived, concrete obligations rather than a field count
            # retained from an earlier prompt.
            self._refresh_turn_obligations(state)
        if not self._uses_expert_turn_loop:
            return False
        if candidate.option_type is OptionType.ATTACK:
            attack_id = self._scorer._attack_id(candidate)
            if attack_id not in {ROCKET_FEATHERS, R_COMMAND, HAMMER_IN}:
                return False
            if self._variant_attack_is_lethal(state, candidate):
                return False
            return True
        if candidate.option_type is OptionType.RETREAT:
            return not self._retreat_enables_immediate_ko(state)
        return bool(
            candidate.option_type is OptionType.CARD
            and self._scorer._feature_int(candidate, "card_id") == PORYGON2
            and context is SelectContext.TO_ACTIVE
            and not (
                self._scorer._pokemon_is_ready(state, candidate)
                and self._scorer.r_command_knocks_out_active(state)
            )
        )

    def _filter_duplicate_proton_roles(
        self,
        state: GameState,
        selections: Sequence[Selection],
        candidates: Sequence[Candidate],
        context: SelectContext | None,
    ) -> list[Selection]:
        """Apply the active variant's multi-target Proton objective."""
        if context is not SelectContext.TO_HAND:
            return list(selections)
        by_index = {candidate.option_index: candidate for candidate in candidates}
        if self._uses_expert_rounds_1_3:
            ranked: list[tuple[tuple[int, int, int, int], Selection]] = []
            for selection in selections:
                proton_cards = [
                    self._scorer._feature_int(candidate, "card_id")
                    for index in selection.indices
                    if (candidate := by_index.get(index)) is not None
                    and candidate.option.get("sourceCardId") == PROTON
                ]
                ranked.append(
                    (
                        (
                            proton_cards.count(MURKROW),
                            len(proton_cards),
                            proton_cards.count(PORYGON),
                            proton_cards.count(ARTICUNO)
                            if self._scorer._articuno_is_needed(state)
                            else 0,
                        ),
                        selection,
                    )
                )
            best = max((rank for rank, _ in ranked), default=None)
            return [selection for rank, selection in ranked if rank == best]
        filtered: list[Selection] = []
        for selection in selections:
            proton_cards = [
                self._scorer._feature_int(candidate, "card_id")
                for index in selection.indices
                if (candidate := by_index.get(index)) is not None
                and candidate.option.get("sourceCardId") == PROTON
            ]
            roles = {self._proton_role(card_id) for card_id in proton_cards}
            if len(proton_cards) <= 1 or len(roles) == len(proton_cards):
                filtered.append(selection)
        return filtered

    @staticmethod
    def _proton_role(card_id: int) -> str:
        """Return the tactical role used to diversify Proton selections."""
        if card_id == MURKROW:
            return "primary"
        if card_id == PORYGON:
            return "r_command"
        if card_id == ARTICUNO:
            return "defensive"
        return str(card_id)

    def _candidate_is_forbidden(
        self,
        state: GameState,
        candidate: Candidate | None,
        context: SelectContext | None,
    ) -> bool:
        if candidate is None:
            return False
        card_type = self._scorer._metadata_int(candidate.card, "cardType")
        target_id = self._scorer._feature_int(candidate, "target_card_id")
        card_id = self._scorer._feature_int(candidate, "card_id")
        if (
            self._uses_supporter_lethal_commitment
            and candidate.option_type is OptionType.PLAY
            and card_type == 3
            and state.supporter_played
        ):
            return True
        if self._uses_retreat_guard and self._candidate_completes_committed_ignition(candidate):
            return False
        if candidate.option_type is OptionType.END and self._scorer._productive_line_available(
            state
        ):
            if self._turn_ledger.resource_guard != "rocket_feathers_nonlethal_veto":
                self._turn_ledger.resource_guard = "productive_action_remains"
            self._turn_ledger.end_reason = "veto_productive_line"
            self._turn_ledger.end_veto_reason = "productive_public_line"
            return True
        if candidate.option_type is OptionType.END and self._turn_ledger.unresolved_obligations:
            self._turn_ledger.resource_guard = "unresolved_turn_obligation"
            self._turn_ledger.end_reason = "veto_" + ",".join(
                self._turn_ledger.unresolved_obligations
            )
            self._turn_ledger.end_veto_reason = self._turn_ledger.end_reason
            return True
        if (
            self._uses_expert_turn_loop
            and candidate.option_type is OptionType.ATTACK
            and self._scorer._own_turn_number(state) == 1
            and self._scorer._own_active_card_id(state) in {PORYGON, PORYGON2}
            and not self._attack_wins_game(state, candidate)
        ):
            self._turn_ledger.setup_guard_reason = "block_initial_porygon_partial_attack"
            return True
        if (
            candidate.option_type is OptionType.PLAY
            and card_type in {1, 2}
            and self._opponent_budew_item_lock(state)
        ):
            self._turn_ledger.resource_guard = "budew_itchy_pollen_item_lock"
            return True
        if (
            candidate.option_type is OptionType.ATTACK
            and self._supporter_resolution_required_before_attack(state)
        ):
            self._turn_ledger.resource_guard = "resolve_supporter_resource_before_attack"
            return True
        if candidate.option_type is OptionType.ATTACH and card_type in {5, 6}:
            if self._scorer._feature_int(candidate, "target_energy_count") >= (
                self._scorer._attack_energy_target(target_id)
            ):
                return True
            energy_id = self._scorer._feature_int(candidate, "card_id")
            if energy_id == ROCKET_ENERGY and target_id == PORYGON2:
                return True
            if energy_id == IGNITION_ENERGY:
                active = self._scorer._own_active(state)
                if active is None or not self._candidate_targets_active(candidate, active):
                    return True
            if target_id == ARTICUNO:
                return True
            if (
                energy_id == IGNITION_ENERGY
                and self._ignition_attack_plan(state, candidate) is None
            ):
                self._turn_ledger.energy_attachment_reason = "defer_without_same_turn_attack"
                return True
            if (
                energy_id == ROCKET_ENERGY
                and self._public_abra_threat(state)
                and not self._energy_has_same_turn_productive_line(state)
            ):
                self._turn_ledger.energy_veto_threat = "public_abra_line"
                self._turn_ledger.energy_attachment_reason = "defer_against_abra_without_attack"
                return True
            rocket_murkrow_attack = bool(
                energy_id == ROCKET_ENERGY
                and target_id == MURKROW
                and candidate.option.get("enablesAttack", candidate.option.get("enables", False))
            )
            if self._only_energy_in_hand(state) and not (
                (energy_id == IGNITION_ENERGY and self._ignition_attack_plan(state, candidate))
                or rocket_murkrow_attack
                or self._scorer._energy_attachment_is_committed(state, candidate)
            ):
                return True
            return False
        if (
            candidate.option_type is OptionType.ATTACK
            and self._scorer._attack_id(candidate) == ARTICUNO_ATTACK
        ):
            return True
        if (
            candidate.option_type is OptionType.ATTACK
            and self._scorer._attack_id(candidate) == HACKING
        ):
            return True
        if (
            candidate.option_type is OptionType.ATTACK
            and self._scorer._attack_id(candidate) == TORMENT
            and self._evolution_ko_commitment is not None
        ):
            return True
        if (
            candidate.option_type is OptionType.ATTACK
            and self._scorer._attack_id(candidate) == ROCKET_FEATHERS
            and not self._rocket_feathers_is_immediate_ko(state, candidate)
        ):
            self._turn_ledger.resource_guard = "rocket_feathers_nonlethal_veto"
            return True
        if (
            candidate.option_type is OptionType.ATTACK
            and self._scorer._attack_id(candidate) in {R_COMMAND, HAMMER_IN}
            and not self._scorer._attack_has_committed_ko(state, candidate)
        ):
            self._turn_ledger.resource_guard = "resource_attack_nonlethal_veto"
            return True
        if candidate.option_type is OptionType.ATTACK:
            attack_id = self._scorer._attack_id(candidate)
            damage = self._candidate_damage(state, candidate)
            if (
                damage <= 0
                and attack_id != TORMENT
                and (
                    self._scorer._card_in_hand(state, ARIANA)
                    or self._scorer._card_in_hand(state, POKE_PAD)
                    or self._scorer._articuno_is_needed(state)
                )
                and not (
                    self._candidate_completes_committed_ignition(candidate)
                    or (
                        self._switch_commitment is not None
                        and self._switch_commitment.method == "ignition"
                    )
                )
            ):
                self._turn_ledger.resource_guard = "zero_damage_attack_vetoed_for_public_plan"
                return True
        if (
            candidate.option_type is OptionType.ATTACK
            and self._scorer._attack_id(candidate) == DECEIT
        ):
            damage = max(
                self._scorer._metadata_int(candidate.attack, "damage"),
                self._scorer._metadata_int(candidate.option, "damage"),
                self._scorer._metadata_int(candidate.option, "expectedDamage"),
            )
            if not self._scorer._deceit_is_decisive(state, candidate, damage) and not (
                self._uses_expert_rounds_1_3 and self._scorer._deceit_is_survival_line(state)
            ):
                return True
        if (
            candidate.option_type is OptionType.ATTACK
            and self._scorer._attack_id(candidate) == ROCKET_FEATHERS
        ):
            return self._scorer._effective_supporters_in_hand(state) == 0
        if candidate.option_type is OptionType.PLAY and card_id == ROTO_STICK:
            if state.supporter_played:
                return not self._post_supporter_roto_can_close_rocket_ko(state)
            return not (
                self._scorer._roto_stick_is_needed(state)
                or (self._uses_expert_turn_loop and self._canonical_roto_is_productive(state))
                or (self._uses_expert_rounds_1_3 and self._roto_setup_mode(state))
            )
        if candidate.option_type is OptionType.ATTACH and card_id == IGNITION_ENERGY:
            return self._ignition_attack_plan(state, candidate) is None
        if candidate.option_type is OptionType.PLAY and card_id == ULTRA_BALL:
            return not self._canonical_ultra_ball_is_productive(state)
        if candidate.option_type is OptionType.PLAY and card_id == TOOL_SCRAPPER:
            return not self._opponent_has_scrappable_tool(state)
        if (
            candidate.option_type is OptionType.CARD
            and context is SelectContext.TO_HAND
            and candidate.option.get("sourceCardId") == TRANSCEIVER
            and card_id == ARIANA
        ):
            if state.supporter_played:
                self._turn_ledger.transceiver_rejected_target = ARIANA
                self._turn_ledger.resource_guard = "transceiver_ariana_after_supporter_veto"
                return True
            return self._scorer._effective_supporters_in_hand(state) >= 2
        if candidate.option_type is OptionType.PLAY and card_id == MIRACLE_HEADSET:
            if self._uses_retreat_guard:
                return not (
                    self._headset_plan(state) is not None
                    or self._headset_ariana_recovery_is_useful(state)
                )
            return not self._scorer._miracle_headset_is_useful(state)
        if candidate.option_type is OptionType.PLAY and card_id == NIGHT_STRETCHER:
            return not self._canonical_night_stretcher_is_productive(state)
        if candidate.option_type is OptionType.PLAY and card_id == ARCHER:
            allowed = self._scorer._archer_is_safe_and_useful(
                state, candidate
            ) or self._scorer._archer_preserves_nonlethal_rocket_resources(state, candidate)
            if not allowed:
                self._turn_ledger.archer_veto_reason = "visible_attack_setup_or_draw_line"
            self._turn_ledger.archer_line_comparison = (
                "draw_line_rejected_against_public_ariana_factory_transceiver_petrel"
                if not allowed
                else "draw_line_selected_after_public_line_filter"
            )
            return not allowed
        if candidate.option_type is OptionType.PLAY and card_id == PROTON:
            return not self._scorer._proton_setup_is_useful(state)
        if candidate.option_type is OptionType.PLAY and card_id == ARIANA:
            return bool(
                not self._scorer._ariana_is_safe_and_useful(state)
                or bool(self._turn_ledger.development_obligations_pending)
                or (
                    self._scorer._proton_setup_is_useful(state)
                    and self._scorer._card_in_hand(state, PROTON)
                )
            )
        factory_ability = self._is_factory_effect_candidate(candidate, state)
        if candidate.option_type is OptionType.ABILITY and factory_ability:
            return not self._scorer._factory_is_useful(state)
        if candidate.option_type is OptionType.PLAY and card_id == FACTORY:
            if self._scorer._stadium_in_play(state, SPIKEMUTH_GYM):
                return False
            return not (
                self._scorer._factory_is_useful(state)
                or self._scorer._factory_play_is_useful(state)
            )
        if candidate.option_type is OptionType.PLAY and card_id == GIOVANNI:
            if self._uses_expert_turn_loop and self._canonical_giovanni_is_productive(state):
                return False
            if self._uses_expert_turn_loop and self._scorer._giovanni_pivot_is_productive(state):
                return False
            if self._uses_retreat_guard:
                opponent = self._scorer._opponent_player(state)
                if opponent is not None and not any(
                    pokemon is not None for pokemon in opponent.bench
                ):
                    return self._giovanni_switch_plan(state) is None
            return not self._giovanni_is_productive(state, candidate)
        if candidate.option_type is OptionType.PLAY and card_id == ARTICUNO:
            return not self._scorer._articuno_is_needed(state)
        if (
            candidate.option_type is OptionType.CARD
            and context is SelectContext.TO_ACTIVE
            and card_id == PORYGON2
        ):
            player = self._scorer._own_player(state)
            opponent = self._scorer._opponent_player(state)
            attacker = next(
                (
                    pokemon
                    for pokemon in [
                        player.active if player is not None else None,
                        *(player.bench if player is not None else ()),
                    ]
                    if pokemon is not None
                    and pokemon.card_id == card_id
                    and (
                        not self._scorer._feature_int(candidate, "target_serial")
                        or pokemon.serial == self._scorer._feature_int(candidate, "target_serial")
                    )
                ),
                None,
            )
            target = opponent.active if opponent is not None else None
            attack_id = R_COMMAND
            if attacker is None or target is None:
                return True
            line = self._evaluate_public_attack_line(state, attacker, target, attack_id)
            if not line.knocks_out:
                self._turn_ledger.resource_guard = line.veto_reason
                return True
        if (
            candidate.option_type in {OptionType.EVOLVE, OptionType.PLAY}
            and card_id in {HONCHKROW, PORYGON2}
            and self._scorer._articuno_is_needed(state)
            and not self._scorer._articuno_is_on_field(state)
            and self._scorer._card_in_hand(state, ARTICUNO)
            and not self._scorer._own_bench_full(state)
        ):
            self._turn_ledger.resource_guard = "hold_evolution_until_articuno_protection"
            return True
        if (
            candidate.option_type is OptionType.CARD
            and context in {SelectContext.TO_ACTIVE, SelectContext.SWITCH}
            and card_id == ARTICUNO
            and self._scorer._articuno_is_needed(state)
        ):
            self._turn_ledger.resource_guard = "keep_articuno_on_bench_against_dragapult"
            return True
        if (
            card_id == ARTICUNO
            and not self._scorer._articuno_is_needed(state)
            and self._scorer._own_field_count(state) >= 2
        ):
            if candidate.option_type is OptionType.ATTACH:
                return True
            if candidate.option_type is OptionType.CARD and context in {
                SelectContext.SETUP_ACTIVE_POKEMON,
                SelectContext.SETUP_BENCH_POKEMON,
                SelectContext.TO_ACTIVE,
                SelectContext.TO_FIELD,
            }:
                return True
        if candidate.option_type is OptionType.CARD and card_id == HONCHKROW:
            if context in {SelectContext.TO_HAND, SelectContext.LOOK}:
                if candidate.option.get(
                    "sourceCardId"
                ) == POKE_PAD and self._scorer._pokepad_ariana_hand_reduction_is_useful(state):
                    self._turn_ledger.resource_guard = "pokepad_hand_reduction_for_ariana"
                    return False
                if self._scorer._card_selected_from_night_stretcher(candidate):
                    return not self._scorer._night_stretcher_target_is_immediately_playable(
                        state, card_id
                    )
                return not self._scorer._pokepad_honchkrow_is_useful(state, candidate)
        if candidate.option_type is OptionType.CARD and card_id == PORYGON2:
            if (
                context is SelectContext.TO_HAND
                and candidate.option.get("sourceCardId") == ULTRA_BALL
                and self._scorer._proton_setup_is_useful(state)
            ):
                self._turn_ledger.setup_guard_reason = "block_ultra_ball_porygon2_before_proton"
                return True
            if context in {
                SelectContext.TO_HAND,
                SelectContext.LOOK,
            } and not self._scorer._porygon2_search_is_valid(state):
                self._turn_ledger.resource_guard = "reject_porygon2_without_porygon_field"
                return True
            if context is SelectContext.TO_ACTIVE and not (
                self._scorer._pokemon_is_ready(state, candidate)
                and self._scorer.r_command_knocks_out_active(state)
            ):
                self._turn_ledger.resource_guard = "porygon2_vetoed_r_command_damage_insufficient"
                return True
            if (
                context
                in {
                    SelectContext.SETUP_BENCH_POKEMON,
                    SelectContext.TO_BENCH,
                    SelectContext.TO_FIELD,
                }
                and self._scorer._own_field_count(state) == 0
            ):
                return True
            if (
                context in {SelectContext.SETUP_BENCH_POKEMON, SelectContext.TO_BENCH}
                and self._scorer._proton_targets_remaining(state).get(MURKROW, 0) > 0
            ):
                return True
        if candidate.option_type is OptionType.CARD and context is SelectContext.TO_HAND:
            if self._scorer._card_selected_from_night_stretcher(candidate):
                return card_id not in self._recovery_plan(state).recovered_cards
            if card_id in {ROCKET_ENERGY, IGNITION_ENERGY}:
                return False
            if card_id == ARTICUNO:
                return not self._scorer._articuno_is_needed(state)
        if (
            candidate.option_type is OptionType.CARD
            and context
            in {
                SelectContext.TO_HAND,
                SelectContext.TO_FIELD,
            }
            and card_id == NIGHT_STRETCHER
        ):
            return False
        if (
            candidate.option_type is OptionType.CARD
            and context
            in {
                SelectContext.TO_HAND,
                SelectContext.TO_FIELD,
            }
            and card_type in {5, 6, 2}
        ):
            if self._scorer._card_selected_from_night_stretcher(candidate):
                return card_id not in self._recovery_plan(state).recovered_cards
        if context in {SelectContext.DISCARD, SelectContext.DISCARD_CARD_OR_ATTACHED_CARD}:
            if card_id == MIRACLE_HEADSET and self._opponent_played_xerosic(state):
                self._turn_ledger.resource_guard = "preserve_headset_after_xerosic"
                return True
            if card_id == ARIANA and not (
                self._scorer._discard_is_required_for_ko(state, candidate)
                or self._scorer._ultra_ball_completes_r_command(state)
            ):
                self._turn_ledger.resource_guard = "preserve_ariana_without_guaranteed_ko"
                return True
            if self._scorer._is_energy_card(card_id, candidate.card):
                return not state.energy_attached
            if self._scorer._is_rocket_supporter(card_id, candidate.card):
                opponent = self._scorer._opponent_player(state)
                protected = bool(
                    opponent
                    and opponent.active
                    and has_splashing_dodge_protection(state.raw, opponent.active.serial)
                )
                if protected:
                    self._turn_ledger.resource_guard = "preserve_supporter_against_splashing_dodge"
                    return True
                if (
                    self._uses_supporter_lethal_commitment
                    and self._attack_sequence is not None
                    and self._attack_sequence.attack_id == ROCKET_FEATHERS
                    and self._attack_sequence.minimum_damage > 0
                ):
                    return False
                if card_id == ARIANA and not self._scorer._discard_is_required_for_ko(
                    state, candidate
                ):
                    return True
                if self._scorer._effective_supporters_in_hand(state) <= 1:
                    return True
        if context is SelectContext.TO_HAND and candidate.option.get("sourceCardId") == PETREL:
            return not self._petrel_target_is_useful(state, candidate)
        if candidate.option_type is OptionType.RETREAT:
            if self._uses_retreat_guard:
                justified = self._paid_retreat_plan(state) is not None
                self._turn_ledger.resource_guard = (
                    "paid_retreat_to_committed_attacker"
                    if justified
                    else "paid_retreat_without_attack_conversion"
                )
                return not justified
            justified = self._retreat_enables_immediate_ko(state)
            self._turn_ledger.resource_guard = (
                "retreat_enables_immediate_ko" if justified else "retreat_without_immediate_ko"
            )
            return not justified
            if self._active_has_productive_attack(state) or self._active_has_guaranteed_ko(state):
                return True
        return False

    def _candidate_matches_switch_commitment(self, candidate: Candidate | None) -> bool:
        """Return whether a switch option is the exact committed attacker."""
        commitment = self._switch_commitment
        if candidate is None or commitment is None or candidate.option_type is not OptionType.CARD:
            return False
        serial = self._scorer._feature_int(candidate, "card_serial")
        if commitment.target_serial is not None and serial:
            return serial == commitment.target_serial
        return bool(self._scorer._feature_int(candidate, "card_id") == commitment.target_card_id)

    def _candidate_matches_evolution_commitment(self, candidate: Candidate | None) -> bool:
        """Return whether an evolution option targets the committed Murkrow."""
        commitment = self._evolution_ko_commitment
        if (
            candidate is None
            or commitment is None
            or candidate.option_type not in {OptionType.PLAY, OptionType.EVOLVE}
            or self._scorer._feature_int(candidate, "card_id") != HONCHKROW
        ):
            return False
        target_serial = self._scorer._feature_int(candidate, "target_serial")
        return bool(
            commitment.murkrow_serial is None
            or not target_serial
            or target_serial == commitment.murkrow_serial
        )

    def _active_matches_switch_commitment(self, state: GameState) -> bool:
        """Return whether the committed attacker is now the Active Pokémon."""
        commitment = self._switch_commitment
        player = self._scorer._own_player(state)
        active = player.active if player is not None else None
        if commitment is None or active is None:
            return False
        if commitment.target_serial is not None and active.serial is not None:
            return bool(active.serial == commitment.target_serial)
        return bool(active.card_id == commitment.target_card_id)

    def _candidate_completes_committed_ignition(self, candidate: Candidate | None) -> bool:
        """Return whether an attachment completes the committed attack setup."""
        commitment = self._switch_commitment
        if (
            candidate is None
            or commitment is None
            or not commitment.requires_ignition
            or candidate.option_type is not OptionType.ATTACH
            or self._scorer._feature_int(candidate, "card_id") != IGNITION_ENERGY
            or self._scorer._feature_int(candidate, "target_card_id") != commitment.target_card_id
            or not bool(candidate.features.get("target_is_active", False))
        ):
            return False
        target_serial = self._scorer._feature_int(candidate, "target_serial")
        return bool(
            commitment.target_serial is None
            or not target_serial
            or target_serial == commitment.target_serial
        )

    def _giovanni_switch_plan(self, state: GameState) -> SwitchCommitment | None:
        """Plan a free Giovanni switch only when it converts into an immediate attack."""
        player = self._scorer._own_player(state)
        opponent = self._scorer._opponent_player(state)
        if (
            player is None
            or opponent is None
            or opponent.active is None
            or state.supporter_played
            or not any(
                self._scorer._card_id_from_value(card) == GIOVANNI for card in player.hand or ()
            )
        ):
            return None
        # Giovanni may select an opposing Bench target.  Bind both public
        # serials so the later promotion and target prompts cannot drift.
        for attacker in player.bench:
            if attacker is None or attacker.card_id != PORYGON2:
                continue
            for target in opponent.bench:
                if target is None:
                    continue
                line = self._evaluate_public_attack_line(
                    state, attacker, target, R_COMMAND, supporters_spent=(GIOVANNI,)
                )
                if not line.knocks_out or not line.wins_game:
                    continue
                return SwitchCommitment(
                    method="giovanni",
                    turn=state.turn,
                    target_card_id=PORYGON2,
                    target_serial=attacker.serial,
                    attack_id=R_COMMAND,
                    planned_damage=line.damage_after,
                    opponent_target_card_id=int(target.card_id),
                    opponent_target_serial=target.serial,
                )
        bench_plan = self._best_switch_plan(state, method="giovanni", giovanni_played=True)
        if bench_plan is None:
            return None
        active_choice = self._pokemon_attack_choice(state, player.active, giovanni_played=False)
        active_damage = active_choice[1] if active_choice is not None else 0
        target_hp = max(0, int(opponent.active.hp))
        if bench_plan.planned_damage < target_hp:
            return None
        if active_damage > 0 and not (active_damage < target_hp <= bench_plan.planned_damage):
            return None
        return bench_plan

    def _paid_retreat_plan(self, state: GameState) -> SwitchCommitment | None:
        """Allow paid retreat only when it creates an immediate productive attack."""
        player = self._scorer._own_player(state)
        opponent = self._scorer._opponent_player(state)
        if player is None or player.active is None or opponent is None or opponent.active is None:
            return None
        if self._giovanni_switch_plan(state) is not None:
            return None
        active_choice = self._pokemon_attack_choice(state, player.active, giovanni_played=False)
        plan = self._best_switch_plan(state, method="retreat", giovanni_played=False)
        if plan is None:
            return None
        target_hp = max(0, int(opponent.active.hp))
        active_damage = active_choice[1] if active_choice is not None else 0
        if plan.planned_damage < target_hp:
            return None
        if active_damage > 0 and not (active_damage < target_hp <= plan.planned_damage):
            return None
        return plan

    def _best_switch_plan(
        self,
        state: GameState,
        *,
        method: str,
        giovanni_played: bool,
    ) -> SwitchCommitment | None:
        """Return the highest-damage ready Bench attacker for one switch method."""
        player = self._scorer._own_player(state)
        if player is None:
            return None
        plans: list[SwitchCommitment] = []
        for pokemon in player.bench:
            choice = self._pokemon_attack_choice(state, pokemon, giovanni_played=giovanni_played)
            if pokemon is None or choice is None:
                continue
            attack_id, damage, requires_ignition = choice
            plans.append(
                SwitchCommitment(
                    method=method,
                    turn=state.turn,
                    target_card_id=int(pokemon.card_id),
                    target_serial=pokemon.serial,
                    attack_id=attack_id,
                    planned_damage=damage,
                    requires_ignition=requires_ignition,
                )
            )
        if method == "giovanni":
            porygon2_ko_plans = [
                plan
                for plan in plans
                if plan.target_card_id == PORYGON2
                and self._scorer.r_command_knocks_out_active(
                    state,
                    discarded_supporters=self._scorer._rocket_supporters_in_discard(state) + 1,
                )
            ]
            if porygon2_ko_plans:
                return max(porygon2_ko_plans, key=lambda plan: plan.planned_damage)
            plans = [plan for plan in plans if plan.target_card_id != PORYGON2]
        return max(plans, key=lambda plan: plan.planned_damage, default=None)

    def _pokemon_attack_choice(
        self,
        state: GameState,
        pokemon: Any | None,
        *,
        giovanni_played: bool,
    ) -> tuple[int, int, bool] | None:
        """Return the best current or post-Ignition attack for a Pokémon."""
        if pokemon is None or not isinstance(pokemon.card_id, int):
            return None
        can_attach_ignition = self._ignition_available_for(state, pokemon)
        choices: list[tuple[int, int, bool]] = []

        def add_choice(attack_id: int, damage: int) -> None:
            if damage <= 0 or not self._attack_cost_satisfied(pokemon, attack_id):
                if not self._attack_cost_satisfied(
                    pokemon, attack_id, include_ignition=can_attach_ignition
                ):
                    return
            requires_ignition = not self._attack_cost_satisfied(pokemon, attack_id)
            if requires_ignition and not can_attach_ignition:
                return
            choices.append((attack_id, damage, requires_ignition))

        if pokemon.card_id == HONCHKROW:
            supporters = self._scorer._effective_supporters_in_hand(state) - int(giovanni_played)
            if supporters > 0:
                add_choice(
                    ROCKET_FEATHERS,
                    self._dark_attack_damage(state, supporters * 60),
                )
            add_choice(HAMMER_IN, self._dark_attack_damage(state, 100))
        elif pokemon.card_id == PORYGON2:
            supporters = self._scorer._rocket_supporters_in_discard(state) + int(giovanni_played)
            if supporters > 0:
                add_choice(
                    R_COMMAND,
                    supporters * 20,
                )
        card = self._scorer.catalog.get_card(str(pokemon.card_id)) or {}
        for raw_attack_id in card.get("attacks", []):
            if not isinstance(raw_attack_id, int):
                continue
            if raw_attack_id in {ROCKET_FEATHERS, R_COMMAND, HAMMER_IN}:
                continue
            attack = self._scorer.catalog.get_attack(str(raw_attack_id)) or {}
            energies = attack.get("energies", [])
            damage = self._scorer._metadata_int(attack, "damage")
            if isinstance(energies, list):
                add_choice(
                    raw_attack_id,
                    self._dark_attack_damage(state, damage),
                )
        return max(choices, key=lambda choice: choice[1], default=None)

    def _attack_cost_satisfied(
        self,
        pokemon: Any,
        attack_id: int,
        *,
        include_ignition: bool = False,
    ) -> bool:
        """Return whether attached energy types can pay an attack cost.

        Rocket Energy contributes two units that may independently be Darkness or
        Psychic. Ignition Energy contributes three Colorless units on Evolution
        Pokémon. The simulator's numeric attack costs use ``0`` for Colorless.
        """
        attack = self._scorer.catalog.get_attack(str(attack_id)) or {}
        cost = attack.get("energies", [])
        if not isinstance(cost, list):
            return False
        units = self._attached_energy_units(pokemon)
        if include_ignition and pokemon.card_id in {HONCHKROW, PORYGON2}:
            units.append((3, {0}))
        requirements = [int(value) for value in cost]
        typed = [value for value in requirements if value != 0]
        colorless = len(requirements) - len(typed)
        for required in typed:
            compatible = [
                index
                for index, (capacity, allowed) in enumerate(units)
                if capacity > 0 and required in allowed
            ]
            if not compatible:
                return False
            index = min(compatible, key=lambda item: units[item][0])
            capacity, allowed = units[index]
            units[index] = (capacity - 1, allowed)
        return sum(capacity for capacity, _ in units) >= colorless

    def _attached_energy_units(self, pokemon: Any) -> list[tuple[int, set[int]]]:
        """Translate simulator energy cards into typed, consumable energy units."""
        units: list[tuple[int, set[int]]] = []
        card_values = list(getattr(pokemon, "energy_card_ids", ()) or ())
        if card_values:
            for value in card_values:
                card_id = self._scorer._card_id_from_value(value)
                if card_id == ROCKET_ENERGY:
                    units.append((2, {5, 7}))
                    continue
                if card_id == IGNITION_ENERGY:
                    units.append((3, {0}))
                    continue
                card = self._scorer.catalog.get_card(str(card_id)) or {}
                energy_type = self._scorer._metadata_int(card, "energyType")
                if energy_type:
                    units.append((1, {energy_type}))
            if units:
                return units
        for value in list(getattr(pokemon, "energies", ()) or ()):
            if isinstance(value, Mapping):
                units.append((1, {0, 5, 7}))
                continue
            try:
                energy_type = int(value)
            except (TypeError, ValueError):
                continue
            if energy_type == 11:
                units.append((2, {5, 7}))
            else:
                units.append((1, {energy_type}))
        return units

    def _ignition_available_for(self, state: GameState, pokemon: Any) -> bool:
        """Return whether this Evolution Pokémon can receive Ignition this turn."""
        if state.energy_attached or pokemon.card_id not in {HONCHKROW, PORYGON2}:
            return False
        player = self._scorer._own_player(state)
        return bool(
            player is not None
            and any(
                self._scorer._card_id_from_value(card) == IGNITION_ENERGY
                for card in player.hand or ()
            )
        )

    def _dark_attack_damage(self, state: GameState, base_damage: int) -> int:
        """Apply visible Darkness weakness and resistance to a planned attack."""
        opponent = self._scorer._opponent_player(state)
        target = opponent.active if opponent is not None else None
        if target is None:
            return max(0, base_damage)
        card = self._scorer.catalog.get_card(str(target.card_id)) or {}
        attacker = self._scorer._own_active(state)
        attacker_card = self._scorer.catalog.get_card(str(attacker.card_id)) if attacker else None
        return calculate_damage(
            base_damage,
            (attacker_card or {}).get("energyType"),
            card,
            prevented=has_splashing_dodge_protection(state.raw, target.serial),
            state_raw=state.raw,
            defender_serial=target.serial,
        )

    def _retreat_enables_immediate_ko(self, state: GameState) -> bool:
        """Require retreat to exchange a nonlethal Active for an immediate KO."""
        player = self._scorer._own_player(state)
        active = player.active if player is not None else None
        if player is None or active is None:
            return False
        active_card = self._scorer.catalog.get_card(str(active.card_id)) or {}
        retreat_cost = self._scorer._metadata_int(active_card, "retreatCost")
        if retreat_cost <= 0 or len(active.energies) < retreat_cost:
            return False
        if self._scorer._pokemon_has_immediate_ko(state, active):
            return False
        return any(
            pokemon is not None and self._scorer._pokemon_has_immediate_ko(state, pokemon)
            for pokemon in player.bench
        )

    def _active_has_productive_attack(self, state: GameState) -> bool:
        """Return whether the Active has an energized, damaging public attack."""
        active = self._scorer._own_active(state)
        if active is None or not isinstance(active.card_id, int):
            return False
        card = self._scorer.catalog.get_card(str(active.card_id)) or {}
        for attack_id in card.get("attacks", []):
            attack = self._scorer.catalog.get_attack(str(attack_id)) or {}
            energies = attack.get("energies", [])
            if not isinstance(energies, list) or len(energies) > len(active.energies):
                continue
            if self._scorer._metadata_int(attack, "damage") > 0:
                return True
        return False

    def _active_has_guaranteed_ko(self, state: GameState) -> bool:
        """Return whether any legal Active attack deterministically takes a KO."""
        active = self._scorer._own_active(state)
        if active is None:
            return False
        card = self._scorer.catalog.get_card(str(active.card_id)) or {}
        opponent_hp = self._scorer._effective_opponent_hp(state)
        return any(
            isinstance(attack_id, int)
            and len((self._scorer.catalog.get_attack(str(attack_id)) or {}).get("energies", []))
            <= len(active.energies)
            and self._scorer._metadata_int(
                self._scorer.catalog.get_attack(str(attack_id)) or {}, "damage"
            )
            >= opponent_hp
            for attack_id in card.get("attacks", [])
        )

    def _candidate_phase(self, state: GameState, candidate: Candidate) -> tuple[DecisionPhase, str]:
        """Put lethal and KO-enabling actions before ordinary development."""
        if candidate.option_type is OptionType.ATTACK:
            if self._scorer._truthy(candidate.option, "win", "wins", "ko", "knockout", "isKo"):
                return DecisionPhase.ATTACK_PRIORITY, "guaranteed_ko"
        if candidate.option_type is OptionType.RETREAT and self._retreat_enables_immediate_ko(
            state
        ):
            return DecisionPhase.ATTACK_PRIORITY, "retreat_enables_immediate_ko"
        if candidate.option_type is OptionType.DISCARD and self._scorer._discard_is_required_for_ko(
            state, candidate
        ):
            return DecisionPhase.ATTACK_PRIORITY, "discard_enables_ko"
        return super()._candidate_phase(state, candidate)

    def _only_energy_in_hand(self, state: GameState) -> bool:
        """Return whether the visible hand contains exactly one Energy card."""
        player = self._scorer._own_player(state)
        if player is None or player.hand is None:
            return False
        energies = 0
        for card in player.hand:
            card_id = self._scorer._card_id_from_value(card)
            metadata = self._scorer.catalog.get_card(str(card_id)) or {}
            energies += int(self._scorer._metadata_int(metadata, "cardType") in {5, 6})
        return energies == 1

    def _v3_miracle_headset_is_useful(self, state: GameState) -> bool:
        """Spend Headset only for two Supporters that complete an immediate KO."""
        if self._scorer._miracle_headset_emergency_is_useful(state):
            return True
        player = self._scorer._own_player(state)
        opponent = self._scorer._opponent_player(state)
        if player is None or opponent is None or opponent.active is None:
            return False
        active = player.active
        if (
            active is None
            or active.card_id != HONCHKROW
            or len(active.energies) < self._scorer._attack_energy_target(HONCHKROW)
        ):
            return False
        discarded = self._scorer._rocket_supporters_in_discard(state)
        recoverable = min(2, discarded)
        if recoverable == 0:
            return False
        supporters_after = self._scorer._effective_supporters_in_hand(state) + recoverable
        damage = self._dark_attack_damage(state, supporters_after * 60)
        return damage >= max(0, int(opponent.active.hp)) > 0

    def _ignition_target_is_valid(self, state: GameState, candidate: Candidate) -> bool:
        """Return whether Ignition completes a damaging attack this turn."""
        return self._scorer._ignition_attachment_is_productive(state, candidate)

    def _giovanni_is_productive(self, state: GameState, candidate: Candidate) -> bool:
        """Require a committed attackable switch target before playing Giovanni."""
        opponent = self._scorer._opponent_player(state)
        player = self._scorer._own_player(state)
        if opponent is None or player is None:
            return False
        ready_bench = [
            pokemon
            for pokemon in player.bench
            if pokemon is not None
            and pokemon.card_id in {HONCHKROW, PORYGON2}
            and len(pokemon.energies) >= self._scorer._attack_energy_target(int(pokemon.card_id))
        ]
        if not ready_bench:
            return False
        opponent_bench = [pokemon for pokemon in opponent.bench if pokemon is not None]
        if not opponent_bench:
            return not self._active_has_productive_attack(state)
        max_damage = max(
            self._scorer._effective_supporters_in_hand(state) * 60 * 2,
            self._scorer._rocket_supporters_in_discard(state) * 20,
            100,
        )
        return any(
            max_damage >= int(pokemon.hp) for pokemon in opponent_bench
        ) or self._scorer._truthy(candidate.option, "enablesKo", "ko", "knockout", "isKo")

    def _petrel_target_is_useful(self, state: GameState, candidate: Candidate) -> bool:
        """Limit Petrel to exact trainer targets with immediate tactical value."""
        card_id = self._scorer._feature_int(candidate, "card_id")
        card_type = self._scorer._metadata_int(candidate.card, "cardType")
        if self._opponent_budew_item_lock(state) and card_type in {1, 2}:
            self._turn_ledger.resource_guard = "budew_item_lock_reject_petrel_item"
            return False
        if card_id == PROTON:
            return not self._scorer._card_in_hand(
                state, PROTON
            ) and self._scorer._proton_setup_is_useful(state)
        if card_id == ARIANA:
            if self._scorer._card_in_hand(state, ARIANA):
                self._turn_ledger.deferred_petrel_reason = "ariana_already_in_hand"
                return False
            return self._scorer._ariana_is_safe_and_useful(state)
        if card_id == FACTORY:
            return not bool(state.stadium) and self._scorer._own_player(state) is not None
        if card_id == NIGHT_STRETCHER:
            return self._canonical_night_stretcher_is_productive(state)
        if card_id == MIRACLE_HEADSET:
            return self._scorer._miracle_headset_is_useful(state)
        if card_id == POKE_PAD:
            return self._scorer._has_murkrow_ready_to_evolve(state)
        if card_id == ULTRA_BALL:
            if self._scorer._card_in_hand(state, ROTO_STICK) and self._scorer._roto_stick_is_needed(
                state
            ):
                return False
            return self._scorer._ultra_ball_is_productive(state)
        return False

    def _opponent_budew_item_lock(self, state: GameState) -> bool:
        """Return whether the latest public attack is opposing Budew's Itchy Pollen."""
        logs = state.raw.get("_logs", state.raw.get("logs", ()))
        if not isinstance(logs, list):
            return False
        for event in reversed(logs):
            if not isinstance(event, Mapping) or "attackId" not in event:
                continue
            return (
                self._scorer._metadata_int(event, "attackId") == 323
                and self._scorer._metadata_int(event, "cardId") == 235
                and self._scorer._metadata_int(event, "playerIndex") != state.your_index
            )
        return False

    def _opponent_played_xerosic(self, state: GameState) -> bool:
        """Return whether the latest public opposing Supporter play was Xerosic."""
        logs = state.raw.get("_logs", state.raw.get("logs", ()))
        if not isinstance(logs, list):
            return False
        return any(
            isinstance(event, Mapping)
            and bool(
                self._scorer._metadata_int(event, "cardId") == 1197
                and self._scorer._metadata_int(event, "playerIndex") != state.your_index
            )
            for event in logs
        )
