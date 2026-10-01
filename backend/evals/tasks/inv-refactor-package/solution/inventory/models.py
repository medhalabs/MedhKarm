"""Inventory data model."""

from dataclasses import dataclass


@dataclass
class Item:
    sku: str
    name: str
    price: float  # per unit
    quantity: int = 0
