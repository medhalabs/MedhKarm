from app.core.config import get_settings
from app.core.database import session_factory
from app.features.jobs.dependencies import get_job_queue
from app.features.runs.repository import SqlRunRepository
from app.features.runs.service import RunService


def get_run_service() -> RunService:
    return RunService(
        SqlRunRepository(session_factory),
        get_job_queue(),
        max_attempts=get_settings().build_max_attempts,
    )
