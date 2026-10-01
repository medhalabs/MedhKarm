from app.core.errors import AppError


class RepoError(AppError):
    """Cloning, pushing or opening a pull request failed."""

    status_code = 502
    code = "repo_error"
