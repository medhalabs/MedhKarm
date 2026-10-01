import pytest

from inventory import Inventory


def make():
    inv = Inventory()
    inv.add_item("C3", "Clip", 5.0, 2)
    inv.add_item("A1", "Shampoo", 120.0, 5)
    inv.add_item("B2", "Comb", 35.5, 0)
    inv.add_item("D4", "Gel", 80.0, 9)
    return inv


def test_default_threshold_is_five_and_strict():
    assert make().low_stock() == ["B2", "C3"]


def test_custom_threshold():
    assert make().low_stock(10) == ["A1", "B2", "C3", "D4"]
    assert make().low_stock(0) == []


def test_negative_threshold_rejected():
    with pytest.raises(ValueError):
        make().low_stock(-1)
