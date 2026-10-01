import inventory
from inventory import Inventory, Item
from inventory.models import Item as ModelItem
from inventory.store import Inventory as StoreInventory


def test_is_a_package():
    assert hasattr(inventory, "__path__")


def test_reexports_are_the_same_classes():
    assert Inventory is StoreInventory
    assert Item is ModelItem


def test_behaviour_unchanged():
    inv = Inventory()
    inv.add_item("A1", "Shampoo", 120.0, 10)
    assert inv.sell("A1", 2) == 240.0
    assert isinstance(inv.get("A1"), Item)
