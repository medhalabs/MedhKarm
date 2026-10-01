from app.core.errors import AppError, NotFoundError


class InvalidTemplateError(AppError):
    status_code = 500
    code = "invalid_team_template"


class TemplateNotFoundError(NotFoundError):
    code = "team_template_not_found"
