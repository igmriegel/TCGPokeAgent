from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from typing import Any

from src.core import (
    AgentPolicy,
    Candidate,
    CardCatalog,
    DeckDefinition,
    DeckProfile,
    DefaultParser,
    DefaultSelectionGenerator,
    GameState,
    GenericDeckProfileBuilder,
    HeuristicScorer,
    OptionType,
    PolicyDecision,
    PrizeChecker,
    PrizeCheckMode,
    PrizeCheckResult,
    PrizeMap,
    PrizeMapBuilder,
    SelectContext,
    Selection,
    SelectionRanker,
)
from src.ranking.features import SelectionFeatureExtractor
from src.ranking.rankers import HeuristicSelectionRanker

WEIGHTS: dict[str, float] = {
    "win_now": 100.0,
    "efficient_attack": 10.0,
    "useful_evolution": 8.0,
    "attack_enabling_energy": 6.0,
    "bench_development": 4.0,
    "draw_search": 5.0,
    "resource_preservation": 3.0,
    "safe_end_turn": 2.0,
    "wasted_energy": -5.0,
    "key_piece_discard": -8.0,
    "pointless_evolution": -6.0,
    "blocked_bench": -4.0,
    "premature_end": -10.0,
}

FEATURE_FLAGS = {
    "use_attack_signals",
    "use_resource_signals",
    "use_setup_signals",
}

_CG_CATALOG = CardCatalog.from_cg()


def _validated_weights(weights: Mapping[str, Any] | None) -> dict[str, float]:
    """Validate and merge a caller-provided weight profile."""
    result = dict(WEIGHTS)
    for name, value in (weights or {}).items():
        if name not in WEIGHTS:
            raise ValueError(f"unknown heuristic weight: {name}")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"heuristic weight {name!r} must be numeric")
        result[name] = float(value)
    return result


def _validated_flags(flags: Mapping[str, Any] | None) -> dict[str, bool]:
    """Validate feature switches and fill enabled defaults."""
    result = {name: True for name in FEATURE_FLAGS}
    for name, value in (flags or {}).items():
        if name not in FEATURE_FLAGS:
            raise ValueError(f"unknown heuristic feature flag: {name}")
        if not isinstance(value, bool):
            raise ValueError(f"heuristic feature flag {name!r} must be boolean")
        result[name] = value
    return result


