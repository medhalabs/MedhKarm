from fastapi.testclient import TestClient

from app import create_app


def seeded(*titles_and_bodies):
    c = TestClient(create_app())
    for title, body in titles_and_bodies:
        assert c.post("/notes", json={"title": title, "body": body}).status_code == 201
    return c


def test_patch_title_only_keeps_body():
    c = seeded(("Groceries", "milk"))
    r = c.patch("/notes/1", json={"title": "Shopping"})
    assert r.status_code == 200
    assert r.json() == {"id": 1, "title": "Shopping", "body": "milk"}
    assert c.get("/notes/1").json()["title"] == "Shopping"


def test_patch_body_only_keeps_title():
    c = seeded(("Groceries", "milk"))
    assert c.patch("/notes/1", json={"body": "eggs"}).json() == {
        "id": 1,
        "title": "Groceries",
        "body": "eggs",
    }


def test_patch_both():
    c = seeded(("A", "a"))
    assert c.patch("/notes/1", json={"title": "B", "body": "b"}).json()["body"] == "b"


def test_patch_unknown_is_404():
    assert seeded().patch("/notes/7", json={"title": "x"}).status_code == 404
