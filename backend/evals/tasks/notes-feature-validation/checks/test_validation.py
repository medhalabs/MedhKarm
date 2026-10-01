from fastapi.testclient import TestClient

from app import create_app


def seeded(*titles_and_bodies):
    c = TestClient(create_app())
    for title, body in titles_and_bodies:
        assert c.post("/notes", json={"title": title, "body": body}).status_code == 201
    return c


import pytest


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 101},
        {"title": "ok", "body": "b" * 5001},
    ],
)
def test_invalid_input_is_422(payload):
    assert seeded().post("/notes", json=payload).status_code == 422


def test_limits_are_inclusive():
    r = seeded().post("/notes", json={"title": "x" * 100, "body": "b" * 5000})
    assert r.status_code == 201


def test_title_is_trimmed():
    r = seeded().post("/notes", json={"title": "  Groceries  "})
    assert r.json()["title"] == "Groceries"
