from app.store import Store
from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    assert TestClient(app).get("/health").json() == {"ok": True}


def test_store_round_trip() -> None:
    store = Store(":memory:")
    note = store.insert("notes", {"title": "Buy milk", "done": False})
    store.insert("notes", {"title": "Call Ravi", "done": True})

    assert store.get("notes", note["id"])["title"] == "Buy milk"
    assert [n["title"] for n in store.find("notes", done=True)] == ["Call Ravi"]
    assert store.update("notes", note["id"], {"done": True})["done"] is True
    assert store.remove("notes", note["id"]) and store.get("notes", note["id"]) is None
