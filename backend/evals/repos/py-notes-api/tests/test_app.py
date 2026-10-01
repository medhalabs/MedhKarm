from fastapi.testclient import TestClient

from app import create_app


def client() -> TestClient:
    return TestClient(create_app())


def test_create_and_get():
    c = client()
    created = c.post("/notes", json={"title": "Groceries", "body": "milk"}).json()
    assert created["id"] == 1
    assert c.get("/notes/1").json()["title"] == "Groceries"


def test_list_sorted_by_id():
    c = client()
    c.post("/notes", json={"title": "A"})
    c.post("/notes", json={"title": "B"})
    assert [n["title"] for n in c.get("/notes").json()] == ["A", "B"]


def test_missing_note_is_404():
    assert client().get("/notes/42").status_code == 404


def test_delete():
    c = client()
    c.post("/notes", json={"title": "A"})
    assert c.delete("/notes/1").status_code == 204
    assert c.get("/notes/1").status_code == 404
