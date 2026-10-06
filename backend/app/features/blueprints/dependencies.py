from app.core.config import get_settings
from app.core.database import session_factory
from app.features.blueprints.repository import SqlBlueprintRepository
from app.features.blueprints.service import BlueprintService
from app.features.jobs.dependencies import get_job_queue
from app.features.runs.dependencies import get_run_service


def get_blueprint_service() -> BlueprintService:
    return BlueprintService(
        SqlBlueprintRepository(session_factory),
        get_job_queue(),
        get_run_service(),
        max_attempts=get_settings().build_max_attempts,
    )
