from functools import cache

from app.features.starters.catalog import FileCatalog
from app.features.starters.service import StarterService


@cache
def get_starter_service() -> StarterService:
    return StarterService(FileCatalog())
