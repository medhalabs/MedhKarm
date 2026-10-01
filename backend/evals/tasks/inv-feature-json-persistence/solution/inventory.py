"""Simple stock tracking for a small shop. Prices are in rupees."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Item:
    sku: str
    name: str
    price: float  # per unit
    quantity: int = 0


class Inventory:
    def __init__(self) -> None:
        self._items: dict[str, Item] = {}

    def add_item(self, sku: str, name: str, price: float, quantity: int = 0) -> Item:
        if sku in self._items:
            raise ValueError(f"Item {sku} already exists")
        if price < 0 or quantity < 0:
            raise ValueError("Price and quantity must not be negative")
        item = Item(sku, name, price, quantity)
        self._items[sku] = item
        return item

    def get(self, sku: str) -> Item:
        return self._items[sku]

    def restock(self, sku: str, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self._items[sku].quantity += amount

    def sell(self, sku: str, amount: int) -> float:
        """Sell `amount` units and return the sale value."""
        item = self._items[sku]
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > item.quantity:
            raise ValueError("Not enough stock")
        item.quantity -= amount
        return round(item.price * amount, 2)

    def total_value(self) -> float:
        """Value of all stock on hand."""
        return sum(item.price for item in self._items.values())

    def save(self, path: str | Path) -> None:
        data = [asdict(item) for item in self.items()]
        Path(path).write_text(json.dumps(data))

    @classmethod
    def load(cls, path: str | Path) -> "Inventory":
        inv = cls()
        for row in json.loads(Path(path).read_text()):
            inv.add_item(row["sku"], row["name"], row["price"], row["quantity"])
        return inv

    def items(self) -> list[Item]:
        return sorted(self._items.values(), key=lambda item: item.sku)
