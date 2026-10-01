"""Team templates: list them, fetch one, and assemble a team from one."""

from app.features.teams.exceptions import TemplateNotFoundError
from app.features.teams.schemas import Team, TeamMember, TeamTemplate, TemplateSummary


class TeamService:
    def __init__(self, templates: dict[str, TeamTemplate]) -> None:
        self._templates = templates

    def list_templates(self) -> list[TemplateSummary]:
        return [
            TemplateSummary(
                id=t.id,
                name=t.name,
                description=t.description,
                roles=[role.title for role in t.roles if role.active],
            )
            for t in self._templates.values()
        ]

    def get_template(self, template_id: str) -> TeamTemplate:
        if template_id not in self._templates:
            raise TemplateNotFoundError(f"No team template {template_id!r}")
        return self._templates[template_id]

    def assemble(self, template_id: str, counts: dict[str, int] | None = None) -> Team:
        """The team's members: each active role, `count` times (or the requested number,
        capped at the role's max_count), named from its display names in order."""
        template = self.get_template(template_id)
        members: list[TeamMember] = []
        for role in template.roles:
            if not role.active:
                continue
            wanted = (counts or {}).get(role.id, role.count)
            for i in range(max(1, min(wanted, role.max_count))):
                members.append(
                    TeamMember(role=role.id, title=role.title, name=role.display_names[i])
                )
        return Team(template_id=template.id, members=members)
