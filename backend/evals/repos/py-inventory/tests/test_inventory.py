import pytest

from inventory import Inventory


def make() -> Inventory:
    inv = Inventory()
    inv.add_item("A1", "Shampoo", 120.0, 10)
    inv.add_item("B2", "Comb", 35.5, 4)
    return inv


def test_add_and_get():
    inv = make()
    assert inv.get("A1").name == "Shampoo"


def test_duplicate_sku_rejected():
    inv = make()
    with pytest.raises(ValueError):
        inv.add_item("A1", "Other", 1.0)


def test_sell_reduces_stock_and_returns_value():
    inv = make()
    assert inv.sell("B2", 2) == 71.0
    assert inv.get("B2").quantity == 2


def test_cannot_oversell():
    inv = make()
    with pytest.raises(ValueError):
        inv.sell("B2", 5)


def test_restock():
    inv = make()
    inv.restock("A1", 5)
    assert inv.get("A1").quantity == 15


def test_items_sorted_by_sku():
    inv = make()
    assert [item.sku for item in inv.items()] == ["A1", "B2"]
