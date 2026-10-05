"""Creates the FastAPI app and registers every feature's router."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.features.auth.dependencies import get_current_user
from app.features.auth.router import router as auth_router
from app.features.events.router import router as events_router
from app.features.health.router import router as health_router
from app.features.inbox.router import router as inbox_router
from app.features.intake.router import router as intake_router
from app.features.integrations.router import router as integrations_router
from app.features.messages.router import router as messages_router
from app.features.notifications.router import router as notifications_router
from app.features.projects.router import router as projects_router
from app.features.runs.router import router as runs_router
from app.features.standups.router import router as standups_router
from app.features.starters.router import router as starters_router
from app.features.teams.router import router as teams_router


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)

    # Feature routers — add one line per feature.
    signed_in = [Depends(get_current_user)]  # catalogs: any signed-in founder may read them
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(projects_router)
    app.include_router(runs_router)
    app.include_router(events_router)
    app.include_router(teams_router, dependencies=signed_in)
    app.include_router(standups_router)
    app.include_router(integrations_router, dependencies=signed_in)
    app.include_router(starters_router, dependencies=signed_in)
    app.include_router(inbox_router)
    app.include_router(messages_router)
    app.include_router(notifications_router)
    app.include_router(intake_router)

    return app


app = create_app()
