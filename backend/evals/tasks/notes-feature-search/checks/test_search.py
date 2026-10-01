from fastapi.testclient import TestClient

from app import create_app


def seeded(*titles_and_bodies):
    c = TestClient(create_app())
    for title, body in titles_and_bodies:
        assert c.post("/notes", json={"title": title, "body": body}).status_code == 201
    return c


def test_matches_title_or_body_ignoring_case():
    c = seeded(("Groceries", "Milk and eggs"), ("Work", "send invoice"), ("milk tea", ""))
    assert [n["id"] for n in c.get("/notes", params={"q": "MILK"}).json()] == [1, 3]
    assert [n["id"] for n in c.get("/notes", params={"q": "invoice"}).json()] == [2]


def test_no_match():
    assert seeded(("A", "b")).get("/notes", params={"q": "zzz"}).json() == []


def test_without_or_empty_q_returns_all():
    c = seeded(("A", ""), ("B", ""))
    assert len(c.get("/notes").json()) == 2
    assert len(c.get("/notes", params={"q": ""}).json()) == 2
