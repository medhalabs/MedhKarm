from app.core.database import session_factory
from app.features.artifacts.dependencies import get_artifact_service
from app.features.events.dependencies import get_event_store
from app.features.runs.dependencies import get_run_service
from app.features.shares.repository import SqlShareRepository
from app.features.shares.schemas import PublicMember
from app.features.shares.service import ShareService
from app.features.teams.dependencies import get_team_service
from app.shared.rate_limit import RateLimiter

# 60 opens a minute from one address: plenty for people, not for a script
public_views = RateLimiter(limit=60, seconds=60)


class TeamRoster:
    def members(self) -> list[PublicMember]:
        template = get_team_service().get_template("software")
        return [
            PublicMember(role=r.id, title=r.title, name=name)
            for r in template.roles
            for name in r.display_names
        ]


def get_share_service() -> ShareService:
    return ShareService(
        SqlShareRepository(session_factory),
        get_run_service(),
        get_event_store(),
        get_artifact_service(),
        TeamRoster(),
    )
