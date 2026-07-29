from __future__ import annotations

import csv
from dataclasses import asdict
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

    @property
    def loaded(self) -> bool:
        return self._cards is not None
