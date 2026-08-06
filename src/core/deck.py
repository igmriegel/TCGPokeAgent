"""Deck definitions and declarative strategy profiles."""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .catalog import CardCatalog


@dataclass(frozen=True, slots=True)
class AttackPlan:
    """Describe one deck-specific attack without embedding it in policy code."""

    attack_id: int
    name: str
    energy_cost: int
    guaranteed_damage: int = 0
    potential_damage: int = 0
    requires_guaranteed_ko: bool = False
    previous_attack_id: int | None = None
    damage_per_basic_energy_in_discard: int = 0
    basic_energy_role: str = "basic_energy"
    returns_basic_energy_from_discard: bool = False

    @classmethod
    def from_dict(cls, attack_id: int, data: Mapping[str, Any]) -> AttackPlan:
        """Parse one attack plan mapping.

        Args:
            attack_id: Canonical attack identifier.
            data: Declarative attack attributes.

        Returns:
            Validated immutable attack plan.
        """
        previous = data.get("previous_attack_id")
        return cls(
            attack_id=attack_id,
            name=str(data.get("name", "")),
            energy_cost=max(0, int(data.get("energy_cost", 0))),
            guaranteed_damage=max(0, int(data.get("guaranteed_damage", 0))),
            potential_damage=max(0, int(data.get("potential_damage", 0))),
            requires_guaranteed_ko=bool(data.get("requires_guaranteed_ko", False)),
            previous_attack_id=(
                int(previous)
                if isinstance(previous, (int, str))
                and not isinstance(previous, bool)
                and str(previous).isdigit()
                else None
            ),
            damage_per_basic_energy_in_discard=max(
                0, int(data.get("damage_per_basic_energy_in_discard", 0))
            ),
            basic_energy_role=str(data.get("basic_energy_role", "basic_energy")),
            returns_basic_energy_from_discard=bool(
                data.get("returns_basic_energy_from_discard", False)
            ),
        )


