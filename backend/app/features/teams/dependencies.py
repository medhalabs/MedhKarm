from functools import lru_cache

from app.features.teams.loader import load_templates
from app.features.teams.service import TeamService


@lru_cache
def get_team_service() -> TeamService:
    """Templates are read once per process; restart to pick up edits."""
    return TeamService(load_templates())
