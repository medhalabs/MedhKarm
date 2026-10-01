from inventory import Inventory


def test_total_uses_quantity():
    inv = Inventory()
    inv.add_item("A1", "Shampoo", 120.0, 10)
    inv.add_item("B2", "Comb", 35.5, 4)
    assert inv.total_value() == 1342.0


def test_zero_quantity_counts_nothing():
    inv = Inventory()
    inv.add_item("A1", "Shampoo", 120.0, 0)
    assert inv.total_value() == 0


def test_empty_inventory():
    assert Inventory().total_value() == 0


def test_rounded_to_two_decimals():
    inv = Inventory()
    inv.add_item("C3", "Clip", 0.1, 3)
    assert inv.total_value() == 0.3
