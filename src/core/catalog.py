from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


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
