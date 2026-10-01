from fastapi.testclient import TestClient

from app import create_app


def seeded(*titles_and_bodies):
    c = TestClient(create_app())
    for title, body in titles_and_bodies:
        assert c.post("/notes", json={"title": title, "body": body}).status_code == 201
    return c


import pytest


def many(n):
    return seeded(*[(f"N{i}", "") for i in range(1, n + 1)])


def test_defaults_return_first_fifty():
    data = many(60).get("/notes").json()
    assert len(data) == 50
    assert data[0]["id"] == 1


def test_limit_and_offset():
    c = many(10)
    assert [n["id"] for n in c.get("/notes", params={"limit": 3, "offset": 4}).json()] == [5, 6, 7]
    assert [n["id"] for n in c.get("/notes", params={"offset": 8}).json()] == [9, 10]
    assert c.get("/notes", params={"offset": 20}).json() == []


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_out_of_range_is_422(params):
    assert many(1).get("/notes", params=params).status_code == 422


def test_max_limit_allowed():
    assert len(many(3).get("/notes", params={"limit": 100}).json()) == 3
