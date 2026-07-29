from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

_all_attack: Callable[[], list[Any]] | None
_all_card_data: Callable[[], list[Any]] | None
try:
    from cg.api import all_attack as _all_attack
    from cg.api import all_card_data as _all_card_data
except (ImportError, OSError):
    _all_attack = None
    _all_card_data = None


@dataclass(frozen=True, slots=True)
class CardTraits:
    """Normalized strategic traits derived from canonical card metadata."""

    card_id: int
    is_pokemon: bool
    has_rule_box: bool
    is_ex: bool
    is_mega_ex: bool
    is_tera: bool
    base_prize_value: int
    prevents_damage_from_ex: bool = False
    prevents_damage_from_ability: bool = False
    prevents_prizes_when_ko_by_ex: bool = False
    prize_reduction_when_ko: int = 0


class CardCatalog:
    _cards: dict[str, dict[str, Any]] | None = None
    _attacks: dict[str, dict[str, Any]] | None = None

    @classmethod
    def from_csv(cls, path: str | Path) -> "CardCatalog":
        """Load the English card catalog exported by the competition."""
        catalog = cls()
        with Path(path).open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        catalog.load_cards(rows)
        attacks = [
            {
                "id": f"{row.get('Card ID', '')}:{row.get('Move Name', '')}",
                **row,
            }
            for row in rows
            if row.get("Move Name")
        ]
        catalog.load_attacks(attacks)
        return catalog

    @classmethod
    def from_cg(cls) -> "CardCatalog":
        """Load the canonical card and attack metadata bundled with the CABT SDK."""
        catalog = cls()
        if _all_card_data is None or _all_attack is None:
            return catalog
        catalog.load_cards([{"id": card.cardId, **asdict(card)} for card in _all_card_data()])
        catalog.load_attacks(
            [{"id": attack.attackId, **asdict(attack)} for attack in _all_attack()]
        )
        return catalog

    def load_cards(self, cards: list[dict[str, Any]]) -> None:
        self._cards = {str(c.get("id", c.get("Card ID", ""))): c for c in cards}

    def load_attacks(self, attacks: list[dict[str, Any]]) -> None:
        self._attacks = {str(a.get("id", "")): a for a in attacks}

    def get_card(self, card_id: str) -> dict[str, Any] | None:
        if self._cards is None:
            return None
        return self._cards.get(str(card_id))

    def get_attack(self, attack_id: str) -> dict[str, Any] | None:
        if self._attacks is None:
            return None
        return self._attacks.get(str(attack_id))

    def get_traits(self, card_id: str | int) -> CardTraits:
        """Return safe strategic traits for a card.

        Args:
            card_id: Canonical card identifier.

        Returns:
            Derived traits. Unknown cards return conservative defaults.
        """
        card = self.get_card(str(card_id)) or {}
        numeric_id = int(card_id) if str(card_id).isdigit() else 0
        is_pokemon = int(card.get("cardType", -1)) == 0
        is_mega_ex = bool(card.get("megaEx", False))
        is_ex = bool(card.get("ex", False))
        has_rule_box = is_pokemon and (is_ex or is_mega_ex)
        text = " ".join(
            str(skill.get("text", ""))
            for skill in card.get("skills", [])
            if isinstance(skill, dict)
        ).casefold()
        prevents_all = "prevent all damage" in text
        return CardTraits(
            card_id=numeric_id,
            is_pokemon=is_pokemon,
            has_rule_box=has_rule_box,
            is_ex=is_ex,
            is_mega_ex=is_mega_ex,
            is_tera=bool(card.get("tera", False)),
            base_prize_value=3 if is_mega_ex else 2 if is_ex else 1 if is_pokemon else 0,
            prevents_damage_from_ex=prevents_all
            and ("pokémon {ex}" in text or "pokemon {ex}" in text),
            prevents_damage_from_ability=prevents_all and "have an ability" in text,
            prevents_prizes_when_ko_by_ex=(
                "can't take any prize" in text or "can’t take any prize" in text
            )
            and ("pokémon {ex}" in text or "pokemon {ex}" in text),
            prize_reduction_when_ko=1 if "takes 1 fewer prize card" in text else 0,
        )

    @property
    def loaded(self) -> bool:
        return self._cards is not None
