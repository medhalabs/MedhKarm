from app.core.config import get_settings
from app.features.intake.service import IntakeService
from app.features.models.service import build_provider
from app.features.teams.dependencies import get_team_service


def get_intake_service() -> IntakeService:
    """The CTO's own model and name, from the software team's template."""
    cto = get_team_service().get_template("software").role("cto")
    return IntakeService(build_provider(get_settings(), cto.model), cto.display_names[0])


def get_project_intake_service() -> IntakeService:
    """The PM's own model and name, from the software team's template."""
    pm = get_team_service().get_template("software").role("pm")
    return IntakeService(build_provider(get_settings(), pm.model), pm.display_names[0])
