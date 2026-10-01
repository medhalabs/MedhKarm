"""Creates the FastAPI app and registers every feature's router."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.features.events.router import router as events_router
from app.features.health.router import router as health_router
from app.features.standups.router import router as standups_router
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
    app.include_router(health_router)
    app.include_router(events_router)
    app.include_router(teams_router)
    app.include_router(standups_router)

    return app


app = create_app()
