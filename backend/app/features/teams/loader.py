"""Reads team templates (`templates/*.toml`) and rejects anything the platform can't run."""

import tomllib
from pathlib import Path

from pydantic import ValidationError

from app.features.approvals.service import policy_problems
from app.features.teams.catalog import KNOWN_CHECKERS, KNOWN_TOOLS, WORKFLOW_FACTS, WORKFLOW_ROLES
from app.features.teams.exceptions import InvalidTemplateError
from app.features.teams.schemas import TeamTemplate

TEMPLATES_DIR = Path(__file__).parent / "templates"


def load_templates(directory: Path = TEMPLATES_DIR) -> dict[str, TeamTemplate]:
    templates: dict[str, TeamTemplate] = {}
    for path in sorted(directory.glob("*.toml")):
        template = parse_template(path.read_text(encoding="utf-8"), source=path.name)
        if template.id in templates:
            raise InvalidTemplateError(f"{path.name}: duplicate template id {template.id!r}")
        templates[template.id] = template
    return templates


def parse_template(text: str, source: str = "template") -> TeamTemplate:
    try:
        template = TeamTemplate.model_validate(tomllib.loads(text))
    except (tomllib.TOMLDecodeError, ValidationError) as exc:
        raise InvalidTemplateError(f"{source}: {exc}") from exc
    problems = _problems(template)
    if problems:
        raise InvalidTemplateError(f"{source}: " + "; ".join(problems))
    return template


def _problems(template: TeamTemplate) -> list[str]:
    problems: list[str] = []
    ids = [role.id for role in template.roles]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        problems.append(f"duplicate roles: {', '.join(duplicates)}")
    if template.workflow not in WORKFLOW_ROLES:
        problems.append(f"unknown workflow {template.workflow!r}")
    else:
        active = {role.id for role in template.roles if role.active}
        missing = sorted(WORKFLOW_ROLES[template.workflow] - active)
        if missing:
            problems.append(
                f"workflow {template.workflow!r} needs active roles: {', '.join(missing)}"
            )
        problems += policy_problems(template.approval, WORKFLOW_FACTS[template.workflow])
    if template.checker not in KNOWN_CHECKERS:
        problems.append(f"unknown checker {template.checker!r}")
    for role in template.roles:
        unknown = sorted(set(role.tools) - KNOWN_TOOLS)
        if unknown:
            problems.append(f"role {role.id}: unknown tools {', '.join(unknown)}")
        if len(role.display_names) < role.max_count:
            problems.append(f"role {role.id}: needs {role.max_count} display names")
    return problems
