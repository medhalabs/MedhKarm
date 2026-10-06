import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import register_error_handlers
from app.features.teams.exceptions import TemplateNotFoundError
from app.features.teams.loader import load_templates
from app.features.teams.router import router
from app.features.teams.service import TeamService


def service() -> TeamService:
    return TeamService(load_templates())


def test_list_shows_active_roles_only() -> None:
    [software] = service().list_templates()

    assert software.id == "software"
    assert software.roles == [
        "Product Manager",
        "CTO",
        "Developer",
        "QA engineer",
        "Security engineer",
        "DevOps",
        "Documentation",
    ]


def test_unknown_template() -> None:
    with pytest.raises(TemplateNotFoundError):
        service().get_template("nope")


def test_assemble_default_team() -> None:
    team = service().assemble("software")

    assert [(m.role, m.name) for m in team.members] == [
        ("pm", "Mira"),
        ("cto", "Kabir"),
        ("developer", "Isha"),
        ("qa", "Tara"),
        ("security", "Vikram"),
        ("devops", "Neel"),
        ("docs", "Lekha"),
    ]


def test_assemble_caps_counts_at_max() -> None:
    team = service().assemble("software", {"developer": 7})

    assert [m.name for m in team.members if m.role == "developer"] == ["Isha", "Arjun", "Ravi"]


def client() -> TestClient:
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router)
    return TestClient(app)


def test_api_lists_and_fetches_templates() -> None:
    c = client()

    assert [t["id"] for t in c.get("/teams/templates").json()] == ["software"]
    template = c.get("/teams/templates/software").json()
    assert template["workflow"] == "build_app"
    assert len(template["roles"]) == 7
    members = c.get("/teams/templates/software/team").json()["members"]
    assert [m["name"] for m in members] == [
        "Mira",
        "Kabir",
        "Isha",
        "Tara",
        "Vikram",
        "Neel",
        "Lekha",
    ]


def test_api_unknown_template_is_404() -> None:
    response = client().get("/teams/templates/nope")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "team_template_not_found"
