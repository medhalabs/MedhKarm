from app.features.blueprints.dependencies import get_blueprint_service
from app.features.inbox.service import InboxService
from app.features.messages.dependencies import get_message_service
from app.features.projects.dependencies import get_project_service
from app.features.runs.dependencies import get_run_service


def get_inbox_service() -> InboxService:
    return InboxService(
        get_run_service(),
        get_project_service(),
        get_message_service(),
        get_blueprint_service(),
    )
