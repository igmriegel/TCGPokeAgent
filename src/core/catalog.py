from __future__ import annotations

from typing import Any


class CardCatalog:
    _cards: dict[str, dict[str, Any]] | None = None
    _attacks: dict[str, dict[str, Any]] | None = None

    def load_cards(self, cards: list[dict[str, Any]]) -> None:
        self._cards = {c.get("id", ""): c for c in cards}

    def load_attacks(self, attacks: list[dict[str, Any]]) -> None:
        self._attacks = {a.get("id", ""): a for a in attacks}

    def get_card(self, card_id: str) -> dict[str, Any] | None:
        if self._cards is None:
            return None
        return self._cards.get(card_id)

    def get_attack(self, attack_id: str) -> dict[str, Any] | None:
        if self._attacks is None:
            return None
        return self._attacks.get(attack_id)

    @property
    def loaded(self) -> bool:
        return self._cards is not None