class SimpleHeuristicScorer(HeuristicScorer):
    """Score legal selections using deterministic, auditable option signals."""

    def __init__(
        self,
        weights: Mapping[str, Any] | None = None,
        feature_flags: Mapping[str, Any] | None = None,
        deck_profile: DeckProfile | None = None,
        catalog: CardCatalog | None = None,
    ) -> None:
        self.weights = _validated_weights(weights)
        self.feature_flags = _validated_flags(feature_flags)
        self.deck_profile = deck_profile
        self.catalog = catalog or _CG_CATALOG
        self.prize_check: PrizeCheckResult | None = None
        self.prize_map: PrizeMap | None = None

    def set_deck_profile(self, profile: DeckProfile) -> None:
        """Replace the declarative deck strategy for a new match."""
        self.deck_profile = profile

    def set_strategic_context(
        self,
        prize_check: PrizeCheckResult | None,
        prize_map: PrizeMap | None,
    ) -> None:
        """Set match-scoped Prize knowledge used for the current decision."""
        self.prize_check = prize_check
        self.prize_map = prize_map

    def score(
        self,
        state: GameState,
        selection: Selection,
        candidates: Sequence[Candidate] | None = None,
    ) -> tuple[float, list[str]]:
        """Return a weighted score and stable reason codes for a selection."""
        by_index = {candidate.option_index: candidate for candidate in candidates or ()}
        selected = [by_index[index] for index in selection.indices if index in by_index]
        if not selected:
            return 0.0, ["no_signal"]

        score = 0.0
        reasons: list[str] = []
        for candidate in selected:
            option = candidate.option
            context = selection.context.value if selection.context else ""
            is_attack = candidate.option_type.value == "ATTACK" or "ATTACK" in context
            is_energy = candidate.option_type.value in {"ENERGY", "ENERGY_CARD"}
            is_end = candidate.option_type.value == "END"
            sdk_score, sdk_reasons = self._sdk_score(state, candidate, selection.context)
            score += sdk_score
            reasons.extend(sdk_reasons)

            if self._truthy(option, "win", "wins", "isWin", "gameOver"):
                score += self.weights["win_now"] * 100.0
                reasons.append("win_now")
            if self.feature_flags["use_attack_signals"] and is_attack:
                damage = self._number(option, "damage", "expectedDamage", "value")
                cost = max(1.0, self._number(option, "cost", "energyCost"))
                if damage > 0:
                    score += self.weights["efficient_attack"] * min(1.0, damage / cost)
                    reasons.append("efficient_attack")
                if self._truthy(option, "ko", "knockout", "isKo"):
                    score += self.weights["win_now"] * 0.5
                    reasons.append("ko_threat")
            if self._truthy(option, "evolve", "isEvolution") or "EVOLVE" in context:
                if self._truthy(option, "useful", "enablesAttack", "survivalGain"):
                    score += self.weights["useful_evolution"]
                    reasons.append("useful_evolution")
                else:
                    score += self.weights["pointless_evolution"]
                    reasons.append("pointless_evolution")
            if self.feature_flags["use_attack_signals"] and is_energy:
                count = self._number(option, "count", "energyCount")
                if self._truthy(option, "enablesAttack", "enables"):
                    score += self.weights["attack_enabling_energy"]
                    reasons.append("attack_enabling_energy")
                elif count > 1 or self._truthy(option, "wasted", "waste"):
                    score += self.weights["wasted_energy"]
                    reasons.append("wasted_energy")
            if self.feature_flags["use_setup_signals"] and self._truthy(
                option, "bench", "developBench", "setup"
            ):
                score += self.weights["bench_development"]
                reasons.append("bench_development")
            if self._truthy(option, "draw", "search", "drawSearch"):
                score += self.weights["draw_search"]
                reasons.append("draw_search")
            if self.feature_flags["use_resource_signals"]:
                if self._truthy(option, "preserve", "preservesKeyPiece"):
                    score += self.weights["resource_preservation"]
                    reasons.append("resource_preservation")
                if self._truthy(option, "keyPiece", "keyCard") or (
                    candidate.option_type.value == "DISCARD" and self._truthy(option, "rare")
                ):
                    score += self.weights["key_piece_discard"]
                    reasons.append("key_piece_discard")
            if is_end:
                if state.turn_action_count == 0 or self._truthy(option, "premature"):
                    score += self.weights["premature_end"]
                    reasons.append("premature_end")
                else:
                    score += self.weights["safe_end_turn"]
                    reasons.append("safe_end_turn")
            if self._truthy(option, "blockedBench", "benchFull"):
                score += self.weights["blocked_bench"]
                reasons.append("blocked_bench")

        return score, list(dict.fromkeys(reasons)) or ["no_signal"]

    def _sdk_score(
        self,
        state: GameState,
        candidate: Candidate,
        context: SelectContext | None,
    ) -> tuple[float, list[str]]:
        option_type = candidate.option_type
        if context is SelectContext.MAIN:
            return self._main_action_score(state, candidate)
        if option_type is OptionType.NUMBER:
            number = self._number(candidate.option, "number")
            return number * 10.0, ["prefer_larger_count"]
        if option_type in {OptionType.YES, OptionType.NO}:
            prefer_yes = context is not SelectContext.MULLIGAN
            preferred = (
                option_type is OptionType.YES if prefer_yes else option_type is OptionType.NO
            )
            return (20.0 if preferred else 0.0), ["prefer_yes" if prefer_yes else "avoid_mulligan"]
        if option_type is OptionType.CARD:
            return self._card_selection_score(state, candidate, context)
        if option_type is OptionType.ATTACK:
            return self._attack_score(state, candidate)
        if option_type in {OptionType.ENERGY, OptionType.ENERGY_CARD}:
            if context is None:
                return 0.0, []
            count = max(1.0, self._number(candidate.option, "count"))
            return count * 10.0, ["satisfy_energy_cost"]
        return 0.0, []

    def _main_action_score(self, state: GameState, candidate: Candidate) -> tuple[float, list[str]]:
        option_type = candidate.option_type
        if option_type is OptionType.END:
            return -1000.0, ["end_only_after_productive_actions"]
        if option_type is OptionType.EVOLVE:
            energy = self._feature_int(candidate, "target_energy_count")
            return 500.0 + energy * 10.0, ["evolve_attacker"]
        if option_type is OptionType.ABILITY:
            return 450.0, ["use_available_ability"]
        if option_type is OptionType.ATTACH:
            return self._attachment_score(candidate)
        if option_type is OptionType.PLAY:
            return self._play_score(state, candidate)
        if option_type is OptionType.ATTACK:
            return self._attack_score(state, candidate)
        if option_type is OptionType.RETREAT:
            return 60.0, ["legal_retreat"]
        if option_type is OptionType.DISCARD:
            return 20.0, ["resolve_discard_action"]
        return 1.0, ["productive_legal_action"]

    def _attachment_score(self, candidate: Candidate) -> tuple[float, list[str]]:
        card_type = self._metadata_int(candidate.card, "cardType")
        target_id = self._feature_int(candidate, "target_card_id")
        energy_count = self._feature_int(candidate, "target_energy_count")
        if card_type in {5, 6}:
            target_goal = self._attack_energy_target(target_id)
            deficit = max(0, target_goal - energy_count)
            active_bonus = 30.0 if bool(candidate.features.get("target_is_active", False)) else 0.0
            return 350.0 + deficit * 25.0 + active_bonus, ["develop_attacker_energy"]
        return 300.0, ["attach_useful_tool"]

    def _play_score(self, state: GameState, candidate: Candidate) -> tuple[float, list[str]]:
        card_id = self._feature_int(candidate, "card_id")
        card_type = self._metadata_int(candidate.card, "cardType")
        if card_type == 0:
            bonus = 30.0 if self._has_role(card_id, "evolution_basic") else 20.0
            return 300.0 + bonus, [
                "develop_bench",
                "play_available_pokemon_before_attack",
            ]
        if card_type == 1:
            return 240.0, ["play_item"]
        if card_type == 2:
            return 280.0, ["attach_tool"]
        if card_type == 3:
            hand_count = self._own_hand_count(state)
            return 250.0 + max(0, 8 - hand_count) * 10.0, ["play_supporter"]
        if card_type == 4:
            return 180.0, ["play_stadium"]
        return 150.0, ["play_known_legal_card"]

    def _attack_score(self, state: GameState, candidate: Candidate) -> tuple[float, list[str]]:
        active_target = next(
            (
                target
                for target in (self.prize_map.targets if self.prize_map else ())
                if target.zone == "active"
            ),
            None,
        )
        if active_target and active_target.damage_prevented:
            return -1000.0, ["attack_damage_prevented"]
        damage = self._metadata_int(candidate.attack, "damage")
        text = str((candidate.attack or {}).get("text", "")).casefold()
        if "damage for each basic" in text and "discard pile" in text:
            energy_type = self._attack_energy_type(candidate)
            multiplier = self._leading_damage_multiplier(text)
            damage = multiplier * self._discard_basic_energy_count(state, energy_type)
        elif "discard the top 6 cards" in text and "100 damage for each basic" in text:
            damage = 300 if self._own_deck_count(state) > 12 else 50
        score = 200.0 + max(0, damage)
        if damage <= 0:
            score -= 80.0
        return score, ["attack_for_damage"]

    def _card_selection_score(
        self,
        state: GameState,
        candidate: Candidate,
        context: SelectContext | None,
    ) -> tuple[float, list[str]]:
        card_id = self._feature_int(candidate, "card_id")
        card_type = self._metadata_int(candidate.card, "cardType")
        energy_count = self._feature_int(candidate, "card_energy_count")
        hp = self._feature_int(candidate, "card_hp")
        if context is SelectContext.SETUP_ACTIVE_POKEMON:
            score = 120.0 if self._has_role(card_id, "evolution_basic") else 110.0
            return score, ["setup_active_attacker"]
        if context is SelectContext.SETUP_BENCH_POKEMON:
            score = 100.0 if card_type == 0 else -100.0
            return score, ["setup_bench"]
        if context in {
            SelectContext.SWITCH,
            SelectContext.TO_ACTIVE,
            SelectContext.TO_FIELD,
        }:
            return hp + energy_count * 100.0, ["promote_prepared_attacker"]
        if context is SelectContext.TO_HAND:
            if self.prize_check and self.prize_check.mode is PrizeCheckMode.EXACT:
                availability = self.prize_check.availability(card_id)
                if availability and availability.searchable_exact == 0:
                    return -1000.0, ["confirmed_prized_unsearchable"]
            return self._card_resource_value(card_id, card_type), ["search_useful_card"]
        if context in {
            SelectContext.DISCARD,
            SelectContext.DISCARD_CARD_OR_ATTACHED_CARD,
        }:
            if card_type in {5, 6}:
                return 120.0, ["discard_energy_for_synergy"]
            if card_type == 0:
                return -100.0, ["preserve_pokemon"]
            return 20.0, ["discard_replaceable_card"]
        if context in {
            SelectContext.DAMAGE,
            SelectContext.DAMAGE_COUNTER,
            SelectContext.DAMAGE_COUNTER_ANY,
            SelectContext.EFFECT_TARGET,
        }:
            owner_is_self = bool(candidate.features.get("card_owner_is_self", False))
            return (-hp if owner_is_self else 1000.0 - hp), ["target_vulnerable_pokemon"]
        if context in {
            SelectContext.HEAL,
            SelectContext.REMOVE_DAMAGE_COUNTER,
        }:
            max_hp = self._feature_int(candidate, "card_max_hp")
            return max_hp - hp, ["heal_most_damaged"]
        return self._card_resource_value(card_id, card_type), ["card_resource_value"]

    def _card_resource_value(self, card_id: int, card_type: int) -> float:
        if self.deck_profile and card_id in self.deck_profile.resource_values:
            return self.deck_profile.resource_values[card_id]
        if self._has_role(card_id, "primary_attacker"):
            return 160.0
        if self._has_role(card_id, "evolution_basic"):
            return 150.0
        if self._has_role(card_id, "attacker"):
            return 140.0
        return {0: 120.0, 1: 100.0, 2: 90.0, 3: 100.0, 4: 70.0}.get(card_type, 10.0)

    def _has_role(self, card_id: int, role: str) -> bool:
        return bool(self.deck_profile and self.deck_profile.has_role(card_id, role))

    def _attack_energy_target(self, card_id: int) -> int:
        if self.deck_profile and card_id in self.deck_profile.attack_energy_targets:
            return max(1, self.deck_profile.attack_energy_targets[card_id])
        card = self.catalog.get_card(str(card_id)) or {}
        costs = []
        for attack_id in card.get("attacks", []):
            attack = self.catalog.get_attack(str(attack_id)) or {}
            energies = attack.get("energies", [])
            if isinstance(energies, list):
                costs.append(len(energies))
        return max(costs, default=1)

    def _attack_energy_type(self, candidate: Candidate) -> int:
        energies = (candidate.attack or {}).get("energies", [])
        if not isinstance(energies, list) or not energies:
            return -1
        value = energies[0]
        return value if isinstance(value, int) and not isinstance(value, bool) else -1

    def _discard_basic_energy_count(self, state: GameState, energy_type: int) -> int:
        player = self._own_player(state)
        if player is None:
            return 0
        count = 0
        for card in player.discard:
            if not isinstance(card, Mapping):
                continue
            card_id = card.get("id", card.get("cardId"))
            metadata = self.catalog.get_card(str(card_id)) or {}
            if (
                self._metadata_int(metadata, "cardType") == 5
                and self._metadata_int(metadata, "energyType") == energy_type
            ):
                count += 1
        return count

    def _leading_damage_multiplier(self, text: str) -> int:
        words = text.split()
        for index, word in enumerate(words):
            if word == "damage" and index:
                try:
                    return int(words[index - 1])
                except ValueError:
                    return 0
        return 0

    def _own_player(self, state: GameState) -> Any:
        if 0 <= state.your_index < len(state.players):
            return state.players[state.your_index]
        return None

    def _own_hand_count(self, state: GameState) -> int:
        player = self._own_player(state)
        return player.hand_count if player is not None else 0

    def _own_deck_count(self, state: GameState) -> int:
        player = self._own_player(state)
        return player.deck_count if player is not None else 0

    def _discard_count(self, state: GameState, card_id: int) -> int:
        player = self._own_player(state)
        if player is None:
            return 0
        return sum(
            1
            for card in player.discard
            if isinstance(card, Mapping)
            and (card.get("id") == card_id or card.get("cardId") == card_id)
        )

    def _feature_int(self, candidate: Candidate, name: str) -> int:
        value = candidate.features.get(name, 0)
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

    def _metadata_int(self, metadata: Mapping[str, Any] | None, name: str) -> int:
        if metadata is None:
            return 0
        value = metadata.get(name)
        return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0

    def _mapping_int(self, mapping: Mapping[str, Any], name: str) -> int:
        value = mapping.get(name)
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

    def _truthy(self, option: Mapping[str, Any], *names: str) -> bool:
        return any(bool(option.get(name, False)) for name in names)

    def _number(self, option: Mapping[str, Any], *names: str) -> float:
        for name in names:
            value = option.get(name)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
        return 0.0


