from app.core.database import session_factory
from app.features.events.dependencies import get_event_store
from app.features.jobs.dependencies import get_job_queue
from app.features.messages.owner import ServiceOwner
from app.features.messages.repository import SqlMessageRepository
from app.features.messages.service import MessageService
from app.features.projects.dependencies import get_project_service
from app.features.runs.dependencies import get_run_service


def get_message_service() -> MessageService:
    return MessageService(
        SqlMessageRepository(session_factory),
        ServiceOwner(get_run_service(), get_project_service()),
        get_job_queue(),
        get_event_store(),
    )
