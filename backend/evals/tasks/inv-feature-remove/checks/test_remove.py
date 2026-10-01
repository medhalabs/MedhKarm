import pytest

from inventory import Inventory


def test_remove_returns_item_and_deletes_it():
    inv = Inventory()
    inv.add_item("A1", "Shampoo", 120.0, 10)
    removed = inv.remove_item("A1")
    assert removed.sku == "A1"
    assert inv.items() == []
    with pytest.raises(KeyError):
        inv.get("A1")


def test_remove_unknown_raises_key_error():
    with pytest.raises(KeyError):
        Inventory().remove_item("nope")


def test_can_add_again_after_remove():
    inv = Inventory()
    inv.add_item("A1", "Shampoo", 120.0)
    inv.remove_item("A1")
    inv.add_item("A1", "Shampoo v2", 130.0)
    assert inv.get("A1").name == "Shampoo v2"
