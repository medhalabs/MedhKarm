from app.core.database import session_factory
from app.features.events.interfaces import EventStore
from app.features.events.service import EventService
from app.features.events.stores.sql_store import SqlEventStore


def get_event_store() -> EventStore:
    return SqlEventStore(session_factory)


def get_event_service() -> EventService:
    return EventService(get_event_store())
