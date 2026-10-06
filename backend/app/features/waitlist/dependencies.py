from app.core.database import session_factory
from app.features.waitlist.repository import SqlWaitlistRepository
from app.features.waitlist.service import WaitlistService
from app.shared.rate_limit import RateLimiter

# Five sign-ups an hour from one address: a person needs one
joins = RateLimiter(limit=5, seconds=3600)


def get_waitlist_service() -> WaitlistService:
    return WaitlistService(SqlWaitlistRepository(session_factory))
