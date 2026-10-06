import pytest

from app.features.teams.exceptions import InvalidTemplateError
from app.features.teams.loader import load_templates, parse_template

VALID = """
id = "mini"
name = "Mini team"
description = "Test team"
workflow = "build_app"
checker = "test_command"

[[roles]]
id = "cto"
title = "CTO"
display_names = ["Kabir"]
responsibilities = "Plans"
instructions = "Plan it."

[[roles]]
id = "developer"
title = "Developer"
display_names = ["Isha", "Arjun"]
responsibilities = "Builds"
tools = ["write_file", "run_command"]
max_count = 2

[[roles]]
id = "qa"
title = "QA"
display_names = ["Tara"]
responsibilities = "Checks"
"""


def test_valid_template_parses() -> None:
    template = parse_template(VALID)

    assert template.id == "mini"
    assert template.role("developer").tools == ["write_file", "run_command"]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (
            ('tools = ["write_file", "run_command"]', 'tools = ["write_file", "hack_server"]'),
            "unknown tools hack_server",
        ),
        (('workflow = "build_app"', 'workflow = "make_coffee"'), "unknown workflow"),
        (('checker = "test_command"', 'checker = "vibes"'), "unknown checker"),
        (('id = "qa"', 'id = "cto"'), "duplicate roles: cto"),
        (
            ('display_names = ["Isha", "Arjun"]', 'display_names = ["Isha"]'),
            "needs 2 display names",
        ),
        (
            ('id = "qa"\ntitle = "QA"', 'id = "qa"\ntitle = "QA"\nactive = false'),
            "needs active roles: qa",
        ),
        (("max_count = 2", "count = 3\nmax_count = 2"), "exceeds max_count"),
        (('name = "Mini team"', "name = "), "mini"),  # broken TOML
    ],
)
def test_invalid_templates_are_rejected(change: tuple[str, str], message: str) -> None:
    old, new = change
    with pytest.raises(InvalidTemplateError, match=message):
        parse_template(VALID.replace(old, new), source="mini")


def test_shipped_templates_load() -> None:
    templates = load_templates()

    software = templates["software"]
    assert [r.id for r in software.roles] == [
        "pm",
        "cto",
        "developer",
        "qa",
        "security",
        "devops",
        "docs",
        "design",
        "office",
    ]
    assert [r.id for r in software.roles if not r.active] == []
    assert software.role("developer").max_count == 3


def test_approval_rules_must_use_the_workflows_facts() -> None:
    import pytest

    from app.features.teams.exceptions import InvalidTemplateError
    from app.features.teams.loader import TEMPLATES_DIR, parse_template

    text = (TEMPLATES_DIR / "software.toml").read_text() + (
        '\n[[approval.rules]]\nid = "refunds"\naction = "ask"\nreason = "Big refund."\n'
        'when = [{ fact = "refund_amount", op = "gt", value = 2000 }]\n'
    )

    with pytest.raises(InvalidTemplateError, match="unknown facts refund_amount"):
        parse_template(text)


def test_specialties_must_name_members_once() -> None:
    import pytest

    from app.features.teams.exceptions import InvalidTemplateError
    from app.features.teams.loader import TEMPLATES_DIR, parse_template

    text = (TEMPLATES_DIR / "software.toml").read_text()
    with pytest.raises(InvalidTemplateError, match="unknown members"):
        parse_template(text.replace('names = ["Arjun"]', 'names = ["Zara"]'))
    with pytest.raises(InvalidTemplateError, match="more than one specialty"):
        parse_template(text.replace('names = ["Arjun"]', 'names = ["Arjun", "Isha"]'))
