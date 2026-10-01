import pytest

from inventory import Inventory


def test_round_trip(tmp_path):
    inv = Inventory()
    inv.add_item("A1", "Shampoo", 120.0, 10)
    inv.add_item("B2", "Comb", 35.5, 4)
    path = tmp_path / "stock.json"
    inv.save(path)
    loaded = Inventory.load(path)
    assert [(i.sku, i.name, i.price, i.quantity) for i in loaded.items()] == [
        ("A1", "Shampoo", 120.0, 10),
        ("B2", "Comb", 35.5, 4),
    ]


def test_accepts_string_paths(tmp_path):
    inv = Inventory()
    inv.add_item("A1", "Shampoo", 120.0, 1)
    inv.save(str(tmp_path / "s.json"))
    assert Inventory.load(str(tmp_path / "s.json")).get("A1").quantity == 1


def test_loaded_inventory_is_independent(tmp_path):
    inv = Inventory()
    inv.add_item("A1", "Shampoo", 120.0, 10)
    inv.save(tmp_path / "s.json")
    loaded = Inventory.load(tmp_path / "s.json")
    loaded.sell("A1", 3)
    assert inv.get("A1").quantity == 10


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        Inventory.load(tmp_path / "missing.json")
