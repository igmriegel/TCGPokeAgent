"""Rule Box, Prize route, and own-deck prize-check strategy."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

from .catalog import CardCatalog, CardTraits
from .damage import calculate_damage, has_splashing_dodge_protection
from .deck import DeckDefinition
from .state import GameState, PokemonState


class PrizeCheckMode(str, Enum):
    """Confidence state for own Prize-card knowledge."""

    PROBABILISTIC = "probabilistic"
    EXACT = "exact"
    INCONSISTENT = "inconsistent"


@dataclass(frozen=True, slots=True)
class CardAvailability:
    """Availability of one card between the searchable deck and Prize cards."""

    card_id: int
    total_count: int
    searchable_min: int
    searchable_max: int
    searchable_expected: float
    prized_min: int
    prized_max: int
    prized_expected: float
    probability_at_least_one_prized: float

    @property
    def searchable_exact(self) -> int | None:
        """Return the exact searchable count when known."""
        return self.searchable_min if self.searchable_min == self.searchable_max else None

    @property
    def prized_exact(self) -> int | None:
        """Return the exact prized count when known."""
        return self.prized_min if self.prized_min == self.prized_max else None


@dataclass(frozen=True, slots=True)
class PrizeCheckResult:
    """Own-card availability derived without exposing hidden state as fact."""

    mode: PrizeCheckMode
    cards: Mapping[int, CardAvailability] = field(default_factory=dict)
    deck_count: int = 0
    prize_count: int = 0
    violations: tuple[str, ...] = ()

    def availability(self, card_id: int) -> CardAvailability | None:
        """Return availability for one card."""
        return self.cards.get(card_id)

    def searchable_count(self, card_id: int) -> int | float:
        """Return exact or expected searchable copies."""
        availability = self.availability(card_id)
        if availability is None:
            return 0
        exact = availability.searchable_exact
        return exact if exact is not None else availability.searchable_expected


class PrizeChecker:
    """Infer own prized cards and search availability from visible observations."""

    def __init__(self, deck: DeckDefinition) -> None:
        self._deck = deck
        self._exact_prized: Counter[int] | None = None

    def check(self, observation: Mapping[str, Any]) -> PrizeCheckResult:
        """Build an exact or probabilistic Prize check.

        Args:
            observation: Actor-perspective CABT observation.

        Returns:
            Availability snapshot with explicit confidence mode.
        """
        current = observation.get("current")
        if not isinstance(current, Mapping):
            return PrizeCheckResult(PrizeCheckMode.INCONSISTENT, violations=("missing_current",))
        players = current.get("players")
        your_index = _int(current.get("yourIndex"))
        if not isinstance(players, list) or not 0 <= your_index < len(players):
            return PrizeCheckResult(PrizeCheckMode.INCONSISTENT, violations=("missing_own_player",))
        player = players[your_index]
        if not isinstance(player, Mapping):
            return PrizeCheckResult(PrizeCheckMode.INCONSISTENT, violations=("invalid_own_player",))

        deck_count = _int(player.get("deckCount"))
        prize = player.get("prize")
        prize_count = len(prize) if isinstance(prize, list) else 0
        select = observation.get("select")
        exposed_deck = select.get("deck") if isinstance(select, Mapping) else None
        known_non_hidden = _count_known_cards(observation, player, your_index, include_prize=False)
        initial = self._deck.counts

        if isinstance(exposed_deck, list):
            exact_deck = _count_cards(exposed_deck)
            if sum(exact_deck.values()) != deck_count:
                return PrizeCheckResult(
                    PrizeCheckMode.INCONSISTENT,
                    deck_count=deck_count,
                    prize_count=prize_count,
                    violations=("exposed_deck_cardinality",),
                )
            prized = initial - known_non_hidden - exact_deck
            result = self._exact_result(
                initial,
                known_non_hidden,
                exact_deck,
                prized,
                deck_count,
                prize_count,
            )
            if result.mode is PrizeCheckMode.EXACT:
                self._exact_prized = prized
            return result

        updated_prized = self._updated_exact_prized(observation.get("logs"), prize_count)
        if updated_prized is not None:
            exact_deck = initial - known_non_hidden - updated_prized
            result = self._exact_result(
                initial,
                known_non_hidden,
                exact_deck,
                updated_prized,
                deck_count,
                prize_count,
            )
            if result.mode is PrizeCheckMode.EXACT:
                self._exact_prized = updated_prized
                return result
            self._exact_prized = None

        hidden = initial - known_non_hidden
        if sum(hidden.values()) != deck_count + prize_count:
            return PrizeCheckResult(
                PrizeCheckMode.INCONSISTENT,
                deck_count=deck_count,
                prize_count=prize_count,
                violations=("hidden_zone_cardinality",),
            )
        cards = {
            card_id: _probabilistic_availability(
                card_id,
                initial[card_id],
                hidden[card_id],
                deck_count,
                prize_count,
            )
            for card_id in sorted(initial)
        }
        return PrizeCheckResult(PrizeCheckMode.PROBABILISTIC, cards, deck_count, prize_count)

    def _updated_exact_prized(self, logs: Any, prize_count: int) -> Counter[int] | None:
        if self._exact_prized is None:
            return None
        prized = self._exact_prized.copy()
        for event in logs if isinstance(logs, list) else []:
            if not isinstance(event, Mapping):
                continue
            card_id = _card_id(event)
            if event.get("fromArea") == 6:
                if not card_id or prized[card_id] <= 0:
                    return None
                prized[card_id] -= 1
            if event.get("toArea") == 6:
                if not card_id:
                    return None
                prized[card_id] += 1
        prized += Counter()
        return prized if sum(prized.values()) == prize_count else None

    def _exact_result(
        self,
        initial: Counter[int],
        known_non_hidden: Counter[int],
        exact_deck: Counter[int],
        prized: Counter[int],
        deck_count: int,
        prize_count: int,
    ) -> PrizeCheckResult:
        violations = _counter_violations(initial, known_non_hidden + exact_deck + prized)
        if sum(exact_deck.values()) != deck_count:
            violations.append("deck_cardinality")
        if sum(prized.values()) != prize_count:
            violations.append("prize_cardinality")
        if violations:
            return PrizeCheckResult(
                PrizeCheckMode.INCONSISTENT,
                deck_count=deck_count,
                prize_count=prize_count,
                violations=tuple(violations),
            )
        cards = {
            card_id: CardAvailability(
                card_id=card_id,
                total_count=initial[card_id],
                searchable_min=exact_deck[card_id],
                searchable_max=exact_deck[card_id],
                searchable_expected=float(exact_deck[card_id]),
                prized_min=prized[card_id],
                prized_max=prized[card_id],
                prized_expected=float(prized[card_id]),
                probability_at_least_one_prized=float(prized[card_id] > 0),
            )
            for card_id in sorted(initial)
        }
        return PrizeCheckResult(PrizeCheckMode.EXACT, cards, deck_count, prize_count)


@dataclass(frozen=True, slots=True)
class PrizeTarget:
    """One opponent Pokémon considered in the current Prize route."""

    card_id: int | str
    zone: str
    index: int
    hp: int
    has_rule_box: bool
    base_prize_value: int
    effective_prize_value: int
    reachable_now: bool
    expected_damage: int
    damage_prevented: bool


@dataclass(frozen=True, slots=True)
class PrizeMap:
    """Current tactical map from opponent Pokémon to a Prize-winning route."""

    prizes_needed: int
    targets: tuple[PrizeTarget, ...]
    route: tuple[PrizeTarget, ...]

    @property
    def available_prizes(self) -> int:
        """Return total contextual Prize value currently in play."""
        return sum(target.effective_prize_value for target in self.targets)


class PrizeMapBuilder:
    """Build Rule Box-aware Prize routes from factual public board state."""

    def __init__(self, catalog: CardCatalog) -> None:
        self._catalog = catalog

    def build(self, state: GameState) -> PrizeMap:
        """Build a deterministic tactical Prize route.

        Args:
            state: Parsed factual state.

        Returns:
            Current targets and a greedy minimum-KO route.
        """
        own = _player(state, state.your_index)
        opponent = _player(state, 1 - state.your_index)
        prizes_needed = len(own.prize) if own is not None else 0
        if opponent is None:
            return PrizeMap(prizes_needed, (), ())

        attacker = own.active if own is not None else None
        attacker_traits = self._traits(attacker)
        targets: list[PrizeTarget] = []
        for zone, pokemon in [("active", opponent.active)] + [
            ("bench", item) for item in opponent.bench
        ]:
            if pokemon is None or pokemon.card_id is None:
                continue
            traits = self._traits(pokemon)
            prevented = self._damage_prevented(
                attacker,
                attacker_traits,
                pokemon,
                traits,
                state,
            )
            attack_damage = self._best_attack_damage_for_target(attacker, state, pokemon)
            effective_prizes = traits.base_prize_value
            if traits.prevents_prizes_when_ko_by_ex and attacker_traits.has_rule_box:
                effective_prizes = 0
            effective_prizes = max(
                0,
                effective_prizes - self._attached_prize_reduction(pokemon),
            )
            targets.append(
                PrizeTarget(
                    card_id=pokemon.card_id,
                    zone=zone,
                    index=0
                    if zone == "active"
                    else len([target for target in targets if target.zone == "bench"]),
                    hp=pokemon.hp,
                    has_rule_box=traits.has_rule_box,
                    base_prize_value=traits.base_prize_value,
                    effective_prize_value=effective_prizes,
                    reachable_now=not prevented and attack_damage >= pokemon.hp,
                    expected_damage=0 if prevented else attack_damage,
                    damage_prevented=prevented,
                )
            )

        ordered = sorted(
            targets,
            key=lambda target: (
                not target.reachable_now,
                -target.effective_prize_value,
                target.hp,
                target.zone != "active",
                target.index,
            ),
        )
        route: list[PrizeTarget] = []
        collected = 0
        for target in ordered:
            if collected >= prizes_needed:
                break
            route.append(target)
            collected += target.effective_prize_value
        return PrizeMap(prizes_needed, tuple(targets), tuple(route))

    def _traits(self, pokemon: PokemonState | None) -> CardTraits:
        card_id = pokemon.card_id if pokemon is not None else 0
        return self._catalog.get_traits(str(card_id or 0))

    def _best_attack_damage(self, pokemon: PokemonState | None) -> int:
        return self._best_attack_damage_for_target(pokemon, None, None)

    def _best_attack_damage_for_target(
        self,
        pokemon: PokemonState | None,
        state: GameState | None,
        defender: PokemonState | None,
    ) -> int:
        if pokemon is None or pokemon.card_id is None:
            return 0
        card = self._catalog.get_card(str(pokemon.card_id)) or {}
        attacker_type = card.get("energyType")
        damages = []
        for attack_id in card.get("attacks", []):
            attack = self._catalog.get_attack(str(attack_id)) or {}
            damage = attack.get("damage", 0)
            if isinstance(damage, int) and not isinstance(damage, bool):
                damages.append(
                    calculate_damage(
                        damage,
                        attacker_type,
                        self._catalog.get_card(str(defender.card_id)) if defender else None,
                        prevented=bool(
                            state
                            and defender
                            and has_splashing_dodge_protection(state.raw, defender.serial)
                        ),
                    )
                )
        return max(damages, default=0)

    def _damage_prevented(
        self,
        attacker: PokemonState | None,
        attacker_traits: CardTraits,
        defender: PokemonState,
        defender_traits: CardTraits,
        state: GameState,
    ) -> bool:
        if defender_traits.prevents_damage_from_ex and attacker_traits.has_rule_box:
            return True
        if defender_traits.prevents_damage_from_ability and self._has_ability(attacker):
            return True
        if has_splashing_dodge_protection(state.raw, defender.serial):
            return True
        stadium = state.stadium
        stadium_cards = stadium if isinstance(stadium, list) else [stadium]
        for card in stadium_cards:
            card_id = _card_id(card)
            metadata = self._catalog.get_card(str(card_id)) or {}
            text = _card_text(metadata)
            if (
                "prevent all damage" in text
                and "don't have a rule box" in text.replace("’", "'")
                and not defender_traits.has_rule_box
                and attacker_traits.has_rule_box
            ):
                return True
        return False

    def _has_ability(self, pokemon: PokemonState | None) -> bool:
        if pokemon is None or pokemon.card_id is None:
            return False
        card = self._catalog.get_card(str(pokemon.card_id)) or {}
        return bool(card.get("skills"))

    def _attached_prize_reduction(self, pokemon: PokemonState) -> int:
        reduction = 0
        attached_energies = pokemon.energy_card_ids if pokemon.energy_card_ids else pokemon.energies
        for card in [*pokemon.tool_ids, *attached_energies]:
            card_id = _card_id(card)
            reduction += self._catalog.get_traits(str(card_id)).prize_reduction_when_ko
            metadata = self._catalog.get_card(str(card_id)) or {}
            text = " ".join(
                str(metadata.get(key, "")) for key in ("name", "text", "effect")
            ).casefold()
            if "legacy energy" in text:
                reduction += 1
        return reduction


def _probabilistic_availability(
    card_id: int,
    total_count: int,
    hidden_count: int,
    deck_count: int,
    prize_count: int,
) -> CardAvailability:
    hidden_total = deck_count + prize_count
    prized_min = max(0, hidden_count - deck_count)
    prized_max = min(hidden_count, prize_count)
    prized_expected = hidden_count * prize_count / hidden_total if hidden_total else 0.0
    searchable_expected = hidden_count - prized_expected
    probability = 0.0
    if hidden_count and prize_count and hidden_total:
        no_prized = (
            math.comb(hidden_total - hidden_count, prize_count)
            / math.comb(hidden_total, prize_count)
            if hidden_total - hidden_count >= prize_count
            else 0.0
        )
        probability = 1.0 - no_prized
    return CardAvailability(
        card_id=card_id,
        total_count=total_count,
        searchable_min=max(0, hidden_count - prize_count),
        searchable_max=min(hidden_count, deck_count),
        searchable_expected=searchable_expected,
        prized_min=prized_min,
        prized_max=prized_max,
        prized_expected=prized_expected,
        probability_at_least_one_prized=probability,
    )


def _count_player_cards(player: Mapping[str, Any], *, include_prize: bool) -> Counter[int]:
    result: Counter[int] = Counter()
    for zone in ("hand", "discard", "active", "bench"):
        result.update(_count_cards(player.get(zone)))
    if include_prize:
        result.update(_count_cards(player.get("prize")))
    return result


def _count_known_cards(
    observation: Mapping[str, Any],
    player: Mapping[str, Any],
    your_index: int,
    *,
    include_prize: bool,
) -> Counter[int]:
    roots: list[Any] = [
        player.get("hand"),
        player.get("discard"),
        player.get("active"),
        player.get("bench"),
    ]
    if include_prize:
        roots.append(player.get("prize"))
    current = observation.get("current")
    if isinstance(current, Mapping):
        roots.extend((current.get("stadium"), current.get("looking")))
    select = observation.get("select")
    if isinstance(select, Mapping):
        roots.extend((select.get("effect"), select.get("contextCard")))

    result: Counter[int] = Counter()
    seen_serials: set[tuple[int, int]] = set()
    for root in roots:
        for card in _iter_card_objects(root):
            owner = _int(card.get("playerIndex"))
            if "playerIndex" in card and owner != your_index:
                continue
            card_id = _card_id(card)
            if not card_id:
                continue
            serial = _int(card.get("serial"))
            key = (owner, serial)
            if serial and key in seen_serials:
                continue
            if serial:
                seen_serials.add(key)
            result[card_id] += 1
    return result


def _iter_card_objects(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        if _card_id(value):
            yield value
        for child_zone in ("energyCards", "tools", "preEvolution", "preEvolutions"):
            yield from _iter_card_objects(value.get(child_zone))
    elif isinstance(value, list):
        for item in value:
            yield from _iter_card_objects(item)


def _count_cards(cards: Any) -> Counter[int]:
    result: Counter[int] = Counter()
    values: Sequence[Any] = cards if isinstance(cards, list) else [cards]
    for card in values:
        card_id = _card_id(card)
        if card_id:
            result[card_id] += 1
        if isinstance(card, Mapping):
            for child_zone in ("energyCards", "tools", "preEvolution", "preEvolutions"):
                result.update(_count_cards(card.get(child_zone)))
    return result


def _counter_violations(expected: Counter[int], observed: Counter[int]) -> list[str]:
    return [
        f"card_count:{card_id}" for card_id, count in observed.items() if count > expected[card_id]
    ]


def _card_id(card: Any) -> int:
    if isinstance(card, int) and not isinstance(card, bool):
        return card
    if not isinstance(card, Mapping):
        try:
            return int(card)
        except (TypeError, ValueError):
            return 0
    value = card.get("id", card.get("cardId", 0))
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _card_text(card: Mapping[str, Any]) -> str:
    return " ".join(
        str(skill.get("text", "")) for skill in card.get("skills", []) if isinstance(skill, Mapping)
    ).casefold()


def _int(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _player(state: GameState, index: int) -> Any:
    return state.players[index] if 0 <= index < len(state.players) else None
