from app.features.intake.service import IntakeService
from app.features.model_settings.dependencies import get_model_settings_service
from app.features.model_settings.routed import CompanyRoutedProvider
from app.features.teams.dependencies import get_team_service


def get_intake_service() -> IntakeService:
    """The CTO's model (the founder's own choice and key, when set) and name."""
    cto = get_team_service().get_template("software").role("cto")
    llm = CompanyRoutedProvider(get_model_settings_service(), "cto", cto.model)
    return IntakeService(llm, cto.display_names[0])


def get_project_intake_service() -> IntakeService:
    """The PM's model (the founder's own choice and key, when set) and name."""
    pm = get_team_service().get_template("software").role("pm")
    llm = CompanyRoutedProvider(get_model_settings_service(), "pm", pm.model)
    return IntakeService(llm, pm.display_names[0])