class HeuristicAgent(AgentPolicy):
    """Select the highest-scoring legal option with deterministic tie-breaking."""

    def __init__(
        self,
        weights: Mapping[str, Any] | None = None,
        feature_flags: Mapping[str, Any] | None = None,
        deck_profile: DeckProfile | None = None,
        ranker: SelectionRanker | None = None,
    ) -> None:
        self._parser = DefaultParser(_CG_CATALOG)
        self._generator = DefaultSelectionGenerator()
        self._scorer = SimpleHeuristicScorer(
            weights, feature_flags, deck_profile=deck_profile, catalog=_CG_CATALOG
        )
        self._configured_profile = deck_profile
        self._active_deck_profile = deck_profile
        self._deck: DeckDefinition | None = None
        self._prize_checker: PrizeChecker | None = None
        self._prize_map_builder = PrizeMapBuilder(_CG_CATALOG)
        self._feature_extractor = SelectionFeatureExtractor(self._scorer)
        self._heuristic_ranker = HeuristicSelectionRanker()
        self._ranker = ranker or self._heuristic_ranker
        self._fallback_count = 0
        self._last_decision: PolicyDecision | None = None

    def start_match(self, deck: DeckDefinition) -> None:
        """Reset the deck strategy without changing generic policy code."""
        self._deck = deck
        self._prize_checker = PrizeChecker(deck)
        profile = (
            self._configured_profile
            if self._configured_profile and self._configured_profile.deck_sha256 == deck.sha256
            else GenericDeckProfileBuilder(_CG_CATALOG).build(deck)
        )
        evolution_basics = tuple(sorted({line[0] for line in profile.evolution_lines if line}))
        roles = dict(profile.roles)
        roles["evolution_basic"] = evolution_basics
        active_profile = DeckProfile(
            deck_id=profile.deck_id,
            deck_sha256=profile.deck_sha256,
            schema_version=profile.schema_version,
            roles=roles,
            evolution_lines=profile.evolution_lines,
            attack_energy_targets=profile.attack_energy_targets,
            board_targets=profile.board_targets,
            resource_values=profile.resource_values,
        )
        self._active_deck_profile = active_profile
        self._scorer.set_deck_profile(active_profile)

    @property
    def weights(self) -> dict[str, float]:
        """Return a copy of the active heuristic weights."""
        return dict(self._scorer.weights)

    @property
    def fallback_count(self) -> int:
        """Return the number of learned inference failures in this process."""
        return self._fallback_count

    @property
    def last_decision(self) -> PolicyDecision | None:
        """Return the latest auditable decision, if a decision has run."""
        return self._last_decision

    @classmethod
    def from_profile(cls, profile_path: str, *, deck_id: str, deck_path: str) -> HeuristicAgent:
        """Load a validated RFL profile, falling back to baseline weights."""
        from src.rfl.profiles import agent_from_profile

        return agent_from_profile(profile_path, active_deck_id=deck_id, active_deck_path=deck_path)

    def select(self, observation: dict[str, Any]) -> list[int]:
        """Return the best legal selection while preserving the public contract."""
        return list(self.decide(observation).selection.indices)

    def decide(self, observation: dict[str, Any]) -> PolicyDecision:
        """Return an auditable ranking decision for one observation.

        Args:
            observation: Raw actor-visible CABT observation.

        Returns:
            Complete policy decision including alternatives, features, and latency.
        """
        started = time.perf_counter()
        parsed = self._parser.parse(observation)
        prize_check = self._prize_checker.check(observation) if self._prize_checker else None
        prize_map = self._prize_map_builder.build(parsed.state)
        self._scorer.set_strategic_context(prize_check, prize_map)
        if parsed.max_count == 0:
            return self._record_empty_decision(started)
        selections = self._generator.generate(
            parsed.candidates,
            parsed.min_count,
            parsed.max_count,
            parsed.remain_energy_cost,
            parsed.remain_damage_counter,
        )
        if not selections:
            return self._record_empty_decision(started)
        required_development = self._required_board_development_indices(
            parsed.state, parsed.candidates, parsed.select_context
        )
        if required_development:
            development_selections = [
                selection
                for selection in selections
                if any(index in required_development for index in selection.indices)
            ]
            if development_selections:
                selections = development_selections
        contextualized = [
            Selection(
                indices=selection.indices,
                option_types=selection.option_types,
                context=parsed.select_context,
            )
            for selection in selections
        ]
        features = self._feature_extractor.extract(
            parsed,
            contextualized,
            deck_profile=self._active_deck_profile,
            prize_check=prize_check,
        )
        fallback_used = False
        ranker = self._ranker
        try:
            ranked = ranker.rank(parsed, contextualized, features)
            self._validate_ranking(contextualized, ranked)
        except Exception:
            if ranker is self._heuristic_ranker:
                raise
            self._fallback_count += 1
            fallback_used = True
            ranker = self._heuristic_ranker
            ranked = ranker.rank(parsed, contextualized, features)
        result = PolicyDecision(
            selection=ranked[0].selection,
            ranked=tuple(ranked),
            features=tuple(features),
            fallback_used=fallback_used,
            model_backend=str(getattr(ranker, "backend", "heuristic")),
            model_version=str(getattr(ranker, "model_version", "heuristic-v1")),
            duration_ms=(time.perf_counter() - started) * 1000.0,
        )
        self._last_decision = result
        return result

    def _record_empty_decision(self, started: float) -> PolicyDecision:
        selection = Selection(indices=(), option_types=())
        result = PolicyDecision(
            selection=selection,
            ranked=(),
            features=(),
            fallback_used=False,
            model_backend=str(getattr(self._ranker, "backend", "heuristic")),
            model_version=str(getattr(self._ranker, "model_version", "heuristic-v1")),
            duration_ms=(time.perf_counter() - started) * 1000.0,
        )
        self._last_decision = result
        return result

    @staticmethod
    def _validate_ranking(selections: Sequence[Selection], ranked: Sequence[Any]) -> None:
        expected = {selection.indices for selection in selections}
        actual = {item.selection.indices for item in ranked}
        if not ranked or expected != actual or len(ranked) != len(selections):
            raise RuntimeError("ranker did not return every legal selection exactly once")

    @staticmethod
    def _required_board_development_indices(
        state: GameState,
        candidates: Sequence[Candidate],
        context: SelectContext | None,
    ) -> set[int]:
        if context is not SelectContext.MAIN or not state.players:
            return set()
        player_index = state.your_index if 0 <= state.your_index < len(state.players) else 0
        player = state.players[player_index]
        occupied_bench = sum(pokemon is not None for pokemon in player.bench)
        if occupied_bench >= player.bench_max:
            return set()
        return {
            candidate.option_index
            for candidate in candidates
            if HeuristicAgent._is_pokemon_play(candidate)
        }

    @staticmethod
    def _is_pokemon_play(candidate: Candidate) -> bool:
        if candidate.option_type is not OptionType.PLAY or not isinstance(candidate.card, Mapping):
            return False
        try:
            return int(candidate.card.get("cardType", -1)) == 0
        except (TypeError, ValueError):
            return False
