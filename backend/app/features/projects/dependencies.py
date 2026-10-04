from app.core.config import get_settings
from app.core.database import session_factory
from app.features.jobs.dependencies import get_job_queue
from app.features.projects.progress import BacklogProgress
from app.features.projects.repository import SqlProjectRepository
from app.features.projects.service import ProjectService
from app.features.repos.github import GitHubRepoHost
from app.features.runs.dependencies import get_run_service


def get_project_service() -> ProjectService:
    return ProjectService(SqlProjectRepository(session_factory), get_job_queue())


def get_backlog_progress() -> BacklogProgress:
    settings = get_settings()
    return BacklogProgress(
        SqlProjectRepository(session_factory),
        get_run_service(),
        GitHubRepoHost(settings.github_token),
        settings.standup_timezone,
    )