@dataclass(frozen=True, slots=True)
class DeckDefinition:
    """Identify an immutable deck independently from its card order."""

    card_ids: tuple[int, ...]
    deck_id: str
    sha256: str

    @classmethod
    def from_path(cls, path: str | Path, deck_id: str | None = None) -> DeckDefinition:
        """Load and validate a 60-card deck.

        Args:
            path: Text file containing one card identifier per line.
            deck_id: Optional stable identifier. The filename stem is used by default.

        Returns:
            Validated immutable deck definition.
        """
        deck_path = Path(path)
        cards = tuple(
            int(line.strip())
            for line in deck_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        return cls.from_cards(cards, deck_id or deck_path.stem)

    @classmethod
    def from_cards(cls, cards: tuple[int, ...] | list[int], deck_id: str) -> DeckDefinition:
        """Create a deck definition from card identifiers.

        Args:
            cards: Exactly 60 positive card identifiers.
            deck_id: Stable human-readable identifier.

        Returns:
            Validated immutable deck definition.
        """
        normalized = tuple(int(card) for card in cards)
        if len(normalized) != 60:
            raise ValueError(f"deck has {len(normalized)} cards, expected 60")
        if any(card <= 0 for card in normalized):
            raise ValueError("deck card identifiers must be positive")
        canonical = "\n".join(str(card) for card in sorted(normalized)).encode()
        return cls(normalized, deck_id, hashlib.sha256(canonical).hexdigest())

    @property
    def counts(self) -> Counter[int]:
        """Return card multiplicities."""
        return Counter(self.card_ids)


@dataclass(frozen=True, slots=True)
class DeckProfile:
    """Describe strategic card roles without adding deck-specific policy code."""

    deck_id: str
    deck_sha256: str
    schema_version: str = "v1"
    roles: Mapping[str, tuple[int, ...]] = field(default_factory=dict)
    evolution_lines: tuple[tuple[int, ...], ...] = ()
    attack_energy_targets: Mapping[int, int] = field(default_factory=dict)
    attack_plans: Mapping[int, AttackPlan] = field(default_factory=dict)
    board_targets: Mapping[str, int] = field(default_factory=dict)
    resource_values: Mapping[int, float] = field(default_factory=dict)
    prize_values: Mapping[int, int] = field(default_factory=dict)
    basic_energy_count: int = 0
    discard_priority: tuple[str, ...] = ()
    promotion_priority: tuple[str, ...] = ()
    bench_priority: tuple[str, ...] = ()
    prize_priority: tuple[str, ...] = ()
    strategic_context: Mapping[str, Any] = field(default_factory=dict)

    def cards_for_role(self, role: str) -> tuple[int, ...]:
        """Return cards assigned to a semantic role.

        Args:
            role: Role such as ``primary_attacker`` or ``support``.

        Returns:
            Stable tuple of card identifiers.
        """
        return tuple(self.roles.get(role, ()))

    def has_role(self, card_id: int, role: str) -> bool:
        """Return whether a card has a declared role."""
        return card_id in self.cards_for_role(role)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DeckProfile:
        """Parse a profile mapping."""
        roles = {
            str(name): tuple(int(card) for card in cards)
            for name, cards in dict(data.get("roles", {})).items()
        }
        return cls(
            deck_id=str(data.get("deck_id", "")),
            deck_sha256=str(data.get("deck_sha256", "")),
            schema_version=str(data.get("schema_version", "v1")),
            roles=roles,
            evolution_lines=tuple(
                tuple(int(card) for card in line) for line in data.get("evolution_lines", ())
            ),
            attack_energy_targets={
                int(card): int(value)
                for card, value in dict(data.get("attack_energy_targets", {})).items()
            },
            attack_plans={
                int(attack_id): AttackPlan.from_dict(int(attack_id), attributes)
                for attack_id, attributes in dict(data.get("attack_plans", {})).items()
                if isinstance(attributes, Mapping)
            },
            board_targets={
                str(name): int(value) for name, value in dict(data.get("board_targets", {})).items()
            },
            resource_values={
                int(card): float(value)
                for card, value in dict(data.get("resource_values", {})).items()
            },
            prize_values={
                int(card): int(value) for card, value in dict(data.get("prize_values", {})).items()
            },
            basic_energy_count=max(0, int(data.get("basic_energy_count", 0))),
            discard_priority=tuple(str(value) for value in data.get("discard_priority", ())),
            promotion_priority=tuple(str(value) for value in data.get("promotion_priority", ())),
            bench_priority=tuple(str(value) for value in data.get("bench_priority", ())),
            prize_priority=tuple(str(value) for value in data.get("prize_priority", ())),
            strategic_context=dict(data.get("strategic_context", {})),
        )

    @classmethod
    def from_path(cls, path: str | Path) -> DeckProfile:
        """Load a YAML deck profile."""
        import yaml

        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        if not isinstance(data, Mapping):
            raise ValueError("deck profile must be a mapping")
        return cls.from_dict(data)


class GenericDeckProfileBuilder:
    """Infer safe, generic roles from deck composition and card metadata."""

    def __init__(self, catalog: CardCatalog) -> None:
        self._catalog = catalog

    def build(self, deck: DeckDefinition) -> DeckProfile:
        """Build a deterministic fallback profile.

        Args:
            deck: Active deck.

        Returns:
            Profile based only on catalog traits.
        """
        pokemon: list[int] = []
        attackers: list[int] = []
        support: list[int] = []
        evolution_by_name: dict[str, int] = {}
        evolution_lines: list[tuple[int, ...]] = []
        attack_energy_targets: dict[int, int] = {}
        attack_plans: dict[int, AttackPlan] = {}
        resource_values: dict[int, float] = {}
        prize_values: dict[int, int] = {}
        basic_energy_count = 0

        for card_id in sorted(deck.counts):
            card = self._catalog.get_card(str(card_id)) or {}
            if int(card.get("cardType", -1)) == 5 and int(card.get("energyType", 0)) == 3:
                basic_energy_count += deck.counts[card_id]
            if int(card.get("cardType", -1)) != 0:
                resource_values[card_id] = 80.0
                continue
            pokemon.append(card_id)
            name = str(card.get("name", ""))
            if name:
                evolution_by_name[name] = card_id
            attacks = card.get("attacks", [])
            if isinstance(attacks, list) and attacks:
                attackers.append(card_id)
                costs = []
                for attack_id in attacks:
                    attack = self._catalog.get_attack(str(attack_id)) or {}
                    energies = attack.get("energies", [])
                    if isinstance(energies, list):
                        costs.append(len(energies))
                    damage = attack.get("damage", 0)
                    guaranteed_damage = (
                        damage if isinstance(damage, int) and not isinstance(damage, bool) else 0
                    )
                    attack_plans[int(attack_id)] = AttackPlan(
                        attack_id=int(attack_id),
                        name=str(attack.get("name", "")),
                        energy_cost=len(energies) if isinstance(energies, list) else 0,
                        guaranteed_damage=max(0, guaranteed_damage),
                        potential_damage=max(0, guaranteed_damage),
                    )
                attack_energy_targets[card_id] = min(costs) if costs else 1
            elif card.get("skills"):
                support.append(card_id)
            traits = self._catalog.get_traits(str(card_id))
            resource_values[card_id] = 100.0 + traits.base_prize_value * 10.0
            prize_values[card_id] = traits.base_prize_value

        for card_id in pokemon:
            card = self._catalog.get_card(str(card_id)) or {}
            parent = evolution_by_name.get(str(card.get("evolvesFrom", "")))
            if parent is not None:
                evolution_lines.append((parent, card_id))

        return DeckProfile(
            deck_id=deck.deck_id,
            deck_sha256=deck.sha256,
            roles={
                "pokemon": tuple(pokemon),
                "attacker": tuple(attackers),
                "primary_attacker": tuple(
                    sorted(
                        attackers,
                        key=lambda card_id: (
                            -self._catalog.get_traits(str(card_id)).base_prize_value,
                            card_id,
                        ),
                    )
                ),
                "support": tuple(support),
            },
            evolution_lines=tuple(sorted(evolution_lines)),
            attack_energy_targets=attack_energy_targets,
            attack_plans=attack_plans,
            board_targets={"minimum_attackers": 2, "reserved_bench_slots": 1},
            resource_values=resource_values,
            prize_values=prize_values,
            basic_energy_count=basic_energy_count,
            discard_priority=(
                "basic_energy",
                "redundant_resource",
                "duplicate_pokemon",
                "protected_resource",
            ),
            promotion_priority=("ready_attacker", "lowest_ko_risk", "lowest_prize_value"),
            bench_priority=("attacker", "evolution_basic"),
            prize_priority=("guaranteed_win", "highest_prize_ko", "lowest_effort"),
        )
